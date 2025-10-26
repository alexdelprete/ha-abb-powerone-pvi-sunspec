#!/usr/bin/env python3
"""Complete the Modbus/SunSpec integration structure."""

from pathlib import Path

CURRENT_DIR = Path(__file__).parent
PARENT_DIR = CURRENT_DIR.parent
MODBUS_DIR = PARENT_DIR / "ha-abb-fimer-pvi-sunspec"


def create_file(path: Path, content: str):
    """Create a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"✓ {path.relative_to(MODBUS_DIR)}")


base = MODBUS_DIR
comp = base / "custom_components" / "abb_fimer_pvi_sunspec"
client = comp / "async_sunspec_client"

print("Creating missing Modbus integration files...\n")

# Client library
create_file(client / "client.py", '''"""Main SunSpec client implementation."""
import logging
from .discovery import discover_models
from .models import load_model_definition
from .parser import SunSpecParser
from .exceptions import SunSpecConnectionError

_LOGGER = logging.getLogger(__name__)

class AsyncSunSpecClient:
    """Async SunSpec Modbus client."""

    def __init__(self, modbus_client, base_addr: int = 0, device_id: int = 2):
        self.modbus_client = modbus_client
        self.base_addr = base_addr
        self.device_id = device_id
        self.discovered_models = []
        self.parsers = {}

    async def connect(self):
        """Connect and discover models."""
        self.discovered_models = await discover_models(
            self.modbus_client, self.base_addr, self.device_id
        )
        for model_id, offset in self.discovered_models:
            try:
                model_def = load_model_definition(model_id)
                self.parsers[model_id] = SunSpecParser(model_def)
            except Exception as err:
                _LOGGER.warning("Failed to load model %d: %s", model_id, err)

    async def read_all(self):
        """Read all discovered models."""
        # TODO: Implement Modbus reading
        return {}
''')

# Coordinator
create_file(comp / "coordinator.py", '''"""DataUpdateCoordinator for SunSpec."""
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

class ABBFimerPVISunSpecCoordinator(DataUpdateCoordinator):
    """Coordinator for SunSpec data."""

    def __init__(self, hass, config_entry, client):
        scan_interval = config_entry.data.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        super().__init__(
            hass, None, name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval)
        )
        self.client = client
        self.config_entry = config_entry

    async def _async_update_data(self):
        """Fetch data from SunSpec client."""
        try:
            return await self.client.read_all()
        except Exception as err:
            raise UpdateFailed(f"Error: {err}") from err
''')

# Sensor platform
create_file(comp / "sensor.py", '''"""Sensor platform for SunSpec."""
from homeassistant.components.sensor import SensorEntity

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up sensors."""
    # TODO: Implement dynamic sensor creation
    pass
''')

# Workflow
create_file(base / ".github" / "workflows" / "lint.yml", '''name: Lint
on: [push, pull_request]
jobs:
  ruff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: chartboost/ruff-action@v1
''')

# Tests
create_file(base / "tests" / "test_discovery.py", '''"""Discovery tests."""
def test_placeholder():
    """Placeholder test."""
    assert True
''')

create_file(base / "tests" / "test_parser.py", '''"""Parser tests."""
def test_placeholder():
    """Placeholder test."""
    assert True
''')

# Vendor README
create_file(base / "vendor" / "sunspec_models" / "README.md", '''# SunSpec Models

Download JSON models from: https://github.com/sunspec/models

Required files in `json/` directory:
- model_1.json (Common)
- model_101.json, model_103.json (Inverters)
- model_120.json (Nameplate)
- model_124.json (Storage)
- model_160.json (MPPT)
- model_201.json, model_203.json, model_204.json (Meters)
- model_802.json, model_803.json, model_804.json (Battery)
- model_64061.json (ABB vendor - if available)

Create NOTICE file with Apache-2.0 license text.
Create NAMESPACE file with upstream URL, ref, and timestamp.
''')

print("\n✅ Modbus integration structure complete!")
print(f"\nLocation: {MODBUS_DIR}")
