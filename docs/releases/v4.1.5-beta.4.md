# Release Notes - v4.1.5-beta.4

## What's Changed

### 🔄 Integration Lifecycle Improvements

This release modernizes the integration's unload process to follow the official Home Assistant 2025.3.0+ recommended pattern, fixing resource leaks and improving reliability.

#### Major Refactor: `async_unload_entry()`

- **Follows official HA 2025.3.0+ pattern** from [Config Entry States blog post](https://developers.home-assistant.io/blog/2025/02/19/new-config-entry-states/)
- **Conditional cleanup with walrus operator**: Only cleans up runtime_data (API connection, update listener) if platform unload succeeds
- **Fixed resource leak**: Per-entry resources are now properly cleaned up for all config entries, not just the last one
- **Removed backwards compatibility code** for HA < 2025.3.0
- **Simplified last-entry check**: Uses `async_loaded_entries(DOMAIN)` directly
- **Improved logging**: Better tracking of success/failure paths for debugging

### Technical Details

**Before (problematic):**
```python
# Always cleaned up resources, even if platform unload failed
unload_ok = await async_unload_platforms(...)
await api.close()  # Wrong: cleanup even if unload_ok=False
listener()
```

**After (correct):**
```python
# Only cleanup if platform unload succeeds
if unload_ok := await async_unload_platforms(...):
    await api.close()  # Correct: conditional cleanup
    listener()
```

### Breaking Changes

⚠️ **Requires Home Assistant 2025.3.0 or newer**
- Dropped backwards compatibility with HA < 2025.3.0
- Uses modern config entry state management

### Bug Fixes

- **Fixed resource leak** when multiple config entries exist
  - Previously: Only the last entry being unloaded would close API connections
  - Now: Every entry properly closes its API connection when unloaded
- **Fixed potential errors** when platform unload fails
  - Previously: Would cleanup runtime_data even if entry remained loaded
  - Now: Skips cleanup if unload fails, preventing errors

### Improvements

- Cleaner, more maintainable code (-15 lines)
- Better adherence to HA best practices
- More reliable multi-entry scenarios
- Enhanced debug logging

### Testing

- Test unloading individual config entries with multiple entries configured
- Test reload functionality
- Verify API connections are properly closed for all entries
- Test failure scenarios (platform unload failures)

### Upgrade Notes

This is a **beta release** - please test in a non-production environment first.

- **Required**: Home Assistant 2025.3.0 or newer
- Safe to upgrade from v4.1.5-beta.3
- Fixes will prevent resource leaks in multi-entry setups
- No configuration changes required

**Full Changelog**: https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/compare/v4.1.5-beta.3...v4.1.5-beta.4
