# Release Notes - v4.1.5

## What's Changed

This release includes comprehensive code quality improvements, critical bug fixes, and modernization to follow Home Assistant 2025.3.0+ best practices.

### 🐛 Critical Bug Fixes

#### Fixed Sensor Availability (v4.1.5-beta.6)
**The most important fix in this release** - sensors now properly show as "unavailable" when the inverter is offline (at night) instead of displaying stale data.

**The Problem:**
- Sensors displayed stale data from sunset throughout the night
- No indication that the inverter was offline
- Users saw incorrect power readings (e.g., "1500W" at midnight)

**The Solution:**
Changed error handling in `api.py` to raise exceptions instead of returning `False`:
- `connect()` method: Raises `VSNConnectionError` when inverter is unreachable
- `async_get_data()` method: Raises exceptions when data read or connection fails
- Coordinator now properly marks entities as unavailable when exceptions occur

**Files changed:**
- [api.py](custom_components/abb_powerone_pvi_sunspec/api.py): 5 changes to exception handling
- [config_flow.py](custom_components/abb_powerone_pvi_sunspec/config_flow.py): Updated to catch custom exceptions

#### Fixed Integration Lifecycle (v4.1.5-beta.3, beta.4, beta.5)
- **Fixed KeyError on integration unload** - Removed invalid cleanup of non-existent `hass.data[DOMAIN][entry_id]`
- **Fixed RuntimeWarning** - Added missing `await` to `api.close()` coroutine call
- **Fixed duplicate cleanup error** - Removed incorrect `async_on_unload()` registration causing double cleanup
- **Fixed resource leak** - Per-entry resources now properly cleaned up for all config entries
- **Fixed incorrect async/await usage** - Corrected `@callback` decorator usage on synchronous methods

**Files changed:**
- [__init__.py](custom_components/abb_powerone_pvi_sunspec/__init__.py): Refactored to HA 2025.3.0+ pattern

### ✨ Code Quality Improvements (v4.1.5-beta.1, beta.2)

#### Comprehensive Refactoring
- **Fixed all ruff warnings** across the entire codebase
- **Created centralized logging helpers** in [helpers.py](custom_components/abb_powerone_pvi_sunspec/helpers.py):
  - `log_debug()`, `log_info()`, `log_warning()`, `log_error()`
  - Standardized logging with context and kwargs
  - Converted 34+ logging calls across all modules
- **Added comprehensive type hints** to all classes and instance variables
- **Improved error handling patterns**:
  - Created `_check_modbus_exception_response()` helper
  - Created `_handle_connection_exception()` helper
  - Created `_handle_modbus_exception()` helper

#### Specific Fixes
- Renamed `ConnectionError` to `VSNConnectionError` (avoid shadowing Python builtin)
- Fixed IPv6 address validation in `host_valid()` function
- Fixed all TRY300 warnings (moved return statements outside try blocks)
- Fixed all TRY301 warnings (abstracted raise statements to helpers)
- Fixed RET505 warnings (removed unnecessary else after return)
- Replaced f-strings in logger calls with `%s` formatting (ruff G004)
- Fixed PIE796 warnings (converted duplicate enum values to aliases)
- Moved `host_valid()` utility to [helpers.py](custom_components/abb_powerone_pvi_sunspec/helpers.py) for better organization

**Files improved:**
- [api.py](custom_components/abb_powerone_pvi_sunspec/api.py)
- [coordinator.py](custom_components/abb_powerone_pvi_sunspec/coordinator.py)
- [sensor.py](custom_components/abb_powerone_pvi_sunspec/sensor.py)
- [config_flow.py](custom_components/abb_powerone_pvi_sunspec/config_flow.py)
- [helpers.py](custom_components/abb_powerone_pvi_sunspec/helpers.py) (new module)
- [pymodbus_*.py](custom_components/abb_powerone_pvi_sunspec/) modules

### ♻️ Modernization

#### Update Listener Pattern (v4.1.5-beta.5)
Refactored to official HA pattern from [Config Entry Options docs](https://developers.home-assistant.io/docs/config_entries_options_flow_handler/#signal-updates):
- Uses `async_on_unload(add_update_listener())` for automatic cleanup
- Removed manual cleanup code (handled automatically by HA)
- Removed `update_listener` from `RuntimeData` dataclass

#### Callback Optimizations (v4.1.5-beta.5)
- `async_reload_entry`: Changed to `@callback` decorator (synchronous)
- `async_update_device_registry`: Changed to `@callback` decorator (synchronous)
- Improved performance with fewer async context switches

#### Integration Unload (v4.1.5-beta.4)
Follows official HA 2025.3.0+ pattern from [Config Entry States blog post](https://developers.home-assistant.io/blog/2025/02/19/new-config-entry-states/):
- Conditional cleanup with walrus operator (only if platform unload succeeds)
- Uses `async_loaded_entries(DOMAIN)` for last-entry check
- Better error handling and logging

### 📦 Dependencies

- **Updated ruff** from 0.13.3 to 0.14.0
- **Updated softprops/action-gh-release** from 2.3.4 to 2.4.0
- Compatible with **pymodbus >= 3.11.1**
- Compatible with **Home Assistant 2025.3.0+**

### 🧹 Other Changes

- Added `.zed` folder to [.gitignore](/.gitignore)

### ⚠️ Breaking Changes

**Requires Home Assistant 2025.3.0 or newer**
- Dropped backwards compatibility with HA < 2025.3.0
- Uses modern config entry state management

### 📋 Testing Recommendations

#### Sensor Availability
1. Disconnect inverter or VSN card from network
2. Wait for next update cycle (check scan_interval)
3. Verify all sensors show "Unavailable"
4. Reconnect and verify sensors restore with fresh data
5. Monitor day/night cycle for proper availability transitions

#### Integration Lifecycle
1. Test integration reload (Settings → Devices & Services → Configure → Reload)
2. Test integration removal (verify no errors in logs)
3. Test with multiple config entries
4. Verify update listener triggers on options changes

### 🚀 Upgrade Notes

This is an **official stable release** - thoroughly tested through 6 beta releases.

- **Highly recommended upgrade** - fixes critical sensor availability issue
- Safe to upgrade from v4.1.0 or any v4.1.5-beta.x
- **Requires Home Assistant 2025.3.0 or newer**
- No configuration changes required
- All changes are internal improvements and bug fixes

### 🎯 Summary of Beta Testing

This release went through extensive beta testing (6 beta releases) to ensure stability:
- **beta.1 & beta.2**: Code quality improvements and ruff compliance
- **beta.3**: Fixed unload bugs (KeyError, missing await)
- **beta.4**: Modernized unload process for HA 2025.3.0+
- **beta.5**: Fixed update listener lifecycle and callback optimizations
- **beta.6**: Critical sensor availability fix

### 📝 Commits Since v4.1.0

All 30 commits from v4.1.0 to v4.1.5 including:
- Code quality improvements and refactoring
- Fixed all ruff warnings across codebase
- Multiple lifecycle management fixes
- Critical sensor availability fix
- Dependency updates

**Full Changelog**: https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/compare/v4.1.0...v4.1.5
