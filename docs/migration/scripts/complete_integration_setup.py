#!/usr/bin/env python3
"""Complete setup for both integrations - adds remaining files and documentation."""

import shutil
from pathlib import Path
from datetime import datetime

# Base paths
CURRENT_DIR = Path(__file__).parent
PARENT_DIR = CURRENT_DIR.parent
MODBUS_DIR = PARENT_DIR / "ha-abb-fimer-pvi-sunspec"
REST_DIR = PARENT_DIR / "ha-abb-fimer-pvi-vsn-rest"

VERSION = "1.0.0-beta.1"
YEAR = datetime.now().year


def create_file(path: Path, content: str):
    """Create a file with the given content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"Created: {path}")


def copy_file(src: Path, dst: Path):
    """Copy a file."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"Copied: {src} -> {dst}")


def add_modbus_documentation():
    """Add documentation files for Modbus integration."""
    print("\n=== Adding Modbus Integration Documentation ===\n")

    base = MODBUS_DIR
    docs = base / "docs"

    # CLAUDE.md
    create_file(base / "CLAUDE.md", f"""# Claude Code Development Guidelines - ABB/FIMER PVI SunSpec (Modbus)

## Project Overview

This repository provides a Home Assistant custom integration for ABB/FIMER PVI inverters via **direct Modbus/TCP** communication using SunSpec protocol.

**Version:** {VERSION} (BETA)

**Key Technologies:**
- ModbusLink - Async Modbus client library
- SunSpec protocol - Industry-standard solar inverter communication
- Vendored JSON models from github.com/sunspec/models (Apache-2.0)

## Architecture Overview

### async-sunspec-client (Embedded Library)

The integration includes an embedded async SunSpec client library:

**discovery.py** - Model Discovery
- Scan for "SunS" magic number at base addresses (0 or 40000)
- Read M1 (Common) model header
- Follow model chain until 0xFFFF sentinel
- Return list of discovered (model_id, offset) tuples

**models.py** - Model Definitions
- Load JSON model definitions from vendor/sunspec_models/json/
- Parse register layouts, data types, scale factors
- Handle repeating groups (e.g., MPPT channels)
- Provide structured model metadata

**parser.py** - Data Parser
- Read raw Modbus registers via ModbusLink
- Apply scale factors for unit conversion
- Detect and handle invalid sentinels (0x8000, 0x7FFF, NaN markers)
- Parse repeating groups dynamically
- Build component tree with stable device IDs

**exceptions.py** - Custom Exceptions
- SunSpecConnectionError - Modbus communication failures
- SunSpecDiscoveryError - Model discovery failures
- SunSpecModelError - Model loading/parsing errors
- SunSpecParseError - Data parsing errors

### Home Assistant Integration

**__init__.py**
- async_setup_entry(): Initialize ModbusLink client + SunSpec discovery + coordinator
- async_unload_entry(): Clean shutdown and resource cleanup
- Uses config_entry.runtime_data to store coordinator

**coordinator.py**
- ABBFimerPVISunSpecCoordinator extends DataUpdateCoordinator
- Polls discovered models at configured interval
- Handles connection errors and retries
- Provides parsed data to sensor platform

**config_flow.py**
- ConfigFlow: Initial setup with host, port, device_id, base_addr, scan_interval
- OptionsFlow: Runtime reconfiguration without restart
- Validation: Test connection and discover models during setup

**sensor.py**
- Dynamic sensor creation from discovered models
- Entity unique_id: `{{device_type}}_{{serial}}_{{sunspec_point}}`
- State class logic:
  - `total_increasing`: Lifetime energy counters (WH, TotWhImp, etc.)
  - `total`: Periodic counters (DayWH, WeekWH, MonthWH, YearWH from M64061)
  - `measurement`: Instantaneous values (W, A, V, Hz, SoC, etc.)

## SunSpec Models

### Core Models
- **M1** - Common (manufacturer, model, serial, version)
- **M101** - Single-phase inverter
- **M103** - Three-phase inverter
- **M120** - Nameplate ratings
- **M124** - Storage control
- **M160** - MPPT (up to 4 channels with repeating groups)

### Storage Models
- **M802** - Battery base model
- **M803** - Lithium-ion battery
- **M804** - Flow battery

### Meter Models
- **M201** - Single-phase meter
- **M203** - Three-phase meter (WYE)
- **M204** - Three-phase meter (Delta)

### Vendor Models
- **M64061** - ABB vendor-specific (diagnostics, isolation, periodic energy counters)

## Development Patterns

### Error Handling
- Use custom exceptions from async_sunspec_client.exceptions
- Log errors with context using helpers.py functions
- Graceful degradation: if one model fails, continue with others

### Logging
- Use helpers from helpers.py:
  - log_debug(logger, context, message, **kwargs)
  - log_info(logger, context, message, **kwargs)
  - log_warning(logger, context, message, **kwargs)
  - log_error(logger, context, message, **kwargs)
- Never use f-strings in logger calls
- Always include context parameter

### Async/Await
- All I/O must be async
- ModbusLink is async-only
- Coordinator runs in async context

### Data Storage
- Use config_entry.runtime_data with typed RuntimeData dataclass
- Never use hass.data[DOMAIN]

## Code Quality Standards

### Ruff Configuration
- Follow .ruff.toml strictly
- Key rules: A001, TRY300, TRY301, G004, SIM222, PIE796
- Run `ruff check .` before committing

### Type Hints
- Add type hints to all functions and class methods
- Use modern type syntax (e.g., `list[str]` not `List[str]`)
- Type alias: `type ABBFimerPVISunSpecConfigEntry = ConfigEntry[RuntimeData]`

### Testing
- Unit tests for parser, discovery, model loading
- Integration tests for actual Modbus communication
- Test with different inverter models and configurations

## Vendor SunSpec Models

**Source:** https://github.com/sunspec/models (Apache-2.0)

**Location:** vendor/sunspec_models/json/

**Files Required:**
- model_1.json (Common)
- model_101.json, model_103.json (Inverters)
- model_120.json (Nameplate)
- model_124.json (Storage)
- model_160.json (MPPT)
- model_201.json, model_203.json, model_204.json (Meters)
- model_802.json, model_803.json, model_804.json (Battery)
- model_64061.json (ABB vendor - if available)

**Attribution:**
- NOTICE file with Apache-2.0 license text
- NAMESPACE file with upstream URL, ref, timestamp

## Git Workflow

### Commit Messages
- Use conventional commits (feat:, fix:, docs:, etc.)
- Include Claude attribution block:
  ```
  🤖 Generated with [Claude Code](https://claude.com/claude-code)

  Co-Authored-By: Claude <noreply@anthropic.com>
  ```

### Branch Strategy
- Main branch: master
- Feature branches: feature/xxx
- Beta releases tagged as v1.0.0-beta.1, v1.0.0-beta.2, etc.

### Releases
- Tag beta releases with `--prerelease` flag
- Use docs/releases/vX.Y.Z.md for detailed notes
- Update CHANGELOG.md summary

## Beta Testing Checklist

- [ ] Single-phase inverters (M101)
- [ ] Three-phase inverters (M103)
- [ ] MPPT configurations (1-4 channels)
- [ ] Battery/storage systems (M802, M124)
- [ ] Meter integration (M201, M203, M204)
- [ ] M64061 vendor model points
- [ ] Different base addresses (0 vs 40000)
- [ ] Various device_id configurations (1-247)
- [ ] Long-term stability (24+ hours)
- [ ] Error recovery (network interruptions)

## Key Files to Review

- .ruff.toml - Linting configuration
- const.py - Constants and defaults
- helpers.py - Logging helpers
- async_sunspec_client/ - Client library implementation
- docs/pysunspec2-analysis.md - Decision record (copied from old repo)

## Don't Do

- Do not use hass.data[DOMAIN]; use runtime_data
- Do not shadow builtins
- Do not use f-strings in logging
- Do not forget to await async methods
- Do not mix sync/async patterns
- Do not hardcode model IDs - use dynamic discovery
""")

    # docs/architecture-plan.md
    create_file(docs / "architecture-plan.md", """# Architecture Plan - ABB/FIMER PVI SunSpec (Modbus)

## Executive Summary

This integration provides direct Modbus/TCP communication with ABB/FIMER PVI inverters using the industry-standard SunSpec protocol. Dynamic model discovery ensures support for various inverter configurations without hardcoding.

## Goals

1. **Dynamic Discovery**: Scan and detect all SunSpec models present
2. **Multi-Device Support**: Handle inverter + meter + storage + MPPT
3. **Stable Device IDs**: Synthesize deterministic IDs when needed
4. **Robust Parsing**: Handle scale factors, repeating groups, invalid sentinels
5. **HA Best Practices**: Config flow, coordinator pattern, proper entity types

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Home Assistant Integration                     │
├─────────────────────────────────────────────────────────────┤
│  config_flow.py │ coordinator.py │ sensor.py │ __init__.py │
└────────────┬────────────────────────────────────────────────┘
             │
             ├──> async_sunspec_client/
             │    ├── discovery.py   (Model scanning)
             │    ├── models.py      (JSON model loader)
             │    ├── parser.py      (Data parsing & scaling)
             │    └── exceptions.py  (Custom errors)
             │
             └──> ModbusLink (async Modbus client)
                  └──> Inverter (Modbus/TCP)
```

## Discovery Algorithm

```python
async def discover():
    1. Scan for "SunS" (0x53756e53) at base_addr (0 or 40000)
    2. If found, read M1 (Common) model:
       - Manufacturer, Model, Serial, Version
       - Model length (L bytes)
    3. Set offset = base_addr + 2 + L
    4. Loop:
       a. Read model_id at offset
       b. If model_id == 0xFFFF: break (end of chain)
       c. Read model_length at offset + 1
       d. Store (model_id, offset)
       e. offset += 2 + model_length
    5. Return discovered_models list
```

## Model Loading

```python
def load_model(model_id: int):
    1. Load vendor/sunspec_models/json/model_{model_id}.json
    2. Parse:
       - Registers (address, type, units, scale factor)
       - Repeating groups (MPPT channels, batteries)
       - Invalid sentinels (0x8000 for int16, NaN for others)
    3. Build lookup tables for parsing
    4. Return structured model definition
```

## Data Parsing

```python
def parse(model_def, raw_registers):
    1. For each register in model_def:
       a. Extract value from raw_registers[offset]
       b. Check if value == invalid_sentinel
       c. If not invalid:
          - Apply scale factor if present
          - Convert to appropriate type
          - Store in points dict
    2. For repeating groups:
       a. Read count register
       b. Loop count times:
          - Parse group registers
          - Store with index (_1, _2, etc.)
    3. Return points dict
```

## Entity Creation

```python
# Unique ID format
entity_id = f"{device_type}_{serial}_{sunspec_point}"

# Examples:
"inverter_077909_W"          # AC Power
"inverter_077909_WH"         # Lifetime Energy
"mppt_077909_DCA_1"          # MPPT 1 DC Current
"battery_123456_SoC"         # Battery State of Charge
"meter_789012_TotWhImp"      # Meter Total Import Energy
```

## State Class Logic

```python
# total_increasing: Lifetime counters
"WH", "TotWhImp", "TotWhExp", "ECharge", "EDischarge"

# total: Periodic counters (reset after period)
"DayWH", "WeekWH", "MonthWH", "YearWH"

# measurement: Instantaneous values
"W", "A", "V", "Hz", "SoC", "SoH", "Tmp"
```

## Error Handling

1. **Connection Errors**: Retry with exponential backoff
2. **Discovery Failures**: Log and fail setup (can't proceed without models)
3. **Model Load Errors**: Skip that model, continue with others
4. **Parse Errors**: Log warning, mark point as unavailable
5. **Invalid Sentinels**: Detect and skip (don't create entity with bad data)

## Testing Strategy

### Unit Tests
- discovery.py: Model scanning logic
- models.py: JSON parsing
- parser.py: Scale factor application, sentinel detection, repeating groups

### Integration Tests
- Full discovery + parse cycle with mock Modbus data
- Different inverter types (M101 vs M103)
- MPPT variations (1-4 channels)
- Battery + meter combinations

### Real-World Testing
- Beta user feedback across different hardware
- Long-term stability testing
- Network interruption recovery

## Performance Targets

- Discovery: < 5 seconds
- Polling cycle: < 2 seconds for typical setup
- Memory: < 50MB for large multi-device install

## Milestones

**Phase 1: Core Implementation**
- [x] Project structure
- [ ] async_sunspec_client library
- [ ] Basic config flow
- [ ] Simple coordinator
- [ ] Test with M1 + M103 only

**Phase 2: Full Model Support**
- [ ] M101, M120, M160 support
- [ ] Repeating groups (MPPT)
- [ ] Scale factors and sentinels
- [ ] Dynamic sensor creation

**Phase 3: Storage & Meters**
- [ ] M124, M802-804 (batteries)
- [ ] M201, M203, M204 (meters)
- [ ] Multi-device topology
- [ ] Device ID synthesis

**Phase 4: Vendor Models**
- [ ] M64061 (ABB vendor)
- [ ] Periodic energy counters
- [ ] Diagnostics and isolation

**Phase 5: Polish & Release**
- [ ] Documentation
- [ ] Beta testing
- [ ] Bug fixes
- [ ] v1.0.0 stable release
""")

    # Copy pysunspec2-analysis.md from old repo
    old_analysis = CURRENT_DIR / "docs" / "pysunspec2-analysis.md"
    if old_analysis.exists():
        copy_file(old_analysis, docs / "pysunspec2-analysis.md")

    print(f"\n✅ Modbus documentation added")


def add_rest_integration_files():
    """Add all REST integration files."""
    print("\n=== Generating REST Integration Files ===\n")

    base = REST_DIR
    comp = base / "custom_components" / "abb_fimer_pvi_vsn_rest"
    client = comp / "abb_fimer_vsn_rest_client"

    # LICENSE
    create_file(base / "LICENSE", f"""MIT License

Copyright (c) 2019 - {YEAR} Alessandro Del Prete @alexdelprete

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""")

    # manifest.json
    create_file(comp / "manifest.json", f'''{{
  "domain": "abb_fimer_pvi_vsn_rest",
  "name": "ABB/FIMER PVI VSN REST",
  "codeowners": ["@alexdelprete"],
  "config_flow": true,
  "documentation": "https://github.com/alexdelprete/ha-abb-fimer-pvi-vsn-rest",
  "integration_type": "hub",
  "iot_class": "local_polling",
  "issue_tracker": "https://github.com/alexdelprete/ha-abb-fimer-pvi-vsn-rest/issues",
  "loggers": ["custom_components.abb_fimer_pvi_vsn_rest"],
  "requirements": ["aiohttp>=3.9.0"],
  "single_config_entry": false,
  "version": "{VERSION}"
}}
''')

    # const.py
    create_file(comp / "const.py", f'''"""Constants for ABB FIMER PVI VSN REST integration."""

DOMAIN = "abb_fimer_pvi_vsn_rest"
VERSION = "{VERSION}"

# Configuration
CONF_HOST = "host"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_VSN_MODEL = "vsn_model"  # Cached detection result

DEFAULT_USERNAME = "admin"
DEFAULT_SCAN_INTERVAL = 60
MIN_SCAN_INTERVAL = 30
MAX_SCAN_INTERVAL = 600

# VSN Models
VSN_MODEL_300 = "vsn300"
VSN_MODEL_700 = "vsn700"

# REST API Endpoints
ENDPOINT_STATUS = "/v1/status"
ENDPOINT_LIVEDATA = "/v1/livedata"
ENDPOINT_FEEDS = "/v1/feeds"

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
ABB/FIMER PVI VSN REST
Version: {VERSION}
This is a custom integration for Home Assistant
If you have any issues, please report them at:
https://github.com/alexdelprete/ha-abb-fimer-pvi-vsn-rest/issues
-------------------------------------------------------------------
"""
''')

    # __init__.py stub
    create_file(comp / "__init__.py", '''"""ABB FIMER PVI VSN REST Integration.

https://github.com/alexdelprete/ha-abb-fimer-pvi-vsn-rest
"""

import logging
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, STARTUP_MESSAGE

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

type ABBFimerPVIVSNRestConfigEntry = ConfigEntry[RuntimeData]


@dataclass
class RuntimeData:
    """Runtime data for the integration."""

    coordinator: object  # TODO: Add actual type when coordinator is implemented


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ABBFimerPVIVSNRestConfigEntry
) -> bool:
    """Set up ABB FIMER PVI VSN REST from a config entry."""
    _LOGGER.info(STARTUP_MESSAGE)

    # TODO: Initialize abb-fimer-vsn-rest-client and coordinator
    # client = ABBFimerVSNRestClient(...)
    # await client.connect()
    # coordinator = ABBFimerPVIVSNRestCoordinator(hass, config_entry, client)
    # await coordinator.async_config_entry_first_refresh()

    # config_entry.runtime_data = RuntimeData(coordinator=coordinator)
    # await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    raise ConfigEntryNotReady("TODO: Implement async_setup_entry")


async def async_unload_entry(
    hass: HomeAssistant, config_entry: ABBFimerPVIVSNRestConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
''')

    # Client library __init__.py
    create_file(client / "__init__.py", '''"""ABB FIMER VSN REST Client Library."""

from .exceptions import (
    VSNClientError,
    VSNAuthenticationError,
    VSNConnectionError,
    VSNDetectionError,
)

__all__ = [
    "VSNClientError",
    "VSNAuthenticationError",
    "VSNConnectionError",
    "VSNDetectionError",
]
''')

    # Client exceptions
    create_file(client / "exceptions.py", '''"""Exceptions for abb-fimer-vsn-rest-client."""


class VSNClientError(Exception):
    """Base exception for VSN client."""


class VSNConnectionError(VSNClientError):
    """Connection error."""


class VSNAuthenticationError(VSNClientError):
    """Authentication error."""


class VSNDetectionError(VSNClientError):
    """VSN model detection error."""
''')

    # Copy .ruff.toml
    ruff_content = (CURRENT_DIR / ".ruff.toml").read_text(encoding="utf-8")
    create_file(base / ".ruff.toml", ruff_content)

    # hacs.json
    create_file(base / "hacs.json", '''{
  "name": "ABB FIMER PVI VSN REST",
  "homeassistant": "2025.10.0",
  "content_in_root": false,
  "render_readme": true,
  "zip_release": true,
  "filename": "abb_fimer_pvi_vsn_rest.zip"
}
''')

    # Copy mapping Excel and scripts
    mapping_excel = CURRENT_DIR / "docs" / "vsn-sunspec-point-mapping.xlsx"
    if mapping_excel.exists():
        copy_file(mapping_excel, base / "docs" / "vsn-sunspec-point-mapping.xlsx")

    analyze_script = CURRENT_DIR / "analyze_abb_points.py"
    if analyze_script.exists():
        copy_file(analyze_script, base / "scripts" / "analyze_abb_points.py")

    generate_script = CURRENT_DIR / "generate_mapping_excel.py"
    if generate_script.exists():
        copy_file(generate_script, base / "scripts" / "generate_mapping_excel.py")

    print(f"\n✅ REST integration files added")


def create_init_script():
    """Create repository initialization script."""
    print("\n=== Creating Repository Initialization Script ===\n")

    script_path = PARENT_DIR / "ha-abb-powerone-pvi-sunspec" / "init_repos.sh"
    create_file(script_path, f'''#!/bin/bash
# Initialize both new repositories for BETA release

set -e

PARENT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
MODBUS_DIR="$PARENT_DIR/ha-abb-fimer-pvi-sunspec"
REST_DIR="$PARENT_DIR/ha-abb-fimer-pvi-vsn-rest"

echo "==================================================================="
echo "Initializing ABB/FIMER PVI Integration Repositories"
echo "==================================================================="

# Initialize Modbus repo
echo ""
echo "Initializing Modbus integration..."
cd "$MODBUS_DIR"
git init
git add .
git commit -m "Initial commit: v{VERSION}

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
git tag -a v{VERSION} -m "Release v{VERSION} (BETA)"
echo "✅ Modbus repo initialized"

# Initialize REST repo
echo ""
echo "Initializing REST integration..."
cd "$REST_DIR"
git init
git add .
git commit -m "Initial commit: v{VERSION}

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
git tag -a v{VERSION} -m "Release v{VERSION} (BETA)"
echo "✅ REST repo initialized"

echo ""
echo "==================================================================="
echo "✅ Repositories initialized!"
echo "==================================================================="
echo ""
echo "Next steps:"
echo "1. Review the generated files in both repositories"
echo "2. Create GitHub repos using:"
echo "   cd $MODBUS_DIR && gh repo create alexdelprete/ha-abb-fimer-pvi-sunspec --public --source=. --push"
echo "   cd $REST_DIR && gh repo create alexdelprete/ha-abb-fimer-pvi-vsn-rest --public --source=. --push"
echo ""
echo "3. Create pre-releases:"
echo "   cd $MODBUS_DIR && gh release create v{VERSION} --prerelease --title 'v{VERSION}' --notes 'Initial beta release'"
echo "   cd $REST_DIR && gh release create v{VERSION} --prerelease --title 'v{VERSION}' --notes 'Initial beta release'"
echo ""
''')

    # Make executable
    import stat
    script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC)
    print(f"✅ Created: {script_path}")


if __name__ == "__main__":
    print("=" * 70)
    print("Completing Integration Setup")
    print("=" * 70)

    add_modbus_documentation()
    add_rest_integration_files()
    create_init_script()

    print("\n" + "=" * 70)
    print("✅ Complete setup finished!")
    print("=" * 70)
    print("\nFiles created for both integrations:")
    print("- Core integration files (manifest, __init__, const, config_flow, helpers)")
    print("- Client libraries (embedded)")
    print("- Documentation (README, CLAUDE.md, CHANGELOG, architecture)")
    print("- Configuration (.ruff.toml, hacs.json, LICENSE)")
    print("- Initialization script (init_repos.sh)")
    print("\nTODO:")
    print("1. Implement TODO sections in stub files")
    print("2. Copy SunSpec model JSON files to vendor/sunspec_models/json/")
    print("3. Add GitHub workflows")
    print("4. Review and test")
    print("5. Run init_repos.sh to create git repositories")
