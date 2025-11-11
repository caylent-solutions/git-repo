# Cayalent Repo Fork

This is Cayalent's fork of Google's repo tool with additional features.

## Installation

### From a Specific Tag (Recommended for Production)

```bash
# Install repo from GitHub - <ref> can be a tag, branch, or commit
pip install git+https://github.com/caylent-solutions/git-repo@<ref>

# If using asdf, reshim
asdf reshim python

# Initialize with Cayalent's fork - REQUIRED: specify --repo-url and --repo-rev
# <ref> must match the version installed above
repo init -u <YOUR_MANIFEST_URL> \
  --repo-url=https://github.com/caylent-solutions/git-repo \
  --repo-rev=<ref>
```

Replace `<ref>` with a tag (e.g., `caylent-1.0.0`), branch (e.g., `main`), or commit hash.

**IMPORTANT**: You MUST specify `--repo-url` and `--repo-rev` when running `repo init`, otherwise it will download the official Google repo instead of this fork. Both `pip install` and `--repo-rev` accept the same reference types: tags, branches, or commit hashes.

### Example: Installing from a Branch

```bash
# Example: Install from feature branch
pip install git+https://github.com/caylent-solutions/git-repo@<ref>

# If using asdf, reshim
asdf reshim python

# Initialize with the same reference
repo init -u <YOUR_MANIFEST_URL> \
  --repo-url=https://github.com/caylent-solutions/git-repo \
  --repo-rev=<ref>
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

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/cayalent/git-repo
cd git-repo

# Install development dependencies
pip install -r requirements-dev.txt

# Install system dependencies (Ubuntu/Debian)
sudo apt-get install help2man
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
