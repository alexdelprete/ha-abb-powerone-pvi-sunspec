# ⚠️ BETA RELEASE - NOT FOR PRODUCTION USE

This is a pre-release version for testing purposes only. Please use in a test environment before deploying to production.

## What's Changed

### 🚀 Major Update: pymodbus 3.11.x Compatibility

This beta release ensures full compatibility with HomeAssistant 2025.9.x which uses pymodbus 3.11.x.

### ⚠️ Breaking Changes
- **IMPORTANT**: This version updates all Modbus communication to use the new pymodbus 3.10+ API
- All `slave` parameters have been replaced with `device_id` throughout the codebase
- Configuration remains backward compatible - no user action required

### Features & Improvements
- ✅ Full compatibility with pymodbus 3.11.x (HomeAssistant 2025.9.x ready)
- ✅ Updated all Modbus API calls to use `device_id` parameter instead of deprecated `slave`
- ✅ Improved timeout handling logic for better connection stability
- ✅ Raised temperature threshold to 70°C for better compatibility
- ✅ Fixed type hints for timeout parameters

### Bug Fixes
- Fixed ConnectionError timeout type hint to accept float values
- Removed unused MIN_TIMEOUT_BUFFER constant
- Improved error handling with ModbusError exceptions

### Dependencies
- **Updated pymodbus requirement to >=3.11.1** (matching HomeAssistant 2025.9.x)
- Bumped various development dependencies (ruff, actions/checkout, actions/setup-python)

### Technical Changes
- Renamed all internal variables from `slave_id` to `device_id`
- Updated all constants: `CONF_SLAVE_ID` → `CONF_DEVICE_ID`, etc.
- Updated function names: `_validate_slave_id` → `_validate_device_id`
- Updated translations to use "device" terminology
- Updated documentation to reflect new terminology

### 🧪 Testing Required
**This is a BETA release. Please:**
- Test with HomeAssistant 2025.9.x
- Verify your inverter communication works correctly
- Report any issues to the issue tracker
- DO NOT use in production until thoroughly tested

### Known Limitations
- This is a beta release and may contain bugs
- Not recommended for production use
- Requires testing with various inverter models

**Full Changelog**: https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/compare/v4.0.1-beta.1...v4.0.1-beta.2