"""Helper tests: host validation and structured logging."""

from __future__ import annotations

from collections.abc import Callable
import logging

import pytest

from custom_components.abb_powerone_pvi_sunspec.helpers import (
    host_valid,
    log_debug,
    log_error,
    log_info,
    log_warning,
)

_LOGGER = logging.getLogger("custom_components.abb_powerone_pvi_sunspec.tests")


@pytest.mark.parametrize(
    ("host", "valid"),
    [
        ("192.168.1.50", True),
        ("fe80::1", True),
        ("inverter", True),
        ("inverter.local", True),
        ("my-inverter.example.com", True),
        ("not a host!", False),
        ("under_score.local", False),
        ("double..dot", False),
    ],
)
def test_host_valid(host: str, valid: bool) -> None:
    """IP addresses and RFC 1123 host names are accepted, anything else is not."""
    assert host_valid(host) is valid


@pytest.mark.parametrize(
    ("log", "level"),
    [
        (log_debug, logging.DEBUG),
        (log_info, logging.INFO),
        (log_warning, logging.WARNING),
        (log_error, logging.ERROR),
    ],
)
def test_log_helpers(
    caplog: pytest.LogCaptureFixture, log: Callable[..., None], level: int
) -> None:
    """Each helper logs at its level as "(context) [key=value, ...]: message"."""
    caplog.set_level(logging.DEBUG)

    log(_LOGGER, "my_function", "Something happened", host="1.2.3.4", port=502)
    log(_LOGGER, "my_function", "No context")

    records = [record for record in caplog.records if record.name == _LOGGER.name]
    assert [record.levelno for record in records] == [level, level]
    assert [record.getMessage() for record in records] == [
        "(my_function) [host=1.2.3.4, port=502]: Something happened",
        "(my_function): No context",
    ]
