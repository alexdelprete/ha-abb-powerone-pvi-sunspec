# Claude Alignment Notes - Repository Split Decision

## ⚠️ IMPORTANT: Architecture Decision Change

**This repository (ha-abb-powerone-pvi-sunspec v4.x) will NOT implement the universal client architecture.**

Instead, the project is splitting into **two new focused integrations:**

### 1. ha-abb-fimer-pvi-sunspec (Modbus/TCP Only)

**Repository:** <https://github.com/alexdelprete/ha-abb-fimer-pvi-sunspec>

**Status:** v1.0.0-beta.x

**Focus:**

- Direct Modbus/TCP communication with ABB/FIMER inverters
- Dynamic SunSpec model discovery
- No REST/VSN support

**Architecture:**

- async-sunspec-client (embedded library)
  - ModbusLink-based async SunSpec engine
  - Vendored SunSpec JSON models (Apache-2.0)
  - Discovery: scan M1, follow chain until 0xFFFF
  - Parser: scale factors, repeating groups, invalid sentinels
  - Component tree: inverter, meter, storage, MPPT with stable IDs
- HA Integration
  - config_flow: host, port, device_id, base_addr
  - coordinator: async polling via ModbusLink
  - sensor: dynamic creation from discovered models

**Dependencies:**

- ModbusLink (async Modbus client)
- Vendor: SunSpec JSON models (M1, M101/103, M120, M160, M124, M802-804, M201-204, M64061)

### 2. ha-abb-fimer-pvi-vsn-rest (REST API Only)

**Repository:** <https://github.com/alexdelprete/ha-abb-fimer-pvi-vsn-rest>

**Status:** v1.0.0-beta.x

**Focus:**

- VSN300/VSN700 datalogger support via REST API
- Automatic VSN model detection
- Data normalization to SunSpec schema
- No Modbus support

**Architecture:**

- abb-fimer-vsn-rest-client (embedded library)
  - aiohttp-based async REST client
  - Auto-detection: probe /v1/status WWW-Authenticate header
  - VSN300: X-Digest authentication (non-standard digest)
  - VSN700: Preemptive Basic authentication
  - Endpoints: /v1/status, /v1/livedata, /v1/feeds
  - Normalizer: VSN700 vendor names → SunSpec, VSN300 extract from m{model}_{instance}_{register}
  - Multi-device: inverter + batteries + meter topology
- HA Integration
  - config_flow: host, username, password, optional vsn_model cache
  - coordinator: async polling via REST client
  - sensor: dynamic creation from normalized SunSpec data

**Dependencies:**

- aiohttp (async HTTP client)
- Vendor: SunSpec JSON models (for normalization mapping reference)

## Rationale for Split

**Original Plan Issues:**

- Universal client added complexity without clear user benefit
- Most users have EITHER Modbus OR REST access, not both
- Protocol switching is rare in practice
- Combined codebase harder to maintain and test

**Benefits of Split:**

- **Focused codebases**: Each integration optimized for its protocol
- **Simpler maintenance**: Protocol-specific bug fixes don't affect the other
- **Better testing**: Isolated test suites for each protocol
- **Clearer documentation**: Protocol-specific guides without cross-contamination
- **Easier onboarding**: Contributors can focus on one protocol
- **Independent releases**: Beta testing and versioning per protocol

## Current Repository Status (v4.x)

**This repository will:**

- ✅ Remain available at v4.1.6 for existing users
- ✅ Receive critical bug fixes only
- ❌ No new features
- ❌ No universal client implementation
- ❌ No migration to ModbusLink

**Users should:**

- Continue using v4.1.6 for production (stable)
- Monitor announcements for new integrations
- Migrate to appropriate new integration when ready:
  - **Direct Modbus users** → ha-abb-fimer-pvi-sunspec
  - **VSN datalogger users** → ha-abb-fimer-pvi-vsn-rest

## Migration Path (Future)

**When migrating from v4.x to new integrations:**

**For Modbus users (v4.x → ha-abb-fimer-pvi-sunspec):**

1. Install new integration via HACS
2. Configure with same host/port/device_id
3. New entity unique_ids will differ (SunSpec-based)
4. Manually update dashboards/automations
5. Remove old integration when satisfied

**For VSN users (hypothetical v4.x VSN → ha-abb-fimer-pvi-vsn-rest):**

1. Install new integration via HACS
2. Configure with VSN host/credentials
3. Auto-detection handles VSN300 vs VSN700
4. New entity unique_ids based on normalized SunSpec schema
5. Manually update dashboards/automations
6. Remove old integration when satisfied

**No automated migration:** Clean separation ensures no entity ID conflicts.

## Development References

**For new integrations development:**

- See respective repository CLAUDE.md files
- Both use same coding standards (.ruff.toml, logging helpers)
- Both vendor SunSpec JSON models (identical copy)
- Both follow HA integration best practices

**Key shared patterns:**

- Logging: helpers.py (log_debug, log_info, log_warning, log_error)
- Coordinator: DataUpdateCoordinator with retry logic
- Config flow: ConfigFlow/OptionsFlow structure
- Error handling: Custom exceptions, structured error messages
- Type hints: Modern syntax, runtime_data pattern

**Documents moved to new repos:**

- docs/architecture-plan.md → split into protocol-specific plans
- docs/pysunspec2-analysis.md → moved to ha-abb-fimer-pvi-sunspec
- Analysis artifacts (mapping Excel, scripts) → moved to ha-abb-fimer-pvi-vsn-rest

---

## Legacy Notes (v4.x - ARCHIVED)

The original plan for a universal client architecture (as documented below) was abandoned in favor of the two-integration split approach.

**Original planned architecture (NOT IMPLEMENTED):**

- abb-fimer-universal-client facade
- async-sunspec2 + abb-fimer-rest-client backends
- Protocol switching in config flow
- Unified entity schema

**Why abandoned:**

- Added complexity without proportional user value
- Rare use case for protocol switching
- Harder to maintain and test
- Better served by two focused integrations
