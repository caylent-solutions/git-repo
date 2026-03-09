"""Tests for ruff.toml configuration.

Validates that the git-repo ruff configuration is valid and catches
known-bad Python patterns.
"""

import os
import shutil
import subprocess
import tempfile

import pytest

_REPO_ROOT = os.path.join(os.path.dirname(__file__), os.pardir)
_RUFF_PATH = shutil.which("ruff")


@pytest.mark.unit
def test_ruff_config_valid_syntax():
    """Validate that ruff.toml is valid ruff configuration.

    Given: ruff.toml exists at repo root
    When: ruff check is invoked with --config pointing to it
    Then: ruff does not report a config error
    """
    assert _RUFF_PATH is not None, "ruff is not installed. Install with: pip install ruff"
    config_path = os.path.join(_REPO_ROOT, "ruff.toml")
    assert os.path.isfile(config_path), f"ruff.toml must exist at repo root: {config_path}"
    result = subprocess.run(
        [
            "ruff",
            "check",
            "--config",
            config_path,
            "--stdin-filename",
            "test.py",
        ],
        input="",
        capture_output=True,
        text=True,
    )
    assert "Failed to parse" not in result.stderr, f"ruff.toml has invalid syntax: {result.stderr}"


@pytest.mark.unit
def test_ruff_catches_known_bad_python():
    """Validate that ruff catches lint errors in known-bad Python code.

    Given: A Python file with an unused import
    When: ruff check is run against it with the repo config
    Then: ruff reports errors and exits non-zero
    """
    assert _RUFF_PATH is not None, "ruff is not installed. Install with: pip install ruff"
    config_path = os.path.join(_REPO_ROOT, "ruff.toml")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("import os\nimport sys\n\nx = 1\n")
        bad_file = f.name
    try:
        result = subprocess.run(
            ["ruff", "check", "--config", config_path, bad_file],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, (
            f"ruff check should report errors on known-bad file, stdout: {result.stdout}, stderr: {result.stderr}"
        )
    finally:
        os.unlink(bad_file)
