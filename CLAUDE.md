# Claude Code Development Guidelines

## Project Overview

This is a Home Assistant custom integration for ABB/Power-One/FIMER PVI inverters using SunSpec Modbus TCP protocol. The integration communicates with inverters either directly or through VSN300/VSN700 WiFi logger cards.

## Code Architecture

### Core Components

1. **`__init__.py`** - Integration lifecycle management
   - `async_setup_entry()` - Initialize coordinator and platforms
   - `async_unload_entry()` - Clean shutdown and resource cleanup
   - `async_migrate_entry()` - Config migration logic
   - Uses `runtime_data` for storing coordinator and update listener

2. **`api.py`** - Modbus TCP communication layer
   - `ABBPowerOneFimerAPI` class handles all Modbus operations
   - Reads SunSpec model 160 registers
   - Auto-detects register map base address
   - Implements connection pooling and timeout handling

3. **`coordinator.py`** - Data update coordination
   - `ABBPowerOneFimerCoordinator` manages polling cycles
   - Handles data refresh from API
   - Error handling and retry logic

4. **`config_flow.py`** - UI configuration
   - ConfigFlow for initial setup
   - OptionsFlow for runtime reconfiguration
   - Validates host, port, device_id, base_addr, scan_interval

5. **`sensor.py`** - Entity platform
   - Creates sensors from coordinator data
   - Dynamic sensor creation based on inverter type (single/three-phase)
   - MPPT configuration detection

## Important Patterns

### Error Handling

- Use custom exceptions: `VSNConnectionError`, `ModbusError`, `ExceptionError`
- Helper functions in `api.py`:
  - `_check_modbus_exception_response()`
  - `_handle_connection_exception()`
  - `_handle_modbus_exception()`

### Logging

- Use centralized logging helpers from `helpers.py`:
  - `log_debug(logger, context, message, **kwargs)`
  - `log_info(logger, context, message, **kwargs)`
  - `log_warning(logger, context, message, **kwargs)`
  - `log_error(logger, context, message, **kwargs)`
- Never use f-strings in logger calls (use `%s` formatting)
- Always include context parameter (function name)

### Async/Await

- All coordinator methods are async
- API `close()` method is async - always use `await`
- Config entry methods follow HA conventions:
  - `add_update_listener()` - sync
  - `async_on_unload()` - sync (despite the name)
  - `async_forward_entry_setups()` - async
  - `async_unload_platforms()` - async

### Data Storage

- Modern pattern: Use `config_entry.runtime_data` (not `hass.data[DOMAIN][entry_id]`)
- `runtime_data` is typed with `RuntimeData` dataclass
- Automatically cleaned up on unload

## Code Quality Standards

### Ruff Configuration

- Follow `.ruff.toml` rules strictly
- Key rules:
  - A001: Don't shadow builtins (e.g., use `VSNConnectionError` not `ConnectionError`)
  - TRY300: Move return/break outside try blocks
  - TRY301: Abstract raise statements to helpers
  - RET505: Remove unnecessary else after return
  - G004: Use `%s` not f-strings in logging
  - SIM222: Correct boolean logic
  - PIE796: Use enum aliases for duplicate values

### Type Hints

- Add type hints to all classes and instance variables
- Use modern type syntax where possible
- Config entry type alias: `type ABBPowerOneFimerConfigEntry = ConfigEntry[RuntimeData]`

### Testing Approach

- Test with both single-phase and three-phase inverters
- Test with VSN300/VSN700 dataloggers
- Verify register base address auto-detection
- Test reload/unload scenarios

## Common Patterns

### Version Updates

When bumping version:

1. Update `manifest.json` - `"version": "X.Y.Z"`
2. Update `const.py` - `VERSION = "X.Y.Z"`
3. Create detailed release notes: `docs/releases/vX.Y.Z.md`
   - Use existing release notes as template
   - Include all sections: What's Changed, Bug Fixes, Features, Breaking Changes, etc.
4. Update `CHANGELOG.md` with version summary
   - Add new version section at top (below Unreleased)
   - Include emoji-enhanced section headers
   - Link to detailed release notes: `[docs/releases/vX.Y.Z.md](docs/releases/vX.Y.Z.md)`
   - Add comparison link at bottom
5. Commit: "Bump version to vX.Y.Z"
6. Tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
7. Push: `git push && git push --tags`
8. Create GitHub release: `gh release create vX.Y.Z --prerelease/--latest`

### Release Documentation Structure

The project follows industry best practices for release documentation:

- **`CHANGELOG.md`** (root) - Quick overview of all releases
  - Based on [Keep a Changelog](https://keepachangelog.com/) format
  - Summarized entries for each version
  - Links to detailed release notes
  - Comparison links for GitHub diffs

- **`docs/releases/`** - Detailed release notes
  - One file per version: `vX.Y.Z.md` or `vX.Y.Z-beta.N.md`
  - Comprehensive technical details
  - Upgrade instructions
  - Testing recommendations
  - Breaking changes documentation

- **`docs/releases/README.md`** - Release directory guide
  - Explains structure for users and developers
  - Documents release workflow

### Configuration Parameters

- `host` - IP/hostname (not used for unique_id, can be changed without losing data)
- `port` - TCP port (default: 502)
- `device_id` - Modbus unit ID (default: 2, range: 1-247)
- `base_addr` - Register map base (default: 0, can be 40000)
- `scan_interval` - Polling frequency (default: 60s, range: 30-600)

### Entity Unique IDs

- Sensors: `{serial_number}_{sensor_key}` (e.g., "12345678_accurrent")
- Device identifier: `(DOMAIN, serial_number)`
- Serial number read from inverter is used for all identifiers
- Changing host/IP does not affect entity IDs or historical data

### SunSpec Models

- M1 (Common) - Basic inverter info
- M103 - Three-phase inverter
- M160 - MPPT data (offset detection: 122, 1104, 208)

## Git Workflow

### Commit Messages

- Use conventional commits style
- Always include Claude attribution:

  ```
  <commit message>

  🤖 Generated with [Claude Code](https://claude.com/claude-code)

  Co-Authored-By: Claude <noreply@anthropic.com>
  ```

### Branch Strategy

- Main branch: `master`
- Create tags for releases
- Use pre-release flag for beta versions

## Dependencies

- Home Assistant core
- `pymodbus>=3.11.1` - Modbus TCP client library
- Compatible with HA 2025.9.x+

## Key Files to Review

- `.ruff.toml` - Linting configuration
- `const.py` - Constants and sensor definitions
- `helpers.py` - Shared utilities
- `pymodbus_*.py` - Pymodbus compatibility layer
- `CHANGELOG.md` - Release history overview
- `docs/releases/` - Detailed release notes

## Don't Do

- ❌ Use `hass.data[DOMAIN][entry_id]` - use `runtime_data` instead
- ❌ Shadow Python builtins (ConnectionError, etc.)
- ❌ Use f-strings in logging
- ❌ Forget `await` on async API methods
- ❌ Mix sync/async patterns incorrectly
- ❌ Create documentation files without request
