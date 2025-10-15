# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

No unreleased changes at this time.

## [4.1.6] - 2025-10-15

Maintenance release with dependency updates and CI/CD improvements.

### 📦 Dependencies

- Bumped pymodbus from 3.11.1 to 3.11.2
- Updated Home Assistant requirement to 2025.10.0+
- Updated development dependencies

### 🔧 CI/CD Improvements

- Fixed lint workflow: upgraded to Python 3.13 for HA 2025.10.2 compatibility
- Updated GitHub Actions dependencies

### 📚 Documentation

- Restructured release documentation following best practices

**Full Release Notes:** [docs/releases/v4.1.6.md](docs/releases/v4.1.6.md)

**Full Changelog:** https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/compare/v4.1.5...v4.1.6

---

## [4.1.5] - 2025-10-12

Official stable release with comprehensive code quality improvements, critical bug fixes, and modernization to Home Assistant 2025.3.0+ best practices.

### 🐛 Critical Bug Fixes

- **Fixed Sensor Availability** - Sensors now properly show as "unavailable" when inverter is offline instead of displaying stale data
- **Fixed Integration Unload KeyError** - Removed invalid cleanup of non-existent `hass.data[DOMAIN][entry_id]`
- **Fixed RuntimeWarning** - Added missing `await` to `api.close()` coroutine call
- **Fixed Duplicate Cleanup Error** - Removed incorrect `async_on_unload()` registration causing double cleanup
- **Fixed Resource Leak** - Per-entry resources now properly cleaned up for all config entries

### ✨ Code Quality Improvements

- Fixed all ruff warnings across entire codebase
- Created centralized logging helpers in `helpers.py`
- Added comprehensive type hints to all classes and instance variables
- Improved error handling patterns with dedicated helper methods
- Renamed `ConnectionError` to `VSNConnectionError` (avoid shadowing Python builtin)
- Fixed IPv6 address validation in `host_valid()` function

### ♻️ Modernization

- Updated to Home Assistant 2025.3.0+ patterns
- Refactored update listener to official HA pattern with automatic cleanup
- Optimized callbacks with proper `@callback` decorator usage
- Modernized integration unload process following HA best practices

### 📦 Dependencies

- Updated ruff from 0.13.3 to 0.14.0
- Updated softprops/action-gh-release from 2.3.4 to 2.4.0
- Compatible with pymodbus >= 3.11.1

### ⚠️ Breaking Changes

- **Requires Home Assistant 2025.3.0 or newer**

**Full Release Notes:** [docs/releases/v4.1.5.md](docs/releases/v4.1.5.md)

**Full Changelog:** https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/compare/v4.1.0...v4.1.5

---

## [4.1.5-beta.6] - 2025-10-11

⚠️ **This is a BETA release** - Please test thoroughly before using in production

### 🐛 Critical Bug Fixes

- **Fixed Sensor Availability** - Sensors now properly show as "unavailable" when inverter is offline
  - Changed `api.py` to raise exceptions instead of returning `False` on connection failures
  - Fixes issue where sensors displayed stale data at night
  - `connect()` method now raises `VSNConnectionError` when inverter unreachable
  - `async_get_data()` method now raises exceptions when data read or connection fails

### 🧹 Other Changes

- Added `.zed` folder to `.gitignore`

**Full Release Notes:** [docs/releases/v4.1.5-beta.6.md](docs/releases/v4.1.5-beta.6.md)

**Full Changelog:** https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/compare/v4.1.5-beta.5...v4.1.5-beta.6

---

## [4.1.5-beta.5] - 2025-10-10

⚠️ **This is a BETA release** - Please test thoroughly before using in production

### 🐛 Bug Fixes

- **Fixed Update Listener Management** - Removed incorrect `async_on_unload()` registration causing duplicate cleanup
- **Fixed Incorrect Async/Await Usage** - Corrected `@callback` decorator usage on synchronous methods

### ♻️ Refactoring

- **Refactored Update Listener** to official HA pattern from Config Entry Options docs
- **Optimized Callbacks** - Changed `async_reload_entry` and `async_update_device_registry` to `@callback`
- Removed `update_listener` from `RuntimeData` dataclass
- Removed manual cleanup in `async_unload_entry` (handled automatically by HA)

### 📦 Dependencies

- Bumped ruff from 0.13.3 to 0.14.0
- Bumped softprops/action-gh-release from 2.3.4 to 2.4.0

**Full Release Notes:** [docs/releases/v4.1.5-beta.5.md](docs/releases/v4.1.5-beta.5.md)

**Full Changelog:** https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/compare/v4.1.5-beta.4...v4.1.5-beta.5

---

## [4.1.5-beta.4] - 2025-10-09

⚠️ **This is a BETA release** - Please test thoroughly before using in production

### 🔄 Integration Lifecycle Improvements

- **Modernized Unload Process** to follow HA 2025.3.0+ recommended pattern from Config Entry States blog post
- **Fixed Resource Leak** - Per-entry resources now properly cleaned up for all config entries
- Conditional cleanup with walrus operator (only if platform unload succeeds)
- Uses `async_loaded_entries(DOMAIN)` for last-entry check

### ⚠️ Breaking Changes

- **Requires Home Assistant 2025.3.0 or newer**

**Full Release Notes:** [docs/releases/v4.1.5-beta.4.md](docs/releases/v4.1.5-beta.4.md)

**Full Changelog:** https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/compare/v4.1.5-beta.3...v4.1.5-beta.4

---

## [4.1.5-beta.3] - 2025-10-08

⚠️ **This is a BETA release** - Please test thoroughly before using in production

### 🐛 Bug Fixes

- **Fixed KeyError on Integration Unload** - Removed invalid cleanup of non-existent `hass.data[DOMAIN][entry_id]`
- **Fixed RuntimeWarning** - Added missing `await` to `api.close()` coroutine call
- Code style improvements in `helpers.py`

**Full Release Notes:** [docs/releases/v4.1.5-beta.3.md](docs/releases/v4.1.5-beta.3.md)

**Full Changelog:** https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/compare/v4.1.5-beta.2...v4.1.5-beta.3

---

## [4.1.5-beta.2] - 2025-10-07

⚠️ **This is a BETA release** - Please test thoroughly before using in production

### ✨ Code Quality Improvements

Continuation of beta.1 code quality improvements:

- Fixed all remaining ruff warnings in pymodbus compatibility modules
- Fixed PIE796 warnings (converted duplicate enum values to aliases)
- Removed unnecessary variable assignments before return statements
- All modules now fully compliant with ruff linting standards

**Full Release Notes:** [docs/releases/v4.1.5-beta.2.md](docs/releases/v4.1.5-beta.2.md)

**Full Changelog:** https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/compare/v4.1.5-beta.1...v4.1.5-beta.2

---

## [4.1.5-beta.1] - 2025-10-06

⚠️ **This is a BETA release** - Please test thoroughly before using in production

### 🐛 Bug Fixes

- Fixed IPv6 address validation in `host_valid()` function (was only accepting IPv4)

### ✨ Code Quality Improvements

- Renamed `ConnectionError` to `VSNConnectionError` (avoid shadowing Python builtin)
- Fixed all TRY300 warnings (moved return statements outside try blocks)
- Fixed all TRY301 warnings (abstracted raise statements to helper functions)
- Fixed RET505 warnings (removed unnecessary else after return)
- Replaced f-strings in logger calls with `%s` formatting (ruff G004)
- Created centralized logging helpers module (`helpers.py`)
- Refactored all modules to use centralized logging helpers
- Added comprehensive type hints to all classes
- Created helper methods for consistent exception handling
- Moved `host_valid()` utility to `helpers.py` for better organization
- Fixed Pylance type checker warnings

**Full Release Notes:** [docs/releases/v4.1.5-beta.1.md](docs/releases/v4.1.5-beta.1.md)

**Full Changelog:** https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/compare/v4.1.0...v4.1.5-beta.1

---

## [4.1.0] - Previous stable release

See GitHub releases for details on v4.1.0 and earlier versions.

[Previous release notes available on GitHub](https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/releases)

---

## Links

- [Unreleased]: https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/compare/v4.1.6...HEAD
- [4.1.6]: https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/compare/v4.1.5...v4.1.6
- [4.1.5]: https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/compare/v4.1.0...v4.1.5
- [4.1.5-beta.6]: https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/compare/v4.1.5-beta.5...v4.1.5-beta.6
- [4.1.5-beta.5]: https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/compare/v4.1.5-beta.4...v4.1.5-beta.5
- [4.1.5-beta.4]: https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/compare/v4.1.5-beta.3...v4.1.5-beta.4
- [4.1.5-beta.3]: https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/compare/v4.1.5-beta.2...v4.1.5-beta.3
- [4.1.5-beta.2]: https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/compare/v4.1.5-beta.1...v4.1.5-beta.2
- [4.1.5-beta.1]: https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/compare/v4.1.0...v4.1.5-beta.1
- [4.1.0]: https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/releases/tag/v4.1.0
