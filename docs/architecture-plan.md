# Architecture Plan: Async SunSpec2 + Universal Client

Date: 2025-10-19
Status: Finalized master plan for implementation
Branch: feature/abb-fimer-client-library

Overview

- Goal: Modernize the ABB/Power-One/FIMER integration by introducing a universal data hub that can speak either REST (VSN300/VSN700) or Modbus/TCP (SunSpec), while moving our SunSpec engine to an async, model-driven implementation based on vendored SunSpec JSON models.
- Outcomes:
  - Better reliability and performance with true async I/O across all paths
  - Cleaner device/measurement schema independent of protocol
  - Seamless protocol switching with graceful entity lifecycle handling
  - Removal of pymodbus dependency; adoption of ModbusLink

Key References

- pysunspec2 analysis and decision record: docs/pysunspec2-analysis.md
  - Summary: do not use pysunspec2 runtime; reuse JSON model files only

Architecture

1) Libraries (developed under feature/abb-fimer-client-library)
   - async-sunspec2
     - Purpose: Async SunSpec engine built on ModbusLink, using vendored SunSpec JSON model definitions
     - Core capabilities
       - Discovery of base address and available models (Common, 101/103, 120/121+, 160 MPPT, etc.)
       - Parsing of SunSpec groups/repeats, scale factors, units, and special invalid sentinel values
       - Build a typed device tree (inverter, optional meter, storage, MPPTs) with stable component IDs
       - Async-only API; no blocking/threads
       - Error taxonomy mapped to unified exceptions
     - Data model
       - Raw register reads → model point decoding → scaled measurements
       - Component graph with deterministic, stable identifiers even when Common model is not present for a subcomponent
     - Implementation notes
       - Use ModbusLink for transport (TCP first; leave RTU hooks for future)
       - Vendored SunSpec JSON models from upstream (see Sync Procedure below)
       - Caching of Common/Nameplate info; bounded cache for repeating groups

   - abb-fimer-rest-client
     - Purpose: Async aiohttp client for VSN dataloggers
     - Protocols
       - VSN300: custom HTTP header auth
       - VSN700: bearer token auth (OAuth-like or predefined token)
     - Data handling
       - Merge livedata with feeds where needed
       - Strip path prefixes from feed names where appropriate
       - Device identification via device_type or feeds.description URL and MAC address
       - Support multiple child devices behind one logger
     - Implementation notes
       - Unified error taxonomy; all I/O is async
       - Timeouts, retries, and rate limiting

   - abb-fimer-universal-client
     - Purpose: Facade that selects REST or Modbus at runtime, exposing a normalized schema and capability map
     - Features
       - Normalized schema with two top-level concepts:
         - devices: list of discovered devices (hub + children), each with stable ID, model, serial, relationships
         - measurements: flattened and/or structured measurement sets per device with metadata
       - Capability map to advertise what each protocol/device can provide (e.g., MPPT counts, per-phase telemetry)
       - Protocol switching logic and error translation into unified exceptions
       - Consistent timestamping, units and scaling

2) Home Assistant integration changes
   - Coordinator and entities
     - DataUpdateCoordinator consumes abb-fimer-universal-client hub object, not protocol-specific APIs
     - Sensor entities created from the normalized device/measurement schema
   - Device registry
     - Always create a hub device (logger or inverter)
     - In REST mode: child devices for sub-devices behind the logger
     - In Modbus mode: child devices when SunSpec models indicate subcomponents (MPPT, meter, storage)
       - Synthesize stable IDs if a subcomponent lacks a separate SunSpec Common model
   - Config/Options flow
     - Add protocol selection (REST vs Modbus)
     - For REST: choose VSN model (300 vs 700) and auth method/credentials
     - For Modbus: host/port/unit-id/base-addr
     - Migration path for existing installs (default to Modbus with preserved params)
     - Show warnings on capability deltas when switching protocol (entities may be added/removed/disabled)
   - Entity lifecycle on protocol switch
     - Follow HA guidance:
       - Disable entities that are no longer supported but could return later
       - Mark unavailable when temporarily missing
       - Remove entities only when definitively non-applicable for the new protocol/device

3) Dependencies and migration
   - Remove pymodbus
   - Add ModbusLink (async Modbus library)
   - Vendor SunSpec JSON model definitions
     - License: Apache-2.0; include attribution, NOTICE, and NAMESPACE (origin metadata)
     - Stored under a vendor directory within the repository

4) Testing and QA plan
   - Unit tests
     - SunSpec JSON model parser (points, scale factors, repeats, invalid sentinels)
     - REST client auth and livedata+feeds merge
     - Stable device ID derivation (with and without Common model)
     - Capability map correctness
   - Protocol switching tests
     - Migration of existing entries to universal client
     - Entity lifecycle behavior across mode changes
   - Integration tests
     - Single-phase vs three-phase devices
     - MPPT count variations
     - VSN300 and VSN700 datalogger scenarios
   - Performance targets
     - Coordinator cycle < 500 ms for small setups; < 1.5 s for large (many MPPTs)
     - Memory growth bounded; no unbounded caches

5) Release plan
   - Staged rollout
     - Phase 1: Ship libraries as internal dependency, keep Modbus as default path
     - Phase 2: Expose REST mode as experimental via options
     - Phase 3: Promote universal client as default for new installs
   - Backward compatibility notes
     - Existing Modbus configurations migrate automatically
     - Entities keep stable unique_ids based on serial/component IDs
     - Capability deltas are communicated via Config Options UI and release notes

Milestones & Timeline

- M1: Scaffolding and vendor models (Week 1–2)
  - Create library skeletons (async-sunspec2, abb-fimer-rest-client, abb-fimer-universal-client)
  - Add vendor/sunspec_models with NOTICE and NAMESPACE via the sync procedure
  - Implement JSON manifest and basic parser unit tests
- M2: Async SunSpec core (Week 3–4)
  - ModbusLink-based discovery (base address + models)
  - Implement M1, M101/103, M120, M160 parsing with scale factors and repeats
  - Build component graph + stable IDs; add capability map
- M3: REST client (Week 5)
  - Implement VSN300 header auth and VSN700 bearer auth
  - Livedata+feeds merge, prefix stripping, multi-device identification
  - Error taxonomy; timeouts/retries
- M4: Universal client hub (Week 6)
  - Protocol selection and error translation
  - Normalized devices + measurements schema
  - End-to-end tests on both transports
- M5: HA integration bridge (Week 7)
  - Coordinator consumes hub; entity creation from normalized schema
  - Options UI for protocol selection (default Modbus)
  - Migration for existing entries
- M6: Entity lifecycle + protocol switching (Week 8)
  - Implement disable/unavailable/remove semantics per HA guidance
  - Add tests for switching paths and capability deltas
- M7: Performance & QA (Week 9)
  - Optimize polling; verify memory bounds
  - Full matrix tests (single vs three-phase, MPPT counts, VSN300/VSN700)
- M8: Documentation & Release (Week 10)
  - Update docs and CHANGELOG; staged rollout toggle
  - Prepare release notes and comparisons

SunSpec Model JSON sync procedure

- Source: <https://github.com/sunspec/pysunspec2> (sunspec2/models/json)
- Decision: reuse JSON model files only; do not use pysunspec2 runtime (see docs/pysunspec2-analysis.md)
- Script outline (scripts/sync_sunspec_models.py)
  - Inputs: upstream repo URL, ref (tag/commit), destination vendor path
  - Steps
    - Clone or download archive for the given ref
    - Copy sunspec2/models/json/*.json to vendor/sunspec_models/
    - Write/refresh vendor/sunspec_models/NOTICE (Apache-2.0 NOTICE)
    - Write vendor/sunspec_models/NAMESPACE with:
      - upstream URL
      - ref/commit
      - date, maintainer, and generation command
    - Validate JSON files and produce a manifest (ids, names, checksums)
- Example invocation
  - python3 scripts/sync_sunspec_models.py --ref v1.3.3 --dest vendor/sunspec_models
- Checklist for PR
  - Verified new/changed model files
  - Updated NAMESPACE and NOTICE
  - Manifest updated and committed
  - Unit tests for parser still pass; add tests for any new models used
  - Release notes mention the sync

Contributor guidance

- Work on branch feature/abb-fimer-client-library for all related changes
- Follow coding standards in CLAUDE.md (async-first, logging helpers, unified exceptions, no f-strings in logs)
- Prefer typed dataclasses for schema shapes
- Keep protocol-specific code contained within library boundaries; the HA integration consumes only the universal client
- When adding measurements, extend the normalized schema and update capability maps; do not wire entities directly to protocol-specific structures

Maintenance notes

- Periodically run the SunSpec model sync procedure
- Track ModbusLink and aiohttp minor releases for compatibility with HA core Python version
- Keep REST auth flows for VSN model families in sync with vendor firmware notes
