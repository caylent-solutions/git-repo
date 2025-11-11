# Cayalent Repo Fork

This is Cayalent's fork of Google's repo tool with additional features.

## Installation

### From a Specific Tag (Recommended for Production)

```bash
# Install repo launcher
mkdir -p ~/.bin
curl https://storage.googleapis.com/git-repo-downloads/repo > ~/.bin/repo
chmod a+rx ~/.bin/repo
export PATH="${HOME}/.bin:${PATH}"

# Initialize with Cayalent's fork using a specific tag
repo init -u <YOUR_MANIFEST_URL> \
  --repo-url=https://github.com/cayalent/git-repo \
  --repo-branch=v1.0.0
```

Replace `v1.0.0` with the desired semver tag.

### From a Branch (For Testing)

```bash
# Install repo launcher (if not already installed)
mkdir -p ~/.bin
curl https://storage.googleapis.com/git-repo-downloads/repo > ~/.bin/repo
chmod a+rx ~/.bin/repo
export PATH="${HOME}/.bin:${PATH}"

# Initialize with Cayalent's fork using a branch
repo init -u <YOUR_MANIFEST_URL> \
  --repo-url=https://github.com/cayalent/git-repo \
  --repo-branch=feature/support-cpm
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
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```

2. Users can then install using the tag as shown in the installation section above.

## Upstream Sync

To sync with upstream Google repo:

```bash
git remote add upstream https://gerrit.googlesource.com/git-repo
git fetch upstream
git merge upstream/main
```
