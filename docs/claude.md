# Claude Alignment Notes (Architecture + Branch Strategy)

This repository is transitioning to a universal client architecture. These notes summarize the decisions for cto.new alignment. For full guidelines see the root CLAUDE.md and docs/architecture-plan.md.

Branch
- feature/abb-fimer-client-library (all work for this program of changes happens here)

Libraries
- async-sunspec2
  - ModbusLink-based async SunSpec engine
  - Uses vendored SunSpec JSON models (discovery, parsing, scale factors, repeats, invalid sentinels)
  - Builds a component tree (inverter, meter, storage, MPPT) with stable IDs; async-only API
- abb-fimer-rest-client
  - aiohttp client for VSN loggers
  - VSN300 custom auth header, VSN700 bearer auth
  - Livedata + feeds merge, prefix stripping
  - Device identification via device_type or feeds.description URL and MAC address; multi-device support
- abb-fimer-universal-client
  - Unified facade selecting REST or Modbus at runtime
  - Normalized schema: devices + measurements, capability map
  - Handles protocol switching and exposes unified exceptions

Home Assistant integration changes
- Coordinator consumes the universal client hub and produces sensors from the normalized schema
- Device registry
  - REST mode: hub + child devices behind logger
  - Modbus mode: child devices for subcomponents when SunSpec models indicate them; synthesize stable IDs where no separate Common model exists
- Config/Options
  - Protocol selection, VSN model/auth (REST), Modbus params
  - Migration for existing installs; warn on capability deltas when switching protocol
- Entity lifecycle on protocol switch
  - Disable/mark unavailable/remove per HA guidance

Dependencies/migration
- Remove pymodbus; add ModbusLink
- Vendor SunSpec JSON model files (Apache-2.0 attribution + NAMESPACE + NOTICE)
- Do not use pysunspec2 runtime; reuse JSON models only (see docs/pysunspec2-analysis.md)

Testing & QA plan
- Unit: SunSpec parser, REST auth/merging, device-id logic
- Protocol switching tests, integration tests for VSN300/VSN700 and single/three-phase devices
- Performance targets: <500 ms small setups; <1.5 s large

Release plan
- Staged rollout with backward compatibility; details in docs/architecture-plan.md

References
- docs/architecture-plan.md (finalized plan and milestones)
- docs/pysunspec2-analysis.md (decision record: reuse JSON models only)
- CLAUDE.md (full dev workflow and coding standards)
