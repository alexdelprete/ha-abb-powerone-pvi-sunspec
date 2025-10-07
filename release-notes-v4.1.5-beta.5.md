# Release Notes - v4.1.5-beta.5

## What's Changed

### 🐛 Bug Fixes

#### Fixed Update Listener Management
- **Fixed duplicate cleanup error** that caused "Error unloading entry" during integration unload
  - Removed incorrect `async_on_unload()` registration that caused double cleanup
  - Now follows official HA pattern: `async_on_unload(add_update_listener())` for automatic cleanup
- **Fixed incorrect `await` usage** on synchronous `@callback` methods
  - `async_reload_entry`: Removed incorrect `await` on `async_schedule_reload()`
  - `async_update_device_registry`: Changed from `async def` to `@callback def`

### ♻️ Refactoring

#### Update Listener Pattern Modernization
- **Refactored to official HA pattern** from [Config Entry Options docs](https://developers.home-assistant.io/docs/config_entries_options_flow_handler/#signal-updates)
- **Removed `update_listener` from RuntimeData** (no longer needed with automatic cleanup)
- **Removed manual cleanup** in `async_unload_entry` (handled automatically by HA)
- **Removed unused `hass.data[DOMAIN]`** initialization (using `runtime_data` pattern)

#### Callback Optimizations
- **`async_reload_entry`**: Changed from `async def` to `@callback def`
  - Removed incorrect `await` on `async_schedule_reload()` (it's synchronous)
  - Added `@callback` decorator and return type hint
- **`async_update_device_registry`**: Changed from `async def` to `@callback def`
  - Only calls synchronous methods (`async_get`, `async_get_or_create`)
  - Performance improvement and better type accuracy
  - Fixed typo: "Regiser" → "Register"

#### Code Cleanup
- Removed unused `Callable` import
- Simplified RuntimeData dataclass (only stores coordinator)
- Cleaner, more maintainable code following HA best practices

### 📦 Dependencies

- **Bumped ruff** from 0.13.3 to 0.14.0 (#311)
- **Bumped softprops/action-gh-release** from 2.3.4 to 2.4.0 (#310)

### Technical Details

#### Before (Problematic)
```python
# Setup
update_listener = config_entry.add_update_listener(async_reload_entry)
config_entry.async_on_unload(update_listener)  # Wrong: registers removal callable
config_entry.runtime_data = RuntimeData(coordinator, update_listener)

# Unload
config_entry.runtime_data.update_listener()  # Manual cleanup
# Then HA tries to call it again via async_on_unload → ERROR!
```

#### After (Correct)
```python
# Setup
config_entry.runtime_data = RuntimeData(coordinator)
config_entry.async_on_unload(
    config_entry.add_update_listener(async_reload_entry)
)  # Correct: automatic cleanup

# Unload
# Nothing needed - HA handles cleanup automatically!
```

### Breaking Changes

None - this is a bug fix and optimization release.

### Improvements

- **Fixed integration unload errors** - no more "Error unloading entry" messages
- **Better performance** - fewer async context switches with `@callback` optimizations
- **Cleaner code** - follows official HA patterns and best practices
- **More maintainable** - automatic cleanup reduces error-prone manual management
- **Type safety** - proper use of `@callback` vs `async def`

### Testing Recommendations

- Test integration reload (Settings → Devices & Services → Configure → Reload)
- Test integration removal (verify no errors in logs)
- Test with multiple config entries
- Verify update listener triggers on options changes

### Upgrade Notes

This is a **beta release** - please test in a non-production environment first.

- Safe to upgrade from v4.1.5-beta.4
- Fixes critical unload errors introduced in beta.4
- No configuration changes required
- All changes are internal improvements

### Known Issues

None

### Commits Since v4.1.5-beta.4

- `8ad1461` - Optimize async_update_device_registry: change to @callback
- `04a14ee` - Fix async_reload_entry: use callback decorator and remove await
- `0a9575d` - Style fixes by ruff
- `a106406` - Refactor update_listener to follow official HA pattern
- `2cd12bf` - Bump ruff from 0.13.3 to 0.14.0 (#311)
- `83f327d` - Bump softprops/action-gh-release from 2.3.4 to 2.4.0 (#310)
- `7b36fc5` - Fix async_unload_entry: remove duplicate update_listener cleanup

**Full Changelog**: https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/compare/v4.1.5-beta.4...v4.1.5-beta.5
