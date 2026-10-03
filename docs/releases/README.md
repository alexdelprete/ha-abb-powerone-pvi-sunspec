# Release Workflow

This document describes the release workflow for the ABB/Power-One/FIMER PVI SunSpec integration.

## Version Locations

Versions must be synchronized in:

1. `custom_components/abb_powerone_pvi_sunspec/manifest.json` -> `"version": "X.Y.Z"`
2. `custom_components/abb_powerone_pvi_sunspec/const.py` -> `VERSION = "X.Y.Z"`
3. Git tag -> `vX.Y.Z`

## Release Process

1. Update `CHANGELOG.md` with version summary
2. Ensure versions are correct in `manifest.json` and `const.py`
3. Run linting: `pre-commit run --all-files`
4. Commit and push
5. Verify CI passes (lint, test, validate)
6. Create git tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
7. Push tag: `git push --tags`
8. Create GitHub release with release notes
9. GitHub Actions validates versions and uploads ZIP asset

## Release Types

- **Major** (X.0.0): Breaking changes
- **Minor** (x.Y.0): New features, backward compatible
- **Patch** (x.y.Z): Bug fixes, backward compatible

## Important Rules

- **NEVER** create git tags or GitHub releases without explicit maintainer approval
- **Published releases are FROZEN** -- never modify documentation for released versions
- All commits on the main branch target the next release version
