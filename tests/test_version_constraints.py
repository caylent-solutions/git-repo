# Copyright (C) 2024 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for version_constraints.py — PEP 440 constraint detection and resolution.

Spec references:
- Section 5.5: PEP 440 constraint syntax table, supported types, resolution.
- Section 17.2: Function signatures for is_version_constraint and
  resolve_version_constraint.
"""

import json
import os

import pytest

import error
import version_constraints

_FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _load_fixture():
    """Load version constraint test data from fixture file."""
    fixture_path = os.path.join(_FIXTURES_DIR, "version_constraints_data.json")
    with open(fixture_path) as f:
        return json.load(f)


_DATA = _load_fixture()
_TAG_PREFIX = _DATA["tag_prefix"]
_AVAILABLE_TAGS = tuple(_DATA["resolve"]["available_tags"])

# Build parametrize lists for is_version_constraint True cases.
_CONSTRAINT_TRUE_CASES = []
for suffix in _DATA["is_constraint"]["compatible_release"]:
    _CONSTRAINT_TRUE_CASES.append(
        pytest.param(f"{_TAG_PREFIX}/{suffix}", id=f"compatible-{suffix}")
    )
for entry in _DATA["is_constraint"]["comparison_operators"]:
    _CONSTRAINT_TRUE_CASES.append(
        pytest.param(
            f"{_TAG_PREFIX}/{entry['suffix']}",
            id=f"comparison-{entry['operator']}",
        )
    )
_CONSTRAINT_TRUE_CASES.append(pytest.param(f"{_TAG_PREFIX}/*", id="wildcard"))
for suffix in _DATA["is_constraint"]["range"]:
    _CONSTRAINT_TRUE_CASES.append(
        pytest.param(f"{_TAG_PREFIX}/{suffix}", id=f"range-{suffix}")
    )

# Build parametrize list for is_version_constraint False cases.
_CONSTRAINT_FALSE_CASES = []
for suffix in _DATA["is_constraint"]["exact_pins"]:
    _CONSTRAINT_FALSE_CASES.append(
        pytest.param(f"{_TAG_PREFIX}/{suffix}", id=f"exact-pin-{suffix}")
    )
for rev in _DATA["is_constraint"]["non_prefixed_exact_pins"]:
    _CONSTRAINT_FALSE_CASES.append(pytest.param(rev, id=f"exact-pin-{rev}"))
for rev in _DATA["is_constraint"]["non_constraint_revisions"]:
    _CONSTRAINT_FALSE_CASES.append(
        pytest.param(rev, id=f"non-constraint-{rev}")
    )

# Build parametrize list for resolve happy-path cases.
_RESOLVE_CASES = []
for key in ("patch_compatible", "minor_compatible", "wildcard", "range"):
    case = _DATA["resolve"][key]
    _RESOLVE_CASES.append(
        pytest.param(
            case["constraint"],
            _AVAILABLE_TAGS,
            f"{_TAG_PREFIX}/{case['expected_version']}",
            id=key,
        )
    )
# highest_match uses its own tag list.
_hm = _DATA["resolve"]["highest_match"]
_RESOLVE_CASES.append(
    pytest.param(
        _hm["constraint"],
        tuple(_hm["unsorted_tags"]),
        f"{_TAG_PREFIX}/{_hm['expected_version']}",
        id="highest_match",
    )
)


@pytest.mark.unit
class TestIsVersionConstraint:
    """Tests for is_version_constraint() — PEP 440 operator detection.

    Spec reference: Sections 5.5 and 17.2.

    is_version_constraint() examines the last path component of a revision
    string and returns True when it contains PEP 440 constraint operators
    (~=, >=, <, <=, >, !=, ==, *).
    """

    @pytest.mark.parametrize("revision", _CONSTRAINT_TRUE_CASES)
    def test_spec_5_5_is_constraint_true(self, revision):
        """PEP 440 constraint revisions are detected as constraints.

        Given: Revision string with a PEP 440 operator.
        When: is_version_constraint() is called.
        Then: Returns True.
        Spec: Section 5.5 — constraint detection.
        """
        assert version_constraints.is_version_constraint(revision), (
            f"'{revision}' should be a version constraint"
        )

    @pytest.mark.parametrize("revision", _CONSTRAINT_FALSE_CASES)
    def test_spec_5_5_is_constraint_false(self, revision):
        """Non-constraint revisions are NOT detected as constraints.

        Given: Revision string that is a plain ref, branch, or exact tag.
        When: is_version_constraint() is called.
        Then: Returns False.
        Spec: Section 5.5 — non-constraint revisions.
        """
        assert not version_constraints.is_version_constraint(revision), (
            f"'{revision}' should NOT be a version constraint"
        )


@pytest.mark.unit
class TestResolveVersionConstraint:
    """Tests for resolve_version_constraint() — PEP 440 constraint resolution.

    Spec reference: Sections 5.5 and 17.2.

    resolve_version_constraint() splits a revision into prefix and constraint,
    filters available tags by the prefix, parses versions, evaluates the
    constraint, and returns the full tag name of the highest matching version.
    """

    @pytest.mark.parametrize("constraint,tags,expected", _RESOLVE_CASES)
    def test_spec_5_5_resolve_constraint(self, constraint, tags, expected):
        """Version constraint resolves to the highest matching tag.

        Given: Revision with a PEP 440 constraint and a set of available tags.
        When: resolve_version_constraint() is called.
        Then: Returns the tag for the highest matching version.
        Spec: Section 5.5 — constraint resolution.
        """
        revision = f"{_TAG_PREFIX}/{constraint}"
        result = version_constraints.resolve_version_constraint(
            revision, list(tags)
        )
        assert result == expected, (
            f"{constraint} should resolve to '{expected}', got '{result}'"
        )

    def test_spec_5_5_resolve_no_match_raises_error(self):
        """No matching tags raises ManifestInvalidRevisionError.

        Given: Revision with constraint that matches no available tags.
        When: resolve_version_constraint() is called.
        Then: ManifestInvalidRevisionError is raised.
        Spec: Section 17.2 — error on no match.
        """
        case = _DATA["resolve"]["no_match"]
        revision = f"{_TAG_PREFIX}/{case['constraint']}"
        with pytest.raises(error.ManifestInvalidRevisionError):
            version_constraints.resolve_version_constraint(
                revision, list(_AVAILABLE_TAGS)
            )
