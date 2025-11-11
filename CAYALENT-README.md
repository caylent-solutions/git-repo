# Cayalent Repo Fork

This is Cayalent's fork of Google's repo tool with additional features.

## Table of Contents

- [Installation](#installation)
  - [Quick Start](#quick-start-recommended)
  - [Production (Pinned Version)](#production-pinned-version)
  - [Override Repository URL or Version](#override-repository-url-or-version)
- [New Features](#new-features)
  - [Environment Variable Substitution (envsubst)](#environment-variable-substitution-envsubst)
- [Development](#development)
  - [Setup](#setup)
  - [Running Tests](#running-tests)
  - [Creating a Release](#creating-a-release)
- [Upstream Sync](#upstream-sync)

## Installation

### Quick Start (Recommended)

```bash
# Install repo from GitHub
pip install git+https://github.com/caylent-solutions/git-repo

# Initialize repo - automatically uses latest caylent-* tag
repo init -u <YOUR_MANIFEST_URL>
```

By default, `repo init` will automatically fetch and use the latest `caylent-*` tag from GitHub.

### Production (Pinned Version)

For production environments, pin to a specific tag to ensure consistency:

```bash
# Install specific tag
pip install git+https://github.com/caylent-solutions/git-repo@caylent-1.0.0

# Initialize with the same pinned tag
repo init -u <YOUR_MANIFEST_URL> --repo-rev=caylent-1.0.0
```

Replace `caylent-1.0.0` with your desired version.

### Override Repository URL or Version

To use a specific version or branch instead of the latest tag:

```bash
# Install specific version
pip install git+https://github.com/caylent-solutions/git-repo@<ref>

# Initialize with specific version
repo init -u <YOUR_MANIFEST_URL> --repo-rev=<ref>
```

To use a different fork entirely:

```bash
# Initialize with custom repo URL and version
repo init -u <YOUR_MANIFEST_URL> \
  --repo-url=<CUSTOM_REPO_URL> \
  --repo-rev=<ref>
```

Replace `<ref>` with a tag (e.g., `caylent-1.0.0`), branch (e.g., `main`), or commit hash.

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

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/cayalent/git-repo
cd git-repo

# Install development dependencies
pip install -r requirements-dev.txt
```

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
   git tag -a caylent-1.0.0 -m "Release caylent-1.0.0"
   git push origin caylent-1.0.0
   ```

2. Users can then install using the tag as shown in the installation section above.

## Upstream Sync

To sync with upstream Google repo:

```bash
git remote add upstream https://gerrit.googlesource.com/git-repo
git fetch upstream
git merge upstream/main
```
