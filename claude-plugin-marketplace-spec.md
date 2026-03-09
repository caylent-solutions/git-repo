# Claude Code Plugin Marketplace via RPM: Architecture Specification

## Status: Design Specification (Agent-Ready)

This specification is for **Caylent**. It defines the architecture for
distributing
Claude Code plugins via RPM infrastructure within the Caylent organization. An
implementing agent should be able to build the complete system from this
document alone.

---

## 1. Problem Statement

Claude Code plugins are distributed in a monorepo containing many marketplaces
(sub-repos).
Each marketplace directory contains 1 to many plugins.

Projects need to:

1. Declare which marketplaces they require (from 1 to N of the available
   marketplaces)
2. Pin each marketplace to an independent semantic version or version constraint
3. Sync only the declared marketplaces into a well-known location
4. Automatically register each synced marketplace and install its plugins
5. Avoid namespace collisions across all layers of the system
6. Separate plugin marketplace concerns from build-tooling package concerns

The existing RPM (Repo Package Manager) infrastructure (the `repo` tool,
manifest XML, and
`.rpmenv` configuration) must be leveraged as the delivery mechanism. No new
tooling is
introduced. The `.packages/` naming convention is extended from `<repo-name>` to
`<repo-name>-<flattened-marketplace-path>` to support multiple checkouts of the
same
monorepo at different versions.

**Repository visibility:** The plugin monorepo (`rpm-claude-marketplaces`) and
the
top-level manifest repo (`caylent-private-rpm`) MUST be created as **private**
repositories under the `caylent-solutions` GitHub organization. All RPM package
repositories (e.g., `rpm-python-uv`) MUST also be private. No RPM-managed
repository
should be public.

**RPM naming convention:** Every git repository synced by RPM MUST be prefixed
with
`rpm-`. This includes both build-tooling packages (e.g., `rpm-python-uv`) and
the
plugin monorepo (e.g., `rpm-claude-marketplaces`). Throughout this
specification, `<monorepo>`
is a placeholder for the plugin monorepo's actual `rpm-claude-marketplaces`
name. The
hierarchy within the manifest repo follows
`<runtime>/<build-tool>/<framework>/<architecture>`. The plugin monorepo uses a
broader
structure: `common/<domain>/<runtime>/<build-tool>/<framework>/<architecture>`,
where
all marketplaces live under `common/` and are organized by domain first. For the
`development` domain, the hierarchy aligns with the manifest repo structure.
Other
domains (e.g., `marketing`, `legal`) are freeform. **This hierarchy is a
recommendation,
not a hard requirement.** Any directory structure under `common/` is valid.

**Build package naming convention:** Build packages follow the pattern
`rpm-<runtime>-<descriptive package name>` (e.g., `rpm-python-uv`,
`rpm-node-npm`,
`rpm-dotnet-nuget`). The descriptive name is chosen to clearly identify the
package's
purpose. It is not required to match any specific hierarchy level. If a better
naming
standard emerges, this convention can be updated.

---

## 2. Architecture Overview

```text
  MANIFEST REPO (caylent-private-rpm), the orchestrator
  Contains repo-specs/ with the <runtime>/<build-tool>/<framework>/<architecture> hierarchy
  Each leaf directory has XML manifests that reference both the plugin monorepo and build packages

  ┌───────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │  caylent-private-rpm (top-level manifest repo)                                                            │
  │                                                                                                           │
  │  repo-specs/                                                                                              │
  │    git-connection/                                                                                        │
  │      remote.xml                       ← shared remote definitions (uses ${GITBASE})                       │
  │    common/development/python/uv/django/microservice/                                                      │
  │      meta.xml                         ← includes remote.xml + packages.xml + claude-marketplaces.xml      │
  │      packages.xml                     ← references build package repos (e.g., rpm-python-uv)              │
  │      claude-marketplaces.xml          ← 1-to-many marketplace syncs from rpm-claude-marketplaces monorepo │
  │                                         each line syncs a marketplace dir + creates symlink to it         │
  │    common/development/node/npm/express/microservice/                                                      │
  │      meta.xml                         ← includes remote.xml + packages.xml + claude-marketplaces.xml      │
  │      packages.xml                     ← references build package repos (e.g., rpm-node-npm)               │
  │      claude-marketplaces.xml                   ← 1-to-many marketplace syncs (same pattern as above)      │
  │    ...                                ← one leaf per <runtime>/<build-tool>/<framework>/<architecture>    │
  └───────────────────────────────────────────────────────────────────────────────────────────────────────────┘

        packages.xml references ──────┐            claude-marketplaces.xml syncs marketplaces from ──────┐
              build package repos     │            the monorepo (1-to-many per manifest)                 │
                                      ▼                                                                  ▼

  BUILD PACKAGES (polyrepo)                                    PLUGIN MONOREPO (1 git repo: rpm-claude-marketplaces)
  Each = rpm-<runtime>-<descriptive-name>                      Marketplaces at ANY level of the hierarchy

                                                               ┌──────────────────────────────────────────────┐
                                                               │  rpm-claude-marketplaces monorepo            │
                                                               │                                              │
                                                               │  ┌────────────────────────────────────────┐  │
  (no build package, universal plugins                         │  │ common/sdlc-tools/                     │  │
   are tool-agnostic)                                          │  │  ╰ workflow-plugin                     │  │
                                                               │  │  ╰ review-plugin                       │  │
                                                               │  │  (universal scope)                     │  │
                                                               │  └────────────────────────────────────────┘  │
                                                               │                                              │
  ┌───────────────────────────────────────────────────┐        │  ┌────────────────────────────────────────┐  │
  │                                                   │        │  │ common/development/python/uv/          │  │
  │ rpm-python-uv                                     │◄──────►│  │  quality-agent/                        │  │
  │ (linting, testing, typing, packaging, all in one) │        │  │   ╰ ruff-skills-plugin                 │  │
  │                                                   │        │  │   ╰ pytest-skills-plugin               │  │
  └───────────────────────────────────────────────────┘        │  │  (Python+uv scope)                     │  │
                                                               │  └────────────────────────────────────────┘  │
                                                               │                                              │
                                                               │  ┌────────────────────────────────────────┐  │
  (no separate build package, django tasks                     │  │ common/development/python/uv/django/   │  │
   are part of rpm-python-uv or a                              │  │  django-helpers/                       │  │
   framework-specific overlay)                                 │  │   ╰ models-plugin                      │  │
                                                               │  │   ╰ views-plugin                       │  │
                                                               │  │  (Python+uv+Django scope)              │  │
                                                               │  └────────────────────────────────────────┘  │
                                                               │                                              │
  ┌───────────────────────────────────────────────────┐        │  ┌────────────────────────────────────────┐  │
  │                                                   │        │  │ common/development/node/npm/           │  │
  │ rpm-node-npm                                      │◄──────►│  │  quality-agent/                        │  │
  │ (linting, testing, bundling, all in one)          │        │  │   ╰ eslint-skills-plugin               │  │
  │                                                   │        │  │   ╰ jest-skills-plugin                 │  │
  └───────────────────────────────────────────────────┘        │  │  (Node+npm scope)                      │  │
                                                               │  └────────────────────────────────────────┘  │
                                                               │                                              │
  ┌───────────────────────────────────────────────────┐        │  ┌────────────────────────────────────────┐  │
  │                                                   │        │  │ common/development/dotnet/nuget/       │  │
  │ rpm-dotnet-nuget                                  │◄──────►│  │  quality-agent/                        │  │
  │ (analyzers, testing, compilation, all in one)     │        │  │   ╰ analyzer-plugin                    │  │
  │                                                   │        │  │   ╰ xunit-skills-plugin                │  │
  └───────────────────────────────────────────────────┘        │  │  (dotnet+NuGet scope)                  │  │
                                                               │  └────────────────────────────────────────┘  │
                                                               │                                              │
                                                               └──────────────────────────────────────────────┘

                          │                                                               │
                repo sync (via RPM manifest from caylent-private-rpm)                     │
                Syncs both build packages AND monorepo checkouts                          │
                          │                                                               │
                          ▼                                                               ▼
  ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │                                        CONSUMER PROJECT                                                                            │
  │                                                                                                                                    │
  │  .rpmenv                                                                 ← multi-source RPM configuration                          │
  │    RPM_SOURCES=build,marketplaces                                                                                                  │
  │    RPM_SOURCE_build_URL=caylent-private-rpm repo URL                                                                               │
  │    RPM_SOURCE_build_REVISION=main                                                                                                  │
  │    RPM_SOURCE_build_PATH=repo-specs/.../meta.xml                                                                                   │
  │    RPM_SOURCE_marketplaces_URL=caylent-private-rpm repo URL                                                                        │
  │    RPM_SOURCE_marketplaces_REVISION=main                                                                                           │
  │    RPM_SOURCE_marketplaces_PATH=repo-specs/.../claude-marketplaces.xml                                                             │
  │                                                                                                                                    │
  │  .packages/                                                              ← RPM-managed (gitignored)                                │
  │    rpm-python-uv/                                                        ← build package (synced from packages.xml)                │
  │    <monorepo>-sdlc-tools/                                                ← monorepo checkout (synced from claude-marketplaces.xml) │
  │    <monorepo>-python-uv-quality-agent/                                   ← monorepo checkout                                       │
  │    <monorepo>-python-uv-django-django-helpers/                           ← monorepo checkout                                       │
  │                                                                                                                                    │
  │  $HOME/.claude-marketplaces/                                             ← plugin marketplaces (symlinks via <linkfile>)           │
  │    <monorepo>-sdlc-tools/                                                ← symlink → .packages/.../sdlc-tools                      │
  │    <monorepo>-python-uv-quality-agent/                                   ← symlink → .packages/.../quality-agent                   │
  │    <monorepo>-python-uv-django-django-helpers/                           ← symlink → .packages/.../django-helpers                  │
  │                                                                                                                                    │
  │  .packages/rpm-claude-marketplaces-install/                               ← install tool package (delivered by repo sync)          │
  │    install_claude_marketplaces.py                                        ← install script                                          │
  │    uninstall_claude_marketplaces.py                                      ← uninstall script                                        │
  └────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

There are four distinct concerns with clear separation:

| Concern | Location | Managed By |
|---|---|---|
| Build-tooling packages | `.packages/<repo-name>/` | RPM (`repo sync`), polyrepo, one repo per package |
| Monorepo checkouts | `.packages/<monorepo>-<marketplace>/` | RPM (`repo sync`), same monorepo, different tags |
| Plugin marketplaces | `$HOME/.claude-marketplaces/<monorepo>-<marketplace>/` | RPM (`repo sync` + `<linkfile>`) |
| Install script | `.packages/rpm-claude-marketplaces-install/` (delivered by `repo sync` via `common/claude-marketplaces.xml`) | RPM package (`rpm-claude-marketplaces-install`) |
| Plugin installation | `$HOME/.claude/plugins/` | Install script + Claude Code CLI |

---

## 3. Directory Structure

### 3.1 `$HOME/.claude-marketplaces/`: The Common Marketplace Folder

**Name:** `.claude-marketplaces`

**Rationale:**
- Lives in `$HOME` = outside the git project, shared across projects on the same
  machine
- Dot-prefixed = hidden, not part of normal user files
- `claude` = Claude Code (the tool these marketplaces serve)
- `marketplaces` = the exact term used by `claude plugin marketplace add`
- Distinct from `.packages/` = clear separation of build-tooling from plugin
  concerns

**Properties:**
- MUST be located at `$HOME/.claude-marketplaces/` (the user's home directory
  root)
- Lives outside the git project checkout, does NOT need to be gitignored
- MUST contain only symlinks created by `<linkfile>` directives, never real
  directories
- MUST NOT contain any files directly, only subdirectories (symlinked)
- Symlinks point into `.packages/` of the project that created them

**Invariant:** Every entry in `$HOME/.claude-marketplaces/` is a symlink
pointing to a
marketplace subdirectory within a monorepo checkout under a project's
`.packages/`.

### 3.2 Subdirectory Naming: `<repo-name>-<marketplace-name>`

Each subdirectory within `$HOME/.claude-marketplaces/` follows the convention:

```text
~/.claude-marketplaces/<monorepo-repo-name>-<flattened-marketplace-path>/
```

The **marketplace path** is the marketplace directory's location within the
monorepo hierarchy
(e.g., `common/development/python/uv/django/django-helpers`). The **flattened
marketplace path**
is computed by the path flattening algorithm defined in Section 4.6, which
strips configured
leading path components (from `config-repo.json`) and joins the remaining
segments with dashes
(e.g., `python-uv-django-django-helpers`). Each marketplace directory contains
**1 to many
plugins**.

**Examples (using placeholder names):**

| Monorepo Repo Name | Marketplace Path in Monorepo | Flattened Marketplace Path | Symlink Path |
|---|---|---|---|
| `rpm-claude-marketplaces` | `common/sdlc-tools` | `sdlc-tools` | `$HOME/.claude-marketplaces/rpm-claude-marketplaces-sdlc-tools/` |
| `rpm-claude-marketplaces` | `common/development/python/uv/quality-agent` | `python-uv-quality-agent` | `$HOME/.claude-marketplaces/rpm-claude-marketplaces-python-uv-quality-agent/` |
| `rpm-claude-marketplaces` | `common/development/python/uv/django/django-helpers` | `python-uv-django-django-helpers` | `$HOME/.claude-marketplaces/rpm-claude-marketplaces-python-uv-django-django-helpers/` |
| `rpm-claude-marketplaces` | `common/development/node/npm/quality-agent` | `node-npm-quality-agent` | `$HOME/.claude-marketplaces/rpm-claude-marketplaces-node-npm-quality-agent/` |

**Uniqueness guarantee:** The combination of `<repo-name>` + `-` +
`<flattened-marketplace-path>`
is unique because:
- A single monorepo cannot have duplicate directory paths: the filesystem
  enforces
  that every path within the repository is unique
- The marketplace hierarchy path is therefore unique within its monorepo
- The flattening algorithm (Section 4.6) is deterministic, and CI validates that
  all
    flattened names are unique across the entire monorepo (see
  `config-repo.json` in
  Section 4.5)
- At the Claude Code CLI level, plugins use `plugin@marketplace` composite keys
    (stored in `~/.claude/plugins/installed_plugins.json`), so two plugins with
  the same
    name from different marketplaces are distinct entries, no collision is
  possible
- Skills are additionally namespaced: a skill `review` in plugin `code-quality`
  becomes
  `/code-quality:review`, preventing invocation conflicts across plugins

### 3.3 Monorepo Checkouts

Full monorepo checkouts live in `.packages/` following the
`<repo-name>-<flattened-marketplace-path>` convention:

```text
.packages/<monorepo-repo-name>-<flattened-marketplace-path>/
```

**Examples (using `rpm-claude-marketplaces` as the monorepo name):**

```text
.packages/rpm-claude-marketplaces-sdlc-tools/                      ← checkout @ refs/tags/sdlc-tools/1.0.0
.packages/rpm-claude-marketplaces-python-uv-quality-agent/         ← checkout @ refs/tags/development/python/uv/quality-agent/1.0.0
.packages/rpm-claude-marketplaces-python-uv-django-django-helpers/ ← checkout @ refs/tags/development/python/uv/django/django-helpers/1.0.0
.packages/rpm-claude-marketplaces-node-npm-quality-agent/          ← checkout @ refs/tags/development/node/npm/quality-agent/1.1.0
```

**Properties:**
- Contain the complete monorepo working tree at the tagged revision
- Each checkout is at a different tag (per-marketplace version)
- Git objects are shared across all checkouts of the same monorepo
- The install script MUST NOT scan these directories, only
  `$HOME/.claude-marketplaces/`

### 3.4 Complete Directory Layout Example

This example shows a Python/uv/Django/Frontend project that receives:
- Universal marketplaces (root level: `sdlc-tools`)
- Python-specific marketplaces (inherited via hierarchy)
- Python+uv+Django specific marketplaces (most specific level)

```text
<project-root>/
├── .rpmenv                                                      ← RPM configuration (committed)
├── .gitignore                                                   ← ignores .packages/, .rpm/
├── .packages/                                                   ← RPM-managed (gitignored)
│   │
│   │  [Build-tooling package (existing, grouped)]
│   ├── rpm-python-uv/                                           ← build: all Python/uv tasks
│   │                                                              (linting, testing, typing, packaging)
│   │
│   │  [Plugin monorepo checkouts (new)]
│   ├── rpm-claude-marketplaces-sdlc-tools/                      ← checkout @ sdlc-tools/1.0.0
│   │   ├── common/
│   │   │   ├── sdlc-tools/                                      ← marketplace we need (symlinked)
│   │   │   │   ├── workflow-plugin/                             ← plugin within marketplace
│   │   │   │   │   └── plugin.json
│   │   │   │   └── review-plugin/                               ← another plugin
│   │   │   │       └── plugin.json
│   │   │   └── development/
│   │   │       ├── node/npm/quality-agent/                      ← present but not symlinked
│   │   │       └── dotnet/nuget/quality-agent/                  ← present but not symlinked
│   │   └── ...
│   ├── rpm-claude-marketplaces-python-uv-quality-agent/         ← checkout @ development/python/uv/quality-agent/1.0.0
│   │   └── ...                                                    (correlates with rpm-python-uv)
│   └── rpm-claude-marketplaces-python-uv-django-django-helpers/ ← checkout @ development/python/uv/django/django-helpers/1.0.0
│       └── ...
│
├── .rpm/                                                        ← multi-source repo tool state (gitignored)
│   └── sources/
│       ├── build/
│       │   ├── .repo/                                           ← repo tool metadata for build source
│       │   └── .packages/                                       ← packages synced by build source
│       └── marketplaces/
│           ├── .repo/                                           ← repo tool metadata for marketplaces source
│           └── .packages/                                       ← packages synced by marketplaces source
├── Makefile                                                     ← RPM bootstrap (committed)
└── pyproject.toml                                               ← project config (committed)

$HOME/.claude-marketplaces/                                      ← user home (outside git project)
├── rpm-claude-marketplaces-sdlc-tools/                          ← SYMLINK → .packages/.../common/sdlc-tools
├── rpm-claude-marketplaces-python-uv-quality-agent/             ← SYMLINK → .packages/.../common/development/python/uv/quality-agent
└── rpm-claude-marketplaces-python-uv-django-django-helpers/     ← SYMLINK → .packages/.../common/development/python/uv/django/django-helpers
```

---

## 4. Plugin Monorepo Structure

### 4.1 Repository Layout

The plugin monorepo is a single git repository. All marketplaces live under a
top-level
`common/` directory, organized from broad to specific:

```text
common/<domain>/<runtime>/<build-tool>/<framework>/<architecture>
```

**This hierarchy is a recommendation, not a hard requirement.** Any directory
structure
under `common/` is valid. For the `development` domain, the convention aligns
with the
RPM manifest repo hierarchy. Other domains (e.g., `marketing`, `legal`) use
whatever
structure makes sense for their content.

Marketplaces (directories containing 1 to many plugins) can exist at **any
level** of
the hierarchy. **Where you place a marketplace in the hierarchy determines which
projects
automatically receive it**. Because the manifest XML uses cascading `<include>`
chains
(see Section 5.2), a project at any hierarchy position automatically inherits
ALL
marketplaces from its own level AND every level above it, up to `common/`.

This means:
- A marketplace directly under `common/` (e.g., `common/sdlc-tools/`) is
  inherited by
  **every project** regardless of domain or technology stack
- A marketplace under a **domain** (e.g.,
  `common/development/python/python-commons/`)
  is inherited by **all Python development projects**
- A marketplace at a **deeper** level (e.g.,
  `common/development/python/uv/django/django-helpers/`)
  is only inherited by projects whose hierarchy path passes through that level

**Place a marketplace at the broadest scope where it applies.** The higher in
the tree
you place it, the more projects automatically receive it.

**Hierarchy field definitions (development domain, recommended convention):**

| Level | Field | Description | Inherited by | Examples |
|---|---|---|---|---|
| 0 | `common/` | Universal, applies to all domains and stacks | ALL projects | `common/sdlc-tools`, `common/security-review` |
| 1 | `<domain>` | Business or functional domain | All projects in that domain | `development`, `marketing`, `legal`, `data` |
| 2 | `<runtime>` | Programming language or runtime platform | All projects using that runtime | `python`, `node`, `dotnet` |
| 3 | `<build-tool>` | Build tool, task runner, or package manager | All projects using that runtime+tool | `uv`, `npm`, `nuget` |
| 4 | `<framework>` | Application framework | All projects using that runtime+tool+framework | `django`, `express`, `aspnet` |
| 5 | `<architecture>` | Service architecture pattern | Only projects at that exact position | `microservice`, `frontend`, `serverless` |

**Levels 2-5 are the recommended convention for the `development` domain.**
Other
domains may use fewer levels, different level names, or a completely flat
structure.

**Full monorepo layout:**

```text
<monorepo>/
│
├── common/                                              ← Common wrapper for all marketplaces
│   │
│   │  [Universal marketplaces (apply to ALL stacks)]
│   ├── sdlc-tools/                                      ← MARKETPLACE (universal)
│   │   ├── CODEOWNERS
│   │   ├── workflow-plugin/                             ← plugin 1
│   │   │   └── plugin.json
│   │   ├── review-plugin/                               ← plugin 2
│   │   │   └── plugin.json
│   │   └── planning-plugin/                             ← plugin 3
│   │       └── plugin.json
│   ├── security-review/                                 ← MARKETPLACE (universal)
│   │   ├── CODEOWNERS
│   │   └── security-scanner/                            ← single plugin
│   │       └── plugin.json
│   │
│   └── development/                                     ← Development domain
│       │
│       │  [Python ecosystem]
│       ├── python/
│       │   ├── python-commons/                          ← MARKETPLACE (all Python)
│       │   │   ├── CODEOWNERS
│       │   │   └── python-idioms-plugin/
│       │   │       └── plugin.json
│       │   └── uv/
│       │       └── django/
│       │           └── django-helpers/                  ← MARKETPLACE (Python + uv + Django)
│       │               ├── CODEOWNERS
│       │               ├── django-models-plugin/
│       │               │   └── plugin.json
│       │               └── django-views-plugin/
│       │                   └── plugin.json
│       │
│       │  [Node.js ecosystem]
│       ├── node/
│       │   ├── node-commons/                            ← MARKETPLACE (all Node.js)
│       │   │   ├── CODEOWNERS
│       │   │   └── node-patterns-plugin/
│       │   │       └── plugin.json
│       │   └── npm/
│       │       └── express/
│       │           └── express-patterns/                ← MARKETPLACE (Node + npm + Express)
│       │               ├── CODEOWNERS
│       │               ├── express-routing-plugin/
│       │               │   └── plugin.json
│       │               └── express-middleware-plugin/
│       │                   └── plugin.json
│       │
│       │  [.NET ecosystem]
│       └── dotnet/
│           ├── dotnet-commons/                          ← MARKETPLACE (all .NET)
│           │   ├── CODEOWNERS
│           │   └── dotnet-patterns-plugin/
│           │       └── plugin.json
│           └── nuget/
│               └── aspnet/
│                   └── aspnet-scaffolding/              ← MARKETPLACE (dotnet + NuGet + ASP.NET)
│                       ├── CODEOWNERS
│                       ├── aspnet-controller-plugin/
│                       │   └── plugin.json
│                       └── aspnet-middleware-plugin/
│                           └── plugin.json
│
│  [Monorepo governance]
├── config-repo.json                                     ← monorepo configuration (Section 4.5)
├── CODEOWNERS                                           ← root-level ownership rules
├── .github/
│   └── workflows/
│       └── marketplace-ci.yml                           ← CI pipeline
└── README.md
```

**Key observations:**
- Intermediate hierarchy directories (e.g., `common/development/python/`,
  `common/development/python/uv/`, `common/development/node/npm/`)
  are NOT marketplaces; they are organizational containers
- Only directories that contain plugin subdirectories (with `plugin.json`) are
  marketplaces
- A marketplace always contains **1 to many plugins**, each in its own
  subdirectory
- The hierarchy structure under `common/development/` mirrors the `repo-specs/`
  folder structure in the RPM manifest
  repository, enabling alignment between build packages and plugin marketplaces
- **Where you place a marketplace determines its scope of inheritance**: all
  projects
    at or below that hierarchy level automatically receive it via cascading
  `<include>`
  chains in the manifest XML (see Section 5.2)
- Build packages follow the `rpm-<runtime>-<descriptive package name>` naming
  convention
    (e.g., `rpm-python-uv` covers Python/uv build tasks), while plugin
  marketplaces may
  be more granular across multiple hierarchy levels

### 4.2 Marketplace Subdirectory Requirements

Each marketplace subdirectory MUST:
- Be a valid Claude Code marketplace (i.e., `claude plugin marketplace add
  <path>` succeeds)
- Contain a `.claude-plugin/marketplace.json` file (see Section 4.2.1)
- Contain 1 to many plugins, each in its own subdirectory with a
  `.claude-plugin/plugin.json`
- Be entirely self-contained (no references to files outside its own directory)
- Reside at any level of the
  `common/<domain>/<runtime>/<build-tool>/<framework>/<architecture>` hierarchy

Each marketplace subdirectory MUST NOT:
- Reference files from sibling marketplace directories or other hierarchy
  branches
- Depend on files at the monorepo root or at intermediate hierarchy directories
- Contain nested marketplaces (a marketplace is a leaf in the organizational
  hierarchy)

#### 4.2.1 `marketplace.json` Schema

Each marketplace MUST contain `.claude-plugin/marketplace.json` at the
marketplace root.
This file is the marketplace catalog that Claude Code reads when the marketplace
is
registered via `claude plugin marketplace add <path>`.

**Required fields:**

| Field | Type | Description |
|---|---|---|
| `name` | string (kebab-case) | Marketplace identifier. MUST be globally unique across all monorepos consumed on a given machine. Use the flattened RPM name (e.g., `rpm-claude-marketplaces-sdlc-tools`). |
| `owner` | object | Maintainer info. `name` (string, required), `email` (string, optional). |
| `plugins` | array | List of available plugins in this marketplace. Each entry references a plugin subdirectory. |

**Each entry in `plugins` array:**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string (kebab-case) | Yes | Plugin identifier. |
| `source` | string | Yes | Relative path to the plugin directory (e.g., `"./plugins/review-plugin"`). |
| `description` | string | No | Brief description of the plugin. |
| `version` | string (semver) | No | Plugin version. |

**Example `marketplace.json`:**

```json
{
  "name": "rpm-claude-marketplaces-sdlc-tools",
  "owner": {
    "name": "Caylent Platform Team",
    "email": "platform@caylent.com"
  },
  "metadata": {
    "description": "Universal SDLC tools for all projects"
  },
  "plugins": [
    {
      "name": "workflow-plugin",
      "source": "./workflow-plugin",
      "description": "Git workflow automation",
      "version": "1.0.0"
    },
    {
      "name": "review-plugin",
      "source": "./review-plugin",
      "description": "Code review tooling",
      "version": "1.0.0"
    }
  ]
}
```

**Reserved marketplace names** (Claude Code blocks these):
`claude-code-marketplace`, `claude-code-plugins`, `claude-plugins-official`,
`anthropic-marketplace`, `anthropic-plugins`, `agent-skills`, `life-sciences`.

#### 4.2.2 Marketplace Directory Structure

```text
<marketplace-name>/
├── .claude-plugin/
│   └── marketplace.json           ← marketplace catalog (required)
├── <plugin-a>/
│   ├── .claude-plugin/
│   │   └── plugin.json            ← plugin manifest (required)
│   ├── commands/                  ← custom slash commands (optional)
│   ├── agents/                    ← custom agents (optional)
│   ├── skills/                    ← custom skills (optional)
│   ├── hooks/                     ← hook configurations (optional)
│   │   └── hooks.json
│   └── scripts/                   ← supporting scripts (optional)
├── <plugin-b>/
│   └── ...
├── LICENSE
└── README.md
```

### 4.3 Plugin Metadata Requirements (`plugin.json`)

Each plugin MUST contain `.claude-plugin/plugin.json` at the plugin root. If
omitted,
Claude Code auto-discovers components and derives the plugin name from the
directory name.

**Required fields:**

| Field | Type | Description |
|---|---|---|
| `name` | string (kebab-case) | Unique plugin identifier. |

**Optional fields:**

| Field | Type | Description |
|---|---|---|
| `version` | string (semver) | Plugin version (required for updates — users won't see changes without a version bump). |
| `description` | string | Brief plugin description. |
| `author` | object | Author info: `name` (required), `email` (optional). |
| `homepage` | string | Documentation URL. |
| `repository` | string | Source code URL. |
| `license` | string | SPDX license identifier. |
| `keywords` | array of strings | Discovery tags. |
| `commands` | string or array | Path(s) to custom command files/directories. |
| `agents` | string or array | Path(s) to custom agent files. |
| `skills` | string or array | Path(s) to custom skill directories. |
| `hooks` | string, array, or object | Hook config paths or inline config. |
| `mcpServers` | string, array, or object | MCP server configurations. |
| `outputStyles` | string or array | Output style files/directories. |
| `lspServers` | string, array, or object | Language Server Protocol configurations. |

**Example `plugin.json`:**

```json
{
  "name": "workflow-plugin",
  "version": "1.0.0",
  "description": "Git workflow automation for SDLC",
  "author": {
    "name": "Caylent Platform Team"
  },
  "commands": "./commands/",
  "skills": "./skills/"
}
```

**Auto-discovery defaults** (if component paths are omitted):
- `commands/` for custom commands
- `agents/` for custom agents
- `skills/` for custom skills
- `hooks/hooks.json` for hooks
- `.mcp.json` for MCP servers
- `.lsp.json` for LSP servers

**Runtime variable:** Use `${CLAUDE_PLUGIN_ROOT}` in hooks and MCP server
configs to
reference the plugin's installation directory.

**Caching:** Marketplace plugins are copied to `~/.claude/plugins/cache/` when
installed.
Plugins cannot reference files outside their own directory.

### 4.4 Semantic Tag Convention

Tags follow the monorepo convention: `<marketplace-path>/<semver>`

The `<marketplace-path>` is the marketplace's path relative to the
`marketplace_root`
(defined in `config-repo.json`, typically `common`). The `marketplace_root`
prefix is
stripped from tags to avoid unnecessary filesystem noise — this follows the
monorepo
community standard where tags use logical package paths, not full filesystem
paths.

```text
sdlc-tools/1.0.0                                                                ← universal
sdlc-tools/1.1.0
security-review/1.0.0                                                           ← universal
development/python/python-commons/1.0.0                                         ← runtime level (all Python)
development/python/uv/quality-agent/1.0.0                                       ← build-tool level (Python + uv)
development/python/uv/django/django-helpers/1.0.0                               ← framework level (Python + uv + Django)
development/python/uv/django/django-helpers/1.1.0
development/python/uv/django/frontend/django-frontend/1.0.0                     ← architecture level (most specific)
development/node/node-commons/1.0.0                                             ← runtime level (all Node.js)
development/node/npm/express/express-patterns/1.0.0                             ← framework level (Node + npm + Express)
development/node/npm/express/microservice/express-scaffolding/1.0.0             ← architecture level (most specific)
development/dotnet/dotnet-commons/1.0.0                                         ← runtime level (all .NET)
development/dotnet/nuget/aspnet/aspnet-scaffolding/1.0.0                        ← framework level (.NET + NuGet + ASP.NET)
```

**Rules:**
- The tag prefix MUST match an existing marketplace directory path relative to
  `marketplace_root`
- The tag suffix MUST be a valid semantic version (MAJOR.MINOR.PATCH)
- Tags are immutable: once pushed, never moved or deleted
- A tag represents the release of that specific marketplace at that version
- The monorepo state at the tagged commit is the release artifact
- Git tags support `/` in names, so the full hierarchy path is preserved

### 4.5 Monorepo Configuration: `config-repo.json`

The plugin monorepo MUST contain a `config-repo.json` file at the repository
root. This
file is the single source of truth for the monorepo's structural rules,
including which
directories are organizational containers versus marketplaces, and how
marketplace paths
are flattened into filesystem-safe names.

```json
{
  "monorepo_name": "rpm-claude-marketplaces",
  "marketplace_root": "common",
  "reserved_directories": [
    "development", "example", "marketing", "legal", "data",
    "python", "node", "dotnet",
    "uv", "npm", "nuget", "make",
    "django", "express", "aspnet", "argparse",
    "frontend", "microservice", "serverless", "cli"
  ],
  "flattening_strip_prefixes": ["common", "development"]
}
```

**Field definitions:**

| Field | Type | Purpose |
|---|---|---|
| `monorepo_name` | string | The git repository name (e.g., `rpm-claude-marketplaces`). Used as the prefix for checkout directories and symlink names. |
| `marketplace_root` | string | The top-level directory containing all marketplaces. Always stripped from flattened names. This directory is implicitly reserved (organizational container). |
| `reserved_directories` | string[] | Directory names that are organizational containers, never marketplaces. CI validates that no reserved directory contains `plugin.json` files. Any directory under `marketplace_root` that is NOT reserved and is NOT an intermediate path to a deeper reserved directory MUST be a marketplace. |
| `flattening_strip_prefixes` | string[] | **Ordered** list of path components to strip from the beginning of marketplace paths when computing flattened names. Only consecutive leading segments are stripped, matching the list in order. See Section 4.6 for the algorithm. |

**Reserved directory semantics:**

A **reserved directory** is an organizational container that structures the
monorepo
hierarchy. It MUST NOT contain `plugin.json` files (it is not a marketplace). It
MAY
contain child directories that are either other reserved directories or
marketplaces.

At any level under `marketplace_root`, a directory MUST be one of:
1. **Reserved** (listed in `reserved_directories`) — organizational container,
   can have children
2. **Not reserved** — MUST be a marketplace (contains 1+ plugin subdirectories
   with `plugin.json`)

This rule ensures the monorepo structure is unambiguous: CI can determine
whether any
directory is a marketplace or an organizational container by checking it against
`reserved_directories`.

**Adding new hierarchy levels:** When a new technology or domain needs
organizational
nesting (e.g., adding a `rust` ecosystem), add the directory name to
`reserved_directories` in `config-repo.json`. This is a monorepo-level change
that
requires platform team review via CODEOWNERS.

### 4.6 Path Flattening Algorithm

Marketplace paths in the monorepo hierarchy (e.g.,
`common/development/python/uv/quality-agent`)
must be flattened into dash-separated names for use in checkout directories,
symlink names,
and manifest `path` attributes. The flattening algorithm uses `config-repo.json`
to determine
which leading path components to strip.

**Algorithm:**

1. Start with the marketplace's full hierarchy path (e.g.,
   `common/development/python/uv/quality-agent`)
2. Split into path segments: `["common", "development", "python", "uv",
   "quality-agent"]`
3. Strip consecutive leading segments that match `flattening_strip_prefixes`
   **in order**:
   - Compare segment 0 (`common`) with `flattening_strip_prefixes[0]` (`common`)
     → match, strip
   - Compare segment 1 (`development`) with `flattening_strip_prefixes[1]`
     (`development`) → match, strip
   - No more prefix entries → stop stripping
4. Join remaining segments with `-`: `python-uv-quality-agent`

**The stripping is sequential and ordered.** If segment N does not match
`flattening_strip_prefixes[N]`, stripping stops immediately regardless of
whether later
segments would match. This prevents ambiguous or inconsistent results.

**Examples using the default configuration:**

| Marketplace Path | After Stripping | Flattened Name |
|---|---|---|
| `common/sdlc-tools` | Strip `common`. Next: `sdlc-tools` ≠ `development` → stop | `sdlc-tools` |
| `common/security-review` | Strip `common`. Next: `security-review` ≠ `development` → stop | `security-review` |
| `common/development/python/uv/quality-agent` | Strip `common`, strip `development` → done | `python-uv-quality-agent` |
| `common/development/python/uv/django/django-helpers` | Strip `common`, strip `development` → done | `python-uv-django-django-helpers` |
| `common/development/node/npm/quality-agent` | Strip `common`, strip `development` → done | `node-npm-quality-agent` |
| `common/marketing/campaign-tools` | Strip `common`. Next: `marketing` ≠ `development` → stop | `marketing-campaign-tools` |

**Why non-stripped reserved directories are kept in flattened names:** Reserved
directories
like `python`, `uv`, `django`, `node`, `npm` are organizational containers
(never
marketplaces) but carry technology-specific meaning essential for
**uniqueness**. If these
were stripped, `common/development/python/uv/quality-agent` and
`common/development/node/npm/quality-agent` would both flatten to
`quality-agent` — a
collision. By keeping them in the flattened name, each marketplace has a unique
identifier
that reflects its position in the technology hierarchy.

**Uniqueness invariant:** CI MUST validate that all marketplace flattened names
(computed
by this algorithm) are unique across the entire monorepo. If two marketplace
paths produce
the same flattened name, the CI pipeline MUST fail. This is enforced in addition
to the
filesystem-level uniqueness of full marketplace paths.

---

## 5. RPM Manifest Configuration

### 5.1 Project Entry Pattern

Each marketplace the consumer project needs is declared as a separate
`<project>` entry in
the manifest XML. All entries for the same monorepo share the same `name`
attribute but
differ in `path` and `revision`.

```xml
<project name="<monorepo-repo-name>"
         path=".packages/<monorepo-repo-name>-<flattened-marketplace-path>"
         remote="<remote-name>"
         revision="refs/tags/<marketplace-path>/<semver-or-constraint>">
  <linkfile src="<marketplace-path>"
            dest="${CLAUDE_MARKETPLACES_DIR}/<monorepo-repo-name>-<flattened-marketplace-path>" />
</project>
```

**Path transformation examples:**

| Marketplace Path (in monorepo) | Flattened (for `path` + `dest`) | Tag (for `revision`) |
|---|---|---|
| `common/sdlc-tools` | `sdlc-tools` | `refs/tags/sdlc-tools/1.0.0` |
| `common/development/python/uv/django/django-helpers` | `python-uv-django-django-helpers` | `refs/tags/development/python/uv/django/django-helpers/1.0.0` |
| `common/development/node/npm/express/express-patterns` | `node-npm-express-express-patterns` | `refs/tags/development/node/npm/express/express-patterns/1.0.0` |
| `common/development/dotnet/nuget/aspnet/aspnet-scaffolding` | `dotnet-nuget-aspnet-aspnet-scaffolding` | `refs/tags/development/dotnet/nuget/aspnet/aspnet-scaffolding/1.0.0` |

**Who computes flattened names:** The flattened names in the `path` and `dest`
attributes
are authored by the **manifest maintainer** when writing
`claude-marketplaces.xml` files.
The flattening algorithm (Section 4.6) defines how to compute them from the
marketplace's
hierarchy path using the `flattening_strip_prefixes` in `config-repo.json`. The
`repo` tool
does not perform flattening; it uses the literal `path` and `dest` values from
the manifest.
**CI MUST validate** that every `path` and `dest` in `claude-marketplaces.xml`
files matches
the expected flattened name computed by the algorithm. This prevents human error
in manifest
authoring.

**Note on `<linkfile>` src:** The `src` attribute uses the **original hierarchy
path**
(with `/` separators), not the flattened form. This is the path to the
marketplace
directory within the monorepo checkout. The `repo` tool's `<linkfile>` supports
nested
`src` paths. It creates a symlink from the `dest` location pointing to
`<checkout-path>/<src>`.

**Note on `<linkfile>` dest:** The `repo` tool resolves `<linkfile>` dest paths
relative
to the repo client top directory (the project root). Since
`$HOME/.claude-marketplaces/` lives
outside the project, the `dest` attribute must use either:
- An environment variable placeholder resolved by `repo envsubst`
  (e.g., `${CLAUDE_MARKETPLACES_DIR}`), **preferred**, keeps manifests portable
- A relative path with `../` traversal to reach `$HOME` (fragile, depends on
  checkout depth)

The `CLAUDE_MARKETPLACES_DIR` environment variable MUST be set in `.rpmenv` and
exported
before `repo envsubst` runs, so that the placeholder is resolved to the absolute
path
(e.g., `/home/<user>/.claude-marketplaces`).

> **Note:** The standard `repo` tool restricts `<linkfile dest>` to paths within
the
> project tree. Our Caylent fork MUST support absolute `dest` paths after
`envsubst`
> resolution. See Section 17 for required fork enhancements.

**Attribute breakdown:**

| Attribute | Value | Purpose |
|---|---|---|
| `name` | Monorepo repo name | Identifies the git repository to clone; shared across all marketplace entries |
| `path` | `.packages/<repo>-<flattened-marketplace-path>` | Checkout location; unique per marketplace |
| `remote` | Remote name from `remote.xml` | Git remote hosting the monorepo |
| `revision` | `refs/tags/<marketplace-path>/<semver-or-constraint>` | Exact tag or version constraint (see Section 5.5) |
| `linkfile src` | `<marketplace-path>` | Subdirectory path within the monorepo checkout (hierarchy `/` separators) |
| `linkfile dest` | `${CLAUDE_MARKETPLACES_DIR}/<repo>-<flattened-marketplace-path>` | Symlink target in user home marketplace folder (flattened with `-`) |

### 5.2 Manifest Composition

Marketplace entries live in dedicated `claude-marketplaces.xml` files at each
level of the
hierarchy, separate from build-tooling `packages.xml` files. Each level includes
the
`claude-marketplaces.xml` from the level above it, creating a **cascading
inheritance chain**.
This mirrors the existing `<include>` composition pattern used by `meta.xml` and
`packages.xml`.

**How cascading inheritance works:** A consumer project's `meta.xml` includes
the
`claude-marketplaces.xml` at its own hierarchy level. That file includes the one
from
its parent level, which includes its parent, and so on up to the root. The
`repo` tool
resolves the entire `<include>` chain and merges all `<project>` entries, so the
consumer project automatically receives every marketplace from its own level AND
every
level above it.

**Example: what a Python/uv/Django/frontend project receives:**

```text
ROOT common/ claude-marketplaces.xml                                       →  sdlc-tools, security-review
  ↑ included by
common/development/ claude-marketplaces.xml                                →  (no marketplace at this level, just passes through)
  ↑ included by
common/development/python/ claude-marketplaces.xml                         →  python-commons
  ↑ included by
common/development/python/uv/ claude-marketplaces.xml                      →  quality-agent
  ↑ included by
common/development/python/uv/django/ claude-marketplaces.xml               →  django-helpers
  ↑ included by
common/development/python/uv/django/frontend/ claude-marketplaces.xml      →  django-frontend
                                                            ─────────────────────────────
                                                            TOTAL: 6 marketplaces installed
```

**This is the core organizational principle:** where you place a marketplace in
the
monorepo hierarchy determines which projects automatically receive it. To add a
plugin
that benefits all Python projects, place it in a marketplace under
`common/development/python/`. To add a
plugin for only Django projects, place it under
`common/development/python/uv/django/`. Universal plugins
go at `common/`.

```text
repo-specs/
├── git-connection/
│   └── remote.xml                                  ← shared remote definitions
├── common/
│   ├── claude-marketplaces.xml                     ← UNIVERSAL marketplaces (root)
│   └── development/
│       ├── claude-marketplaces.xml                 ← development-wide (includes ../claude-marketplaces.xml)
│       ├── python/
│       │   ├── claude-marketplaces.xml             ← Python-wide (includes ../claude-marketplaces.xml)
│       │   └── uv/
│       │       ├── claude-marketplaces.xml         ← Python+uv (includes ../claude-marketplaces.xml)
│       │       └── django/
│       │           ├── claude-marketplaces.xml     ← Python+uv+Django (includes ../claude-marketplaces.xml)
│       │           └── frontend/
│       │               ├── packages.xml            ← build-tooling packages
│       │               ├── claude-marketplaces.xml ← most specific (includes ../claude-marketplaces.xml)
│       │               └── meta.xml                ← top-level manifest
│       ├── node/
│       │   ├── claude-marketplaces.xml             ← Node.js-wide (includes ../../claude-marketplaces.xml)
│       │   └── npm/
│       │       └── express/
│       │           ├── claude-marketplaces.xml     ← Node+npm+Express (includes ../claude-marketplaces.xml)
│       │           └── microservice/
│       │               ├── packages.xml
│       │               ├── claude-marketplaces.xml ← includes ../claude-marketplaces.xml
│       │               └── meta.xml
│       └── dotnet/
│           ├── claude-marketplaces.xml             ← .NET-wide (includes ../../claude-marketplaces.xml)
│           └── nuget/
│               └── aspnet/
│                   ├── claude-marketplaces.xml     ← .NET+NuGet+ASP.NET (includes ../claude-marketplaces.xml)
│                   └── microservice/
│                       ├── packages.xml
│                       ├── claude-marketplaces.xml ← includes ../claude-marketplaces.xml
│                       └── meta.xml
```

**Cascading `<include>` chain (example:
`common/development/python/uv/django/frontend`):**

Each `claude-marketplaces.xml` includes the one from its parent level, forming
an inheritance
chain from leaf to root. Every level follows the same pattern; only the
`<include>`
target and `<project>` entries differ:

```xml
<!-- PATTERN: repo-specs/<hierarchy-level>/claude-marketplaces.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <!-- Include parent level's claude-marketplaces.xml (omitted at root) -->
  <include name="repo-specs/<parent-hierarchy-level>/claude-marketplaces.xml" />

  <!-- Marketplace entries specific to THIS level only -->
  <project name="<monorepo>" path=".packages/<monorepo>-<flattened-marketplace-path>"
           remote="<remote>" revision="refs/tags/<marketplace-path-relative-to-marketplace-root>/<semver-or-constraint>">
    <linkfile src="<marketplace-path>"
              dest="${CLAUDE_MARKETPLACES_DIR}/<monorepo>-<flattened-marketplace-path>" />
  </project>
</manifest>
```

**Concrete example, leaf level:**

```xml
<!-- repo-specs/common/development/python/uv/django/frontend/claude-marketplaces.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <include name="repo-specs/common/development/python/uv/django/claude-marketplaces.xml" />
  <project name="<monorepo>" path=".packages/<monorepo>-python-uv-django-frontend-django-frontend"
           remote="<remote>" revision="refs/tags/development/python/uv/django/frontend/django-frontend/1.0.0">
    <linkfile src="common/development/python/uv/django/frontend/django-frontend"
              dest="${CLAUDE_MARKETPLACES_DIR}/<monorepo>-python-uv-django-frontend-django-frontend" />
  </project>
</manifest>
```

**Concrete example, root level (no parent `<include>`):**

```xml
<!-- repo-specs/common/claude-marketplaces.xml (ROOT, universal marketplaces + install tool) -->
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <include name="repo-specs/git-connection/remote.xml" />

  <!-- Install tool package (required by all marketplace consumers) -->
  <project name="rpm-claude-marketplaces-install"
           path=".packages/rpm-claude-marketplaces-install"
           remote="caylent"
           revision="main" />

  <!-- Universal marketplace entries -->
  <project name="<monorepo>" path=".packages/<monorepo>-sdlc-tools"
           remote="<remote>" revision="refs/tags/sdlc-tools/1.0.0">
    <linkfile src="common/sdlc-tools" dest="${CLAUDE_MARKETPLACES_DIR}/<monorepo>-sdlc-tools" />
  </project>
  <project name="<monorepo>" path=".packages/<monorepo>-security-review"
           remote="<remote>" revision="refs/tags/security-review/1.0.0">
    <linkfile src="common/security-review" dest="${CLAUDE_MARKETPLACES_DIR}/<monorepo>-security-review" />
  </project>
</manifest>
```

**Note:** The root `claude-marketplaces.xml` includes the
`rpm-claude-marketplaces-install`
package as a `<project>` entry. This ensures that every project using Claude
Code
marketplaces automatically receives the install and uninstall scripts. The
install tool
package is a separate public repo
(`caylent-solutions/rpm-claude-marketplaces-install`,
Apache 2.0 licensed) that is synced to
`.packages/rpm-claude-marketplaces-install/`.

**Resulting include chain for a Python/uv/Django/Frontend project:**

```text
meta.xml
  ├── remote.xml                                       (remotes)
  ├── packages.xml                                     (build packages)
  └── claude-marketplaces.xml (frontend level)
        └── claude-marketplaces.xml (django level)
              └── claude-marketplaces.xml (uv level)
                    └── claude-marketplaces.xml (python level)
                          └── claude-marketplaces.xml (development level)
                                └── claude-marketplaces.xml (common level, universal)
```

A `common/development/python/uv/django/frontend` project automatically receives
marketplaces from ALL
levels: universal + development + Python + Python/uv + Python/uv/Django +
Python/uv/Django/Frontend.

**`meta.xml` references only the leaf `claude-marketplaces.xml`; inheritance
handles the rest:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <include name="repo-specs/git-connection/remote.xml" />
  <include name="repo-specs/common/development/python/uv/django/frontend/packages.xml" />
  <include name="repo-specs/common/development/python/uv/django/frontend/claude-marketplaces.xml" />
</manifest>
```

**`remote.xml` — shared remote definitions:**

```xml
<!-- repo-specs/git-connection/remote.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="caylent"
          fetch="${GITBASE}" />
  <default revision="main"
           remote="caylent"
           sync-j="4" />
</manifest>
```

The `${GITBASE}` placeholder is resolved by `repo envsubst` to the value from
`.rpmenv`
(e.g., `https://github.com/caylent-solutions/`). All `<project>` entries
referencing
`remote="caylent"` use this as the base URL, with `name` appended (e.g., fetch
URL
becomes `https://github.com/caylent-solutions/rpm-claude-marketplaces.git`).

**`packages.xml` — build-tooling packages (example for
Python/uv/Django/Frontend):**

```xml
<!-- repo-specs/common/development/python/uv/django/frontend/packages.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <project name="rpm-python-uv"
           path=".packages/rpm-python-uv"
           remote="caylent"
           revision="main" />
</manifest>
```

Build packages use a single `<project>` entry per package repo. They do NOT use
`<linkfile>` (build packages are not Claude Code marketplaces). Multiple levels
may
define `packages.xml` if additional build packages are needed at that level.

**`repo envsubst` behavior:**

The `repo envsubst` command operates on all manifest XML files within the
source's
`.repo/manifests/` directory. It substitutes `${VAR}` placeholders with the
values of
exported environment variables. The following variables MUST be exported before
running
`repo envsubst`:

| Variable | Source | Example Value |
|---|---|---|
| `GITBASE` | `.rpmenv` | `https://github.com/caylent-solutions/` |
| `CLAUDE_MARKETPLACES_DIR` | `.rpmenv` (shell expands `${HOME}` at source time) | `/home/vscode/.claude-marketplaces` |

When `.rpmenv` is sourced by the shell, `${HOME}` in
`CLAUDE_MARKETPLACES_DIR=${HOME}/.claude-marketplaces` is resolved by the shell
to the
actual home directory path. The resulting fully-resolved value is then exported
and used
by `repo envsubst`. In multi-source mode, `repo envsubst` runs **per-source**
(after
`repo init`, before `repo sync`) within each source's `.rpm/sources/<name>/`
directory.

Projects at different hierarchy positions (e.g.,
`common/development/python/uv/django/frontend` vs
`common/development/node/npm/express/microservice`) get completely different
marketplace sets except for
the shared universal root.

### 5.3 Resolved Marketplace Set

After cascading resolution, a `common/development/python/uv/django/frontend`
project's effective
marketplace set is the union of all `<project>` entries from every
`claude-marketplaces.xml`
in the chain:

| Source Level | Marketplace Entries |
|---|---|
| Root (universal) | `common/sdlc-tools`, `common/security-review` |
| `common/development/python/` | `common/development/python/python-commons` |
| `common/development/python/uv/` | `common/development/python/uv/quality-agent` |
| `common/development/python/uv/django/` | `common/development/python/uv/django/django-helpers` |
| `common/development/python/uv/django/frontend/` | `common/development/python/uv/django/frontend/django-frontend` |

Each entry follows the `<project>` pattern defined in Section 5.1.

### 5.4 `repo` Tool Behavior With Same-Name Projects

**Why this matters:** The cascading `<include>` chain (Section 5.2) causes
multiple
`<project>` entries to share the **same monorepo `name`** (e.g.,
`rpm-claude-marketplaces`)
but with different `path` and `revision` values, one per marketplace. This is
how a single
monorepo gets checked out multiple times, each marketplace at its own version
into its own
`.packages/` subdirectory. The `repo` tool explicitly supports this pattern:

1. **Shared object store:** All checkouts of the same `name` within a source
   share a single
      `.rpm/sources/<source>/.repo/project-objects/<name>.git/`. The monorepo's
   git objects are
      fetched and stored once, then referenced by all marketplace checkouts, no
   redundant downloads.
2. **Serialized fetch:** The `repo` tool groups same-name projects and fetches
   them
      serially within the same worker thread to prevent race conditions on the
   shared
   object store.
3. **Independent working trees:** Each `<project>` entry gets its own working
   directory
      at its specified `path`, checked out to its own `revision` (tag). This is
   what enables
      independent semantic versioning per marketplace. `sdlc-tools` can be at
   `1.2.0` while
   `quality-agent` is at `3.0.1`.
4. **Precious objects:** The `repo` tool automatically enables `preciousObjects`
   on
      shared object stores to prevent garbage collection from pruning objects
   needed by
   other checkouts.
5. **Linkfile for directories:** The `repo` tool's `<linkfile>` element supports
      directory targets (not just files). This is required because each
   `<linkfile src>`
      points to a marketplace directory within the checkout, creating a symlink
   from
   `${CLAUDE_MARKETPLACES_DIR}/` to that directory.

### 5.5 Version Constraints (Fuzzy Pinning)

The `revision` attribute in `<project>` entries supports two modes:

**Exact pin (default):** A specific tag resolving to a single commit.

```xml
revision="refs/tags/development/python/uv/quality-agent/1.2.3"
```

**Version constraint (fuzzy):** A Python PEP 440-compatible version constraint
that
the Caylent `repo` fork resolves at sync time by scanning available tags and
selecting
the highest version that satisfies the constraint.

```xml
<!-- Patch updates only (1.2.x) -->
revision="refs/tags/development/python/uv/quality-agent/~=1.2.0"

<!-- Minor and patch updates (1.x) -->
revision="refs/tags/development/python/uv/quality-agent/~=1.0"

<!-- Latest available version -->
revision="refs/tags/development/python/uv/quality-agent/*"
```

**Supported constraint syntax (PEP 440):**

| Constraint | Meaning | Resolves to |
|---|---|---|
| `1.2.3` | Exact pin | Only `1.2.3` |
| `~=1.2.0` | Patch-compatible | Highest `1.2.x` (e.g., `1.2.7`) |
| `~=1.2` | Minor-compatible | Highest `1.x.y` where `x >= 2` (e.g., `1.5.0`) |
| `>=1.0.0,<2.0.0` | Range | Highest within range |
| `*` | Latest | Highest available tag |

**How it works:** During `repo sync`, the Caylent fork scans all tags matching
the
`<marketplace-path>/` prefix, parses the semver suffix of each tag, evaluates
the
constraint, and checks out the highest matching version. The resolved version is
logged so the developer knows exactly which version was selected.

> **Note:** Our Caylent fork MUST support version constraint resolution in the
> `revision` attribute. See Section 17 for required fork enhancements.

**This applies to both build packages and plugin marketplaces.** Any `<project>`
entry
in `packages.xml` or `claude-marketplaces.xml` can use version constraints in
its
`revision` attribute.

**When to use version constraints:**

| Use Case | Recommended Constraint | Rationale |
|---|---|---|
| Production projects | Exact pin (`1.2.3`) | Full control, no surprises |
| Active development | Patch-compatible (`~=1.2.0`) | Auto-receive bug fixes |
| Greenfield/prototyping | Minor-compatible (`~=1.0`) | Stay current with features |
| Internal tooling | Latest (`*`) | Always latest, fast iteration |

**REQUIREMENT: Version constraints MUST NOT be used unless the package or
marketplace
has comprehensive unit and functional testing in place.** Fuzzy constraints
allow
automatic version updates at sync time. Without test coverage, an update could
silently
break the developer's workflow. Projects using constraints accept the
responsibility
of validating that upstream changes are compatible.

**Guideline for marketplace and package maintainers:**
- Patch releases (x.y.Z) MUST be backward-compatible bug fixes only
- Minor releases (x.Y.0) MUST be backward-compatible feature additions
- Major releases (X.0.0) MAY contain breaking changes
- Maintainers who violate semver compatibility break downstream consumers using
  constraints

---

## 6. Namespace Control and Collision Avoidance

### 6.1 Claude Code Native Namespacing

Claude Code provides built-in namespace isolation that handles most collision
concerns
natively. Understanding this is critical: it means the RPM delivery layer does
NOT need
to solve plugin-level namespacing; Claude Code already does.

**`plugin@marketplace` composite keys:**

Claude Code identifies every installed plugin by the composite key
`<plugin-name>@<marketplace-name>`. This is stored in
`~/.claude/plugins/installed_plugins.json` and used throughout the system
(settings,
blocklist, enablement). Two plugins with the same name from different
marketplaces are
distinct entries because the marketplace qualifier differs.

**Skill namespacing:**

Plugin skills are namespaced by plugin name using `:` syntax. A skill named
`review`
in a plugin named `code-quality` becomes `/code-quality:review`. The Claude Code
documentation states: "Plugin skills are always namespaced to prevent conflicts
when
multiple plugins have skills with the same name."

**Marketplace identification:**

The `name` field in `marketplace.json` (not the filesystem path) is the
marketplace
identifier. Claude Code uses this name as the key in
`~/.claude/plugins/known_marketplaces.json`.

**Marketplace name collision behavior (verified from CLI source):**

When `claude plugin marketplace add` is called with a marketplace whose `name`
already
exists in `known_marketplaces.json`, Claude Code does **not** reject the
addition.
Instead, it applies **last-write-wins** semantics:

1. If the **same source** (e.g., same git repo) is already registered under any
   name,
   the CLI returns early with "already materialized", no duplicate is created
2. If a **different source** uses the same `name`, the CLI logs a debug warning
      (`"Marketplace '<name>' exists with different source, overwriting"`) and
   **replaces
   the existing entry**. The old marketplace is silently removed
3. If the existing marketplace is **seed-managed** (admin-provisioned), the CLI
   throws
   an error and refuses to overwrite

This means marketplace `name` values in `marketplace.json` MUST be globally
unique
across all monorepos consumed on a given machine. The RPM naming convention
(`rpm-claude-marketplaces` prefix) and the install script SHOULD validate that
no
two marketplace directories declare the same `name` in their `marketplace.json`.

**Reserved name protection:**

Claude Code blocks a hardcoded set of reserved names (e.g.,
`claude-plugins-official`,
`anthropic-marketplace`, `agent-skills`) and rejects any non-Anthropic source
attempting
to use them. An impersonation regex also blocks names like
`official-claude-plugins`.

**Intra-marketplace validation:**

Claude Code validates that no two plugins within a single marketplace share the
same
`name` value, reporting: `"Duplicate plugin name '<name>' found in
marketplace"`.

**Cross-marketplace plugin isolation:**

Plugins from different marketplaces with the same plugin name are fully isolated
via
the `plugin@marketplace` composite key. They occupy separate cache directories
(`~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`) and separate
entries in
`installed_plugins.json`. No collision is possible at the plugin level.

### 6.2 RPM Delivery Layer Uniqueness

The RPM layer provides filesystem and manifest-level guarantees that operate
below
Claude Code's namespacing, preventing conflicts before plugins reach the CLI:

| Layer | Enforced By | Guarantee |
|---|---|---|
| Monorepo directory paths | Filesystem | Each marketplace path within the monorepo is unique |
| Semantic tags | Git | Tags use `<marketplace-path>/<semver>`, globally unique per repo |
| RPM checkout paths | `repo` tool manifest parser | Each `<project>` has a unique `path`; duplicates raise `ManifestParseError` |
| Marketplace symlinks | `<linkfile>` + filesystem | Each symlink in `$HOME/.claude-marketplaces/` has a unique name |

### 6.3 Cross-Monorepo Collision Prevention

If a project consumes marketplaces from multiple monorepos, the `<repo-name>`
prefix in
the marketplace directory name prevents **filesystem** collisions:

```text
~/.claude-marketplaces/rpm-claude-marketplaces-a-sdlc-tools/   ← from monorepo "rpm-claude-marketplaces-a"
~/.claude-marketplaces/rpm-claude-marketplaces-b-sdlc-tools/   ← from monorepo "rpm-claude-marketplaces-b"
```

However, filesystem uniqueness alone is not sufficient. Each marketplace
directory
contains a `marketplace.json` with a `name` field, and Claude Code uses that
`name`
(not the directory path) as its registry key. Because Claude Code applies
last-write-wins
on name collision, the `marketplace.json` `name` values across all consumed
monorepos
MUST be distinct. In single-monorepo deployments (the current primary use case),
the flattening algorithm and CI validation guarantee uniqueness. For future
multi-monorepo deployments, the install script SHOULD verify this invariant
and log a warning if a name conflict is detected before calling
`claude plugin marketplace add`.

---

## 7. Install Script Specification

### 7.1 Script Location and Delivery

The install and uninstall scripts live in a **dedicated RPM package
repository**:
`caylent-solutions/rpm-claude-marketplaces-install` (public, Apache 2.0
licensed).

This package is synced as a `<project>` entry via the root-level
`repo-specs/common/claude-marketplaces.xml` manifest, which means any project
that
uses Claude Code marketplaces automatically receives the install tool. After
sync,
the scripts are available at:

| Script | Path After Sync |
|---|---|
| Install | `.packages/rpm-claude-marketplaces-install/install_claude_marketplaces.py` |
| Uninstall | `.packages/rpm-claude-marketplaces-install/uninstall_claude_marketplaces.py` |

The install script is delivered exclusively via the
`rpm-claude-marketplaces-install`
RPM package, which is synced through the `common/claude-marketplaces.xml`
manifest.
If `RPM_MARKETPLACE_INSTALL=true` and the script is not found at
`.packages/rpm-claude-marketplaces-install/install_claude_marketplaces.py` after
sync,
the target MUST fail-fast with a clear error message.

**Repository:** `caylent-solutions/rpm-claude-marketplaces-install`
- **Visibility:** Public
- **License:** Apache 2.0
- **Purpose:** Contains the install and uninstall scripts for Claude Code
  marketplace
  plugin discovery and registration
- **Synced by:** `repo-specs/common/claude-marketplaces.xml` in
  `caylent-private-rpm`

### 7.2 Preconditions

The scripts MUST be invoked by `rpmConfigure` (install) and `rpmClean`
(uninstall)
respectively, after `repo sync` has completed. The scripts do not perform any
git
operations or `repo` commands. They operate solely on the filesystem state
produced
by `repo sync`.

### 7.3 Configuration

The script reads its configuration from two sources:

| Config | Source | Purpose |
|---|---|---|
| Marketplace directory | `${CLAUDE_MARKETPLACES_DIR}` (defaults to `$HOME/.claude-marketplaces`) | Where to discover plugin marketplaces |
| Claude binary | `claude` on `$PATH` | The `claude` CLI must be on `$PATH`. No fallback paths. |

### 7.4 Required Behavior

#### Step 1: Strict Error Handling

All failures must be immediate and loud. Use Python exception handling with
`sys.exit(1)` on unrecoverable errors.

#### Step 2: Configure Logging

Configure Python `logging` module with structured output. Use `logging.info`,
`logging.warning`, and `logging.error` for all script output.

#### Step 3: Locate Claude Binary

1. Attempt `shutil.which("claude")`
2. If not found, `log_error` and exit with code `127`. No fallback paths.

#### Step 4: Verify Marketplace Directory Exists

Check if `$HOME/.claude-marketplaces` exists.

- If it does NOT exist, log a warning and exit `0`. This is not an error; the
    project's RPM manifest may not declare any Claude Code plugins, or
  `rpmConfigure`
  may not have been run yet.

#### Step 5: Discover Marketplace Entries

List all entries in `$HOME/.claude-marketplaces/` that are:
- Directories (or symlinks to directories)
- NOT dot-prefixed (exclude hidden entries)

Sort the entries alphabetically for deterministic processing order.

If no entries found, log a warning and exit `0`.

#### Step 6: Process Each Marketplace

For each discovered marketplace directory, perform all of the following:

**6a. Validate symlink target:**
- Verify the entry is a symlink (or directory) and its target exists
- If the symlink is broken (target does not exist), `log_error` with the path
  and continue to the next entry (do not abort the entire run)

**6b. Read marketplace name:**
- Parse `.claude-plugin/marketplace.json` from the marketplace directory
- Extract the `name` field (this is the marketplace's registered name, used
  as the `@<marketplace>` qualifier for plugin install commands)
- If `.claude-plugin/marketplace.json` does not exist or has no `name` field,
  `log_error` and continue to the next marketplace entry

**6c. Register marketplace:**
- Run: `claude plugin marketplace add <absolute-path-to-marketplace-directory>`
- Claude Code is idempotent: if the same source path is already registered,
  it returns early ("already materialized"). No pre-check is needed.
- If the command fails (non-zero exit), log error and continue to next entry

**6d. Discover plugins in marketplace:**
- The marketplace directory contains 1 to many plugins, each in its own
  subdirectory
- Each plugin is identified by the presence of `.claude-plugin/plugin.json`
  within an immediate subdirectory of the marketplace
- Read the `name` field from each `.claude-plugin/plugin.json`
- Discovery pattern: `<marketplace-dir>/*/.claude-plugin/plugin.json`

**6e. Install each discovered plugin:**
- For each plugin name discovered in step 6d, run:
  `claude plugin install <plugin-name>@<marketplace-name> --scope user`
  where `<marketplace-name>` is the name extracted in step 6b
- Log success or failure for each plugin individually

#### Step 7: Log Summary

Log the total count of:
- Marketplaces processed
- Marketplaces newly registered
- Plugins installed

Exit `0` on success.

### 7.5 Error Handling Rules

| Condition | Behavior |
|---|---|
| Claude binary not found | Exit `127` with error message |
| `$HOME/.claude-marketplaces/` does not exist | Exit `0` with warning (not an error) |
| No marketplace entries found | Exit `0` with warning (not an error) |
| Broken symlink in `$HOME/.claude-marketplaces/` | Log error for that entry, continue to next |
| `marketplace add` fails | Log error for that entry, continue to next |
| `plugin install` fails | Log error for that plugin, continue to next |
| All entries processed with failures | Exit non-zero with summary of failures |
| All entries processed successfully | Exit `0` with success summary |

### 7.6 Idempotency

The install script MUST be safe to run multiple times:
- Marketplace registration checks before adding (skip if already registered)
- Plugin installation is inherently idempotent (reinstall overwrites)
- No side effects on repeated runs beyond log output

### 7.7 Uninstall Script (`uninstall_claude_marketplaces.py`)

The uninstall script reverses the install script's operations. It is called by
`rpmClean` before removing symlinks and RPM state.

**Steps:**

1. Verify `claude` CLI on PATH (fail-fast with exit 127 if missing)
2. Verify `$CLAUDE_MARKETPLACES_DIR` exists (exit 0 if missing — nothing to
   uninstall)
3. Discover marketplace entries (same logic as install script Step 5)
4. For each marketplace:
      a. Read marketplace name from `.claude-plugin/marketplace.json` (same as
   install Step 6b)
      b. Discover plugins via `.claude-plugin/plugin.json` files (same as
   install Step 6d)
      c. Uninstall each plugin: `claude plugin uninstall
   <plugin-name>@<marketplace-name> --scope user`
      d. Remove marketplace registration: `claude plugin marketplace remove
   <marketplace-name>`
5. Log summary of uninstalled plugins and removed marketplaces

**Error handling:** Same rules as install script (Section 7.5). Individual
failures
do not abort the entire run; all entries are processed and a summary is logged.

**Idempotency:** Safe to run multiple times. Uninstalling an already-uninstalled
plugin
or removing an already-removed marketplace is a no-op.

---

## 8. RPM Bootstrap Integration

### 8.1 Multi-Source `.rpmenv` Format

RPM supports 1-to-many manifest sources. Each source has a URL, revision, and
manifest
path. The `.rpmenv` file uses **named sources** with a registry variable that
controls
discovery and processing order.

```properties
# Repo tool (fork with envsubst + version constraint support)
REPO_URL=https://github.com/caylent-solutions/git-repo.git
REPO_REV=caylent-2.0.0

# Shared env vars for envsubst (exported before repo envsubst)
GITBASE=https://github.com/caylent-solutions/
CLAUDE_MARKETPLACES_DIR=${HOME}/.claude-marketplaces

# Marketplace install toggle (true/false, defaults to false)
# When true, rpmConfigure runs install_claude_marketplaces.py after sync
RPM_MARKETPLACE_INSTALL=true

# Source registry (comma-separated, processed in order)
RPM_SOURCES=build,marketplaces

# Source: build — build tooling packages
RPM_SOURCE_build_URL=https://github.com/caylent-solutions/caylent-private-rpm.git
RPM_SOURCE_build_REVISION=main
RPM_SOURCE_build_PATH=repo-specs/common/development/python/make/argparse/cli/meta.xml

# Source: marketplaces — claude plugin marketplaces
RPM_SOURCE_marketplaces_URL=https://github.com/caylent-solutions/caylent-private-rpm.git
RPM_SOURCE_marketplaces_REVISION=main
RPM_SOURCE_marketplaces_PATH=repo-specs/common/development/python/make/argparse/cli/claude-marketplaces.xml
```

**Named source rules:**

| Rule | Behavior |
|---|---|
| `RPM_SOURCES` is required | Comma-separated list of source names, processed in declaration order |
| Each name requires 3 variables | `RPM_SOURCE_<name>_URL`, `RPM_SOURCE_<name>_REVISION`, `RPM_SOURCE_<name>_PATH` — missing any triggers fail-fast with error naming the missing variable |
| Same URL allowed across sources | Different revisions or paths of the same repo are valid (e.g., same manifest repo at different tags) |
| All `<project path>` values must be unique | After sync, if two sources produce the same package name in `.packages/`, rpmConfigure MUST fail-fast with an error identifying both sources and the conflicting path |
| Source name → directory | Each source gets isolated state under `.rpm/sources/<name>/` |
| All values overridable | Every `.rpmenv` variable can be overridden by an environment variable of the same name (useful for CI/CD pipelines) |

**Multi-source directory structure after sync:**

```text
project-root/
├── .rpm/
│   └── sources/
│       ├── build/
│       │   ├── .repo/              ← repo tool state for build source
│       │   └── .packages/          ← packages synced by build source
│       └── marketplaces/
│           ├── .repo/              ← repo tool state for marketplaces source
│           └── .packages/          ← packages synced by marketplaces source
├── .packages/                      ← symlinks aggregated from all sources
│   ├── pkg-a → ../.rpm/sources/build/.packages/pkg-a
│   ├── pkg-b → ../.rpm/sources/marketplaces/.packages/pkg-b
│   └── rpm-claude-marketplaces-install → ../.rpm/sources/marketplaces/.packages/rpm-claude-marketplaces-install
```

Each source gets its own isolated `.repo/` state and `.packages/` directory
under
`.rpm/sources/<name>/`. The top-level `.packages/` directory contains only
symlinks
aggregated from all sources. This isolation ensures sources do not interfere
with
each other and can be synced independently.

### 8.2 `rpmConfigure` Lifecycle (Multi-Source)

The `rpmConfigure` target MUST execute the following steps in order:

1. Parse `.rpmenv`, discover `RPM_SOURCES` and all `RPM_SOURCE_<name>_*`
   variable groups
2. Validate: all required variables present for each source → fail-fast if
   missing
3. Install repo tool (once): `pipx install git+${REPO_URL}@${REPO_REV}` where
   `REPO_URL`
      and `REPO_REV` are defined in `.rpmenv`. This installs the Caylent fork of
   repo.
4. If `RPM_MARKETPLACE_INSTALL=true`: `mkdir -p $CLAUDE_MARKETPLACES_DIR`,
   pre-sync
   cleanup `rm -rf ${CLAUDE_MARKETPLACES_DIR}/*`
5. For each source in `RPM_SOURCES` order:
   a. `mkdir -p .rpm/sources/<name>`
   b. `cd .rpm/sources/<name>` → `repo init -u <URL> -b <REVISION> -m <PATH>`
   c. Export shared env vars → `repo envsubst`
   d. `repo sync`
6. Aggregate: for each `.rpm/sources/<name>/.packages/*`, create a symlink in
   the top-level `.packages/` directory
7. Collision check: if two sources produce the same package name → fail-fast
   with
   error identifying both sources and the conflicting path
8. Update `.gitignore` with `.rpm/` and `.packages/` if not already present
9. If `RPM_MARKETPLACE_INSTALL=true`:
      a. Look for
   `.packages/rpm-claude-marketplaces-install/install_claude_marketplaces.py`
   b. If not found → fail-fast: `"RPM_MARKETPLACE_INSTALL=true but
            rpm-claude-marketplaces-install package not found. Ensure a
      marketplace source
      is defined in RPM_SOURCES that includes the install tool package."`
      c. Execute `python3
   .packages/rpm-claude-marketplaces-install/install_claude_marketplaces.py`

### 8.3 `rpmClean` Behavior

The `rpmClean` target MUST perform a full teardown of both RPM state and Claude
Code
plugin/marketplace registrations:

```text
1. If RPM_MARKETPLACE_INSTALL=true:
   a. Run uninstall_claude_marketplaces.py (uninstalls plugins and removes marketplaces)
   b. rm -rf $HOME/.claude-marketplaces/
2. rm -rf .packages/ .rpm/
```

Steps MUST execute in this order. Uninstalling plugins first ensures Claude
Code's
registry is clean. Removing marketplaces before deleting symlinks ensures the
CLI can
resolve paths during removal. Deleting `.packages/` and `.rpm/` last avoids
broken
symlinks during the uninstall steps.

### 8.4 `RPM_MARKETPLACE_INSTALL` Toggle

The `RPM_MARKETPLACE_INSTALL` variable controls whether the install script runs
after
sync. It defaults to `false` if not set. This allows projects to use RPM for
build
packages without pulling or installing Claude Code marketplaces.

| Value | Behavior |
|---|---|
| `true` | `rpmConfigure` creates `$CLAUDE_MARKETPLACES_DIR`, cleans it pre-sync, and runs the install script after sync. `rpmClean` runs the uninstall script before cleanup. |
| `false` (default) | `rpmConfigure` skips marketplace directory creation and install script execution. `rpmClean` skips uninstall. |

### 8.5 Makefile Auto-Apply Logic

The existing auto-apply logic in the `Makefile` includes task definitions from
directories in `.packages/`. Monorepo checkouts for Claude Code marketplaces may
contain
files that should NOT be auto-applied as Make targets.

The auto-apply logic SHOULD be verified to confirm that monorepo checkout
directories
do not contain `Makefile` or `.mk` files. If they do, a filter MUST be added to
skip
directories that are monorepo checkouts (identifiable by the
`rpm-claude-marketplaces-<marketplace>` naming pattern, which differs from the
`rpm-<runtime>-<descriptive-name>` pattern used by build packages).

### 8.6 Makefile Implementation Requirements

The `Makefile` MUST implement three public targets: `rpmConfigure`, `rpmClean`,
and
`rpmHostSetup`. All complex logic MUST be delegated to Python scripts located
under
`scripts/rpm/` in the `caylent-private-rpm` repository. The Makefile is a thin
orchestration layer that calls Python — it does NOT contain shell loops, parsing
logic, or conditional branching beyond simple Make prerequisites.

#### Architecture: Makefile delegates to Python

```text
Makefile targets:            Python scripts (scripts/rpm/):
─────────────────            ─────────────────────────────
rpmHostSetup     ──────►     scripts/rpm/host_setup.py
rpmConfigure     ──────►     scripts/rpm/configure.py
rpmClean         ──────►     scripts/rpm/clean.py
```

The Makefile simply calls `python3 scripts/rpm/<script>.py` with the `.rpmenv`
path
as an argument. Each Python script reads `.rpmenv`, performs its work, and exits
with
an appropriate code. This avoids all Make-specific complexity (variable
expansion
differences, per-line shell invocation, CSV parsing in Make syntax).

**Reference Makefile structure:**

```makefile
RPMENV ?= .rpmenv
SCRIPTS_DIR := scripts/rpm

.PHONY: rpmHostSetup rpmConfigure rpmClean

rpmHostSetup:
    python3 $(SCRIPTS_DIR)/host_setup.py $(RPMENV)

rpmConfigure: rpmHostSetup
    python3 $(SCRIPTS_DIR)/configure.py $(RPMENV)

rpmClean:
    python3 $(SCRIPTS_DIR)/clean.py $(RPMENV)
```

**Python script: `scripts/rpm/host_setup.py`**

Acceptance criteria:
1. Read `.rpmenv` path from `sys.argv[1]`
2. Verify `python3`, `repo`, `claude` are on PATH using `shutil.which()`
3. Exit 127 with named error if any tool is missing
4. Idempotent — safe to call every time

**Python script: `scripts/rpm/configure.py`**

Acceptance criteria:
1. Read and parse `.rpmenv` (source it via `subprocess` or parse `KEY=VALUE`
   lines,
   resolving shell variables like `${HOME}`)
2. Parse `RPM_SOURCES` (comma-separated) into an ordered list
3. For each source name, validate that `RPM_SOURCE_<name>_URL`,
   `RPM_SOURCE_<name>_REVISION`,
      and `RPM_SOURCE_<name>_PATH` are all set. Exit non-zero with error naming
   the missing
   variable and source name if any are absent.
4. If `RPM_MARKETPLACE_INSTALL=true`:
   a. `os.makedirs(CLAUDE_MARKETPLACES_DIR, exist_ok=True)`
   b. Remove all contents: delete everything in `CLAUDE_MARKETPLACES_DIR`
5. For each source in order:
   a. `os.makedirs(f".rpm/sources/{name}", exist_ok=True)`
      b. In `.rpm/sources/{name}/`: run `repo init -u <URL> -b <REVISION> -m
   <PATH>`
      c. Export `GITBASE` and `CLAUDE_MARKETPLACES_DIR` to environment, run
   `repo envsubst`
   d. Run `repo sync`
      e. If `repo sync` exits non-zero, abort immediately. Do NOT continue to
   next source.
6. Aggregate: for each `.rpm/sources/{name}/.packages/*`, create symlink in
   `.packages/`.
      If two sources produce the same package name, exit non-zero with error
   naming both
   sources and the conflicting package.
7. Ensure `.gitignore` contains `.packages/` and `.rpm/` entries
8. If `RPM_MARKETPLACE_INSTALL=true`:
      a. Verify
   `.packages/rpm-claude-marketplaces-install/install_claude_marketplaces.py`
   exists
   b. If not found, exit non-zero: "RPM_MARKETPLACE_INSTALL=true but
      rpm-claude-marketplaces-install package not found"
   c. Run the install script via `subprocess`

**Python script: `scripts/rpm/clean.py`**

Acceptance criteria:
1. Read and parse `.rpmenv`
2. If `RPM_MARKETPLACE_INSTALL=true` and uninstall script exists at
   `.packages/rpm-claude-marketplaces-install/uninstall_claude_marketplaces.py`:
   run it via `subprocess`
3. If `RPM_MARKETPLACE_INSTALL=true`: `shutil.rmtree(CLAUDE_MARKETPLACES_DIR)`
4. `shutil.rmtree(".packages/", ignore_errors=True)`
5. `shutil.rmtree(".rpm/", ignore_errors=True)`

**Fail-fast rules (applies to all scripts):**

- No fallback logic of any kind
- No silent failures — every error MUST produce output identifying the failure
- No hard-coded values — all paths, URLs, and configuration come from `.rpmenv`
- Exit non-zero immediately on any failure
- No retry loops or temporal delays
- All subprocess calls MUST check exit codes and propagate failures

**Script location:** These scripts live in `caylent-private-rpm` at
`scripts/rpm/` and
are committed to the repo. They are available before `repo sync` (unlike the
install
script which is delivered by sync). Consumer projects receive them as part of
the
`.packages/` symlink to the build source.

### 8.7 Symlink Chain Architecture

After multi-source aggregation, paths from `$HOME/.claude-marketplaces/` to
actual
files traverse two levels of symlinks:

```text
$HOME/.claude-marketplaces/<monorepo>-<marketplace>/
  → <project-root>/.packages/<monorepo>-<marketplace>/common/<marketplace-path>/
    → <project-root>/.rpm/sources/<source>/.packages/<monorepo>-<marketplace>/common/<marketplace-path>/
```

The first link is created by `<linkfile>` during `repo sync`. The second link is
created
by the aggregation step in `rpmConfigure`. Both are standard filesystem symlinks
and
work correctly on Linux and macOS. Tools that need to resolve the actual
filesystem path
MUST use `readlink -f` or `realpath`, not just the symlink target.

### 8.8 Claude CLI Requirements

The `claude` CLI MUST support the following subcommands (verified during
`rpmHostSetup`):

| Command | Purpose |
|---|---|
| `claude plugin marketplace add <path>` | Register a local marketplace directory |
| `claude plugin marketplace remove <name>` | Unregister a marketplace |
| `claude plugin marketplace list` | List registered marketplaces |
| `claude plugin install <name>@<marketplace> --scope user` | Install a plugin from a marketplace |
| `claude plugin uninstall <name>@<marketplace> --scope user` | Uninstall a plugin |

The spec does not pin a minimum Claude CLI version. The `rpmHostSetup` target
validates
that `claude` is on PATH; the install script validates that the required
subcommands
are functional by checking the exit code of its first `claude plugin`
invocation.

---

## 9. Lifecycle Operations

### 9.0 Project Bootstrapping (How RPM Files Arrive)

Before `make rpmConfigure` can run, the project must contain the RPM bootstrap
files
(`.rpmenv`, `Makefile`). How these files arrive depends on whether the project
uses
Caylent DevContainers.

#### 9.0.1 DevContainer Path: `cdevcontainer setup-devcontainer`

The **Caylent Devcontainer CLI** (`cdevcontainer`) bootstraps projects by
cloning a
**DevContainer catalog repository**, selecting a catalog entry, and copying its
files
into the project. The catalog system has three layers:

| Layer | Source Directory in Catalog Repo | Copied To | Purpose |
|---|---|---|---|
| Catalog entry files | `catalog/<entry-name>/` | `.devcontainer/` | Entry-specific `devcontainer.json`, `catalog-entry.json`, `VERSION`, and additional files |
| Common devcontainer assets | `common/devcontainer-assets/` | `.devcontainer/` | Shared scripts: `postcreate-wrapper.sh`, `.devcontainer.postcreate.sh`, `devcontainer-functions.sh`, `project-setup.sh`, proxy toolkits |
| Root project assets | `common/root-project-assets/` | project root | Organization-wide files (e.g., `CLAUDE.md`, `.claude/`) |

To bootstrap a project with RPM:

```bash
cdevcontainer setup-devcontainer <project-path>
```

Or, to select a specific catalog entry directly:

```bash
cdevcontainer setup-devcontainer --catalog-entry rpm-python-uv <project-path>
```

**Where the RPM files come from:** The RPM bootstrap files are **part of the
catalog
repository**, not generated by the CLI tool itself. The CLI copies them to the
project
just like any other catalog file:

- `.rpmenv` and `Makefile` live in `common/root-project-assets/` (copied to
  project
  root)

The install script is NOT part of the DevContainer catalog. It is delivered
exclusively
by `repo sync` as part of the `rpm-claude-marketplaces-install` RPM package
(synced via
`common/claude-marketplaces.xml`). It appears at
`.packages/rpm-claude-marketplaces-install/install_claude_marketplaces.py` after
sync.

After setup, the project contains:

```text
<project-path>/
├── .rpmenv                                        ← from common/root-project-assets/
├── Makefile                                       ← from common/root-project-assets/
├── CLAUDE.md                                      ← from common/root-project-assets/
├── .devcontainer/
│   ├── devcontainer.json                          ← from catalog entry
│   ├── catalog-entry.json                         ← from catalog entry (augmented with catalog_url)
│   ├── VERSION                                    ← from catalog entry
│   ├── postcreate-wrapper.sh                      ← from common/devcontainer-assets/
│   ├── .devcontainer.postcreate.sh                ← from common/devcontainer-assets/
│   ├── devcontainer-functions.sh                  ← from common/devcontainer-assets/
│   ├── project-setup.sh                           ← from common/devcontainer-assets/ (project team customizes)
│   ├── nix-family-os/                             ← from common/devcontainer-assets/ (proxy toolkit)
│   └── wsl-family-os/                             ← from common/devcontainer-assets/ (proxy toolkit)
└── ...
```

The project team customizes `project-setup.sh` to call `make rpmConfigure` (see
Section 14.2 for the lifecycle hook chain).

**`.rpmenv` contains placeholders that must be filled in.** The `.rpmenv` file
from
`common/root-project-assets/` is a template with placeholder values for
project-specific
RPM configuration. The developer MUST edit these values before opening the
project in a
devcontainer:

```properties
# RPM Configuration
# Fill in the values below before reopening in a devcontainer.

# Repo Tool (fork with envsubst + version constraint support)
REPO_URL=https://github.com/caylent-solutions/git-repo.git
REPO_REV=caylent-2.0.0

# Shared env vars for envsubst (exported before repo envsubst)
GITBASE=<your-git-org-base-url>
CLAUDE_MARKETPLACES_DIR=${HOME}/.claude-marketplaces

# Marketplace install toggle (true/false, defaults to false)
RPM_MARKETPLACE_INSTALL=true

# Source registry (comma-separated, processed in order)
RPM_SOURCES=build,marketplaces

# Source: build — build tooling packages
# REQUIRED: replace URL, revision, and path with your manifest repo values
RPM_SOURCE_build_URL=<your-manifest-repo-url>
RPM_SOURCE_build_REVISION=<your-manifest-tag>
RPM_SOURCE_build_PATH=<path-to-meta.xml-in-manifest-repo>

# Source: marketplaces — claude plugin marketplaces
# REQUIRED: replace URL, revision, and path with your marketplace manifest values
RPM_SOURCE_marketplaces_URL=<your-manifest-repo-url>
RPM_SOURCE_marketplaces_REVISION=<your-manifest-tag>
RPM_SOURCE_marketplaces_PATH=<path-to-claude-marketplaces.xml-in-manifest-repo>
```

Values like `REPO_URL`, `REPO_REV`, `CLAUDE_MARKETPLACES_DIR`, and
`RPM_MARKETPLACE_INSTALL` have sensible defaults and rarely change. The
project-specific values that MUST be filled in are each source's `_URL`,
`_REVISION`,
`_PATH` variables and `GITBASE`.

**The `cdevcontainer code` workflow.** After `cdevcontainer setup-devcontainer`
scaffolds the project, the developer uses `cdevcontainer code` to open the
project in
VS Code on the host:

```bash
cdevcontainer code <project-path>
```

This opens the project **on the host** (not in a devcontainer). What happens
next
depends on whether the project is new or already configured:

**First-time project setup (project lead, once per project):**

1. `cdevcontainer code <project-path>` opens the project on the host
2. Edit `.rpmenv` to fill in the project-specific RPM values (manifest URL, tag,
   etc.)
3. Edit `project-setup.sh` to add `make rpmConfigure` to the lifecycle hook
4. Commit these files to git
5. Reopen in VS Code, accept the "Reopen in Container" prompt
6. The devcontainer builds, `postCreateCommand` runs `project-setup.sh`, which
   calls
   `make rpmConfigure` with the actual values from `.rpmenv`

Once `.rpmenv` and `project-setup.sh` are committed, every subsequent developer
who
clones the project gets RPM automatically. They do not need to edit any files.

**Subsequent developers (project already configured):**

1. Clone the project (`.rpmenv` and `project-setup.sh` are already committed
   with
   real values and `make rpmConfigure` in the hook)
2. `cdevcontainer code <project-path>` opens the project on the host
3. Reopen in container
4. `postCreateCommand` → `project-setup.sh` → `make rpmConfigure` runs
   automatically

**If the project team does NOT add `make rpmConfigure` to `project-setup.sh`**,
RPM
will not run automatically during the devcontainer lifecycle. In that case, the
developer must run `make rpmConfigure` manually after the devcontainer is built.

#### 9.0.2 DevContainer Catalogs and the `rpm-` Naming Convention

Catalogs are Git repositories containing one or more catalog entries under
`catalog/`.
Each entry has a `catalog-entry.json` with metadata:

```json
{
  "name": "rpm-python-uv",
  "description": "Python/uv development environment with RPM build packages and Claude Code marketplaces",
  "tags": ["python", "uv", "rpm", "claude"],
  "maintainer": "Platform Team",
  "min_cli_version": "2.0.0"
}
```

Entry names follow the pattern `^[a-z][a-z0-9-]*[a-z0-9]$`. Catalog entries that
include RPM are prefixed with `rpm-` so developers can identify which entries
come with
RPM (and therefore include build packages and Claude Code marketplaces):

| Catalog Entry | What It Includes |
|---|---|
| `rpm-python-uv` | DevContainer + RPM + Python/uv build packages + Claude marketplaces for Python/uv |
| `rpm-python-uv-django` | DevContainer + RPM + Python/uv/Django build packages + Claude marketplaces for Python/uv/Django |
| `rpm-node-npm` | DevContainer + RPM + Node/npm build packages + Claude marketplaces for Node/npm |
| `default` (no prefix) | General-purpose DevContainer, no RPM, no packages, no marketplaces |

The `rpm-` prefix signals: "this entry bootstraps RPM, which manages build
packages
and Claude Code plugin marketplaces." Entries without the `rpm-` prefix provide
a
DevContainer but do not include RPM infrastructure.

Users browse available entries with:

```bash
cdevcontainer catalog list
cdevcontainer catalog list --tags python,rpm
```

Catalogs are consumed by setting `DEVCONTAINER_CATALOG_URL` (supports `@tag`
suffix
for pinning) or by passing `--catalog-url` directly.

#### 9.0.3 What the Catalog Repo Must Contain for RPM Support

To support RPM, the catalog repository MUST include the following files in its
**common** directories (shared across all entries):

| File | Location in Catalog Repo | Copied To | Scope |
|---|---|---|---|
| `.rpmenv` | `common/root-project-assets/` | project root | All entries |
| `Makefile` | `common/root-project-assets/` | project root | All entries |

The install script is NOT part of the DevContainer catalog. It is delivered by
`repo sync`
as part of the `rpm-claude-marketplaces-install` RPM package. Both files above
live in
common directories because they are identical across all `rpm-` catalog entries.
Non-RPM
entries (e.g., `default`) will also receive these files, but that is harmless:
`make
rpmConfigure` only runs when `project-setup.sh` invokes it for RPM-configured
projects.

**Catalog maintainer responsibility:** When adding RPM support to a catalog, the
maintainer MUST add these three files to the common directories and ensure
`project-setup.sh` documents `make rpmConfigure` as the expected project-setup
command.

#### 9.0.4 Non-DevContainer Path: Manual Setup

Projects that do not use Caylent DevContainers must set up the RPM bootstrap
files
manually. The developer creates the following at the project root:

| File | Source | Purpose |
|---|---|---|
| `.rpmenv` | Copy from RPM documentation or another RPM-enabled project | RPM configuration (manifest URL, revision, variables) |
| `Makefile` | Copy from RPM documentation or another RPM-enabled project | RPM Make targets (`rpmConfigure`, `rpmClean`) |

The `Makefile` and `.rpmenv` are committed to git. Once these files exist, the
developer runs `make rpmConfigure` (see Section 9.1), which handles the rest:
prerequisite checks (`rpmHostSetup`), repo sync, and marketplace/plugin
installation.

**Install script delivery:** The install script is delivered as part of the
`rpm-claude-marketplaces-install` RPM package during `repo sync` (synced via
`common/claude-marketplaces.xml`). After sync completes, the script is available
at
`.packages/rpm-claude-marketplaces-install/install_claude_marketplaces.py` and
the
Makefile locates and runs it. There is no need to pre-stage the script before
the first
sync. This applies to both DevContainer and non-DevContainer projects.

#### 9.0.5 What Each Path Produces

Regardless of how the bootstrap files arrive, the end state is the same:

| File | DevContainer Path | Non-DevContainer Path |
|---|---|---|
| `.rpmenv` | From catalog `common/root-project-assets/` | Created manually |
| `Makefile` | From catalog `common/root-project-assets/` | Created manually |
| Install script | `.packages/rpm-claude-marketplaces-install/install_claude_marketplaces.py` (delivered by `repo sync` via `common/claude-marketplaces.xml`) | `.packages/rpm-claude-marketplaces-install/install_claude_marketplaces.py` (delivered by `repo sync` via `common/claude-marketplaces.xml`) |
| Setup command | `make rpmConfigure` (automatic via lifecycle hook) | `make rpmConfigure` (manual) |

After bootstrapping, the lifecycle is identical: `make rpmConfigure` to set up,
`make rpmClean` to tear down, regardless of how the project was initially
bootstrapped.

### 9.1 What `make rpmConfigure` Does (Step-by-Step)

This section is a reference for the internal steps of `make rpmConfigure`. The
target
is idempotent: running it multiple times produces the same result. It runs
automatically
via `project-setup.sh` in the devcontainer lifecycle (Section 14.2), or manually
by the
developer outside a devcontainer (Section 15.5).

The Makefile delegates all logic to `python3 scripts/rpm/configure.py .rpmenv`
(see Section 8.6). The steps below describe what the Python script does:

```text
make rpmConfigure → python3 scripts/rpm/configure.py .rpmenv

1. make rpmHostSetup (idempotent)             → prerequisite checks + environment setup:
   a. Verify python3, repo, claude, make on PATH (fail fast if missing)
2. source .rpmenv                             → loads RPM_SOURCES, RPM_SOURCE_<name>_*, GITBASE,
                                                 CLAUDE_MARKETPLACES_DIR, RPM_MARKETPLACE_INSTALL, etc.
3. Validate sources                           → for each name in RPM_SOURCES, verify RPM_SOURCE_<name>_URL,
                                                 _REVISION, _PATH all exist (fail fast if any missing)
4. If RPM_MARKETPLACE_INSTALL=true:
   a. mkdir -p ${CLAUDE_MARKETPLACES_DIR}
   b. rm -rf ${CLAUDE_MARKETPLACES_DIR}/*     → pre-sync cleanup (ensures clean slate)
5. For each source in RPM_SOURCES order:
   a. mkdir -p .rpm/sources/<name>
   b. cd .rpm/sources/<name>
   c. repo init -u <URL> -b <REVISION> -m <PATH>
   d. Export shared env vars → repo envsubst  → resolves ${GITBASE}, ${CLAUDE_MARKETPLACES_DIR}
   e. repo sync                               → syncs packages to .rpm/sources/<name>/.packages/
6. Aggregate symlinks                         → for each .rpm/sources/<name>/.packages/*, create symlink in .packages/
   a. Collision check: if two sources produce same package name → fail fast with error
7. .gitignore updated with .packages/, .rpm/
8. If RPM_MARKETPLACE_INSTALL=true:
   a. Check .packages/rpm-claude-marketplaces-install/install_claude_marketplaces.py
   b. If not found → fail fast: "RPM_MARKETPLACE_INSTALL=true but rpm-claude-marketplaces-install
      package not found. Ensure a marketplace source is defined in RPM_SOURCES."
   c. Run install_claude_marketplaces.py      → marketplace + plugin installation:
      i.  Discovers ${CLAUDE_MARKETPLACES_DIR}/*/
      ii. Registers each as marketplace
      iii.Discovers and installs plugins from each marketplace
```

**Pre-sync cleanup rationale:** Step 4b clears all existing marketplace symlinks
before
`repo sync` creates fresh ones. This ensures the marketplace directory always
reflects
exactly the current manifests' declared marketplaces, with no stale symlinks
from
previous syncs or different project configurations. Step 4 only executes when
`RPM_MARKETPLACE_INSTALL=true`. See Section 14.5 for multi-project
considerations.

### 9.2 Adding a Marketplace to a Project

```text
Manifest maintainer:
1. Add <project> + <linkfile> entry to claude-marketplaces.xml
2. Tag manifest repo

Project developer:
1. Update RPM_SOURCE_marketplaces_REVISION in .rpmenv (or the relevant source revision)
2. make rpmClean    (uninstalls plugins + removes marketplaces + cleans RPM state)
3. make rpmConfigure (syncs + installs marketplaces and plugins)
```

### 9.3 Removing a Marketplace From a Project

```text
Manifest maintainer:
1. Remove <project> entry from claude-marketplaces.xml
2. Tag manifest repo

Project developer:
1. Update RPM_SOURCE_marketplaces_REVISION in .rpmenv (or the relevant source revision)
2. make rpmClean    (uninstalls all plugins + removes all marketplaces)
3. make rpmConfigure (re-syncs + re-installs only the remaining marketplaces and plugins)
```

### 9.4 Upgrading a Marketplace Version

```text
Monorepo maintainer (must happen first):
1. Publish the new marketplace version in the monorepo (see Section 9.5)
   (e.g., git tag python/uv/django/django-helpers/1.1.0)

Manifest maintainer:
1. Update revision attribute in claude-marketplaces.xml to the new tag
2. Tag manifest repo

Project developer:
1. Update RPM_SOURCE_marketplaces_REVISION in .rpmenv to the new manifest tag
2. make rpmClean    (uninstalls plugins + removes marketplaces + cleans RPM state)
3. make rpmConfigure (re-syncs at new version + reinstalls marketplaces and plugins)
```

### 9.5 Publishing a New Marketplace Version (Monorepo Maintainer)

```text
1. Make changes to <marketplace-path>/ subdirectory
   (e.g., python/uv/django/django-helpers/)
2. Open PR, scoped CI validates, CODEOWNERS approve
3. Merge PR
4. git tag <marketplace-path>/<new-semver>
   (e.g., python/uv/django/django-helpers/1.1.0)
5. git push origin <branch> <marketplace-path>/<new-semver>
```

### 9.6 Adding a New Marketplace to the Monorepo

```text
1. Create marketplace directory at the appropriate hierarchy level
   (e.g., mkdir -p node/npm/express/express-patterns/)
2. Add plugin subdirectories with plugin.json and implementation files
3. git commit
4. Open PR, scoped CI validates, CODEOWNERS approve
5. Merge PR
6. git tag <marketplace-path>/1.0.0
   (e.g., node/npm/express/express-patterns/1.0.0)
7. git push origin <branch> <marketplace-path>/1.0.0
8. Add <project> entry to appropriate claude-marketplaces.xml in manifest repo
```

---

## 10. CI Validation Requirements (Monorepo)

### 10.1 Automated Validation Rules

The plugin monorepo MUST have CI that enforces:

| Rule | Validation |
|---|---|
| **Single-scope PRs** | Each PR MUST touch either (a) exactly one marketplace directory, or (b) only repo-level config files (`.github/`, `CODEOWNERS`, `README.md`, etc.). A PR MUST NOT mix changes across multiple marketplaces, and MUST NOT mix marketplace changes with repo config changes. CI MUST fail the PR if changed files span more than one scope. |
| Marketplace directories are valid | Every directory containing `plugin.json` files must be a valid Claude Code marketplace |
| Tags follow convention | On tag push: validate format `<marketplace-path>/<semver>`, verify `<marketplace-path>` exists as a directory containing plugins |
| Marketplace is self-contained | No symlinks or references outside the marketplace's own directory tree |
| Hierarchy directories are organizational only | Intermediate directories (e.g., `common/development/python/`, `common/development/python/uv/`) must NOT contain `plugin.json`; only leaf marketplace directories contain plugins. CI MUST validate this against the `reserved_directories` list in `config-repo.json`: every directory listed as reserved MUST NOT contain `plugin.json`, and every non-reserved directory under `marketplace_root` MUST be a marketplace (contain plugin subdirectories). |
| Flattened names are unique | Compute the flattened name for every marketplace using the algorithm in Section 4.6 and the `config-repo.json` configuration. No two marketplaces may produce the same flattened name. |
| Plugin names are globally unique | Scan all `plugin.json` across all marketplaces; no two plugins may share the same `name` value |
| **Claude CLI round-trip** | For the changed marketplace directory, CI MUST verify the full lifecycle using the `claude` CLI: (1) `claude plugin marketplace add <path>` succeeds, (2) `claude plugin install <name> --scope user` succeeds for each plugin in the marketplace, (3) `claude plugin uninstall <name> --scope user` succeeds for each plugin, (4) `claude plugin marketplace remove <path>` succeeds. All four steps must pass. This validates that the Claude CLI can discover, install, and cleanly remove the marketplace and its plugins. |

### 10.2 CODEOWNERS and Governance

The monorepo MUST use GitHub CODEOWNERS to enforce ownership at different levels
of
the hierarchy. This enables teams with domain expertise to own their respective
marketplace scopes while maintaining shared governance for universal
marketplaces.

**CODEOWNERS file:**

```text
# Root-level governance, universal marketplaces require platform team approval
/common/sdlc-tools/                    @caylent-solutions/platform-team
/common/security-review/               @caylent-solutions/security-team

# Python ecosystem, owned by Python guild
/common/development/python/                        @caylent-solutions/python-guild
/common/development/python/uv/django/              @caylent-solutions/django-team

# Node.js ecosystem, owned by Node guild
/common/development/node/                          @caylent-solutions/node-guild
/common/development/node/npm/express/              @caylent-solutions/express-team

# .NET ecosystem, owned by .NET guild
/common/development/dotnet/                        @caylent-solutions/dotnet-guild
/common/development/dotnet/nuget/aspnet/           @caylent-solutions/aspnet-team

# CI/CD and monorepo config, requires platform team
/.github/                       @caylent-solutions/platform-team
/config-repo.json               @caylent-solutions/platform-team
/CODEOWNERS                     @caylent-solutions/platform-team
```

**Single dynamic pipeline (marketplace path as input):**

Because the single-scope PR rule (Section 10.1) guarantees that each PR touches
exactly
one marketplace, all pipelines share a single reusable workflow that receives
the
**marketplace path as an input parameter**. There are no per-marketplace
pipeline
definitions. The pipeline determines the marketplace path by inspecting the
changed
files and extracting the common marketplace directory prefix.

**Three separate pipelines, each triggered by a different event:**

| Pipeline | Trigger | Input | Actions |
|---|---|---|---|
| **CI** | `pull_request` | Marketplace path from changed files | Single-scope check, self-containment, metadata validation, plugin uniqueness, Claude CLI round-trip (Section 10.1). CODEOWNERS peer review required before merge. |
| **QA** | `push` to main (merge event) | Marketplace path from merged commit | Same quality checks as CI, re-run against the merged state. CODEOWNERS must approve QA results. |
| **Tag and Release** | QA approval event | Marketplace path + semver | Creates `<marketplace-path>/<semver>` tag and publishes the release. |

**CI and QA run the same quality checks.** The CI pipeline validates the PR
branch, and
the QA pipeline re-runs the identical checks against the merged commit on main.
This
ensures that merge conflicts or concurrent merges have not introduced
regressions. Both
pipelines call the same reusable validation workflow with the marketplace path
as input.

**Pipeline flow:**

```text
1. Developer opens PR modifying a single marketplace directory
2. CI pipeline detects marketplace path from changed files
3. CI runs: scope check, validation, Claude CLI round-trip
4. CODEOWNERS-designated team reviews and approves the PR
5. PR is merged to main
                    ↓
6. Merge triggers QA pipeline on the merged commit
7. QA pipeline runs full validation against merged state
8. CODEOWNERS-designated team approves QA results
                    ↓
9. QA approval triggers Tag and Release pipeline
10. Tag and Release creates: <marketplace-path>/<new-semver>
```

**GitHub Actions example (reusable workflow with marketplace path input):**

```yaml
# .github/workflows/marketplace-ci.yml (PR pipeline)
name: Marketplace CI

on:
  pull_request:

jobs:
  detect-scope:
    runs-on: ubuntu-latest
    outputs:
      marketplace_path: ${{ steps.detect.outputs.marketplace_path }}
      scope_type: ${{ steps.detect.outputs.scope_type }}
    steps:
      - uses: actions/checkout@v4
      - id: detect
        run: |
          # Determine changed marketplace path or "config" for repo-level changes
          # Fail if changes span multiple scopes

  validate:
    needs: detect-scope
    if: needs.detect-scope.outputs.scope_type == 'marketplace'
    uses: ./.github/workflows/marketplace-validate.yml
    with:
      marketplace_path: ${{ needs.detect-scope.outputs.marketplace_path }}

  claude-cli-roundtrip:
    needs: [detect-scope, validate]
    if: needs.detect-scope.outputs.scope_type == 'marketplace'
    uses: ./.github/workflows/marketplace-cli-test.yml
    with:
      marketplace_path: ${{ needs.detect-scope.outputs.marketplace_path }}
```

```yaml
# .github/workflows/marketplace-qa.yml (merge pipeline)
name: Marketplace QA

on:
  push:
    branches: [main]

jobs:
  detect-scope:
    # Same scope detection logic as CI pipeline
  qa-validate:
    needs: detect-scope
    if: needs.detect-scope.outputs.scope_type == 'marketplace'
    uses: ./.github/workflows/marketplace-validate.yml
    with:
      marketplace_path: ${{ needs.detect-scope.outputs.marketplace_path }}
    # QA results require CODEOWNERS approval before release
```

```yaml
# .github/workflows/marketplace-release.yml (QA approval pipeline)
name: Marketplace Tag and Release

on:
  # Triggered by QA approval event (e.g., deployment environment approval,
  # manual dispatch, or review approval on the QA run)

jobs:
  tag-and-release:
    uses: ./.github/workflows/marketplace-tag.yml
    with:
      marketplace_path: ${{ inputs.marketplace_path }}
      version: ${{ inputs.version }}
```

---

## 11. Constraints and Invariants

### Hard Constraints

1. The `repo` tool is the ONLY mechanism for syncing marketplace content. No git
   clone, fetch,
   checkout, or pull commands in the install script.
2. The install script performs ZERO git operations. It operates on filesystem
   state only.
3. `$HOME/.claude-marketplaces/` contains ONLY symlinks created by `<linkfile>`.
   Never real
   directories.
4. Each marketplace directory maps to exactly one `<project>` entry in the
   manifest.
5. The plugin monorepo is checked out N times (once per needed marketplace).
   Each checkout is
   at a different tag.
6. Git objects are shared across all checkouts of the same monorepo. This is
   automatic
   (`repo` tool behavior, not a configuration option).

### Soft Constraints (Conventions)

1. Marketplace symlinks live in `$HOME/.claude-marketplaces/` (outside the git
   project)
2. Monorepo checkouts live in `.packages/<repo>-<flattened-marketplace-path>/`
   (inside the git project)
3. Semantic tags follow `<marketplace-path>/<semver>` with hierarchy `/`
   separators
4. Checkout paths and symlink names flatten the hierarchy with `-` separators
5. Version constraints (Section 5.5) may be used in place of exact pins when the
   package or marketplace has comprehensive test coverage
6. The install script is located at
   `.packages/rpm-claude-marketplaces-install/install_claude_marketplaces.py`
   (delivered by `repo sync` via `common/claude-marketplaces.xml`)

### Invariants (Must Always Be True)

1. For every symlink in `$HOME/.claude-marketplaces/`, there exists a
   corresponding
   checkout in `.packages/`.
2. For every monorepo checkout in `.packages/`, the `<linkfile>` src path (the
   hierarchy
   path to the marketplace directory) exists within it.
3. The marketplace hierarchy path matches the tag prefix, which matches the
   `<linkfile> src`
   attribute.
4. No two marketplace entries share the same absolute path.
5. No two `<project>` entries share the same `path` attribute.
6. Each `claude-marketplaces.xml` at a given hierarchy level includes the
   `claude-marketplaces.xml` from the
   parent level, forming an unbroken inheritance chain from leaf to root.

---

## 12. Flow Diagram

This diagram shows the two-phase process: `make rpmConfigure` syncs all packages
and
creates marketplace symlinks, then `install_claude_marketplaces.py` discovers
and
installs them.

```text
┌───────────────────────────────────────────────────────────────────────────────────────┐
│  rpmConfigure (Make target, runs FIRST)                                               │
├───────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  rpmHostSetup → clean $HOME/.claude-marketplaces/* → repo init → envsubst → sync      │
│                                                                                       │
│  For each <project> in manifest (resolved from cascading claude-marketplaces.xml):    │
│                                                                                       │
│  ┌─ Build package (existing, grouped per scope) ───────────────────────────┐          │
│  │  rpm-python-uv → .packages/rpm-python-uv/                               │          │
│  │  (linting + testing + typing + packaging, all in one)                   │          │
│  └─────────────────────────────────────────────────────────────────────────┘          │
│                                                                                       │
│  ┌─ Plugin marketplace entries (NEW, from cascading claude-marketplaces.xml) ───────┐ │
│  │                                                                                  │ │
│  │  Universal (from common/claude-marketplaces.xml):                                │ │
│  │  <monorepo> @ sdlc-tools/1.0.0                                                   │ │
│  │    checkout → .packages/<monorepo>-sdlc-tools/                                   │ │
│  │    linkfile → $HOME/.claude-marketplaces/<monorepo>-sdlc-tools/                  │ │
│  │                                                                                  │ │
│  │  Python-wide (from common/development/python/claude-marketplaces.xml):           │ │
│  │  <monorepo> @ development/python/python-commons/1.0.0                            │ │
│  │    checkout → .packages/<monorepo>-python-python-commons/                        │ │
│  │    linkfile → $HOME/.claude-marketplaces/<monorepo>-python-python-commons/       │ │
│  │                                                                                  │ │
│  │  Framework-specific (from common/development/python/uv/django/claude-...):       │ │
│  │  <monorepo> @ development/python/uv/django/django-helpers/1.0.0                  │ │
│  │    checkout → .packages/<monorepo>-python-uv-django-django-helpers/              │ │
│  │    linkfile → $HOME/.claude-marketplaces/<monorepo>-python-uv-django-...         │ │
│  │                                                                                  │ │
│  └──────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                       │
│  Git objects: fetched ONCE, shared at                                                 │
│  .rpm/sources/<source>/.repo/project-objects/<monorepo>.git/                          │
└───────────────────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────────────────────┐
│  install_claude_marketplaces.py (runs AFTER rpmConfigure)                             │
├───────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  ┌─ Setup ─────────────────────────────────────────────────────────────────┐          │
│  │  configure Python logging                                               │          │
│  │  shutil.which("claude") or exit 127                                     │          │
│  └─────────────────────────────────────────────────────────────────────────┘          │
│                                │                                                      │
│                                ▼                                                      │
│  ┌─ Discovery ─────────────────────────────────────────────────────────────┐          │
│  │  Does $HOME/.claude-marketplaces/ exist?                                │          │
│  │    NO  → warn + exit 0                                                  │          │
│  │    YES → list non-dot-prefixed subdirectories, sorted                   │          │
│  │          None found? → warn + exit 0                                    │          │
│  └─────────────────────────────────────────────────────────────────────────┘          │
│                                │                                                      │
│                                ▼                                                      │
│  ┌─ For each marketplace ──────────────────────────────────────────────────┐          │
│  │                                                                         │          │
│  │  7a. Validate: symlink target exists?                                   │          │
│  │        broken → log error, skip to next                                 │          │
│  │                                                                         │          │
│  │  7b. Register: marketplace already registered?                          │          │
│  │        yes → skip                                                       │          │
│  │        no  → claude plugin marketplace add <path>                       │          │
│  │                                                                         │          │
│  │  7c. Read marketplace name from .claude-plugin/marketplace.json         │          │
│  │                                                                         │          │
│  │  7d. Discover: find .claude-plugin/plugin.json in subdirs               │          │
│  │        read plugin name(s), 1 to many per marketplace                   │          │
│  │                                                                         │          │
│  │  7e. Install: for each discovered plugin name                           │          │
│  │        claude plugin install <name>@<marketplace> --scope user          │          │
│  │                                                                         │          │
│  └──────────────────────────────────── (repeat for next marketplace) ──────┘          │
│                                │                                                      │
│                                ▼                                                      │
│  ┌─ Summary ───────────────────────────────────────────────────────────────┐          │
│  │  Log: N marketplaces processed, M plugins installed                     │          │
│  │  Exit 0 (all success) or non-zero (any failures)                        │          │
│  └─────────────────────────────────────────────────────────────────────────┘          │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 13. Marketplace and Build Package Correlation

### 13.1 Parallel Hierarchies

The plugin monorepo hierarchy under `common/development/` and the RPM manifest
`repo-specs/` hierarchy are
**intentionally parallel**. Both follow the same
`<runtime>/<build-tool>/<framework>/<architecture>` taxonomy. This means that
for any
given technology context, the build-tooling packages and the Claude Code plugin
marketplaces are selected by the same hierarchy position.

Build packages follow the **`rpm-<runtime>-<descriptive package name>`** naming
convention. The descriptive name identifies the package's purpose (e.g.,
`rpm-python-uv`
contains all Python/uv build tasks: linting, testing, typing, packaging). Plugin
marketplaces may be **more granular**, with additional marketplaces at deeper
hierarchy
levels (framework, architecture).

The naming convention aligns: a build package named `rpm-python-uv` mirrors the
`common/development/python/uv/` hierarchy level where its correlated plugin
marketplace `common/development/python/uv/quality-agent`
resides. Both are scoped to the same technology context.

### 13.2 Correlation Examples

| Build Package (grouped) | Correlated Marketplace(s) | Relationship |
|---|---|---|
| `rpm-python-uv` | `common/development/python/uv/quality-agent` | Build package provides all Python/uv build tasks (Ruff linting, pytest testing, mypy typing, packaging); marketplace provides Claude Code agent skills that understand and apply those same tools |
| `rpm-python-uv` | `common/development/python/uv/django/django-helpers` | Same build package also establishes the Python/uv environment that Django marketplace plugins work within; django-helpers provides framework-specific patterns on top |
| `rpm-node-npm` | `common/development/node/npm/quality-agent` | Build package provides all Node/npm build tasks (ESLint linting, Jest testing, bundling); marketplace provides Claude Code agent skills for JavaScript/TypeScript tooling compliance |
| `rpm-node-npm` | `common/development/node/npm/express/express-patterns` | Same build package also establishes the Node/npm environment; express-patterns provides framework-specific patterns on top |
| `rpm-dotnet-nuget` | `common/development/dotnet/nuget/quality-agent` | Build package provides all .NET/NuGet build tasks (Roslyn analyzers, xUnit testing, compilation); marketplace provides Claude Code agent skills for .NET code analysis |

**Key pattern:** One build package (`rpm-<runtime>-<descriptive-name>`)
correlates with
one or more plugin marketplaces at the same OR deeper hierarchy levels. The
build package
provides the automated tooling; the correlated marketplaces provide Claude Code
agent
skills that understand and work with that tooling.

### 13.3 How Correlation Works in Practice

Both `packages.xml` and `claude-marketplaces.xml` live at the same hierarchy
level in the
manifest repository and are included by the same `meta.xml`:

```xml
<!-- repo-specs/common/development/python/uv/django/frontend/meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <include name="repo-specs/git-connection/remote.xml" />
  <include name="repo-specs/common/development/python/uv/django/frontend/packages.xml" />
  <include name="repo-specs/common/development/python/uv/django/frontend/claude-marketplaces.xml" />
</manifest>
```

A Python/uv/Django/Frontend project gets its build package AND plugin
marketplaces
tailored to that exact technology stack. Because `claude-marketplaces.xml` uses
cascading `<include>` inheritance (see Section 5.2), the project automatically
receives
ALL marketplaces from its own level up through the root: universal plugins
(`common/sdlc-tools`),
Python-wide plugins (`common/development/python-commons`), Python+uv plugins
(`common/development/quality-agent`), and
Django-specific plugins (`common/development/django-helpers`). The Ruff linting
config (from
`rpm-python-uv`) and the Claude Code "fix Ruff violations" agent skill (from
`common/development/python/uv/quality-agent`) are delivered together. The
developer gets both the
automated tooling AND the AI assistance that understands it.

### 13.4 Correlation Diagram

```text
repo-specs/common/development/python/uv/django/frontend/
│
├── packages.xml                                                     ← BUILD PACKAGE (grouped)
│   └── rpm-python-uv                                                ← all Python/uv build tasks:
│       (linting, testing, typing, packaging, one package)             ruff, pytest, mypy, packaging
│
│
├── claude-marketplaces.xml                                          ← PLUGIN MARKETPLACES (cascading inheritance)
│   │                                                                  includes parent → grandparent → ... → root
│   │                                                                  so this project receives ALL of:
│   ├── common/sdlc-tools (from common/)                             ← workflow, planning, review plugins
│   ├── common/security-review (from common/)                        ← security scanning agent skills
│   ├── common/development/python/python-commons (from python/)      ← Python idioms, debugging plugins
│   ├── common/development/python/uv/quality-agent (from python/uv/) ← QA + linting agent skills
│   └── common/development/python/uv/django/django-helpers (from python/uv/django/) ← Django patterns
│
└── meta.xml                                                         ← includes both packages.xml and claude-marketplaces.xml

  BUILD PACKAGE (grouped)                                        CORRELATED MARKETPLACES
  ───────────────────────                                        ────────────────────────
                                                                 common/sdlc-tools          (universal, no correlation)
                                                                 common/security-review     (universal, no correlation)
                                                                 common/development/python/python-commons (runtime, language idioms)
  rpm-python-uv           ◄──────────►                           common/development/python/uv/quality-agent (QA skills for ruff, pytest, mypy)
  (python/uv scope)       ◄──────────►                           common/development/python/uv/django/django-helpers (framework patterns)
```

---

## 14. Devcontainer Integration

### 14.1 Isolation Model

The devcontainer and host OS environments are **fully isolated**. There are no
volume
mounts between the host `~/.claude` or `~/.claude-marketplaces` and the
container. Each
environment maintains its own:

- `$HOME/.claude/`: Claude Code settings, plugin registry, conversation history
- `$HOME/.claude-marketplaces/`: marketplace symlinks created by `repo sync`
- `.packages/`: RPM-managed checkouts (within the project workspace)

This means plugins installed inside the devcontainer do not appear on the host,
and
vice versa. Each environment runs the same scripts independently.

**One project per devcontainer:** Each devcontainer instance serves exactly one
project.
The `$HOME/.claude-marketplaces/` directory inside the container is exclusively
owned by
that project's `rpmConfigure` run. There is no multi-project conflict within a
devcontainer because each container is an isolated, single-project environment.
This is
the recommended development model.

### 14.2 Lifecycle Hook Integration

Marketplace and plugin installation runs as part of the devcontainer
`postCreateCommand`
lifecycle hook chain. The `make rpmConfigure` target handles the entire process,
from
syncing RPM packages through registering marketplaces and installing plugins.
The
current chain is:

```text
postCreateCommand (devcontainer.json)
  └── postcreate-wrapper.sh
        └── .devcontainer.postcreate.sh
              └── project-setup.sh
                    ├── ... (existing setup: tooling, Snyk, Claude settings, etc.)
                    └── make rpmConfigure
                          ├── rpmHostSetup (idempotent: prereq checks, mkdir -p)
                          ├── Clean ${HOME}/.claude-marketplaces/* (pre-sync cleanup)
                          ├── repo init → repo envsubst → repo sync
                          ├── Build packages synced to .packages/
                          └── install_claude_marketplaces.py
                                ├── Discovers ${HOME}/.claude-marketplaces/*/
                                ├── Registers marketplaces with Claude Code
                                └── Installs plugins to ${HOME}/.claude/plugins/
```

No separate script call is needed. The `make rpmConfigure` target (called by
`project-setup.sh`) is the single entry point that syncs all RPM packages,
creates
marketplace symlinks via `<linkfile>`, and then runs
`install_claude_marketplaces.py`
to register marketplaces and install plugins with the Claude CLI.

### 14.3 `.rpmenv` Configuration

The `CLAUDE_MARKETPLACES_DIR` variable in `.rpmenv` uses `$HOME` which resolves
correctly
in both environments:

```properties
CLAUDE_MARKETPLACES_DIR=${HOME}/.claude-marketplaces
```

- **Inside devcontainer:** `$HOME` = `/home/vscode` →
  `/home/vscode/.claude-marketplaces`
- **Outside devcontainer (host):** `$HOME` = `/home/<user>` →
  `/home/<user>/.claude-marketplaces`

### 14.4 Complete Devcontainer Setup Flow

```text
1. Developer opens project in VS Code / devcontainer CLI

2. Container builds from devcontainer.json
   - Workspace mounted at /workspaces/<project>/

3. postCreateCommand chain:
   a. postcreate-wrapper.sh → .devcontainer.postcreate.sh → project-setup.sh
   b. project-setup.sh runs existing setup (tooling, Snyk, Claude settings, etc.)
   c. project-setup.sh runs: make rpmConfigure
      - rpmHostSetup (idempotent: prereq checks, mkdir -p)
      - repo init → repo envsubst → repo sync
      - Build packages → .packages/<build-packages>/
      - Plugin monorepo checkouts → .packages/<monorepo>-<marketplace>/
      - Linkfiles → /home/vscode/.claude-marketplaces/<monorepo>-<marketplace>/
      - install_claude_marketplaces.py runs automatically:
        - Discovers /home/vscode/.claude-marketplaces/*/
        - Registers marketplaces with Claude Code
        - Installs plugins to /home/vscode/.claude/plugins/

4. Developer is ready, plugins are installed within the devcontainer
```

### 14.5 Multi-Project Considerations and `$HOME/.claude-marketplaces/` Ownership

The `$HOME/.claude-marketplaces/` directory is a **shared, single-owner
resource**.
`rpmConfigure` performs a pre-sync cleanup (step 3 in Section 9.1) that removes
all
existing symlinks before creating fresh ones. This ensures the directory always
reflects
exactly one project's marketplace set with no stale or merged results.

**DevContainer environment (recommended):** Each devcontainer has its own
isolated
`$HOME`, so there is no conflict. One project per container means one owner of
`$HOME/.claude-marketplaces/`. This is the recommended development model.

**Bare-metal / host environment (known limitation):** When a developer works on
multiple
RPM-enabled projects on the same host (outside devcontainers),
`$HOME/.claude-marketplaces/`
is shared across all projects. Because `rpmConfigure` cleans the directory
before syncing,
running `make rpmConfigure` in Project B will remove Project A's marketplace
symlinks
and replace them with Project B's marketplaces. The developer's Claude Code
plugin set
will reflect whichever project ran `rpmConfigure` most recently.

**Impact:** On bare metal, switching between RPM-enabled projects requires
re-running
`make rpmConfigure` in the target project to restore its marketplace set.
Plugins from
the previous project will no longer be registered (their symlinks were cleaned).

**Mitigation:** Use devcontainers. Each devcontainer provides complete isolation
of
`$HOME`, `.packages/`, and the Claude Code plugin registry. Developers working
on
multiple RPM-enabled projects simultaneously SHOULD use separate devcontainers
for each
project. For developers who choose bare-metal development, this limitation MUST
be
documented in the project's developer guide with the instruction to run
`make rpmConfigure` when switching projects.

---

## 15. Non-Devcontainer Installation

### 15.1 Design Principle: One Set of Targets, Works Everywhere

There is exactly **one `Makefile` with one set of targets** (`rpmConfigure`,
`rpmClean`).
The developer runs `make rpmConfigure` and everything works, whether inside a
devcontainer or on a bare host. The `rpmConfigure` target calls `rpmHostSetup`
internally as its first step. `rpmHostSetup` is idempotent, so it is safe to run
on
every invocation. The targets work identically in both environments because:

- `.rpmenv` and `Makefile` live at the project root, which exists in both
  environments
- The install script is delivered by `repo sync` at
  `.packages/rpm-claude-marketplaces-install/install_claude_marketplaces.py`
  (via `common/claude-marketplaces.xml`). Same path in both environments.
- All runtime paths use `$HOME`, which resolves correctly in both environments
- All tools (`repo`, `python3`, `claude`, `make`) are resolved via `$PATH`

The only difference is **who calls `make rpmConfigure`**: in the devcontainer,
`project-setup.sh` calls it automatically during the `postCreateCommand`
lifecycle
hook. Outside the devcontainer, the developer calls it manually. The target
itself is
identical. There is no separate setup step to remember.

### 15.2 Prerequisites

The following must be available on the developer's machine:

| Prerequisite | Purpose | Installation |
|---|---|---|
| `git` | Version control, `repo` tool dependency | OS package manager |
| `repo` tool (with `envsubst` support) | Multi-repo sync, variable substitution | See RPM documentation |
| `python3` | Install script runtime, build tooling | OS package manager or `.tool-versions` |
| `make` | Build automation (RPM targets) | OS package manager (pre-installed on macOS, `apt install make` on Ubuntu) |
| `claude` CLI | Claude Code plugin management | `npm install -g @anthropic-ai/claude-code` or binary |

### 15.3 File Layout: Devcontainer vs. Host

Understanding where files live is critical. In a devcontainer, all project files
are mounted into the container and `$HOME` is `/home/vscode`. On the host, the
developer clones the project to a local directory and `$HOME` is the user's home
directory.

#### 15.3.1 Project Root (checked into git, same in both environments)

These files exist in the repository and are identical whether working inside a
devcontainer or on the host:

```text
<project-root>/
├── .rpmenv                                         ← multi-source RPM configuration (RPM_SOURCES, RPM_SOURCE_<name>_*, etc.)
├── Makefile                                        ← rpmConfigure, rpmClean targets
├── .packages/                                      ← aggregated symlinks from all sources (gitignored)
│   ├── <build-package-1>/                          ← symlink → .rpm/sources/build/.packages/<build-package-1>
│   ├── <build-package-2>/                          ← symlink → .rpm/sources/build/.packages/<build-package-2>
│   ├── rpm-claude-marketplaces-install/            ← symlink → .rpm/sources/marketplaces/.packages/...
│   │   └── install_claude_marketplaces.py          ← install script (synced via common/claude-marketplaces.xml)
│   └── <monorepo>-<marketplace>/                   ← symlink → .rpm/sources/marketplaces/.packages/...
├── .rpm/                                           ← multi-source repo tool state (gitignored)
│   └── sources/
│       ├── build/.repo/                            ← repo tool metadata for build source
│       └── marketplaces/.repo/                     ← repo tool metadata for marketplaces source
└── ...
```

The install script is delivered via `repo sync` as part of the
`rpm-claude-marketplaces-install`
RPM package (synced through `common/claude-marketplaces.xml`). It appears at
`.packages/rpm-claude-marketplaces-install/install_claude_marketplaces.py` after
sync.
The `.rpmenv` file and `Makefile` are always at the project root. The developer
does
NOT need to copy any of these files to `$HOME`.

#### 15.3.2 Home Directory (created at runtime, per-user)

These paths are created by `make rpmConfigure` (or `make rpmHostSetup` for
first-time
host setup). They live under `$HOME` and are specific to each user:

```text
$HOME/
├── .claude-marketplaces/                          ← symlinks created by repo sync <linkfile>
│   ├── <monorepo>-<marketplace-a>/                   (points to <project>/.packages/<monorepo>-<marketplace-a>/)
│   └── <monorepo>-<marketplace-b>/                   (points to <project>/.packages/<monorepo>-<marketplace-b>/)
└── .claude/
    └── plugins/                                   ← Claude Code plugin registry (managed by claude CLI)
        ├── <plugin-a>/
        └── <plugin-b>/
```

#### 15.3.3 Combined View: What the Host Developer Sees (non-DevContainer)

```text
$HOME/                                              ← user home directory
├── .claude-marketplaces/                           ← symlinks into project .packages/
│   └── <monorepo>-<marketplace>/  ──symlink──►       ~/projects/my-service/.packages/<monorepo>-<marketplace>/
├── .claude/plugins/                                ← Claude CLI plugin registry
│
└── projects/
    └── my-service/                                 ← project root (git clone)
        ├── .rpmenv                                 ← sourced by Make targets internally
        ├── Makefile                                ← rpmConfigure, rpmClean, rpmHostSetup
        └── .packages/                              ← aggregated symlinks from all sources (gitignored)
            ├── <build-package>/
            ├── rpm-claude-marketplaces-install/    ← install tool package (via common/claude-marketplaces.xml)
            │   └── install_claude_marketplaces.py
            └── <monorepo>-<marketplace>/           ← actual checkout (symlinked from ~/.claude-marketplaces/)
```

#### 15.3.4 Combined View: What the DevContainer Developer Sees

```text
/home/vscode/                                       ← $HOME inside devcontainer
├── .claude-marketplaces/                           ← symlinks into project .packages/
│   └── <monorepo>-<marketplace>/  ──symlink──►       /workspaces/my-service/.packages/<monorepo>-<marketplace>/
├── .claude/plugins/                                ← Claude CLI plugin registry
│
/workspaces/
└── my-service/                                     ← project root (mounted by devcontainer)
    ├── .rpmenv                                     ← sourced by Make targets internally
    ├── Makefile                                    ← rpmConfigure, rpmClean, rpmHostSetup
    ├── .devcontainer/                              ← DevContainer config (no install script here)
    └── .packages/                                  ← aggregated symlinks from all sources (gitignored)
        ├── <build-package>/
        ├── rpm-claude-marketplaces-install/        ← install tool package (via common/claude-marketplaces.xml)
        │   └── install_claude_marketplaces.py
        └── <monorepo>-<marketplace>/               ← actual checkout (symlinked from ~/.claude-marketplaces/)
```

The install script is delivered by `repo sync` at
`.packages/rpm-claude-marketplaces-install/install_claude_marketplaces.py`. No
copies
to `$HOME`, no PATH installation, no environment detection needed.

### 15.4 `rpmHostSetup` (Idempotent Prerequisite Target)

The `rpmHostSetup` target validates prerequisites and prepares the environment.
It is
**idempotent**: every step uses create-if-not-exists or overwrite semantics, so
running
it multiple times produces the same result as running it once.

`rpmConfigure` calls `rpmHostSetup` as its first step. Developers never need to
call
`rpmHostSetup` directly (though they can, since it is idempotent).

The `rpmHostSetup` target MUST perform the following steps:

| Step | Action | Idempotent? | Purpose |
|---|---|---|---|
| 1 | Verify `python3` is on PATH | Yes (check only) | Fail fast with exit 127 if Python is not installed |
| 2 | Verify `repo` is on PATH | Yes (check only) | Fail fast with exit 127 if repo tool is not installed |
| 3 | Verify `claude` is on PATH | Yes (check only) | Fail fast with exit 127 if Claude CLI is not installed |

`rpmHostSetup` performs **only** prerequisite validation. It does NOT copy or
stage the
install script, and it does NOT create the `$HOME/.claude-marketplaces`
directory (that
is handled conditionally by `rpmConfigure` when `RPM_MARKETPLACE_INSTALL=true`).
The
install script is delivered by `repo sync` as part of the
`rpm-claude-marketplaces-install`
RPM package and is available at
`.packages/rpm-claude-marketplaces-install/install_claude_marketplaces.py`
after sync completes (see Section 9.1, step 8).

If any prerequisite check fails, the target MUST exit with a non-zero code and a
clear error message.

### 15.5 Per-Project Setup

From the project root, the developer runs a single command:

```bash
cd <project-root>
make rpmConfigure
```

This is the only command a developer needs to remember. The `rpmConfigure`
target
sources `.rpmenv` internally and calls `rpmHostSetup` before doing anything
else.
The developer does not need to source `.rpmenv` manually or run `rpmHostSetup`
separately.

The full sequence (matching Section 9.1):

1. `make rpmHostSetup` (idempotent prerequisite checks)
2. `source .rpmenv` (loads `RPM_SOURCES`, `RPM_SOURCE_<name>_*`,
   `CLAUDE_MARKETPLACES_DIR`, `RPM_MARKETPLACE_INSTALL`, etc.)
3. Validate sources (verify all required `RPM_SOURCE_<name>_URL/REVISION/PATH`
   vars exist)
4. If `RPM_MARKETPLACE_INSTALL=true`: `mkdir -p` + pre-sync marketplace cleanup
   (`rm -rf ${CLAUDE_MARKETPLACES_DIR}/*`)
5. For each source in `RPM_SOURCES`: `repo init` → `repo envsubst` → `repo sync`
   (per-source in `.rpm/sources/<name>/`)
6. Aggregate: symlink `.rpm/sources/<name>/.packages/*` into `.packages/`
   (collision check)
7. `.gitignore` updated with `.packages/`, `.rpm/`
8. If `RPM_MARKETPLACE_INSTALL=true`: run
   `.packages/rpm-claude-marketplaces-install/install_claude_marketplaces.py`

### 15.6 Script Portability

The `install_claude_marketplaces.py` script is delivered via the
`rpm-claude-marketplaces-install`
RPM package (synced through `common/claude-marketplaces.xml`). It lives at
`.packages/rpm-claude-marketplaces-install/install_claude_marketplaces.py` after
sync.
The script works identically in both devcontainer and host environments because
it:

1. **Uses `$HOME` for marketplace discovery**: resolves to `/home/vscode` in the
   devcontainer and to the user's home directory on the host
2. **Locates `claude` via `shutil.which`**: works whether Claude is installed
   system-wide
   or via nvm/volta/etc.
3. **Uses Python stdlib only**: `logging`, `subprocess`, `pathlib`, `json`,
   `shutil`
4. **Performs no docker/container-specific operations**: pure filesystem and CLI
   commands
5. **Requires no special permissions**: runs as the current user

### 15.7 Identical Behavior Guarantee

| Operation | In Devcontainer | Outside Devcontainer | Same Target? |
|---|---|---|---|
| Full setup (single command) | `make rpmConfigure` (from project-setup.sh) | `make rpmConfigure` (manual) | Yes |
| Prerequisite checks | `rpmHostSetup` (called by rpmConfigure, idempotent) | `rpmHostSetup` (called by rpmConfigure, idempotent) | Yes |
| Teardown | `make rpmClean` | `make rpmClean` | Yes |
| Install script | `.packages/rpm-claude-marketplaces-install/install_claude_marketplaces.py` | `.packages/rpm-claude-marketplaces-install/install_claude_marketplaces.py` | Yes (same path) |
| Marketplace symlinks | `$HOME/.claude-marketplaces/` | `$HOME/.claude-marketplaces/` | Yes (same path) |
| Plugin registry | `$HOME/.claude/plugins/` | `$HOME/.claude/plugins/` | Yes (same path) |
| Build packages | `.packages/<build-packages>/` | `.packages/<build-packages>/` | Yes (same path) |
| Monorepo checkouts | `.packages/<monorepo>-<marketplace>/` | `.packages/<monorepo>-<marketplace>/` | Yes (same path) |

The developer runs **one command**: `make rpmConfigure`. This calls
`rpmHostSetup`
internally (idempotent, safe to run every time). The install script is always at
`.packages/rpm-claude-marketplaces-install/install_claude_marketplaces.py`
(delivered
by `repo sync`). All paths are identical in both environments. `$HOME` is the
only
runtime variable, and the operating system resolves it correctly in both
environments.

The two environments are **fully isolated**. Plugins installed inside the
devcontainer
do not appear on the host, and vice versa. Both environments use the same Make
targets,
the same scripts, and the same `$HOME`-relative paths, but their state is
independent.

### 15.8 Cleanup

```bash
# Full teardown: uninstalls plugins, removes marketplaces, cleans RPM state
make rpmClean
```

---

## 16. What This Specification Does NOT Cover

The following are explicitly out of scope and must be defined separately:

- The internal structure of individual Claude Code plugins (beyond requiring
  valid metadata)
- The specific marketplaces to include in any given technology context
- The CI/CD pipeline implementation details for the plugin monorepo (beyond the
  governance
  model described in Section 10.2)
- The Claude Code plugin format specification (owned by Anthropic)
- Plugin uninstallation edge cases (bulk uninstall is handled by `make
  rpmClean`)
- Multi-monorepo support details (the architecture supports it via `<repo-name>`
  prefix,
  but specific manifest configuration is project-specific)
- Host OS package manager prerequisites (runtime, build tool, repo tool
  installation)
- IDE-specific configuration beyond VS Code devcontainers

---

## 17. Required Enhancements to Caylent `repo` Fork

This specification depends on two features that MUST be added to the Caylent
`repo` fork (`caylent-solutions/git-repo`) and released as tag `caylent-2.0.0`
(major bump due to breaking validation changes).

> **Implementation note:** Sections 17.1-17.4 describe **design requirements**,
not
> step-by-step implementation instructions. The implementing agent MUST read the
> `git-repo` fork source code to understand current function signatures, class
> hierarchies, and test patterns before making changes. The file names, function
> names, and integration points below are guidance based on the upstream
codebase
> structure — the agent should verify these against the actual fork and adapt as
> needed. The acceptance criteria (what the code must DO) are authoritative; the
> suggested approach (HOW to implement) is advisory.

| Feature | Required By | Description |
|---|---|---|
| Absolute `<linkfile dest>` after `envsubst` | Section 5.1 | The standard `repo` tool restricts `<linkfile dest>` to paths within the project tree. This spec requires `dest` to resolve to `${CLAUDE_MARKETPLACES_DIR}` (an absolute path outside the project, e.g., `$HOME/.claude-marketplaces/`). The fork MUST allow absolute `dest` paths after `envsubst` resolution. **Implementation:** Add `abs_ok` parameter to `_CheckLocalPath()` in `manifest_xml.py`, pass `abs_ok=True` for linkfile dest in `_ValidateFilePaths()`, handle absolute dest in `_LinkFile._Link()` in `project.py` by skipping `_SafeExpandPath` and using the path directly. |
| Version constraint resolution in `revision` | Section 5.5 | The standard `repo` tool treats `revision` as a literal git ref. This spec requires PEP 440-compatible version constraints (e.g., `~=1.2.0`, `~=1.0`, `*`) in the `revision` attribute. The fork MUST scan available tags, evaluate the constraint, and check out the highest matching version. **Implementation:** Create `version_constraints.py` module with `is_version_constraint()` and `resolve_version_constraint()` functions using Python's `packaging.specifiers.SpecifierSet`. Integrate into `GetRevisionId()` in `project.py` — detect constraint syntax, collect tags from local refs or `ls-remote`, resolve to highest match, then continue normal ref resolution. Add `packaging` to `setup.py` dependencies. |

### 17.1 Implementation Details: Absolute Linkfile Dest

**Files to modify:**

| File | Change |
|---|---|
| `manifest_xml.py` | Add `abs_ok=False` parameter to `_CheckLocalPath()`. When `abs_ok=True`, skip the `os.path.isabs(norm)` and `norm.startswith("/")` checks. All other validations (bad codepoints, `.git`, `.repo`, `..`) still apply. |
| `manifest_xml.py` | In `_ValidateFilePaths()`, pass `abs_ok=True` when validating linkfile dest (element == "linkfile"). Copyfile dest remains restricted to relative paths. |
| `project.py` | In `_LinkFile._Link()`, detect `os.path.isabs(self.dest)`. If absolute, use the path directly and create parent directories with `os.makedirs()`. If relative, use existing `_SafeExpandPath(self.topdir, self.dest)` logic. |
| `docs/manifest-format.md` | Update the linkfile element documentation to note that dest may be an absolute path after `repo envsubst`. |
| `tests/test_manifest_xml.py` | Add tests verifying: absolute dest accepted for linkfile, absolute dest rejected for copyfile, bad components (`.git`, `.repo`, unicode) still rejected in absolute paths. |

### 17.2 Implementation Details: PEP 440 Version Constraints

**New file:** `version_constraints.py`

| Function | Purpose |
|---|---|
| `is_version_constraint(revision)` | Detects PEP 440 constraint syntax in the last path component of a revision string. Returns `True` for `~=`, `*`, `>=`, `<`, etc. |
| `resolve_version_constraint(revision, available_tags)` | Splits revision into `<prefix>/<constraint>`, collects tags matching prefix, parses versions with `packaging.version.Version`, evaluates constraint with `packaging.specifiers.SpecifierSet`, returns the full tag name of the highest match. |

**Integration point:** `GetRevisionId()` in `project.py`

1. Before `rem.ToLocal()`, check `is_version_constraint(self.revisionExpr)`
2. If true, call `_ResolveVersionConstraint()` which:
      a. Collects tag names from `all_refs` (local) or
   `_LsRemote("refs/tags/*")` (remote)
   b. Calls `resolve_version_constraint()` to find best match
   c. Returns the resolved tag name
3. Use the resolved tag as the revision expression for normal checkout flow
4. If no matching tag found, raise `ManifestInvalidRevisionError`

**Dependency:** Add `packaging` to `install_requires` in `setup.py`.

### 17.3 Existing Behaviors to Preserve

The fork MUST NOT break:

| Behavior | Verification |
|---|---|
| `<linkfile>` with directory targets | Existing tests + manual verification |
| Multiple independent checkouts of same repo at different revisions | Core to marketplace architecture (Section 5.4) |
| `preciousObjects` for shared object stores | Automatic with same-name projects |
| `repo envsubst` for `${VAR}` substitution | Existing envsubst tests |
| Circular `<include>` detection | Built into upstream, inherited by fork |

### 17.4 Release

After both features are implemented and all tests pass (289+ existing tests plus
new
tests for both features), tag the fork as `caylent-2.0.0`.

---

## 18. Repository Inventory

The complete RPM ecosystem consists of four repositories under
`caylent-solutions`:

| Repository | Visibility | License | Purpose | Default Branch |
|---|---|---|---|---|
| `git-repo` | Public | Apache 2.0 | Caylent fork of Google's repo tool with envsubst, absolute linkfile dest, and PEP 440 version constraints | `main` |
| `caylent-private-rpm` | Private | Proprietary | RPM manifest repository with `repo-specs/` hierarchy, multi-source bootstrap, and cascading marketplace manifests | `main` |
| `rpm-claude-marketplaces` | Private | Proprietary | Plugin monorepo containing all Claude Code marketplace directories with `config-repo.json` governance | `main` |
| `rpm-claude-marketplaces-install` | Public | Apache 2.0 | RPM package containing install and uninstall scripts for Claude Code marketplace plugin discovery and registration | `main` |

**GitHub settings (all repos):**
- Squash merge: allowed
- Merge commit: disabled
- Rebase merge: disabled
- Branch ruleset on `main`: active, requires PR with 1 approving review, code
  owner
    review, last push approval, resolved threads, squash merge only, linear
  history,
  no deletion, no non-fast-forward

---

## 19. Example Implementation: Cascading Manifest Hierarchy

### 19.1 Example Hierarchy in `caylent-private-rpm`

The `repo-specs/` directory in `caylent-private-rpm` contains an example
demonstrating
7 levels of cascading marketplace inheritance through the path:

```text
common → example → development → python → make → argparse → cli
```

This uses the existing `<include>` directive of the `repo` tool (not a
Claude-specific
feature). Any manifest at any depth can include any other manifest by its full
path —
cascading parent-child is a convention, not a requirement.

**Note on example vs. production paths:** The example hierarchy uses
`common/example/`
as the second level, not `common/development/` as used in production. This is
intentional — it demonstrates that the `flattening_strip_prefixes` algorithm
(`["common", "development"]`) only strips matching prefixes. Since `example`
does not
match `development`, it is retained in flattened names (e.g.,
`rpm-claude-marketplaces-example-example-tools`). This validates that the
stripping
logic is prefix-specific, not position-based.

**Full manifest hierarchy:**

```text
repo-specs/
├── git-connection/remote.xml                                              [EXISTS]
└── common/
    ├── claude-marketplaces.xml                                            [real root, contains install tool package]
    └── example/
        ├── claude-marketplaces.xml                                        [includes common/, adds example-level marketplace]
        └── development/
            ├── claude-marketplaces.xml                                    [includes example/]
            └── python/
                ├── claude-marketplaces.xml                                [includes development/]
                └── make/
                    ├── claude-marketplaces.xml                            [includes python/]
                    └── argparse/
                        ├── claude-marketplaces.xml                        [includes make/]
                        └── cli/
                            ├── claude-marketplaces.xml                    [leaf, includes argparse/]
                            ├── packages.xml                               [build packages]
                            └── meta.xml                                   [entry point]
```

**`repo-specs/common/claude-marketplaces.xml` (real root):**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <include name="repo-specs/git-connection/remote.xml" />
  <project name="rpm-claude-marketplaces-install"
           path=".packages/rpm-claude-marketplaces-install"
           remote="caylent"
           revision="main" />
</manifest>
```

This root manifest includes the install tool package. Every manifest that
includes
this (directly or through cascading inheritance) automatically receives the
install
tool. No marketplace `<project>` entries exist at this level because this is
the real root, not an example — only the install tool is universal.

**Cascading include pattern (each level follows the same structure):**

```xml
<!-- repo-specs/common/example/development/python/make/claude-marketplaces.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <include name="repo-specs/common/example/development/python/claude-marketplaces.xml" />
  <project name="rpm-claude-marketplaces"
           path=".packages/rpm-claude-marketplaces-example-make-utils"
           remote="caylent"
           revision="refs/tags/example/development/python/make/make-utils/1.0.0">
    <linkfile src="common/example/development/python/make/make-utils"
              dest="${CLAUDE_MARKETPLACES_DIR}/rpm-claude-marketplaces-example-make-utils" />
  </project>
</manifest>
```

### 19.2 Example Marketplace Structure in `rpm-claude-marketplaces`

Dummy marketplaces at each level demonstrating cascading inheritance:

Each marketplace contains `.claude-plugin/marketplace.json` and one or more
plugin
subdirectories, each with `.claude-plugin/plugin.json` (per Section 4.2.2):

```text
common/
└── example/
    ├── example-tools/                                    ← marketplace at example root
    │   ├── .claude-plugin/
    │   │   └── marketplace.json
    │   └── example-tool-plugin/                          ← plugin subdirectory
    │       └── .claude-plugin/
    │           └── plugin.json
    └── development/
        ├── dev-lint/                                     ← marketplace at development level
        │   ├── .claude-plugin/
        │   │   └── marketplace.json
        │   └── lint-plugin/
        │       └── .claude-plugin/
        │           └── plugin.json
        └── python/
            ├── python-helpers/                           ← marketplace at python level
            │   ├── .claude-plugin/marketplace.json
            │   └── helpers-plugin/.claude-plugin/plugin.json
            └── make/
                ├── make-utils/                           ← marketplace at make level
                │   ├── .claude-plugin/marketplace.json
                │   └── utils-plugin/.claude-plugin/plugin.json
                └── argparse/
                    ├── argparse-scaffold/                ← marketplace at argparse level
                    │   ├── .claude-plugin/marketplace.json
                    │   └── scaffold-plugin/.claude-plugin/plugin.json
                    └── cli/
                        └── cli-agent/                    ← marketplace at cli leaf level
                            ├── .claude-plugin/marketplace.json
                            └── agent-plugin/.claude-plugin/plugin.json
```

All `marketplace.json` and `plugin.json` files are trivial dummies for
validation
purposes. Each marketplace has exactly one plugin for simplicity. This structure
validates:
- 6 levels of cascading inheritance (a `cli/` project inherits all 6
  marketplaces
  plus the install tool from the root)
- Path flattening at each level
- `<linkfile>` symlink creation with `${CLAUDE_MARKETPLACES_DIR}`
- Install script discovers and processes all inherited marketplaces
- Tag-based versioning

### 19.3 Example Tags

One tag per marketplace in `rpm-claude-marketplaces`:

Tags strip the `marketplace_root` prefix (`common`), matching Section 4.4
convention:

```text
example/example-tools/1.0.0
example/development/dev-lint/1.0.0
example/development/python/python-helpers/1.0.0
example/development/python/make/make-utils/1.0.0
example/development/python/make/argparse/argparse-scaffold/1.0.0
example/development/python/make/argparse/cli/cli-agent/1.0.0
```

### 19.4 Example `.rpmenv` (Multi-Source)

```properties
# Repo tool
REPO_URL=https://github.com/caylent-solutions/git-repo.git
REPO_REV=caylent-2.0.0

# Shared env vars for envsubst
GITBASE=https://github.com/caylent-solutions/
CLAUDE_MARKETPLACES_DIR=${HOME}/.claude-marketplaces

# Marketplace install toggle
RPM_MARKETPLACE_INSTALL=true

# Source registry
RPM_SOURCES=build,marketplaces

# Source: build — build tooling packages
RPM_SOURCE_build_URL=https://github.com/caylent-solutions/caylent-private-rpm.git
RPM_SOURCE_build_REVISION=main
RPM_SOURCE_build_PATH=repo-specs/common/example/development/python/make/argparse/cli/meta.xml

# Source: marketplaces — claude plugin marketplaces
RPM_SOURCE_marketplaces_URL=https://github.com/caylent-solutions/caylent-private-rpm.git
RPM_SOURCE_marketplaces_REVISION=main
RPM_SOURCE_marketplaces_PATH=repo-specs/common/example/development/python/make/argparse/cli/claude-marketplaces.xml
```

### 19.5 What the Example CLI Project Receives

After `rpmConfigure` with the above `.rpmenv`, the example project receives:

| Source Level | Package/Marketplace |
|---|---|
| Root (common/) | `rpm-claude-marketplaces-install` (install tool) |
| example/ | `rpm-claude-marketplaces-example-example-tools` |
| development/ | `rpm-claude-marketplaces-example-dev-lint` |
| python/ | `rpm-claude-marketplaces-example-python-helpers` |
| make/ | `rpm-claude-marketplaces-example-make-utils` |
| argparse/ | `rpm-claude-marketplaces-example-argparse-scaffold` |
| cli/ (leaf) | `rpm-claude-marketplaces-example-cli-agent` |

Total: 1 install tool package + 6 example marketplaces, all delivered through
cascading `<include>` inheritance.

---

## 20. Implementation Order

The repositories MUST be implemented in the following order. Dependencies
between
repos dictate this sequence:

| Order | Repo | Work | Depends On |
|---|---|---|---|
| 1 | `git-repo` | Absolute linkfile dest + PEP 440 version constraints → tag `caylent-2.0.0` | Nothing (foundational) |
| 2 | `rpm-claude-marketplaces-install` | `install_claude_marketplaces.py` + `uninstall_claude_marketplaces.py` | Nothing (independent scripts) |
| 3 | `rpm-claude-marketplaces` | `config-repo.json` + example marketplaces + tags + CI/CD + CODEOWNERS | Nothing (independent monorepo) |
| 4 | `caylent-private-rpm` | Multi-source bootstrap + cascading manifests + validation + CI/CD + docs + examples | git-repo (for `caylent-2.0.0` tag), rpm-claude-marketplaces-install (synced as package), rpm-claude-marketplaces (tags referenced by manifests) |
| 5 | Spec updates | Reconcile this spec with implementation reality | All repos implemented |

**Why this order:**
- Fork features are needed by manifests (git-repo first)
- Install tool is synced by manifests (rpm-claude-marketplaces-install before
  caylent-private-rpm)
- Monorepo tags are referenced by manifests (rpm-claude-marketplaces before
  caylent-private-rpm)

### 20.1 `caylent-private-rpm` Detailed Work Items

| Item | Description |
|---|---|
| `scripts/rpm/` Python scripts | Create `scripts/rpm/host_setup.py`, `scripts/rpm/configure.py`, `scripts/rpm/clean.py` per Section 8.6 |
| Multi-source `.rpmenv` | `configure.py` parses `RPM_SOURCES` and `RPM_SOURCE_<name>_*` groups |
| `rpmConfigure` rewrite | `configure.py`: isolated source workspaces under `.rpm/sources/<name>/`, symlink aggregation, collision detection |
| `rpmClean` update | `clean.py`: multi-source cleanup + `RPM_MARKETPLACE_INSTALL` toggle |
| Makefile update | Thin orchestration — three targets delegating to `python3 scripts/rpm/<script>.py` per Section 8.6 |
| Cascading manifest hierarchy | Create `repo-specs/common/claude-marketplaces.xml` (root) + 7 levels of example manifests |
| Enhanced XML validation | Extend `scripts/validate_xml.py` for linkfile dest, include chain integrity, flattened name uniqueness, tag format |
| CI/CD workflows | `marketplace-validate.yml`, `marketplace-cli-test.yml`, `marketplace-ci.yml`, `marketplace-qa.yml`, `marketplace-release.yml` |
| CODEOWNERS | `/repo-specs/`, `/scripts/`, `/.github/` owned by `@caylent-solutions/platform-team` |
| Documentation | Update `README.md`, create `docs/claude-marketplaces-guide.md`, create `docs/multi-source-guide.md`, update `docs/contributing.md` |
| Example updates | Update existing `.rpmenv` files to named source format, add `CLAUDE_MARKETPLACES_DIR` and `RPM_MARKETPLACE_INSTALL` |

### 20.2 `rpm-claude-marketplaces` Detailed Work Items

| Item | Description |
|---|---|
| `config-repo.json` | Monorepo governance with `reserved_directories` including `example`, `make`, `argparse`, `cli` |
| Example marketplace structure | 6 dummy marketplaces, each with `.claude-plugin/marketplace.json` and one plugin subdirectory with `.claude-plugin/plugin.json` (per Section 4.2.2) |
| Example tags | One tag per marketplace following `<marketplace-path>/<semver>` convention |
| CI/CD workflows | Single-scope PR validation, plugin name uniqueness, flattened name validation |
| CODEOWNERS | Platform team owns structure; marketplace owners own their directories |

### 20.3 `rpm-claude-marketplaces-install` Detailed Work Items

| Item | Description |
|---|---|
| `install_claude_marketplaces.py` | Full install script per Section 7 specification |
| `uninstall_claude_marketplaces.py` | Full uninstall script per Section 7.7 specification |

---

## Changelog

| Date | Section | Change | Audit Reference |
|------|---------|--------|-----------------|
| 2026-03-06 | 6.3 | Changed collision detection from MUST to SHOULD for multi-monorepo; clarified single-monorepo as primary use case | E5-F2-S1 audit, Section 6 (PARTIAL) |
| 2026-03-06 | 7.1, 7.4, 7.7, 8.6, and all references | Renamed `install-claude-marketplaces.py` to `install_claude_marketplaces.py` (underscores) to match actual implementation and Python naming conventions; same for uninstall script | E5-F2-S1 audit, Section 7 (DISCREPANCY) |
