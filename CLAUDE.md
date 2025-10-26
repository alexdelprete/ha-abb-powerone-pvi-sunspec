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
The original plan for a universal client combining both protocols added complexity without clear user benefit. Most users have either:
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

- This repository provides a Home Assistant custom integration for ABB/Power-One/FIMER PVI inverters. The v4.x integration uses Modbus/TCP via pymodbus library.

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
- Upstream: https://github.com/sunspec/pysunspec2 (sunspec2/models/json)
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
