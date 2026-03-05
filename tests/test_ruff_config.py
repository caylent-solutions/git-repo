"""Tests for ruff.toml configuration.

Validates that the git-repo ruff configuration is valid and catches
known-bad Python patterns in test fixtures.

Spec Reference: Plan: Per-Repo Tooling — ruff.toml for Python linting.
"""

import os
import subprocess

import pytest

REPO_ROOT = os.path.join(os.path.dirname(__file__), os.pardir)


@pytest.mark.unit
def test_ruff_config_valid_syntax():
    """Validate that ruff.toml is valid ruff configuration.

    Given: ruff.toml exists at repo root
    When: ruff check is invoked with --config pointing to it
    Then: ruff does not report a config error
    Spec: Plan: Linter config
    """
    config_path = os.path.join(REPO_ROOT, "ruff.toml")
    assert os.path.isfile(config_path), (
        f"ruff.toml must exist at repo root: {config_path}"
    )
    # ruff check on an empty input with the config validates config syntax
    result = subprocess.run(
        ["ruff", "check", "--config", config_path, "--stdin-filename", "test.py"],
        input="",
        capture_output=True,
        text=True,
    )
    assert "Failed to parse" not in result.stderr, (
        f"ruff.toml has invalid syntax: {result.stderr}"
    )


@pytest.mark.unit
def test_ruff_catches_known_bad_python():
    """Validate that ruff catches lint errors in known-bad fixture.

    Given: A known-bad Python file exists in tests/fixtures/
    When: ruff check is run against it with the repo config
    Then: ruff reports errors and exits non-zero
    Spec: Plan: Linter config
    """
    bad_file = os.path.join(REPO_ROOT, "tests", "fixtures", "linter-test-bad.py")
    assert os.path.isfile(bad_file), (
        f"Known-bad fixture must exist: {bad_file}"
    )
    config_path = os.path.join(REPO_ROOT, "ruff.toml")
    result = subprocess.run(
        ["ruff", "check", "--config", config_path, bad_file],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, (
        f"ruff check should report errors on known-bad file, "
        f"stdout: {result.stdout}, stderr: {result.stderr}"
    )
    assert result.stdout.strip(), (
        f"ruff check should produce output describing the errors, "
        f"stderr: {result.stderr}"
    )
