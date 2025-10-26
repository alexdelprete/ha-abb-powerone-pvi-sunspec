#!/usr/bin/env python3
"""Complete the REST integration structure with all missing files."""

import shutil
from pathlib import Path

CURRENT_DIR = Path(__file__).parent
PARENT_DIR = CURRENT_DIR.parent
REST_DIR = PARENT_DIR / "ha-abb-fimer-pvi-vsn-rest"
VERSION = "1.0.0-beta.1"


def create_file(path: Path, content: str):
    """Create a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"✓ {path.relative_to(REST_DIR)}")


# Run this script
base = REST_DIR
comp = base / "custom_components" / "abb_fimer_pvi_vsn_rest"
client = comp / "abb_fimer_vsn_rest_client"

print("Creating REST integration files...\n")

# Client library files
files = {
    "client.py": '''"""VSN REST API client."""
import asyncio
import logging
from typing import Any
import aiohttp
from .auth import detect_vsn_model
from .exceptions import VSNConnectionError

_LOGGER = logging.getLogger(__name__)

class ABBFimerVSNRestClient:
    """VSN REST client."""

    def __init__(self, session: aiohttp.ClientSession, base_url: str,
                 username: str, password: str, vsn_model: str | None = None):
        self.session = session
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.vsn_model = vsn_model

    async def connect(self) -> str:
        """Connect and detect VSN model."""
        if not self.vsn_model:
            self.vsn_model = await detect_vsn_model(self.session, self.base_url)
        return self.vsn_model

    async def get_all_data(self) -> dict[str, Any]:
        """Fetch all data."""
        # TODO: Implement data fetching
        return {}
''',
    "auth.py": '''"""VSN authentication."""
import aiohttp

async def detect_vsn_model(session: aiohttp.ClientSession, base_url: str) -> str:
    """Detect VSN300 or VSN700."""
    # TODO: Implement detection
    return "vsn700"
''',
    "normalizer.py": '''"""Data normalizer."""

class VSNDataNormalizer:
    """Normalize VSN data."""

    def __init__(self, vsn_model: str):
        self.vsn_model = vsn_model

    def normalize(self, data: dict) -> dict:
        """Normalize data."""
        # TODO: Implement normalization
        return data
''',
    "models.py": '''"""Data models."""
from dataclasses import dataclass
from typing import Any

@dataclass
class VSNDevice:
    """VSN device."""
    device_id: str
    device_type: str
    serial_number: str
    manufacturer: str
    model: str
    points: dict[str, Any]
''',
}

for filename, content in files.items():
    create_file(client / filename, content)

# Integration files
create_file(comp / "coordinator.py", '''"""Coordinator."""
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .const import DOMAIN

class ABBFimerPVIVSNRestCoordinator(DataUpdateCoordinator):
    """Coordinator."""

    def __init__(self, hass, config_entry, client):
        super().__init__(hass, None, name=DOMAIN,
                         update_interval=timedelta(seconds=60))
        self.client = client

    async def _async_update_data(self):
        return await self.client.get_all_data()
''')

create_file(comp / "sensor.py", '''"""Sensor platform."""
from homeassistant.components.sensor import SensorEntity

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up sensors."""
    # TODO: Implement sensor setup
    pass
''')

create_file(comp / "config_flow.py", '''"""Config flow."""
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

class ABBFimerPVIVSNRestConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle user step."""
        if user_input:
            return self.async_create_entry(title=user_input["host"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("host"): str,
                vol.Required("username", default="admin"): str,
                vol.Required("password"): str,
            })
        )
''')

create_file(comp / "helpers.py", '''"""Helper functions."""
import logging

def log_debug(logger: logging.Logger, context: str, message: str, **kwargs):
    """Log debug."""
    extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.debug("%s: %s %s", context, message, extra)

def log_info(logger: logging.Logger, context: str, message: str, **kwargs):
    """Log info."""
    extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.info("%s: %s %s", context, message, extra)

def log_warning(logger: logging.Logger, context: str, message: str, **kwargs):
    """Log warning."""
    extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.warning("%s: %s %s", context, message, extra)

def log_error(logger: logging.Logger, context: str, message: str, **kwargs):
    """Log error."""
    extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.error("%s: %s %s", context, message, extra)
''')

# Documentation
create_file(base / "README.md", f'''# ABB/FIMER PVI VSN REST

⚠️ **BETA v{VERSION}**

REST API integration for VSN300/VSN700 dataloggers.

## Installation

Via HACS or manual installation.

## Configuration

Configure via UI with host, username, password.
''')

create_file(base / "CHANGELOG.md", f'''# Changelog

## [{VERSION}] - 2025-10-26

Initial beta release.
''')

create_file(base / "CLAUDE.md", '''# Development Guidelines

REST integration for VSN dataloggers.

See main repository documentation.
''')

# Workflows
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
create_file(base / "tests" / "test_client.py", '''"""Client tests."""
def test_placeholder():
    """Placeholder."""
    assert True
''')

# Vendor
create_file(base / "vendor" / "sunspec_models" / "README.md",
'''# SunSpec Models

Download from https://github.com/sunspec/models
''')

print("\n✅ REST integration structure complete!")
print(f"\nLocation: {REST_DIR}")
