"""Tests for Makefile lint, format, and check targets.

Validates that the git-repo Makefile lint/format/check targets invoke the
correct tools: ruff for Python, markdownlint for Markdown, yamllint for YAML.

Spec Reference: Plan: Per-Repo Tooling — make lint, make format, make check targets.
"""

import os
import re
import subprocess

import pytest

REPO_ROOT = os.path.join(os.path.dirname(__file__), os.pardir)


@pytest.mark.unit
def test_make_lint_calls_ruff():
    """Validate that make lint invokes ruff check.

    Given: The Makefile has a lint target
    When: make lint is dry-run
    Then: The commands include 'ruff check'
    Spec: Plan: Lint targets
    """
    result = subprocess.run(
        ["make", "-n", "-C", REPO_ROOT, "lint"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"make -n lint failed: {result.stderr}"
    assert "ruff check" in result.stdout, (
        f"lint target must invoke 'ruff check', got: {result.stdout}"
    )


@pytest.mark.unit
def test_make_lint_calls_markdownlint():
    """Validate that make lint invokes markdownlint.

    Given: The Makefile has a lint target
    When: make lint is dry-run
    Then: The commands include 'markdownlint'
    Spec: Plan: Lint targets
    """
    result = subprocess.run(
        ["make", "-n", "-C", REPO_ROOT, "lint"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"make -n lint failed: {result.stderr}"
    assert "markdownlint" in result.stdout, (
        f"lint target must invoke 'markdownlint', got: {result.stdout}"
    )


@pytest.mark.unit
def test_make_lint_calls_yamllint():
    """Validate that make lint invokes yamllint.

    Given: The Makefile has a lint target
    When: make lint is dry-run
    Then: The commands include 'yamllint'
    Spec: Plan: Lint targets
    """
    result = subprocess.run(
        ["make", "-n", "-C", REPO_ROOT, "lint"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"make -n lint failed: {result.stderr}"
    assert "yamllint" in result.stdout, (
        f"lint target must invoke 'yamllint', got: {result.stdout}"
    )


@pytest.mark.unit
def test_make_format_calls_ruff_format():
    """Validate that make format invokes ruff format.

    Given: The Makefile has a format target
    When: make format is dry-run
    Then: The commands include 'ruff format' (without --check)
    Spec: Plan: Format target
    """
    result = subprocess.run(
        ["make", "-n", "-C", REPO_ROOT, "format"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"make -n format failed: {result.stderr}"
    assert "ruff format" in result.stdout, (
        f"format target must invoke 'ruff format', got: {result.stdout}"
    )
    # format target should not use --check (that's format-check)
    format_lines = [
        line for line in result.stdout.splitlines() if "ruff format" in line
    ]
    for line in format_lines:
        assert "--check" not in line, (
            f"format target must not use --check (use format-check instead): {line}"
        )


@pytest.mark.unit
def test_make_check_is_readonly():
    """Validate that make check is read-only (uses --check for format verification).

    Given: The Makefile has check and format-check targets
    When: make format-check is dry-run
    Then: The commands include 'ruff format --check'
    Spec: Plan: Check target
    """
    result = subprocess.run(
        ["make", "-n", "-C", REPO_ROOT, "format-check"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"make -n format-check failed: {result.stderr}"
    assert "ruff format" in result.stdout and "--check" in result.stdout, (
        f"format-check target must invoke 'ruff format --check', got: {result.stdout}"
    )


@pytest.mark.unit
def test_lint_target_has_tool_comments():
    """Validate that lint target Makefile comments document which tools are invoked.

    Given: The Makefile has a lint target
    When: We inspect the Makefile
    Then: The lint target's help comment mentions the tools it uses
    Spec: AC-DOC-1
    """
    makefile_path = os.path.join(REPO_ROOT, "Makefile")
    with open(makefile_path) as f:
        content = f.read()
    match = re.search(r"^lint:.*##\s*(.+)", content, re.MULTILINE)
    assert match, "lint target must have a ## help comment"
    comment = match.group(1).lower()
    assert "ruff" in comment, f"lint help comment must mention ruff, got: {comment}"
    assert "markdownlint" in comment, (
        f"lint help comment must mention markdownlint, got: {comment}"
    )
    assert "yamllint" in comment, (
        f"lint help comment must mention yamllint, got: {comment}"
    )
