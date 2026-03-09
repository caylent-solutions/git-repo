# Caylent Repo Tool

This is Caylent's fork of the Android repo tool with custom enhancements.

## Table of Contents

- [Installation](#installation)
  - [Quick Start](#quick-start-recommended)
  - [Production (Pinned Version)](#production-pinned-version)
  - [Override Repository URL or Version](#override-repository-url-or-version)
- [Usage](#usage)
  - [Important: GPG Verification](#important-gpg-verification)
- [New Features](#new-features)
  - [Environment Variable Substitution (envsubst)](#environment-variable-substitution-envsubst)
  - [Absolute Linkfile Destination](#absolute-linkfile-destination)
  - [PEP 440 Version Constraints](#pep-440-version-constraints)
- [Development](#development)
  - [Setup](#setup)
  - [Running Tests](#running-tests)
  - [Creating a Release](#creating-a-release)
- [Upstream Sync](#upstream-sync)

## Installation

### Quick Start (Recommended)

```bash
# Install repo from latest tag (automatically fetches latest version)
pip install git+https://github.com/caylent-solutions/git-repo@$(curl -s https://api.github.com/repos/caylent-solutions/git-repo/tags | grep -o '"name": "caylent-[^"]*' | head -1 | cut -d'"' -f4)

# Initialize repo - automatically uses latest caylent-* tag
repo init -u <YOUR_MANIFEST_URL> --no-repo-verify
```

During `repo init`, it will automatically fetch and use
the latest `caylent-*` tag from GitHub.

**To uninstall:**

```bash
pip uninstall -y repo
```

### Production (Pinned Version)

For production environments, pin to a specific tag to ensure consistency:

```bash
# Install specific tag
pip install git+https://github.com/caylent-solutions/git-repo@caylent-2.0.0

# Initialize with the same pinned tag
repo init -u <YOUR_MANIFEST_URL> --repo-rev=caylent-2.0.0 --no-repo-verify
```

Replace `caylent-2.0.0` with your desired version.

### Override Repository URL or Version

To use a specific version or branch instead of the latest tag:

```bash
# Install specific version
pip install git+https://github.com/caylent-solutions/git-repo@<ref>

# Initialize with specific version
repo init -u <YOUR_MANIFEST_URL> --repo-rev=<ref> --no-repo-verify
```

To use a different fork entirely:

```bash
# Initialize with custom repo URL and version
repo init -u <YOUR_MANIFEST_URL> \
  --repo-url=<CUSTOM_REPO_URL> \
  --repo-rev=<ref> \
  --no-repo-verify
```

Replace `<ref>` with a tag (e.g., `caylent-2.0.0`),
branch (e.g., `main`), or commit hash.

## Usage

### Important: GPG Verification (Temporary Workaround)

Currently, Caylent tags are not GPG-signed. Until GPG signing is implemented,
you **must** use the `--no-repo-verify` flag when running `repo init`:

```sh
repo init -u <manifest-url> --no-repo-verify
```

**This is a temporary workaround.** The `--no-repo-verify` flag bypasses GPG
signature verification, which is a security check. GPG signing for release tags
is planned. Once implemented, the `--no-repo-verify` flag will no longer be
required and should be removed from all installation commands.

### Example

```sh
# Initialize a repo workspace
repo init -u https://github.com/your-org/manifest.git --no-repo-verify

# Sync all projects
repo sync
```

## New Features

### Environment Variable Substitution (envsubst)

Replace environment variable placeholders in manifest XML files:

```xml
<!-- manifest.xml -->
<manifest>
  <remote name="origin" 
          fetch="${GITBASE}" 
          revision="${GITREV}"/>
  <project name="my-project" 
           path="projects/my-project" 
           remote="origin"/>
</manifest>
```

```bash
# Set environment variables
export GITBASE=https://github.com/myorg
export GITREV=main

# Run envsubst to replace variables
repo envsubst
```

**Result:**

```xml
<manifest>
  <remote name="origin" 
          fetch="https://github.com/myorg" 
          revision="main"/>
  <project name="my-project" 
           path="projects/my-project" 
           remote="origin"/>
</manifest>
```

The command replaces all `${VARIABLE}` placeholders in:
- Attribute values
- Text content
- Any XML element in manifest files under `.repo/manifests/`

### Absolute Linkfile Destination

The `<linkfile>` element's `dest` attribute now supports absolute paths after
`repo envsubst` resolution. This enables symlinks to directories outside the
project tree — for example, creating marketplace symlinks in `$HOME`.

```xml
<!-- Before envsubst -->
<project name="my-plugins" path=".packages/my-plugins" remote="origin"
         revision="refs/tags/tools/1.0.0">
  <linkfile src="common/tools"
            dest="${CLAUDE_MARKETPLACES_DIR}/my-plugins-tools" />
</project>
```

After `repo envsubst` resolves `${CLAUDE_MARKETPLACES_DIR}` to an absolute path
(e.g., `/home/vscode/.claude-marketplaces`), `repo sync` creates the symlink at
that absolute location, including any necessary parent directories.

- **`linkfile`** permits absolute `dest` paths after envsubst
- **`copyfile`** remains restricted to relative paths within the project tree
- Absolute paths are still validated: `..`, `.git`, `.repo`, and unsafe Unicode
  codepoints are rejected

See `docs/manifest-format.md` for full details.

### PEP 440 Version Constraints

The `revision` attribute in `<project>` entries now supports PEP 440-compatible
version constraints in addition to exact tag references. During `repo sync`, the
fork scans available tags matching the tag prefix, evaluates the constraint, and
checks out the highest matching version.

```xml
<!-- Exact pin (existing behavior) -->
<project name="my-repo" revision="refs/tags/tools/1.2.3" ... />

<!-- Patch-compatible: highest 1.2.x -->
<project name="my-repo" revision="refs/tags/tools/~=1.2.0" ... />

<!-- Minor-compatible: highest 1.x where x >= 2 -->
<project name="my-repo" revision="refs/tags/tools/~=1.2" ... />

<!-- Latest available version -->
<project name="my-repo" revision="refs/tags/tools/*" ... />

<!-- Range constraint -->
<project name="my-repo" revision="refs/tags/tools/>=1.0.0,<2.0.0" ... />
```

Supported constraint syntax follows [PEP 440](https://peps.python.org/pep-0440/):
`~=` (compatible release), `>=`, `<=`, `>`, `<`, `!=`, `==`, and `*` (wildcard).

This feature requires the `packaging` Python library, which is included as an
install dependency.

## Caylent Enhancements

- Automatic detection of latest `caylent-*` tag during initialization
- Improved trace file handling for non-writable directories
- Environment variable substitution in manifest files (`repo envsubst`)
- Absolute `<linkfile dest>` paths after `repo envsubst` resolution
- PEP 440 version constraints in `<project revision>` attributes
- Custom bug tracking: <https://github.com/caylent-solutions/git-repo/issues>

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/caylent-solutions/git-repo
cd git-repo

# Install development dependencies
pip install -r requirements-dev.txt

# Install ruff (Python linter and formatter)
pip install ruff
```

**Required development tools:**

| Tool | Purpose | Install |
|---|---|---|
| `python3` | Runtime | OS package manager |
| `ruff` | Python linting and formatting | `pip install ruff` |
| `pytest` | Test runner | `pip install pytest` |

All tools are required. Tests that validate linter configurations will fail
fast with a clear error if any tool is missing.

### Running Tests

```bash
# Run specific tests
tox -- tests/test_subcmds_envsubst.py

# Run all tests
tox
```

### Creating a Release

1. Update version and create a semver tag:

   ```bash
   git tag -a caylent-X.Y.Z -m "Release caylent-X.Y.Z"
   git push origin caylent-X.Y.Z
   ```

2. Users can then install using the tag as shown in the installation section above.

## Upstream Sync

To sync with upstream Google repo:

```bash
git remote add upstream https://gerrit.googlesource.com/git-repo
git fetch upstream
git merge upstream/main
```

## Releases

Latest release: `caylent-2.0.0`

View all releases: <https://github.com/caylent-solutions/git-repo/tags>

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE)
for the full license text.
