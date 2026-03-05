"""Tests for .markdownlint.json configuration.

Validates that the git-repo markdownlint configuration is valid and
catches known-bad Markdown patterns in test fixtures.

Spec Reference: Plan: Per-Repo Tooling — .markdownlint.json for Markdown linting.
"""

import os
import subprocess

import pytest


@pytest.mark.unit
def test_markdownlint_config_valid(repo_root):
    """Validate that .markdownlint.json is valid configuration.

    Given: .markdownlint.json exists at repo root
    When: markdownlint is invoked with a clean file
    Then: It does not report a config error
    Spec: Plan: Linter config
    """
    config_path = os.path.join(repo_root, ".markdownlint.json")
    assert os.path.isfile(config_path), (
        f".markdownlint.json must exist at repo root: {config_path}"
    )
    # Run markdownlint on the config-companion doc (or /dev/null)
    # to verify config parses without error
    result = subprocess.run(
        ["markdownlint", "--config", config_path, "--stdin"],
        input="# Valid Heading\n\nSome text.\n",
        capture_output=True,
        text=True,
    )
    assert "Error" not in result.stderr or result.returncode == 0, (
        f"markdownlint config has errors: {result.stderr}"
    )


@pytest.mark.unit
def test_markdownlint_catches_known_bad_md(repo_root):
    """Validate that markdownlint catches errors in known-bad fixture.

    Given: A known-bad Markdown file exists in tests/fixtures/
    When: markdownlint is run against it
    Then: It reports errors and exits non-zero
    Spec: Plan: Linter config
    """
    bad_file = os.path.join(
        repo_root, "tests", "fixtures", "linter-test-bad.md"
    )
    assert os.path.isfile(bad_file), f"Known-bad fixture must exist: {bad_file}"
    config_path = os.path.join(repo_root, ".markdownlint.json")
    # Use --ignore-path /dev/null to override .markdownlintignore
    # which excludes tests/fixtures/ from normal linting
    result = subprocess.run(
        [
            "markdownlint",
            "--config",
            config_path,
            "--ignore-path",
            "/dev/null",
            bad_file,
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, (
        f"markdownlint should report errors on known-bad file, "
        f"stdout: {result.stdout}, stderr: {result.stderr}"
    )
