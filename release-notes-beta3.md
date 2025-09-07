# ⚠️ BETA RELEASE - NOT FOR PRODUCTION USE

This is a pre-release version for testing purposes only. Please use in a test environment before deploying to production.

## What's Changed in v4.0.1-beta.3

### 🔧 Critical Fix: Backward Compatibility

This beta release fixes the TypeError that occurred when upgrading from older versions that used `slave_id` in their configuration.

### Bug Fixes in this release
- **Fixed**: TypeError when loading existing configurations with `slave_id` instead of `device_id`
- **Added**: Automatic migration from `slave_id` to `device_id` for existing installations
- **Added**: Backward compatibility handling in coordinator and config flow
- **Updated**: Config entry version to 2 with proper migration support

### Features from v4.0.1-beta.2
- ✅ Full compatibility with pymodbus 3.11.x (HomeAssistant 2025.9.x ready)
- ✅ Updated all Modbus API calls to use `device_id` parameter instead of deprecated `slave`
- ✅ Improved timeout handling logic for better connection stability
- ✅ Raised temperature threshold to 70°C for better compatibility
- ✅ Fixed type hints for timeout parameters

### Dependencies
- **Updated pymodbus requirement to >=3.11.1** (matching HomeAssistant 2025.9.x)

### Migration Notes
- Existing configurations will be automatically migrated from `slave_id` to `device_id`
- No manual intervention required
- Configuration remains backward compatible

### 🧪 Testing Required
**This is a BETA release. Please:**
- Test with HomeAssistant 2025.9.x
- Verify your inverter communication works correctly
- Test upgrading from older versions
- Report any issues to the issue tracker
- DO NOT use in production until thoroughly tested

### Known Limitations
- This is a beta release and may contain bugs
- Not recommended for production use
- Requires testing with various inverter models

**Full Changelog**: https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/compare/v4.0.1-beta.2...v4.0.1-beta.3