# Claude Code Development Guidelines

## ⚠️ REPOSITORY STATUS - READ THIS FIRST

**This repository (ha-abb-powerone-pvi-sunspec v4.x) is being superseded by two new specialized integrations:**

1. **[ha-abb-fimer-pvi-sunspec](https://github.com/alexdelprete/ha-abb-fimer-pvi-sunspec)** - Modbus/TCP only (v1.0.0-beta.x)
   - Direct Modbus/TCP communication with inverters
   - Dynamic SunSpec model discovery
   - Based on ModbusLink library with async-sunspec-client

2. **[ha-abb-fimer-pvi-vsn-rest](https://github.com/alexdelprete/ha-abb-fimer-pvi-vsn-rest)** - REST API only (v1.0.0-beta.x)
   - VSN300/VSN700 datalogger support via REST API
   - Automatic VSN model detection
   - Data normalization to SunSpec schema

**Rationale for Split:**
The original plan for a universal client combining both protocols added complexity without clear user benefit. Most
users have either:

- Direct Modbus access to inverters, OR
- VSN dataloggers with REST API

Maintaining two focused integrations provides better code clarity, easier maintenance, and protocol-specific optimization.

**Current Repository:**

- Remains available at v4.1.6 for existing users
- No new features planned
- Critical bug fixes only
- Users should migrate to appropriate new integration when ready

---

## Original Project Overview (v4.x - LEGACY)

- This repository provides a Home Assistant custom integration for ABB/Power-One/FIMER PVI inverters. The v4.x
  integration uses Modbus/TCP via pymodbus library.

Architecture Overview (v4.x - LEGACY)

- Modbus/TCP Client (pymodbus-based)
  - Direct inverter communication
  - Static model reading (M103, M160)
  - Fixed register addresses

Core Components in the HA Integration

1) __init__.py

   - async_setup_entry(): Initialize universal client hub + coordinator and forward platforms
   - async_unload_entry(): Clean shutdown and resource cleanup
   - async_migrate_entry(): Config migration (Modbus-only → universal client format)
   - Uses config_entry.runtime_data to store coordinator and update listener

2) coordinator.py

   - ABBPowerOneFimerCoordinator consumes the universal client hub
   - Manages polling cycles, error handling, retry logic

3) config_flow.py

   - ConfigFlow for initial setup
   - OptionsFlow for runtime reconfiguration
   - Protocol selection (REST vs Modbus)
   - For REST: VSN model/auth; For Modbus: host/port/device_id/base_addr
   - Migration for existing installs; warnings on capability deltas when switching protocol

4) sensor.py

   - Dynamic sensor creation from the normalized devices + measurements schema
   - Supports both single-phase and three-phase inverters, MPPT groups, meters, and storage where available

Important Patterns

- Error Handling
  - Use unified exceptions exposed by the universal client
  - For low-level mapping, prefer helpers:
    - _check_modbus_exception_response()
    - _handle_connection_exception()
    - _handle_modbus_exception()
- Logging
  - Use helpers from helpers.py
    - log_debug(logger, context, message, **kwargs)
    - log_info(logger, context, message, **kwargs)
    - log_warning(logger, context, message, **kwargs)
    - log_error(logger, context, message, **kwargs)
  - Never use f-strings in logger calls; use %s formatting and always include the context
- Async/Await
  - All I/O must be async. The universal client and both protocol clients are async-only
  - API close() methods are async — always await them
- Data Storage
  - Use config_entry.runtime_data with typed RuntimeData

Code Quality Standards

- Ruff Configuration
  - Follow .ruff.toml strictly
  - Key rules: A001, TRY300, TRY301, RET505, G004, SIM222, PIE796
- Type Hints
  - Add type hints to all classes and instance variables
  - Use modern type syntax; alias: type ABBPowerOneFimerConfigEntry = ConfigEntry[RuntimeData]

Testing Approach

- Unit tests
  - SunSpec parser: scale factors, repeats, invalid sentinels
  - REST auth: VSN300 header, VSN700 bearer; livedata+feeds merge
  - Device ID derivation for components with/without Common models
  - Capability map correctness
- Protocol switching
  - Options migration, entity lifecycle (disable/unavailable/remove per HA guidance)
- Integration tests
  - Single-phase and three-phase
  - MPPT variations
  - VSN300/VSN700 scenarios

Common Patterns

- Version Updates
  1) Update manifest.json version
  2) Update const.py VERSION
  3) Create docs/releases/vX.Y.Z.md (full notes)
  4) Update CHANGELOG.md (summary + links)
  5) Commit: "Bump version to vX.Y.Z"
  6) Tag: git tag -a vX.Y.Z -m "Release vX.Y.Z"
  7) Push: git push && git push --tags
  8) Create GitHub release (pre-release/latest as appropriate)

- Release Documentation Structure
  - CHANGELOG.md (overview)
  - docs/releases/ (detailed notes per version)
  - docs/releases/README.md (release directory guide)

Configuration Parameters

- host: IP/hostname (not used for unique_id)
- port: TCP port (default 502 for Modbus)
- device_id: Modbus unit ID (default 2, 1–247)
- base_addr: SunSpec base address (0 or 40000)
- scan_interval: polling frequency (default 60s, 30–600)
- protocol: rest or modbus
- REST options: vsn_model (300 or 700), auth params

Entity Unique IDs

- Device identifier: (DOMAIN, serial_number)
- Sensors: {serial_number}_{sensor_key}
- Stable component IDs synthesized when a subcomponent lacks a separate Common model

SunSpec Models

- Common (M1), Inverter (M101/103), Nameplate (M120+), MPPT (M160)
- Discovery offsets for M160: 122, 1104, 208

Git Workflow

- Commit Messages
  - Use conventional commits
  - Always include Claude attribution block
- Branch Strategy
  - Main branch: master
  - Feature branch for this program of work: feature/abb-fimer-client-library
  - Create tags for releases; use pre-release flag for betas

Dependencies

- Home Assistant core
- ModbusLink (async Modbus client library)
- aiohttp
- Vendored SunSpec JSON model files (Apache-2.0). We reuse JSON definitions only; we do not depend on the pysunspec2 runtime

Key Files to Review

- .ruff.toml
- const.py
- helpers.py
- coordinator.py, config_flow.py, sensor.py
- docs/architecture-plan.md (finalized plan and milestones)
- docs/pysunspec2-analysis.md (decision record)
- vendor/sunspec_models (model JSON and NOTICE/NAMESPACE) once added

pysunspec2 Decision

- Do not use pysunspec2 runtime. Reuse the JSON model definitions only
- See docs/pysunspec2-analysis.md for full analysis and rationale

SunSpec Model JSON Sync Procedure (documented only)

- Upstream: <https://github.com/sunspec/pysunspec2> (sunspec2/models/json)
- Provide a small sync script (e.g., scripts/sync_sunspec_models.py) that:
  - Fetches JSON at a pinned ref and copies into vendor/sunspec_models
  - Writes/refreshes NOTICE (Apache-2.0) and NAMESPACE (origin URL, ref, timestamp)
  - Validates JSON and produces a manifest with IDs, names, checksums
- Checklist is in docs/architecture-plan.md

Don't Do

- Do not use hass.data[DOMAIN][entry_id]; use runtime_data
- Do not shadow builtins
- Do not use f-strings in logging
- Do not forget to await async API methods
- Do not mix sync/async patterns
- Do not add a runtime dependency on pysunspec2

<!-- BEGIN SHARED:repo-sync -->
<!-- Synced by repo-sync on 2026-10-03 -->

<!--
==============================================================================
⚠️  TEMPLATE-MANAGED ZONE — DO NOT EDIT BETWEEN BEGIN SHARED AND END SHARED.

This entire region is auto-generated from
ha-integration-template/templates/markers/CLAUDE_SHARED.md.j2 via
`repo-sync.py`. Edits between the marker lines are silently overwritten
on the next sync.

To change shared guidance:
  1. Edit CLAUDE_SHARED.md.j2 in ha-integration-template
  2. Sync downstream: `python repo-sync.py sync <consumer>`

Integration-specific guidance belongs OUTSIDE the markers (above
BEGIN SHARED or below END SHARED).
==============================================================================
-->

## Context7 for Documentation

Always use Context7 MCP tools automatically (without being asked) when:

- Generating code that uses external libraries
- Providing setup or configuration steps
- Looking up library/API documentation

Use `resolve-library-id` first to get the library ID, then `get-library-docs` to fetch documentation.

## GitHub MCP for Repository Operations

Always use GitHub MCP tools (`mcp__github__*`) for GitHub operations instead of the `gh` CLI:

- **Issues**: `issue_read`, `issue_write`, `list_issues`, `search_issues`, `add_issue_comment`
- **Pull Requests**: `list_pull_requests`, `create_pull_request`, `pull_request_read`, `merge_pull_request`
- **Reviews**: `pull_request_review_write`, `add_comment_to_pending_review`
- **Repositories**: `search_repositories`, `get_file_contents`, `list_branches`, `list_commits`
- **Releases**: `list_releases`, `get_latest_release`, `list_tags`

Benefits over `gh` CLI:

- Direct API access without shell escaping issues
- Structured JSON responses
- Better error handling
- No subprocess overhead

## CI Workflow Status and Logs

> **IMPORTANT**: Always use `gh` CLI for CI workflow status and logs — it's more efficient than GitHub MCP.

The project has 3 CI workflows: **Lint**, **Tests**, and **Validate**.

**List recent workflow runs:**

```bash
gh run list --repo alexdelprete/ha-abb-powerone-pvi-sunspec --limit 5
```

**Get workflow status for a specific run:**

```bash
gh run view <run_id> --repo alexdelprete/ha-abb-powerone-pvi-sunspec
```

**Get test coverage from Tests workflow logs:**

```bash
gh run view <run_id> --repo alexdelprete/ha-abb-powerone-pvi-sunspec --log 2>&1 | grep "TOTAL"
```

**Quick one-liner to get latest Tests run coverage:**

```bash
# Get latest Tests run ID and fetch coverage
gh run list --repo alexdelprete/ha-abb-powerone-pvi-sunspec --limit 5 | grep Tests
# Then use the run ID from the output
gh run view <run_id> --repo alexdelprete/ha-abb-powerone-pvi-sunspec --log 2>&1 | grep "TOTAL"
```

## Coding Standards

### Data Storage Pattern

**DO use `runtime_data`** (modern pattern):

```python
entry.runtime_data = MyData(device_name=name)
```

**DO NOT use `hass.data[DOMAIN]`** (deprecated pattern)

### Translations (Custom Integrations)

Per [HA developer docs](https://developers.home-assistant.io/docs/internationalization/custom_integration/):

- **DO use `translations/en.json`** as the source of truth for English strings
- **DO NOT create `strings.json`** — it is a Core-only build-time feature and is ignored by custom integrations
- All translation files go in `translations/<lang>.json` (e.g., `en.json`, `de.json`, `it.json`)

### Logging

Use structured logging:

```python
_LOGGER.debug("Sensor %s subscribed to %s", key, topic)
```

**DO NOT** use f-strings in logger calls (deferred formatting is more efficient)

Use centralized logging helpers from `helpers.py` when available:

- `log_debug(logger, context, message, **kwargs)`
- `log_info(logger, context, message, **kwargs)`
- `log_warning(logger, context, message, **kwargs)`
- `log_error(logger, context, message, **kwargs)`

Always include context parameter (function name). Format: `(function_name) [key=value]: message`

**Never log manually what HA logs automatically:**

- **DataUpdateCoordinator**: Just raise `UpdateFailed` — HA handles logging automatically
- **ConfigEntryNotReady**: HA logs automatically — don't log manually
- This prevents log spam during extended outages

### Error Handling

- Use custom exceptions (not `return False`) for proper entity availability tracking
- Raise exceptions in the API layer and let the coordinator handle retries
- Define integration-specific exceptions (e.g., `ConnectionError`, `DataError`)

### Type Hints

Always use type hints for function signatures.

### Async/Await Conventions

- All coordinator methods are async
- API methods use async/await properly
- Config entry methods follow HA conventions:
  - `add_update_listener()` — sync
  - `async_on_unload()` — sync (despite the name)
  - `async_forward_entry_setups()` — async
  - `async_unload_platforms()` — async
- Never use blocking calls in async context

## Configuration Best Practices

Following HA best practices, configuration is split between `data` (initial config) and `options` (runtime tuning):

### config_entry.data (changed via Reconfigure flow)

Connection and identity parameters: name, host, port, device ID, etc.

### config_entry.options (changed via Options flow)

Runtime tuning parameters: scan_interval, timeout, etc. Use OptionsFlowWithReload for auto-reload.

### Config Flow Patterns

- Use `vol.Clamp()` for numeric inputs with min/max bounds (better UX than validation errors)
- Use `async_update_reload_and_abort()` for reconfigure flows
- Implement config entry migration (`async_migrate_entry()`) when changing config schema versions

## Entity and Device Patterns

### Device Registry

- Device identifier tuple: `(DOMAIN, unique_id)` where `unique_id` is MAC address, serial number, or similar
- Use `DeviceInfo` with manufacturer, model, sw_version, and configuration_url
- Changing host/IP should not affect entity IDs or historical data

### Entity Unique IDs

- Sensor unique_id pattern: `{device_unique_id}_{sensor_key}`
- Use stable identifiers (MAC address, serial number) — not connection parameters (IP, hostname)
- Config entry type alias: `type MyConfigEntry = ConfigEntry[RuntimeData]`

## Python Version & HA Baseline

These repos are standardized on the **Python 3.14+** toolchain:

- `pyproject.toml`: `requires-python = ">=3.14.2"` (matches Home Assistant
  core's own floor)
- `[tool.ruff]`: `target-version = "py314"`
- Minimum supported Home Assistant core: **2026.8.0** — the
  first HA release with `DeviceRegistry.async_get_device_by_identifier`,
  which replaces the `async_get_device` lookup deprecated in 2026.9.
  `hacs.json` is rendered from the same value, so HACS users on older HA
  don't see updates.

**Implication for source code**: code in these repos may use 3.14-only
syntax (e.g. PEP 758's parenthesis-free `except A, B:`) and is **not**
backwards-compatible with Python 3.13. Ruff with `target-version = "py314"`
will actively *rewrite* `except (A, B):` into the parenthesis-free form —
which is a SyntaxError on Python 3.13. If a contributor's toolchain
regresses to 3.13, expect lint-fixes from these repos to fail to parse
locally until the toolchain is re-aligned.

## Dependencies Best Practices

### Dependency Update Checklist

**Before updating any dependency version in `manifest.json`:**

1. Verify the new version exists on PyPI: `https://pypi.org/project/PACKAGE_NAME/`
1. Check release notes for breaking changes
1. Test locally if possible

> **WARNING**: Always verify PyPI availability before committing dependency updates. Upstream maintainers
> sometimes create GitHub releases but forget to publish to PyPI, breaking the integration for users.

## Git Workflow

### Commit Messages

Use conventional commits with Claude attribution:

```text
feat(api): implement new feature

[Description]

Co-Authored-By: Claude <noreply@anthropic.com>
```

> **NEVER put a GitHub issue-closing keyword in a commit message.**
> `close`/`closes`/`closed`, `fix`/`fixes`/`fixed`, `resolve`/`resolves`/`resolved`
> followed by `#N` auto-close that issue the moment the commit lands on the default
> branch. Reference issues with a neutral phrase only — "Refs #N", "Reported in #N",
> "Addresses #N". Issues are closed manually by the user, never by automation.

### Branch Strategy

- Default branch (`main` or `master`) = next release
- Create tags for releases
- Use pre-release flag for beta versions

## Pre-Commit Configuration

Linting tools and settings are defined in `.pre-commit-config.yaml`:

| Hook        | Tool                           | Purpose                      |
| ----------- | ------------------------------ | ---------------------------- |
| ruff        | `uvx ruff@X check --no-fix`    | Python linting               |
| ruff-format | `uvx ruff@X format --check`    | Python formatting            |
| jsonlint    | `uvx --from demjson3 jsonlint` | JSON validation              |
| yamllint    | `uvx yamllint@X -d "{...}"`    | YAML linting (inline config) |
| pymarkdown  | `uvx --from pymarkdownlnt==X pymarkdown scan` | Markdown linting |
| ty          | `uvx ty@X check --python "$(which python)"` | Type checking (needs the venv's HA) |

All hooks use `language: system` with `verbose: true` for visibility, and every tool
runs through `uvx` at the exact release CI uses (`[tool.repo-sync.tool-versions]` in the template
repo's `pyproject.toml`: ruff 0.16.8, ty 0.0.82,
yamllint 1.38.0, pymarkdownlnt 0.9.39).
Template changes reach this repo as signed `repo-sync/propagate` pull requests opened by the
template's `propagate.yml`; they auto-merge once the required checks pass. Do not edit those
files by hand: change the template and let it propagate.
ty and ruff are pre-1.0 / fast-moving and add rules between releases; unpinned they
turn CI red on code that passes locally. The venv copies of ruff and ty only serve
the VS Code extensions; `repo-sync` rewrites their `pyproject.toml` entries to the same
pins on every sync (and dependabot ignores them), so the editor matches CI too.

## Pre-Commit Checks (MANDATORY)

> **CRITICAL: ALWAYS run pre-commit checks before ANY git commit.**
> This is a hard rule - no exceptions. Never commit without passing all checks.

```bash
pre-commit run --all-files
```

> Use `pre-commit` directly, **not** `uvx pre-commit`. The `ty` hook
> resolves the interpreter at runtime via `$(which python)` to match the
> devcontainer venv. `uvx` would provision its own ephemeral Python 3.14
> first on PATH, and that env doesn't have Home Assistant installed —
> `ty` would false-fail with unresolved-import errors even though the
> code is fine. The git commit hook and CI's lint workflow already use
> the venv-installed `pre-commit`, so plain `pre-commit run` matches
> their behavior exactly.

Or run individual tools:

```bash
# Python formatting and linting
ruff format .
ruff check . --fix

# Markdown linting (same pinned release as the hook and CI)
uvx --from pymarkdownlnt==0.9.39 pymarkdown --config .pymarkdownlint.json scan .
```

All checks must pass before committing. This applies to ALL commits, not just releases.

### Windows Shell Notes

When running shell commands on Windows, stray `nul` files may be created (Windows null device artifact).
Check for and delete them after command execution:

```bash
rm nul  # if it exists
```

## Testing

> **CRITICAL: NEVER run pytest locally. The local environment cannot be set up correctly for
> Home Assistant integration tests. ALWAYS use GitHub Actions CI to run tests.**

To run tests:

1. Commit and push changes to the repository
1. GitHub Actions will automatically run the test workflow
1. Check the workflow results in the Actions tab or use `mcp__github__*` tools

> **CRITICAL: NEVER modify production code to make tests pass. Always fix the tests instead.**
> Production code is the source of truth. If tests fail, the tests are wrong - not the production code.
> The only exception is when production code has an actual bug that tests correctly identified.

## Quality Scale Tracking (MUST DO)

This integration tracks [Home Assistant Quality Scale][qs] rules in `quality_scale.yaml`.

**When implementing new features or fixing bugs:**

1. Check if the change affects any quality scale rules
1. Update `quality_scale.yaml` status accordingly:
   - `done` - Rule is fully implemented
   - `todo` - Rule needs implementation
   - `exempt` with `comment` - Rule doesn't apply (explain why)
1. Aim to complete all Bronze tier rules first, then Silver, Gold, Platinum

[qs]: https://developers.home-assistant.io/docs/core/integration-quality-scale/

## Release Management - CRITICAL

> **STOP: NEVER create git tags or GitHub releases without explicit user command.**
> This is a hard rule. Always stop after commit/push and wait for user instruction.

**Published releases are FROZEN** - Never modify the git tag, the ZIP asset, or the
`docs/releases/vX.Y.Z.md` file in a way that changes the meaning of what shipped.

The GitHub *release body* (what shows on the release page) may be edited via
`gh release edit vX.Y.Z --notes-file docs/releases/vX.Y.Z.md` to fix typos, add
cross-references to companion files that landed on `main` shortly after the release,
or clarify scope — as long as the edit doesn't misrepresent what's actually in the
released ZIP. When you do this, also update the matching `docs/releases/vX.Y.Z.md` so
the file and the live release body stay in sync.

**Master branch = Next Release** - All commits target the next version with version bumped
in manifest.json and const.py.

### Version Bumping Rules

> **IMPORTANT: Do NOT bump version during a session. All changes go into the CURRENT unreleased version.**

- The version in `manifest.json` and `const.py` represents the NEXT release being prepared
- **NEVER bump version until user commands "tag and release"**
- Multiple features/fixes can be added to the same unreleased version
- Only bump to a NEW version number AFTER the current version is released

### Version Locations (Must Be Synchronized)

1. `custom_components/abb_powerone_pvi_sunspec/manifest.json` → `"version": "X.Y.Z"`
1. `custom_components/abb_powerone_pvi_sunspec/const.py` → `VERSION = "X.Y.Z"`

> const.py must declare the version as plain `VERSION = "X.Y.Z"` — no `Final`
> annotation — because the release workflow and repo-sync validate that exact form.

### Complete Release Workflow

> **IMPORTANT: Version Validation**
> The release workflow VALIDATES that tag, manifest.json, and const.py versions all match.
> You MUST update versions BEFORE creating the release, not after.

| Step | Tool           | Action                                                                  |
| ---- | -------------- | ----------------------------------------------------------------------- |
| 1    | Edit           | Update `CHANGELOG.md` with version summary                              |
| 2    | Write          | Create `docs/releases/vX.Y.Z.md` release notes (see format below)      |
| 3    | Edit           | Ensure `manifest.json` and `const.py` have correct version              |
| 4    | Bash           | Run linting: `pre-commit run --all-files`                               |
| 5    | Bash           | `git add . && git commit -m "..."`                                      |
| 6    | Bash           | `git push`                                                              |
| 7    | **STOP**       | Wait for user "tag and release" command                                 |
| 8    | **CI Check**   | Verify ALL CI workflows pass (see CI Verification below)                |
| 9    | **RRR**        | Display Release Readiness Report (see below)                            |
| 10   | Bash           | `git tag -a vX.Y.Z -m "Release vX.Y.Z"`                                |
| 11   | Bash           | `git push --tags`                                                       |
| 12   | gh CLI         | `gh release create vX.Y.Z --title "vX.Y.Z" --notes-file docs/releases/vX.Y.Z.md` |
| 13   | GitHub Actions | Validates versions match, then auto-uploads ZIP asset                   |
| 14   | Edit           | Bump versions in `manifest.json` and `const.py` to next version         |

### CI Verification (MANDATORY)

> **CRITICAL: Before tagging/releasing, ALWAYS verify ALL CI workflows are passing.**
> Use GitHub MCP tools to list workflow runs, then use `gh` CLI to get detailed logs if needed.
> NEVER proceed if any workflow is failing.

**Verification steps:**

1. Use `mcp__GitHub_MCP_Remote__actions_list` to list recent workflow runs:

   ```text
   actions_list(method="list_workflow_runs", owner="alexdelprete", repo="ha-abb-powerone-pvi-sunspec")
   ```

1. Check that ALL workflows show `conclusion: "success"`:
   - Lint workflow
   - Validate workflow
   - Tests workflow

1. If any workflow is failing, use `gh` CLI to get detailed failure logs:

   ```bash
   # View failed run logs (replace <run_id> with actual ID from step 1)
   gh run view <run_id> --log-failed

   # Or view full logs for a specific run
   gh run view <run_id> --log
   ```

1. Fix failing tests/issues, commit, push, and re-verify before proceeding

### Release Notes Format (MANDATORY)

Create a release notes file at `docs/releases/vX.Y.Z.md` using this template.
This file is then used as the body when creating the GitHub release.

```markdown
# Release vX.Y.Z

[![GitHub Downloads](https://img.shields.io/github/downloads/alexdelprete/ha-abb-powerone-pvi-sunspec/vX.Y.Z/total?style=for-the-badge)](https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/releases/tag/vX.Y.Z)

**Release Date:** YYYY-MM-DD

**Type:** [Major/Minor/Patch/Beta] release - Brief description.

## What's Changed

### Added

- Feature 1

### Changed

- Change 1

### Fixed

- Fix 1

**Full Changelog**:
[compare/vPREV...vX.Y.Z](https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/compare/vPREV...vX.Y.Z)
```

### Release Readiness Report (MANDATORY)

> **When user commands "tag and release", ALWAYS display the Release Readiness Report (RRR) BEFORE proceeding.**

Check CI workflows and display:

```markdown
## Release Readiness Report (RRR)

| Check | Status | Details |
|-------|--------|---------|
| **Lint** | status | date |
| **Tests** | status | date |
| **Validate** | status | date |
| **Test Coverage** | status | Minimum required: 97% |
| **Version** | X.Y.Z | manifest.json + const.py |
| **CHANGELOG.md** | status | Updated |
| **Release notes** | status | docs/releases/vX.Y.Z.md |
| **Working Tree** | status | No uncommitted changes |
```

**Test Coverage Requirement:**

> **CRITICAL: Test coverage MUST be at minimum 97%.**
> If coverage drops below 97%, flag it and do not proceed with release until fixed.

**How to get test coverage:**

```bash
gh run list --repo alexdelprete/ha-abb-powerone-pvi-sunspec --limit 5 | grep Tests
gh run view <run_id> --repo alexdelprete/ha-abb-powerone-pvi-sunspec --log 2>&1 | grep "TOTAL"
```

The coverage percentage is the last column in the TOTAL line.

### Issue References in Release Notes

When a release addresses a specific GitHub issue:

- Reference the issue number, but **NEVER use a GitHub closing keyword** —
  `close`/`closes`/`closed`, `fix`/`fixes`/`fixed`, `resolve`/`resolves`/`resolved`
  followed by `#N` — anywhere in commit messages, release notes, the GitHub release
  body, or PR descriptions. Those keywords auto-close the issue when the commit lands
  on the default branch. Use a neutral phrase instead: "Reported in #42",
  "Addresses #42", "Refs #42".
- Thank the user who opened the issue by name and GitHub handle.
- **NEVER close the issue** — the user will do it manually.

### After Publishing a Release

1. Immediately bump versions in `manifest.json` and `const.py` to next version
1. Create new release notes file for next version
1. Mark previous version's documentation as frozen

### Release Documentation Structure

#### Stable/Official Release Notes (e.g., v1.0.0)

- **Scope**: ALL changes since previous stable release
- **Example**: v1.1.0 includes everything since v1.0.0
- **Purpose**: Complete picture for users upgrading from last stable

#### Beta Release Notes (e.g., v1.0.0-beta.1)

- **Scope**: Only incremental changes in this beta
- **Example**: v1.0.0-beta.2 shows only what's new since beta.1
- **Purpose**: Help beta testers focus on what to test

### Documentation Files

- **`CHANGELOG.md`** (root) — quick overview of all releases, Keep a Changelog format
- **`docs/releases/`** — detailed release notes (one file per version)
- **`docs/releases/README.md`** — release directory guide and templates

## Do's and Don'ts

**DO:**

- Run `pre-commit run --all-files` before EVERY commit (NOT `uvx pre-commit` — see Pre-Commit Checks section for why)
- Read CLAUDE.md at session start
- Use `runtime_data` for data storage (not `hass.data[DOMAIN]`)
- Use `@callback` decorator for message handlers
- Log with `%s` formatting (not f-strings)
- Handle missing data gracefully
- Update both manifest.json AND const.py for version bumps
- Get approval before creating tags/releases
- Use custom exceptions for error handling
- Verify PyPI availability before updating dependencies

**NEVER:**

- Commit without running pre-commit checks first
- Modify production code to make tests pass - fix the tests instead
- Use `hass.data[DOMAIN][entry_id]` - use `runtime_data` instead
- Shadow Python builtins (A001)
- Use f-strings in logging (G004)
- Create git tags or GitHub releases without explicit user instruction
- Forget to update VERSION in both manifest.json AND const.py
- Use blocking calls in async context
- Close GitHub issues without explicit user instruction
- Log manually what HA logs automatically (coordinator errors, ConfigEntryNotReady)
- Create documentation files without user request

<!--
==============================================================================
⚠️  END OF TEMPLATE-MANAGED ZONE.

The END SHARED marker line appears below this comment. Anything you add
BELOW the END SHARED marker is integration-specific and safe to edit —
it will not be touched by `repo-sync.py`.
==============================================================================
-->

<!-- END SHARED:repo-sync -->
