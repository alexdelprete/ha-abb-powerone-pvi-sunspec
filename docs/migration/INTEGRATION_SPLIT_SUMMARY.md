# Integration Split Summary

**Date:** 2025-10-26
**Decision:** Split universal client architecture into two focused integrations

## Overview

The original plan for a universal client combining both Modbus and REST protocols has been **replaced** with two separate, focused integrations:

1. **ha-abb-fimer-pvi-sunspec** - Modbus/TCP only
2. **ha-abb-fimer-pvi-vsn-rest** - REST API only

## Rationale

**Problems with Universal Client Approach:**

- Added complexity without clear user benefit
- Most users have EITHER Modbus OR REST access, not both
- Protocol switching is rare in practice
- Combined codebase harder to maintain and test
- Single point of failure for both protocols

**Benefits of Split:**

- Focused codebases optimized for each protocol
- Simpler maintenance (protocol-specific bugs isolated)
- Independent testing and release cycles
- Clearer documentation per protocol
- Easier contributor onboarding
- Better user experience (install only what you need)

## Current Repository Status

**ha-abb-powerone-pvi-sunspec (v4.x):**

- ✅ Updated documentation with deprecation notices
- ✅ CLAUDE.md: Points to new integrations
- ✅ docs/claude.md: Comprehensive split rationale
- ✅ README.md: Prominent beta integration notices
- Status: Frozen at v4.1.6, critical bug fixes only

## New Integrations Status

### 1. ha-abb-fimer-pvi-sunspec (Modbus/TCP)

**Location:** `d:\OSILifeDrive\Dev\HASS\ha-abb-fimer-pvi-sunspec`

**Status:** Boilerplate complete, implementation needed

**Generated Files:**
```
ha-abb-fimer-pvi-sunspec/
├── LICENSE (MIT, 2025)
├── README.md (with beta warning)
├── CHANGELOG.md (v1.0.0-beta.1 entry)
├── CLAUDE.md (development guidelines)
├── hacs.json
├── .ruff.toml (copied from v4.x)
├── custom_components/
│   └── abb_fimer_pvi_sunspec/
│       ├── manifest.json (domain: abb_fimer_pvi_sunspec, v1.0.0-beta.1)
│       ├── const.py (constants, defaults)
│       ├── __init__.py (stub with TODO)
│       ├── config_flow.py (stub with TODO)
│       ├── helpers.py (logging functions)
│       └── async_sunspec_client/
│           ├── __init__.py
│           ├── exceptions.py (complete)
│           ├── discovery.py (stub with TODO)
│           ├── models.py (stub with TODO)
│           └── parser.py (stub with TODO)
├── docs/
│   ├── architecture-plan.md (complete technical plan)
│   ├── pysunspec2-analysis.md (copied from v4.x)
│   └── releases/ (empty, ready for v1.0.0-beta.1.md)
├── vendor/sunspec_models/json/ (empty, needs model files)
├── .github/workflows/ (empty, needs CI/CD)
└── tests/ (empty, needs test files)
```

**Key Features:**

- Dynamic SunSpec model discovery
- ModbusLink-based async client
- Support for M1, M101, M103, M120, M160, M124, M802-804, M201-204, M64061
- Repeating groups (MPPT channels)
- Scale factors and invalid sentinels
- Multi-device topology

**TODO:**

- [ ] Implement async_sunspec_client library (discovery, models, parser)
- [ ] Implement coordinator.py
- [ ] Implement sensor.py
- [ ] Complete config_flow.py and __init__.py
- [ ] Copy SunSpec JSON models to vendor/sunspec_models/json/
- [ ] Create NOTICE and NAMESPACE files for vendor models
- [ ] Add GitHub workflows (lint, validate, release)
- [ ] Write unit and integration tests
- [ ] Create docs/releases/v1.0.0-beta.1.md

### 2. ha-abb-fimer-pvi-vsn-rest (REST API)

**Location:** `d:\OSILifeDrive\Dev\HASS\ha-abb-fimer-pvi-vsn-rest`

**Status:** Partial boilerplate, needs completion

**Generated Files:**
```
ha-abb-fimer-pvi-vsn-rest/
├── LICENSE (MIT, 2025)
├── hacs.json
├── .ruff.toml (copied from v4.x)
├── custom_components/
│   └── abb_fimer_pvi_vsn_rest/
│       ├── manifest.json (domain: abb_fimer_pvi_vsn_rest, v1.0.0-beta.1)
│       ├── const.py (constants, defaults, endpoints)
│       ├── __init__.py (stub with TODO)
│       └── abb_fimer_vsn_rest_client/
│           ├── __init__.py
│           └── exceptions.py (complete)
├── docs/
│   └── vsn-sunspec-point-mapping.xlsx (copied from v4.x)
├── scripts/
│   ├── analyze_abb_points.py (copied from v4.x)
│   └── generate_mapping_excel.py (copied from v4.x)
├── reference/ (empty, ready for vsnx00-monitor)
├── vendor/sunspec_models/json/ (empty, needs model files)
├── .github/workflows/ (empty, needs CI/CD)
└── tests/ (empty, needs test files)
```

**Key Features:**

- Automatic VSN300/VSN700 detection
- VSN300 X-Digest authentication
- VSN700 Preemptive Basic authentication
- Data normalization (VSN700 vendor names → SunSpec)
- Multi-device support (inverter + batteries + meter)
- 162+ data points (54 standard, 61 M64061, 47 ABB proprietary)

**TODO:**

- [ ] Create README.md
- [ ] Create CHANGELOG.md
- [ ] Create CLAUDE.md (development guidelines)
- [ ] Implement abb_fimer_vsn_rest_client library:
  - [ ] client.py (main REST client)
  - [ ] auth.py (VSN300 X-Digest, VSN700 Basic, auto-detection)
  - [ ] normalizer.py (data normalization)
  - [ ] models.py (VSNDevice dataclass)
- [ ] Implement config_flow.py
- [ ] Implement coordinator.py
- [ ] Implement sensor.py
- [ ] Implement helpers.py
- [ ] Complete __init__.py
- [ ] Copy vsnx00-monitor prototype to reference/
- [ ] Copy SunSpec JSON models to vendor/sunspec_models/json/
- [ ] Create documentation:
  - [ ] docs/architecture-plan.md
  - [ ] docs/vsn-authentication.md
  - [ ] docs/vsn-rest-api.md
  - [ ] docs/vsn-data-normalization.md
  - [ ] docs/vsnx00-monitor-analysis.md
  - [ ] docs/releases/v1.0.0-beta.1.md
- [ ] Add GitHub workflows (lint, validate, release)
- [ ] Write unit and integration tests

## Generated Scripts

### 1. generate_new_integrations.py

**Location:** `d:\OSILifeDrive\Dev\HASS\ha-abb-powerone-pvi-sunspec\generate_new_integrations.py`

**Purpose:** Generate initial boilerplate for Modbus integration

**What it does:**

- Creates directory structure
- Generates LICENSE, README, CHANGELOG
- Creates manifest.json with proper domain and version
- Creates const.py with constants
- Creates stub files for __init__.py, config_flow.py
- Creates helpers.py with logging functions
- Creates async_sunspec_client library structure
- Copies .ruff.toml and creates hacs.json

### 2. complete_integration_setup.py

**Location:** `d:\OSILifeDrive\Dev\HASS\ha-abb-powerone-pvi-sunspec\complete_integration_setup.py`

**Purpose:** Add documentation and REST integration files

**What it does:**

- Adds CLAUDE.md to Modbus integration
- Adds docs/architecture-plan.md to Modbus integration
- Copies docs/pysunspec2-analysis.md to Modbus integration
- Creates REST integration basic structure
- Copies mapping Excel and scripts to REST integration
- Creates init_repos.sh for git initialization

### 3. init_repos.sh

**Location:** `d:\OSILifeDrive\Dev\HASS\ha-abb-powerone-pvi-sunspec\init_repos.sh`

**Purpose:** Initialize git repositories for both integrations

**What it does:**

- Initializes git in both integration directories
- Creates initial commits with Claude attribution
- Tags v1.0.0-beta.1
- Provides commands for creating GitHub repos
- Provides commands for creating pre-releases

## Next Steps

### Immediate Tasks

1. **Complete REST Integration Boilerplate**
   - Run additional generation script for remaining files
   - Create all missing documentation files

2. **Vendor SunSpec Models**
   - Download JSON models from https://github.com/sunspec/models
   - Copy to both integrations' vendor/sunspec_models/json/
   - Create NOTICE file (Apache-2.0 license)
   - Create NAMESPACE file (upstream URL, ref, timestamp)

3. **GitHub Workflows**
   - Create .github/workflows/lint.yml (ruff check)
   - Create .github/workflows/validate.yml (HACS validation)
   - Create .github/workflows/release.yml (automated releases)

### Implementation Phase

**Modbus Integration:**

1. Implement async_sunspec_client.discovery (model scanning)
2. Implement async_sunspec_client.models (JSON loading)
3. Implement async_sunspec_client.parser (data parsing, scale factors)
4. Implement coordinator.py (DataUpdateCoordinator)
5. Implement sensor.py (dynamic entity creation)
6. Complete config_flow.py (connection validation, discovery)
7. Complete __init__.py (setup/unload)
8. Write tests

**REST Integration:**

1. Implement abb_fimer_vsn_rest_client.auth (VSN300/700 auth, detection)
2. Implement abb_fimer_vsn_rest_client.client (REST endpoints)
3. Implement abb_fimer_vsn_rest_client.normalizer (data normalization)
4. Implement coordinator.py (DataUpdateCoordinator)
5. Implement sensor.py (dynamic entity creation)
6. Complete config_flow.py (auth validation, detection)
7. Complete __init__.py (setup/unload)
8. Write tests

### Testing Phase

1. Local testing with real hardware
2. Beta release announcements
3. Community testing and feedback
4. Bug fixes and iterations
5. Documentation improvements

### Release Phase

1. v1.0.0-beta.2, beta.3, etc. as needed
2. Collect feedback and fix issues
3. v1.0.0 stable release when ready
4. Update current repo README with links to stable releases

## Migration Guide (for users)

### From v4.x to Modbus Integration

1. Install ha-abb-fimer-pvi-sunspec via HACS
2. Configure with same host/port/device_id as v4.x
3. New entity unique_ids will differ (SunSpec-based)
4. Manually update dashboards/automations
5. Remove old integration when satisfied

### From v4.x to REST Integration

1. Install ha-abb-fimer-pvi-vsn-rest via HACS
2. Configure with VSN host/credentials
3. Auto-detection handles VSN300 vs VSN700
4. New entity unique_ids based on normalized SunSpec schema
5. Manually update dashboards/automations
6. Remove old integration when satisfied

**Note:** No automated migration - clean separation prevents entity ID conflicts.

## File Locations Summary

### Current Repository (v4.x)
- `d:\OSILifeDrive\Dev\HASS\ha-abb-powerone-pvi-sunspec`
- Updated: CLAUDE.md, docs/claude.md, README.md
- Added: generate_new_integrations.py, complete_integration_setup.py, init_repos.sh

### New Modbus Integration
- `d:\OSILifeDrive\Dev\HASS\ha-abb-fimer-pvi-sunspec`
- Boilerplate complete, implementation needed

### New REST Integration
- `d:\OSILifeDrive\Dev\HASS\ha-abb-fimer-pvi-vsn-rest`
- Partial boilerplate, needs completion

## Success Criteria

**Modbus Integration v1.0.0 Stable:**

- [ ] Tested with M101 (single-phase) inverters
- [ ] Tested with M103 (three-phase) inverters
- [ ] Tested with various MPPT configurations (1-4 channels)
- [ ] Tested with battery systems (M802, M124)
- [ ] Tested with meters (M201, M203, M204)
- [ ] Tested with M64061 vendor model
- [ ] Different base addresses validated (0 vs 40000)
- [ ] 24+ hour stability confirmed
- [ ] Error recovery working
- [ ] No critical bugs

**REST Integration v1.0.0 Stable:**

- [ ] Tested with VSN300 dataloggers
- [ ] Tested with VSN700 dataloggers
- [ ] Auto-detection reliable
- [ ] All 162+ data points validated
- [ ] Multi-device configurations tested
- [ ] 24+ hour stability confirmed
- [ ] Error recovery working
- [ ] No critical bugs

## Contact and Support

**GitHub Repositories (once created):**

- Modbus: https://github.com/alexdelprete/ha-abb-fimer-pvi-sunspec
- REST: https://github.com/alexdelprete/ha-abb-fimer-pvi-vsn-rest

**Issue Tracking:**

- Report issues to respective GitHub repo issue trackers
- Include configuration details, logs, hardware info

**Community:**

- Home Assistant Community Forum discussions
- HACS integration pages

---

**Last Updated:** 2025-10-26
**Status:** Boilerplate generation complete, implementation in progress
