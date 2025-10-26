# Migration Archive

This directory contains scripts and documentation used during the migration from the unified integration (v4.x) to two separate integrations.

## Date

2025-10-26

## New Integrations Created

1. **[ha-abb-fimer-pvi-sunspec](https://github.com/alexdelprete/ha-abb-fimer-pvi-sunspec)** - Modbus/TCP only (v1.0.0-beta.x)
   - Direct Modbus/TCP communication with inverters
   - Dynamic SunSpec model discovery
   - Based on ModbusLink library with async-sunspec-client

2. **[ha-abb-fimer-pvi-vsn-rest](https://github.com/alexdelprete/ha-abb-fimer-pvi-vsn-rest)** - REST API only (v1.0.0-beta.x)
   - VSN300/VSN700 datalogger support via REST API
   - Automatic VSN model detection
   - Data normalization to SunSpec schema

## Archive Contents

### Generation Scripts (`scripts/`)

These Python scripts and shell scripts were used to generate the complete boilerplate for both new integrations:

- `generate_new_integrations.py` - Initial boilerplate generation for both integrations
- `complete_integration_setup.py` - Added documentation and structure
- `complete_rest_integration.py` - Completed REST integration files
- `complete_modbus_integration.py` - Completed Modbus integration files
- `copy_config_folders.py` - Copied configuration folders (.claude, .github, .vscode, etc.)
- `init_repos.sh` - Initial repository initialization script (superseded)
- `init_repos_corrected.sh` - Corrected script that created GitHub repos first

### Status Documentation

- `INTEGRATION_SPLIT_SUMMARY.md` - Summary of the split decision and implementation plan
- `COMPLETION_STATUS.md` - Status tracking during integration generation
- `CONFIG_FOLDERS_COMPLETE.md` - Configuration folder copy completion status
- `FINAL_STATUS.md` - Final completion checklist

## Migration Rationale

The original plan for a universal client combining both Modbus and REST protocols added complexity without clear user benefit. Most users have either:
- Direct Modbus access to inverters, OR
- VSN dataloggers with REST API

Maintaining two focused integrations provides:
- Better code clarity
- Easier maintenance
- Protocol-specific optimization
- Simpler user experience

## Files Generated

Each integration received ~40 files including:
- Complete Python implementation structure with stubs
- Home Assistant integration components
- Configuration folders (.claude, .devcontainer, .github, .vscode)
- Documentation (README, CHANGELOG, CLAUDE.md)
- GitHub workflows (lint, validate, release)
- Test structures
- SunSpec model JSON files
- Helper scripts (REST integration only)

## Timeline

- **2025-10-26**: Decision to split integrations
- **2025-10-26**: Generated complete boilerplate for both integrations
- **2025-10-26**: Copied configuration folders with adaptations
- **2025-10-26**: Downloaded SunSpec models to both integrations
- **2025-10-26**: Created GitHub repositories and pushed v1.0.0-beta.1

## Current Repository Status

This repository (ha-abb-powerone-pvi-sunspec v4.x) remains available for existing users:
- v4.1.6 is the final feature release
- Critical bug fixes only
- Users should migrate to appropriate new integration when ready

---

*These files are preserved for historical reference and to document the migration process.*
