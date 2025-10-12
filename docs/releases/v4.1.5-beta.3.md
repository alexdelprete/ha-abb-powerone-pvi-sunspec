# Release Notes - v4.1.5-beta.3

## What's Changed

### 🐛 Bug Fixes

This release fixes critical bugs in the integration's unload process that could cause errors when removing or reloading the integration.

#### Fixed Issues

- **Fixed KeyError on integration unload** (`__init__.py`)
  - Removed invalid cleanup of `hass.data[DOMAIN][entry_id]` which doesn't exist
  - Integration uses `runtime_data` instead, which is automatically cleaned up
  - Fixes error: `KeyError: '54dcc9b0ac601ef0a7d78ebcd861cc76'`

- **Fixed RuntimeWarning on API connection close** (`__init__.py`)
  - Added missing `await` to `api.close()` coroutine call
  - Fixes warning: `coroutine 'ABBPowerOneFimerAPI.close' was never awaited`

- **Code style improvements** (`helpers.py`)
  - Minor ruff style fixes for code quality

### Technical Details

- All fixes are in the integration lifecycle management
- No breaking changes
- No changes to functionality or features
- Improved error handling and cleanup process

### Testing

- Test integration reload to ensure no KeyError
- Test integration removal to ensure clean shutdown
- No functional changes to inverter communication

### Upgrade Notes

This is a **beta release** - please test in a non-production environment first.

- Safe to upgrade from v4.1.5-beta.1 or v4.1.5-beta.2
- Fixes will prevent errors during integration reload/removal
- No configuration changes required

**Full Changelog**: https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/compare/v4.1.5-beta.2...v4.1.5-beta.3
