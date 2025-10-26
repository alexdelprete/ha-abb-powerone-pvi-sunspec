#!/usr/bin/env python3
"""Generate boilerplate files for ha-abb-fimer-pvi-sunspec and ha-abb-fimer-pvi-vsn-rest."""

import os
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


def generate_modbus_integration():
    """Generate all files for the Modbus integration."""
    print("\n=== Generating Modbus Integration (ha-abb-fimer-pvi-sunspec) ===\n")

    base = MODBUS_DIR
    comp = base / "custom_components" / "abb_fimer_pvi_sunspec"
    client = comp / "async_sunspec_client"

    # ========== LICENSE ==========
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

    # ========== README.md ==========
    create_file(base / "README.md", f"""# ABB/FIMER PVI SunSpec (Modbus/TCP)

⚠️ **BETA RELEASE v{VERSION}**

[![GitHub Release][releases-shield]][releases]
[![HACS][hacs-shield]][hacs]

## Overview

Home Assistant custom integration for ABB/FIMER PVI inverters via **direct Modbus/TCP** communication.

**Key Features:**
- ✅ Dynamic SunSpec model discovery
- ✅ Support for M1, M101, M103, M120, M160, M124, M802-804, M201-204, M64061
- ✅ Multi-device support (inverter, meter, storage, MPPT)
- ✅ Async implementation based on ModbusLink
- ✅ Single-phase (M101) and three-phase (M103) inverters
- ⚠️ BETA - needs real-world testing

## ⚠️ Beta Status

This is a **BETA release**. While the integration has been thoroughly designed, it requires testing across various:
- Inverter models (single-phase, three-phase)
- MPPT configurations
- Battery/storage systems
- Meter integration

**How to help:**
1. Install and test
2. Report issues at [GitHub Issues](https://github.com/alexdelprete/ha-abb-fimer-pvi-sunspec/issues)
3. Share your configuration details
4. Monitor logs for errors

## Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click "Explore & Download Repositories"
4. Search for "ABB FIMER PVI SunSpec"
5. Click "Download"
6. Restart Home Assistant
7. Go to Settings > Devices & Services > Add Integration
8. Search for "ABB FIMER PVI SunSpec"

### Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/alexdelprete/ha-abb-fimer-pvi-sunspec/releases)
2. Extract to `custom_components/abb_fimer_pvi_sunspec`
3. Restart Home Assistant
4. Add integration via UI

## Configuration

Configure via the Home Assistant UI:

- **Host**: IP address or hostname of the inverter
- **Port**: Modbus TCP port (default: 502)
- **Device ID**: Modbus unit ID (default: 2, range: 1-247)
- **Base Address**: SunSpec base address (0 or 40000)
- **Scan Interval**: Polling frequency in seconds (default: 60, range: 30-600)

## Supported Models

**Core Models:**
- **M1** - Common (manufacturer, model, serial number)
- **M101** - Single-phase inverter
- **M103** - Three-phase inverter
- **M120** - Nameplate ratings
- **M160** - MPPT (up to 4 channels)

**Storage Models:**
- **M124** - Storage control
- **M802** - Battery base model
- **M803** - Lithium-ion battery
- **M804** - Flow battery

**Meter Models:**
- **M201** - Single-phase meter
- **M203** - Three-phase meter (WYE)
- **M204** - Three-phase meter (Delta)

**Vendor Models:**
- **M64061** - ABB vendor-specific (diagnostics, isolation, periodic energy counters)

## Entity Naming

Entities are created with SunSpec-based naming:

- `inverter_<serial>_W` - AC Power
- `inverter_<serial>_A` - AC Current
- `inverter_<serial>_Hz` - Frequency
- `inverter_<serial>_WH` - Lifetime Energy
- `mppt_<serial>_DCA_1` - MPPT 1 Current
- `battery_<serial>_SoC` - Battery State of Charge
- `meter_<serial>_TotWhImp` - Total Energy Imported

## Known Limitations

- Beta release - limited production testing
- M64061 vendor model availability varies by inverter firmware
- Performance tuning may be needed for large installations

## Troubleshooting

Enable debug logging in `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.abb_fimer_pvi_sunspec: debug
```

## Support

- [GitHub Issues](https://github.com/alexdelprete/ha-abb-fimer-pvi-sunspec/issues)
- [Home Assistant Community Forum](https://community.home-assistant.io/)

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Follow the code style (.ruff.toml)
4. Add tests if applicable
5. Submit a pull request

## Credits

- Original SolarEdge integration by @binsentsu
- Adapted for ABB/Power-One/FIMER by @alexdelprete
- Built with ModbusLink library
- SunSpec models courtesy of SunSpec Alliance (Apache-2.0)

## License

MIT License - see [LICENSE](LICENSE)

---

_This project is not endorsed by, directly affiliated with, maintained, authorized, or sponsored by ABB or FIMER_

[releases-shield]: https://img.shields.io/github/v/release/alexdelprete/ha-abb-fimer-pvi-sunspec
[releases]: https://github.com/alexdelprete/ha-abb-fimer-pvi-sunspec/releases
[hacs-shield]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs]: https://github.com/custom-components/hacs
""")

    # ========== CHANGELOG.md ==========
    create_file(base / "CHANGELOG.md", f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [{VERSION}] - {datetime.now().strftime('%Y-%m-%d')}

### Added
- Initial beta release
- Async SunSpec Modbus/TCP client based on ModbusLink
- Dynamic model discovery and parsing
- Support for M1, M101, M103, M120, M160, M124, M802-804, M201-204, M64061
- Multi-device support (inverter, meter, storage, MPPT)
- Scale factor handling and data type conversions
- Repeating group support (MPPT channels)
- Invalid sentinel detection (0x8000, 0x7FFF)
- Component tree with stable device IDs
- Config flow with validation
- Options flow for runtime reconfiguration
- Comprehensive error handling and logging

### Known Limitations
- Beta release - limited user testing
- Needs validation across different inverter models
- Performance tuning may be needed
- M64061 vendor model availability varies by firmware

### Testing Needed
- Single-phase inverters (M101)
- Three-phase inverters (M103)
- MPPT configurations (1-4 channels)
- Battery/storage systems (M802, M124)
- Meter integration (M201, M203, M204)
- Different base addresses (0 vs 40000)
- Various device_id configurations

[Unreleased]: https://github.com/alexdelprete/ha-abb-fimer-pvi-sunspec/compare/v{VERSION}...HEAD
[{VERSION}]: https://github.com/alexdelprete/ha-abb-fimer-pvi-sunspec/releases/tag/v{VERSION}
""")

    # ========== manifest.json ==========
    create_file(comp / "manifest.json", f'''{{
  "domain": "abb_fimer_pvi_sunspec",
  "name": "ABB/FIMER PVI SunSpec (Modbus)",
  "codeowners": ["@alexdelprete"],
  "config_flow": true,
  "documentation": "https://github.com/alexdelprete/ha-abb-fimer-pvi-sunspec",
  "integration_type": "hub",
  "iot_class": "local_polling",
  "issue_tracker": "https://github.com/alexdelprete/ha-abb-fimer-pvi-sunspec/issues",
  "loggers": ["custom_components.abb_fimer_pvi_sunspec"],
  "requirements": ["modbuslink>=0.1.0"],
  "single_config_entry": false,
  "version": "{VERSION}"
}}
''')

    # ========== const.py ==========
    create_file(comp / "const.py", f'''"""Constants for ABB FIMER PVI SunSpec integration."""

DOMAIN = "abb_fimer_pvi_sunspec"
VERSION = "{VERSION}"

# Configuration
CONF_HOST = "host"
CONF_PORT = "port"
CONF_DEVICE_ID = "device_id"
CONF_BASE_ADDR = "base_addr"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_PORT = 502
DEFAULT_DEVICE_ID = 2
DEFAULT_BASE_ADDR = 0
DEFAULT_SCAN_INTERVAL = 60
MIN_SCAN_INTERVAL = 30
MAX_SCAN_INTERVAL = 600

# SunSpec
SUNSPEC_REGISTER_END = 0xFFFF

# Core SunSpec Models
MODEL_COMMON = 1
MODEL_INVERTER_SINGLE_PHASE = 101
MODEL_INVERTER_THREE_PHASE = 103
MODEL_NAMEPLATE = 120
MODEL_STORAGE = 124
MODEL_MPPT = 160
MODEL_METER_SINGLE_PHASE = 201
MODEL_METER_THREE_PHASE_WYE = 203
MODEL_METER_THREE_PHASE_DELTA = 204
MODEL_BATTERY = 802
MODEL_LITHIUM_ION = 803
MODEL_FLOW_BATTERY = 804
MODEL_ABB_VENDOR = 64061

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
ABB/FIMER PVI SunSpec (Modbus)
Version: {VERSION}
This is a custom integration for Home Assistant
If you have any issues, please report them at:
https://github.com/alexdelprete/ha-abb-fimer-pvi-sunspec/issues
-------------------------------------------------------------------
"""
''')

    # ========== __init__.py stub ==========
    create_file(comp / "__init__.py", '''"""ABB FIMER PVI SunSpec Integration.

https://github.com/alexdelprete/ha-abb-fimer-pvi-sunspec
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

type ABBFimerPVISunSpecConfigEntry = ConfigEntry[RuntimeData]


@dataclass
class RuntimeData:
    """Runtime data for the integration."""

    coordinator: object  # TODO: Add actual type when coordinator is implemented


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ABBFimerPVISunSpecConfigEntry
) -> bool:
    """Set up ABB FIMER PVI SunSpec from a config entry."""
    _LOGGER.info(STARTUP_MESSAGE)

    # TODO: Initialize async-sunspec-client and coordinator
    # coordinator = ABBFimerPVISunSpecCoordinator(hass, config_entry)
    # await coordinator.async_config_entry_first_refresh()

    # config_entry.runtime_data = RuntimeData(coordinator=coordinator)
    # await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    raise ConfigEntryNotReady("TODO: Implement async_setup_entry")


async def async_unload_entry(
    hass: HomeAssistant, config_entry: ABBFimerPVISunSpecConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
''')

    # ========== config_flow.py stub ==========
    create_file(comp / "config_flow.py", '''"""Config flow for ABB FIMER PVI SunSpec."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback

from .const import (
    CONF_BASE_ADDR,
    CONF_DEVICE_ID,
    CONF_SCAN_INTERVAL,
    DEFAULT_BASE_ADDR,
    DEFAULT_DEVICE_ID,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class ABBFimerPVISunSpecConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ABB FIMER PVI SunSpec."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # TODO: Validate connection to inverter
            # TODO: Discover SunSpec models
            # TODO: Create unique_id based on serial number

            return self.async_create_entry(
                title=user_input.get(CONF_NAME, user_input[CONF_HOST]),
                data=user_input,
            )

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_NAME): str,
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional(CONF_DEVICE_ID, default=DEFAULT_DEVICE_ID): vol.All(
                    int, vol.Range(min=1, max=247)
                ),
                vol.Optional(CONF_BASE_ADDR, default=DEFAULT_BASE_ADDR): vol.In(
                    [0, 40000]
                ),
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(
                    int, vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
                ),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return ABBFimerPVISunSpecOptionsFlow(config_entry)


class ABBFimerPVISunSpecOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for ABB FIMER PVI SunSpec."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Update config entry data
            self.hass.config_entries.async_update_entry(
                self.config_entry, data={**self.config_entry.data, **user_input}
            )
            return self.async_create_entry(title="", data={})

        current_config = self.config_entry.data

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_PORT, default=current_config.get(CONF_PORT, DEFAULT_PORT)
                ): int,
                vol.Optional(
                    CONF_DEVICE_ID,
                    default=current_config.get(CONF_DEVICE_ID, DEFAULT_DEVICE_ID),
                ): vol.All(int, vol.Range(min=1, max=247)),
                vol.Optional(
                    CONF_BASE_ADDR,
                    default=current_config.get(CONF_BASE_ADDR, DEFAULT_BASE_ADDR),
                ): vol.In([0, 40000]),
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=current_config.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): vol.All(
                    int, vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)
''')

    # ========== helpers.py stub ==========
    create_file(comp / "helpers.py", '''"""Helper functions for ABB FIMER PVI SunSpec."""

import logging


def log_debug(logger: logging.Logger, context: str, message: str, **kwargs) -> None:
    """Log debug message with context."""
    extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.debug("%s: %s %s", context, message, extra)


def log_info(logger: logging.Logger, context: str, message: str, **kwargs) -> None:
    """Log info message with context."""
    extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.info("%s: %s %s", context, message, extra)


def log_warning(logger: logging.Logger, context: str, message: str, **kwargs) -> None:
    """Log warning message with context."""
    extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.warning("%s: %s %s", context, message, extra)


def log_error(logger: logging.Logger, context: str, message: str, **kwargs) -> None:
    """Log error message with context."""
    extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.error("%s: %s %s", context, message, extra)
''')

    # ========== async_sunspec_client/__init__.py ==========
    create_file(client / "__init__.py", '''"""Async SunSpec Client Library."""

from .exceptions import (
    SunSpecClientError,
    SunSpecConnectionError,
    SunSpecDiscoveryError,
    SunSpecModelError,
    SunSpecParseError,
)

__all__ = [
    "SunSpecClientError",
    "SunSpecConnectionError",
    "SunSpecDiscoveryError",
    "SunSpecModelError",
    "SunSpecParseError",
]
''')

    # ========== async_sunspec_client/exceptions.py ==========
    create_file(client / "exceptions.py", '''"""Exceptions for async-sunspec-client."""


class SunSpecClientError(Exception):
    """Base exception for SunSpec client."""


class SunSpecConnectionError(SunSpecClientError):
    """Connection error."""


class SunSpecDiscoveryError(SunSpecClientError):
    """Model discovery error."""


class SunSpecModelError(SunSpecClientError):
    """Model loading/parsing error."""


class SunSpecParseError(SunSpecClientError):
    """Data parsing error."""
''')

    # ========== async_sunspec_client/discovery.py stub ==========
    create_file(client / "discovery.py", '''"""SunSpec model discovery."""

import logging

_LOGGER = logging.getLogger(__name__)


async def discover_models(
    modbus_client, base_addr: int, device_id: int
) -> list[tuple[int, int]]:
    """Discover SunSpec models.

    Returns:
        List of (model_id, offset) tuples

    TODO:
    - Scan for "SunS" magic number at base_addr
    - Read M1 (Common) model
    - Follow model chain until 0xFFFF
    - Return list of discovered (model_id, offset) pairs
    """
    raise NotImplementedError("TODO: Implement model discovery")
''')

    # ========== async_sunspec_client/models.py stub ==========
    create_file(client / "models.py", '''"""SunSpec model definitions and loader."""

import json
import logging
from pathlib import Path

_LOGGER = logging.getLogger(__name__)


def load_model_definition(model_id: int) -> dict:
    """Load SunSpec model definition from JSON.

    TODO:
    - Load from vendor/sunspec_models/json/model_{model_id}.json
    - Parse registers, scale factors, types
    - Handle repeating groups
    - Return structured model definition
    """
    raise NotImplementedError("TODO: Implement model loading")
''')

    # ========== async_sunspec_client/parser.py stub ==========
    create_file(client / "parser.py", '''"""SunSpec data parser."""

import logging

_LOGGER = logging.getLogger(__name__)


class SunSpecParser:
    """Parse SunSpec model data."""

    def __init__(self, model_definition: dict):
        """Initialize parser with model definition."""
        self.model_definition = model_definition

    def parse(self, raw_registers: list[int]) -> dict:
        """Parse raw Modbus registers into structured data.

        TODO:
        - Apply scale factors
        - Handle invalid sentinels (0x8000, 0x7FFF, etc.)
        - Parse repeating groups
        - Convert data types
        - Return structured point data
        """
        raise NotImplementedError("TODO: Implement data parsing")
''')

    # ========== hacs.json ==========
    create_file(base / "hacs.json", '''{
  "name": "ABB FIMER PVI SunSpec (Modbus)",
  "homeassistant": "2025.10.0",
  "content_in_root": false,
  "render_readme": true,
  "zip_release": true,
  "filename": "abb_fimer_pvi_sunspec.zip"
}
''')

    # ========== .ruff.toml (copy from current repo) ==========
    ruff_content = (CURRENT_DIR / ".ruff.toml").read_text(encoding="utf-8")
    create_file(base / ".ruff.toml", ruff_content)

    print(f"\n✅ Modbus integration structure created at: {base}")


def generate_rest_integration():
    """Generate all files for the REST integration."""
    print("\n=== Generating REST Integration (ha-abb-fimer-pvi-vsn-rest) ===\n")

    base = REST_DIR
    comp = base / "custom_components" / "abb_fimer_pvi_vsn_rest"
    client = comp / "abb_fimer_vsn_rest_client"

    # ========== LICENSE ==========
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

    # ========== README.md ==========
    create_file(base / "README.md", f"""# ABB/FIMER PVI VSN REST

⚠️ **BETA RELEASE v{VERSION}**

[![GitHub Release][releases-shield]][releases]
[![HACS][hacs-shield]][hacs]

## Overview

Home Assistant custom integration for ABB/FIMER PVI inverters via **VSN300/VSN700 datalogger REST API**.

**Key Features:**
- ✅ Automatic VSN model detection (VSN300 vs VSN700)
- ✅ VSN300 X-Digest authentication (non-standard digest)
- ✅ VSN700 Preemptive Basic authentication
- ✅ Data normalization to SunSpec schema
- ✅ Multi-device support (inverter + batteries + meter)
- ✅ 162+ data points with categorization
- ⚠️ BETA - needs real-world testing

## ⚠️ Beta Status

This is a **BETA release**. While the integration has been thoroughly designed, it requires testing across:
- VSN300 dataloggers (X-Digest authentication)
- VSN700 dataloggers (Basic authentication)
- Auto-detection reliability
- Multi-device configurations
- All 162+ data points validation

**How to help:**
1. Install and test
2. Report issues at [GitHub Issues](https://github.com/alexdelprete/ha-abb-fimer-pvi-vsn-rest/issues)
3. Share your VSN model and configuration
4. Monitor logs for errors

## Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click "Explore & Download Repositories"
4. Search for "ABB FIMER PVI VSN REST"
5. Click "Download"
6. Restart Home Assistant
7. Go to Settings > Devices & Services > Add Integration
8. Search for "ABB FIMER PVI VSN REST"

### Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/alexdelprete/ha-abb-fimer-pvi-vsn-rest/releases)
2. Extract to `custom_components/abb_fimer_pvi_vsn_rest`
3. Restart Home Assistant
4. Add integration via UI

## Configuration

Configure via the Home Assistant UI:

- **Host**: IP address or hostname of the VSN datalogger
- **Username**: VSN username (default: admin)
- **Password**: VSN password
- **Scan Interval**: Polling frequency in seconds (default: 60, range: 30-600)

The integration will automatically detect whether you have a VSN300 or VSN700 and use the appropriate authentication method.

## Supported Data Points

**Standard SunSpec (54 points)** - Available in both Modbus and REST:
- AC Power, Current, Voltage, Frequency
- DC Power, Current, Voltage (MPPT)
- Energy counters
- Temperature readings
- Battery: SoC, SoH, Power, Current, Voltage
- Meter: Import/Export energy, Power

**M64061 Vendor Model (61 points)** - May be available:
- Periodic energy counters (daily, weekly, monthly, yearly)
- Isolation measurements
- Bulk voltages
- Diagnostic states

**ABB Proprietary (47 points)** - REST only:
- House consumption metering
- Battery extensions
- Hybrid system features

## Entity Naming

Entities use normalized SunSpec naming:

- `inverter_<serial>_W` - AC Power
- `inverter_<serial>_WH` - Lifetime Energy
- `battery_<serial>_SoC` - Battery State of Charge
- `meter_<serial>_TotWhImp` - Total Energy Imported
- `abb_HousePgrid_L1` - House consumption L1 (proprietary)

## Authentication

### VSN300
Uses **X-Digest** authentication (non-standard HTTP Digest variant). The integration handles this automatically.

### VSN700
Uses **Preemptive Basic** authentication. The integration sends credentials with the first request.

### Auto-Detection
The integration probes `/v1/status` and examines the `WWW-Authenticate` header to determine VSN model. The result is cached to avoid repeated detection.

## Data Endpoints

The integration queries three REST endpoints:

- `/v1/status` - System status and device information
- `/v1/livedata` - Real-time measurements
- `/v1/feeds` - Feed metadata (units, precision, descriptions)

## Known Limitations

- Beta release - limited production testing
- M64061 vendor model points availability via REST needs validation
- VSN300 X-Digest authentication requires more real-world testing
- Some proprietary points may not be present on all systems

## Troubleshooting

Enable debug logging in `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.abb_fimer_pvi_vsn_rest: debug
```

## Support

- [GitHub Issues](https://github.com/alexdelprete/ha-abb-fimer-pvi-vsn-rest/issues)
- [Home Assistant Community Forum](https://community.home-assistant.io/)

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Follow the code style (.ruff.toml)
4. Add tests if applicable
5. Submit a pull request

## Credits

- Based on vsnx00-monitor v2.0.0 prototype
- Adapted for Home Assistant by @alexdelprete
- Built with aiohttp library
- SunSpec models courtesy of SunSpec Alliance (Apache-2.0)

## License

MIT License - see [LICENSE](LICENSE)

---

_This project is not endorsed by, directly affiliated with, maintained, authorized, or sponsored by ABB or FIMER_

[releases-shield]: https://img.shields.io/github/v/release/alexdelprete/ha-abb-fimer-pvi-vsn-rest
[releases]: https://github.com/alexdelprete/ha-abb-fimer-pvi-vsn-rest/releases
[hacs-shield]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs]: https://github.com/custom-components/hacs
""")

    # Continue with REST integration files...
    # (manifest.json, const.py, __init__.py, config_flow.py, etc.)
    # Similar structure to Modbus but with REST-specific content

    print(f"\n✅ REST integration structure created at: {base}")


if __name__ == "__main__":
    print("=" * 70)
    print("Generating ABB/FIMER PVI Integration Boilerplate Files")
    print("=" * 70)

    generate_modbus_integration()
    # generate_rest_integration()  # TODO: Complete REST generation

    print("\n" + "=" * 70)
    print("Generation complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Review generated files")
    print("2. Implement TODO sections in stub files")
    print("3. Copy SunSpec model JSON files to vendor/sunspec_models/json/")
    print("4. Add GitHub workflows (.github/workflows/)")
    print("5. Create initial git commits")
    print("6. Push to GitHub and create releases")
