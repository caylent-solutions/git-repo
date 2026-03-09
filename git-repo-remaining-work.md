# git-repo Remaining Work Spec

## Context

This document captures all remaining work for the
`git-repo` repository (Caylent fork of Google's repo tool)
based on a review of every applicable requirement in
`claude-plugin-marketplace-spec.md`.

**Applicable spec sections:** 17 (Required Enhancements), 18 (Repository Inventory),
20 (Implementation Order).

**Review date:** 2026-03-09

**Current state:** All core features (Section 17.1
absolute linkfile dest, Section 17.2 PEP 440 version
constraints, Section 17.3 existing behavior verification)
are implemented
on `origin/main` and tagged as `caylent-2.0.0`. The items below are gaps identified
during the review.

---

## RW-1: Document New Features in CAYLENT-README.md

**Spec reference:** Section 17.1, 17.2, 18

**Gap:** `CAYLENT-README.md` does not document either of the two new `caylent-2.0.0`
features. The "Caylent Enhancements" section lists only three items (tag detection,
trace file handling, envsubst). The "New Features" section only covers `envsubst`.

**Required changes:**

1. Add "Absolute Linkfile Destination" to the "New Features" section:
   - Explain that `<linkfile dest>` now supports absolute paths after `repo envsubst`
   - Show an example using `${CLAUDE_MARKETPLACES_DIR}`
     expanding to an absolute path
   - Note that `copyfile` remains relative-only
   - Reference `docs/manifest-format.md` for full details

2. Add "PEP 440 Version Constraints" to the "New Features" section:
   - Explain that `revision` attributes in `<project>`
     now support PEP 440 constraints
   - Show examples: `~=1.2.0` (patch-compatible),
     `~=1.0` (minor-compatible), `*` (latest)
   - Explain resolution: scans available tags, selects highest matching version
   - Note the `packaging` dependency

3. Update the "Caylent Enhancements" bullet list to include both features

**Acceptance criteria:**
- Both features are documented with examples
- Existing documentation (envsubst, installation, development) is not altered
- Documentation matches the actual behavior verified by tests on `origin/main`

---

## RW-2: Add Apache 2.0 License Reference to README

**Spec reference:** Section 18

**Gap:** Neither `README.md` nor `CAYLENT-README.md` mention the Apache 2.0 license.
The `LICENSE` file exists and contains the full Apache 2.0 text, but the README should
reference it for visibility.

**Required changes:**

1. Add a "License" section to the bottom of `CAYLENT-README.md`:

   ```text
   ## License

   This project is licensed under the Apache License 2.0.
   See [LICENSE](LICENSE) for the full license text.
   ```

**Acceptance criteria:**
- License section exists in `CAYLENT-README.md`
- References the `LICENSE` file
- Correctly identifies Apache 2.0

---

## RW-3: Replace black/flake8 with ruff and Ensure Tool Is Installed

**Spec reference:** Section 17.3 (test robustness), CLAUDE.md (fail-fast, no fallback)

**Gap:** This branch uses black + flake8 for Python linting. The origin/main branch
uses ruff. The project should use ruff for Python linting and formatting. No markdown
or YAML linters are configured on this branch.

**Required changes:**

1. Replace black + flake8 with ruff in `tox.ini`, `Makefile`, `constraints.txt`,
   and `pyproject.toml`
2. Add `ruff.toml` configuration from origin/main
3. Add `test_ruff_config.py` with fail-fast `shutil.which()` assertion
4. Remove `test_markdownlint_config.py` and `test_yamllint_config.py` (no configs
   to validate on this branch)
5. Install ruff in devcontainer (`project-setup.sh`), CI workflow, and document
   in `CAYLENT-README.md`

**Acceptance criteria:**
- `make lint` and `make format` use ruff
- `tox -e lint` uses ruff
- `test_ruff_config.py` fails fast with actionable message if ruff is missing
- No skip logic, no fallback, no suppression

---

## RW-4: Update CI Workflow to Trigger on Pull Requests

**Spec reference:** Section 18

**Gap:** `.github/workflows/test-ci.yml` only triggers on `push` to specific branches
and `v*` tags. It does not trigger on `pull_request`
events. The spec requires PRs with
1 approving review before merge — CI should validate PRs before they can be approved.

**Required changes:**

1. Add `pull_request` trigger to `.github/workflows/test-ci.yml`:

   ```yaml
   on:
     push:
       branches: [main]
       tags: [caylent-*]
     pull_request:
       branches: [main]
   ```

2. Update tag pattern from `v*` to `caylent-*` to match the Caylent tagging convention.

3. Consider updating the Python version matrix — the current matrix tests
   Python 3.6 through 3.12 on `ubuntu-20.04` (EOL). Evaluate whether the minimum
   supported Python version should be raised given that `packaging` (a new dependency)
   may have dropped older Python support.

**Acceptance criteria:**
- CI runs on every PR targeting `main`
- CI runs on push to `main` and on `caylent-*` tag creation
- Test matrix uses supported OS and Python versions

---

## RW-5: Add CODEOWNERS File

**Spec reference:** Section 18

**Gap:** No `.github/CODEOWNERS` file exists. The spec states that PRs require code
owner review as part of the branch ruleset on `main`.

**Required changes:**

1. Create `.github/CODEOWNERS`:

   ```text
   # Default owners for all files
   * @caylent-solutions/platform-team

   # Core repo tool code
   /manifest_xml.py    @caylent-solutions/platform-team
   /project.py         @caylent-solutions/platform-team
   /version_constraints.py @caylent-solutions/platform-team
   /subcmds/           @caylent-solutions/platform-team

   # CI/CD
   /.github/           @caylent-solutions/platform-team

   # Documentation
   /docs/              @caylent-solutions/platform-team
   ```

2. Adjust team names to match actual GitHub organization team slugs.

**Acceptance criteria:**
- `.github/CODEOWNERS` exists and is syntactically valid
- All critical files have designated owners
- GitHub recognizes the CODEOWNERS file for PR reviews

---

## RW-6: Verify and Configure GitHub Repository Settings

**Spec reference:** Section 18

**Gap:** The following GitHub repository settings cannot be verified from code. They
require manual verification and configuration via the GitHub UI or API.

**Required verifications/actions:**

| Setting | Required Value | How to Verify |
|---|---|---|
| Repository visibility | Public | GitHub Settings > General |
| Squash merge | Allowed | GitHub Settings > General > Pull Requests |
| Merge commit | Disabled | GitHub Settings > General > Pull Requests |
| Rebase merge | Disabled | GitHub Settings > General > Pull Requests |
| Branch ruleset on `main` | Active | GitHub Settings > Rules > Rulesets |
| Requires PR with 1 approving review | Yes | Branch ruleset configuration |
| Requires code owner review | Yes | Branch ruleset configuration |
| Requires last push approval | Yes | Branch ruleset configuration |
| Requires resolved threads | Yes | Branch ruleset configuration |
| Squash merge only | Yes | Branch ruleset configuration |
| Linear history | Yes | Branch ruleset configuration |
| No deletion | Yes | Branch ruleset configuration |
| No non-fast-forward | Yes | Branch ruleset configuration |

**Acceptance criteria:**
- All settings match the table above
- Settings verified by a human with admin access to the repository
- Any deviations documented and justified

---

## RW-7: Evaluate caylent-2.0.0 Tag Position

**Spec reference:** Section 17.4

**Gap:** The `caylent-2.0.0` tag points to commit `b9c4041` (E1-F3-S5-T1), but
`origin/main` HEAD is at `c6c8c2e` (E1-F4-S2-T1: Update CAYLENT-README.md version
references), which is 1 commit ahead of the tag. This means the tag does not include
the README version reference updates.

**Decision required:**

Option A: Accept as-is. The tag contains all feature code and tests. The post-tag
commit is documentation-only. Consumers using `caylent-2.0.0` get all features.

Option B: Create `caylent-2.0.1` at `origin/main` HEAD to include the README update.

Option C: After completing RW-1 and RW-2 (README improvements), create `caylent-2.1.0`
that includes both the original features and the documentation improvements.

**Acceptance criteria:**
- A decision is made and documented
- If a new tag is created, it follows semver and the annotation describes the change

---

## RW-8: GPG Signing for Tags

**Spec reference:** Mentioned in CAYLENT-README.md
("GPG signing support will be added in a future release")

**Gap:** All Caylent tags are unsigned. The README documents that `--no-repo-verify`
is required. The upstream repo tool verifies tag signatures by default. Not having
signed tags means consumers must bypass verification.

**CLAUDE.md concern:** The current README instructs users to use `--no-repo-verify`,
which bypasses GPG signature verification. CLAUDE.md states: "Never use flags, options,
inline comments, configuration changes, or any other mechanism that causes quality
tools to skip or ignore findings." While `--no-repo-verify` is currently necessary
(tags are unsigned), the README should not present this as the permanent recommended
approach. It should be explicitly marked as a temporary workaround with a clear path
to resolution.

**Required changes:**

1. Generate or designate a GPG key for Caylent releases
2. Sign future tags with `git tag -s`
3. Publish the public key so consumers can verify
4. Update CAYLENT-README.md to remove the `--no-repo-verify` requirement
5. Update installation examples to remove `--no-repo-verify`

**Acceptance criteria:**
- Future release tags are GPG-signed
- Public key is published (e.g., in the repo or on a key server)
- README installation instructions work without `--no-repo-verify`

---

## Priority and Dependencies

| Item | Priority | Dependencies | Type |
|---|---|---|---|
| RW-1 | High | None | Documentation |
| RW-2 | High | None | Documentation |
| RW-3 | Medium | RW-4 (CI must install tools) | Prerequisite + test clarity |
| RW-4 | Medium | None | CI/CD |
| RW-5 | Medium | RW-6 (team slugs must exist) | Governance |
| RW-6 | Medium | None (manual, requires admin) | Configuration |
| RW-7 | Low | RW-1, RW-2 (decide after docs done) | Release |
| RW-8 | Low | GPG key infrastructure | Security |

---

## Summary

| Category | Items | Status |
|---|---|---|
| Core features (17.1, 17.2) | Linkfile dest, PEP 440 constraints | Done |
| Existing behavior verification (17.3) | 5 verification tests | Done |
| Release tag (17.4) | caylent-2.0.0 | Done |
| Documentation gaps | RW-1, RW-2 | Open |
| Test prerequisites | RW-3 | Open |
| CI/CD | RW-4 | Open |
| Governance | RW-5, RW-6 | Open |
| Release housekeeping | RW-7 | Open (decision needed) |
| Security (future) | RW-8 | Open (low priority) |

### Total items: 8 (2 high, 4 medium, 2 low)
