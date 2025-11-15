# Release Notes Directory

This directory contains detailed release notes for each version of the ABB/Power-One/FIMER PVI SunSpec integration.

## Structure

Each release has its own markdown file named with the version number:

- `v4.1.5-beta.1.md` - Beta 1 of version 4.1.5
- `v4.1.5.md` - Stable version 4.1.5
- `v4.2.0.md` - Future version 4.2.0
- etc.

## Viewing Release Notes

### For Users
- **Latest release notes:** Check the [CHANGELOG.md](../../CHANGELOG.md) in the root directory
- **Specific version details:** Browse files in this directory
- **GitHub releases:** Visit the [repository releases page](https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/releases)

### For Developers
When creating a new release:

1. Create a new file: `vX.Y.Z.md` or `vX.Y.Z-beta.N.md`
2. Use existing release notes as a template
3. Update [CHANGELOG.md](../../CHANGELOG.md) with a summary
4. Update version in [manifest.json](../../custom_components/abb_powerone_pvi_sunspec/manifest.json)
5. Update version in [const.py](../../custom_components/abb_powerone_pvi_sunspec/const.py)
6. Create a git tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
7. Push changes and tag: `git push && git push --tags`
8. Create GitHub release: `gh release create vX.Y.Z --prerelease` (for beta) or `--latest` (for stable)

## Release Note Template

Each release note file should include:

- Version number in title (with beta/stable indicator)
- Release date
- What's Changed summary
- Critical Bug Fixes (if any)
- New Features (if any)
- Code Quality Improvements
- Breaking Changes (if any)
- Dependencies
- Upgrade Notes
- Testing Recommendations
- Known Issues (if any)
- Acknowledgments (if applicable)
- Links to changelog, full diff, and documentation

## Navigation
- [← Back to CHANGELOG](../../CHANGELOG.md)
- [← Back to Repository Root](../../README.md)
