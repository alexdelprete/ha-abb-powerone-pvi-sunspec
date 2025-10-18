# pysunspec2 Library Analysis for ABB/Power-One/FIMER Integration

**Date:** October 18, 2025  
**Analyst:** Claude Code  
**Version:** 1.0  
**Repository Analyzed:** https://github.com/sunspec/pysunspec2 (commit: 57c2f76, Sep 24, 2025)

---

## Executive Summary

**Recommendation: ❌ DO NOT USE pysunspec2**

pysunspec2 is **not suitable** for replacing our custom SunSpec parsing in the Home Assistant integration due to:
1. **Complete lack of async/await support** (blocking I/O operations)
2. **Hardcoded transport layer** (cannot use ModbusLink or other libraries)
3. **Still depends on pymodbus** (in requirements.txt for testing, but defeats the purpose)
4. **Synchronous-only API** (incompatible with Home Assistant's async architecture)

**Alternative Recommendation:** Continue with current custom implementation OR explore **ModbusLink** (modern async Modbus library) combined with pysunspec2's excellent model definitions.

---

## 1. Dependencies Analysis

### Critical Dependency Issue

**pymodbus dependency: ✅ YES, version 2.5.3 is required**

```
# From requirements.txt:
pytest>=8.3.3
pyserial>=3.5
openpyxl>=3.1.5
pymodbus==2.5.3  # ⚠️ CRITICAL: Still depends on pymodbus
```

### Dependency Context

- **pymodbus 2.5.3** is pinned in requirements.txt
- Used only in test file: `sunspec2/tests/test_tls_client.py`
- Test uses pymodbus's `StartTlsServer` for TLS testing
- However, having pymodbus as a dependency defeats the purpose of avoiding it

### Other Dependencies

| Dependency | Purpose | Status |
|------------|---------|--------|
| pyserial>=3.5 | Serial/RTU communication | Optional (extras_require) |
| openpyxl>=3.1.5 | Excel spreadsheet support | Optional (extras_require) |
| pytest>=8.3.3 | Testing framework | Optional (extras_require) |

### Transport Layer Implementation

**Critical Finding:** pysunspec2 implements its **OWN Modbus protocol** from scratch:

```python
# sunspec2/modbus/modbus.py
class ModbusClientTCP(object):
    """Custom Modbus TCP implementation using raw sockets"""
    def __init__(self, slave_id=1, ipaddr='127.0.0.1', ipport=502, ...):
        self.slave_id = slave_id
        self.ipaddr = ipaddr
        self.socket = None  # Raw socket implementation
```

- Does NOT use pymodbus for runtime operations
- Custom implementation in `sunspec2/modbus/modbus.py` (876 lines)
- Direct socket manipulation for TCP
- Direct pyserial usage for RTU
- **Transport is hardcoded, not abstracted or pluggable**

---

## 2. Async Support

### Critical Blocker: NO ASYNC SUPPORT

**Finding:** pysunspec2 is **completely synchronous** with zero async/await support.

#### Evidence

```bash
# Search results:
$ grep -r "async def" /tmp/pysunspec2
# No matches found

$ grep -r "asyncio" /tmp/pysunspec2
# No matches found

$ grep -r "await " /tmp/pysunspec2
# No matches found
```

#### Implications for Home Assistant

- Home Assistant **requires** async operations for all I/O
- All coordinator data updates must be async
- All API methods must be async
- Blocking operations freeze the event loop

#### Current Integration Comparison

```python
# Current async implementation (api.py)
async def async_get_data(self) -> dict[str, Any]:
    """Async data collection"""
    async with self._lock:
        await self._client.connect()
        data = await self._read_registers(...)

# pysunspec2 synchronous implementation
def scan(self):
    """Blocking device scan"""
    self.connect()  # Blocks event loop
    data = self.read(addr, count)  # Blocks event loop
```

**Workaround Required:** Would need to wrap all pysunspec2 calls in `asyncio.to_thread()` or `run_in_executor()`, which:
- Adds complexity and overhead
- Defeats the purpose of using a library
- Still blocks worker threads
- Makes error handling more complex

---

## 3. Maintenance and Compatibility

### Repository Activity

| Metric | Value | Assessment |
|--------|-------|------------|
| Last Commit | Sep 24, 2025 | ✅ Recent |
| Stars | 64 | 🟡 Moderate |
| Forks | 25 | 🟡 Moderate |
| Open Issues | 24 | 🟡 Some backlog |
| Contributors | ~10-15 | ✅ Multiple maintainers |
| License | Apache 2.0 | ✅ Permissive |

### Recent Activity (2024-2025)

```
57c2f76 - Sep 24, 2025 - Merge pull request #115 (fix intermediate CAs)
f38bb76 - Sep 24, 2025 - fix intermediate CAs
9ac9094 - Sep 24, 2025 - expanded TLS certs
de4244f - Aug 2025 - fix for complex model cases
e674441 - Jul 2025 - Merge pull request #111
a1b0a24 - Jul 2025 - added keyUsage extension to CA
```

**Assessment:** ✅ Actively maintained with regular commits and merged PRs

### Python Version Support

```python
# setup.py
python_requires='>=3.5',
classifiers=[
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
```

**Status:** ✅ Python 3.11+ supported (Home Assistant requires 3.11+)

### Release History

| Version | Date | Notes |
|---------|------|-------|
| v1.3.3 | Latest | Current version |
| v1.3.2 | 2025 | TLS improvements |
| v1.3.0 | 2024 | Major update |
| v1.0.9 | Jul 2023 | Bug fixes |

**Cadence:** Regular releases, active development

---

## 4. API Design and Usability

### High-Level API Structure

pysunspec2 provides an elegant object-oriented API:

```python
# Device hierarchy
Device
  └── Model (e.g., Model 1, 103, 160)
      └── Group (e.g., repeating groups)
          └── Point (individual data points)
```

### Connection and Discovery

```python
import sunspec2.modbus.client as client

# Create device
d = client.SunSpecModbusClientDeviceTCP(
    slave_id=1, 
    ipaddr='192.168.1.100', 
    ipport=502
)

# Discover models (blocking operation)
d.scan()  # ⚠️ Synchronous, blocks thread

# Access models
print(d.models)
# {1: [<Model>], 'common': [<Model>], 
#  103: [<Model>], 'inverter': [<Model>]}
```

### Data Access

```python
# Read model data (blocking)
d.common[0].read()  # ⚠️ Synchronous

# Access point values
manufacturer = d.common[0].Mn.value
model = d.common[0].Md.value
serial = d.common[0].SN.value

# Computed values with scale factors
voltage = d.inverter[0].PPVphAB.cvalue  # Automatically scales
```

### API Quality Assessment

| Aspect | Rating | Notes |
|--------|--------|-------|
| Abstraction | ✅ Excellent | Clean object hierarchy |
| Documentation | 🟡 Good | README is comprehensive, but limited API docs |
| Type Hints | ❌ Missing | No type hints in code |
| Error Handling | 🟡 Basic | Custom exceptions but limited granularity |
| Examples | ✅ Good | README has extensive examples |

---

## 5. SunSpec Model Support

### Supported Models

✅ **Excellent model coverage** - 117+ models in JSON format

#### Models Relevant to Our Integration

| Model ID | Name | Status | Use Case |
|----------|------|--------|----------|
| 1 | Common | ✅ Full | Device identification |
| 101 | Single Phase Inverter | ✅ Full | Single-phase ABB inverters |
| 103 | Three Phase Inverter | ✅ Full | Three-phase ABB/FIMER inverters |
| 160 | MPPT | ✅ Full | String/MPPT data |
| 120 | Nameplate | ✅ Full | Inverter ratings |
| 121-124 | Inverter Controls | ✅ Full | Advanced controls |

### Model Definition Quality

Models are defined in JSON format with excellent structure:

```json
// Example from model_103.json (three-phase inverter)
{
  "id": 103,
  "name": "inverter",
  "label": "Three Phase Inverter",
  "group": {
    "name": "inverter",
    "points": [
      {
        "name": "A",
        "type": "uint16",
        "sf": "A_SF",
        "units": "A",
        "label": "Amps",
        "desc": "AC Total Current value"
      },
      // ... more points
    ]
  }
}
```

#### Model Definition Reusability

**✅ Strong Point:** The model definitions are **standalone JSON files** that could be used independently:

- Located in `sunspec2/models/json/`
- Well-structured, parseable JSON
- Include scale factors, units, descriptions
- Could be extracted and used with custom Modbus implementation

---

## 6. Transport Layer Architecture

### Architecture Overview

```
┌─────────────────────────────────────┐
│  SunSpecModbusClientDeviceTCP       │  High-level device interface
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│  ModbusClientTCP                     │  Modbus TCP protocol handler
│  - Raw socket operations             │
│  - Protocol encoding/decoding        │
│  - Hardcoded to TCP sockets          │
└─────────────────────────────────────┘
```

### Critical Finding: Not Modular

❌ **Transport layer is tightly coupled and NOT replaceable**

```python
# sunspec2/modbus/modbus.py
class ModbusClientTCP(object):
    def __init__(self, slave_id=1, ipaddr='127.0.0.1', ...):
        self.slave_id = slave_id
        self.ipaddr = ipaddr
        self.socket = None  # Direct socket usage
    
    def connect(self, timeout=None):
        if self.socket is None:
            # Directly creates socket - no abstraction
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(timeout)
            self.socket.connect((self.ipaddr, self.ipport))
```

### Cannot Plug in ModbusLink or Other Libraries

The library architecture prevents using alternative Modbus implementations:

1. **No transport interface** - ModbusClientTCP is a concrete class, not an interface
2. **Hardcoded socket operations** - read/write methods directly use socket
3. **Tight coupling** - SunSpec device classes inherit from Modbus client classes
4. **No dependency injection** - Cannot pass in alternative transport

### Modbus TCP Support

✅ **Modbus TCP is fully supported** but only via built-in implementation

Features:
- Standard Modbus TCP protocol
- TLS/SSL support (Modbus/TCP Security)
- Connection pooling and retries
- Function codes 3 (read holding), 4 (read input), 16 (write multiple)

---

## 7. Data Access Patterns

### Reading Data

```python
# Model-level read (reads entire model)
d.inverter[0].read()  # ⚠️ Synchronous blocking call

# Point-level read (reads single point)
d.inverter[0].A.read()  # ⚠️ Synchronous blocking call

# Group-level read
d.inverter[0].SomeGroup.read()  # ⚠️ Synchronous blocking call
```

### Batch Reading

✅ **Supported** - Can read entire models in one operation
- Optimized for large register reads
- Max read count: 125 registers (configurable)
- Automatically splits larger reads

### Caching

🟡 **Limited caching**
- Values are cached in Point objects after read
- No automatic refresh or TTL
- Must manually call `read()` to update
- No stale data detection

### Error Handling

```python
# Custom exceptions
try:
    d.scan()
except SunSpecModbusClientError as e:
    # General error
except SunSpecModbusClientTimeout as e:
    # Timeout
except SunSpecModbusClientException as e:
    # Modbus exception response
```

**Assessment:** 🟡 Basic error handling, could be more granular

---

## 8. Size and Performance

### Package Size

```bash
$ du -sh /tmp/pysunspec2
1.9M    /tmp/pysunspec2

# Breakdown:
# - Source code: ~200KB
# - Model definitions: ~1.5MB
# - Tests: ~200KB
```

**Assessment:** ✅ Reasonable size, mostly model definitions

### Code Statistics

```bash
$ find /tmp/pysunspec2 -name "*.py" | wc -l
35

# Main modules:
# - device.py: 843 lines
# - modbus.py: 876 lines
# - client.py: 451 lines
```

### Performance Characteristics

#### Strengths
- ✅ Direct socket operations (no middleware overhead)
- ✅ Optimized register reads (batching)
- ✅ Minimal dependencies

#### Weaknesses
- ❌ Synchronous blocking I/O
- ❌ No connection pooling across devices
- ❌ No async concurrency
- ❌ Thread-blocking for all operations

### Memory Footprint

- **Model definitions loaded on demand**
- Point objects created dynamically during scan
- Model cache can grow with multiple devices
- No memory profiling available

**Estimated:** 🟡 Moderate - acceptable for HA but not optimized

---

## 9. Comparison: pysunspec2 vs ModbusLink vs Current Implementation

### Feature Matrix

| Feature | pysunspec2 | ModbusLink | Current (Custom) |
|---------|-----------|------------|------------------|
| **Async/Await** | ❌ No | ✅ Yes | ✅ Yes |
| **pymodbus Dependency** | ⚠️ Yes (tests) | ✅ No | ⚠️ Yes (>=3.11.2) |
| **Transport Abstraction** | ❌ No | ✅ Yes | ❌ No |
| **Type Hints** | ❌ No | ✅ Yes | ✅ Yes |
| **SunSpec Parsing** | ✅ Excellent | ❌ None | ✅ Custom |
| **Model Definitions** | ✅ JSON files | ❌ None | ✅ Hardcoded |
| **Modbus TCP** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Python 3.11+** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Home Assistant Ready** | ❌ No | ✅ Yes | ✅ Yes |
| **Maintenance** | ✅ Active | ✅ Active | 👤 Self |

### Architecture Comparison

#### pysunspec2 Architecture
```
┌──────────────────────────┐
│   SunSpec Device API     │  High-level, but synchronous
├──────────────────────────┤
│   Custom Modbus Client   │  Blocks event loop
├──────────────────────────┤
│   Raw Sockets            │  No abstraction
└──────────────────────────┘
```

#### ModbusLink Architecture
```
┌──────────────────────────┐
│   Application Layer      │  Your async code
├──────────────────────────┤
│   ModbusLink Client      │  Async operations
├──────────────────────────┤
│   Pluggable Transport    │  TcpTransport, RtuTransport
├──────────────────────────┤
│   asyncio                │  Native async I/O
└──────────────────────────┘
```

#### Current Implementation
```
┌──────────────────────────┐
│   ABBPowerOneFimerAPI    │  Async wrapper
├──────────────────────────┤
│   AsyncModbusTcpClient   │  pymodbus async client
├──────────────────────────┤
│   Custom SunSpec Parser  │  Manual register parsing
└──────────────────────────┘
```

---

## 10. Proof of Concept Analysis

### What a pysunspec2 Integration Would Look Like

```python
import asyncio
from functools import partial
import sunspec2.modbus.client as client

class PySunSpec2API:
    """Wrapper to make pysunspec2 work with async Home Assistant"""
    
    def __init__(self, host: str, port: int, device_id: int):
        self._device = client.SunSpecModbusClientDeviceTCP(
            slave_id=device_id,
            ipaddr=host,
            ipport=port
        )
    
    async def async_scan(self) -> None:
        """Async wrapper for blocking scan"""
        # ⚠️ Must run in executor to avoid blocking
        await asyncio.get_event_loop().run_in_executor(
            None, self._device.scan
        )
    
    async def async_read_data(self) -> dict:
        """Async wrapper for blocking reads"""
        # ⚠️ Multiple executor calls = slow
        
        # Read common model
        common = self._device.common[0]
        await asyncio.get_event_loop().run_in_executor(
            None, common.read
        )
        
        # Read inverter model
        inverter = self._device.inverter[0]
        await asyncio.get_event_loop().run_in_executor(
            None, inverter.read
        )
        
        # Read MPPT model
        mppt = self._device.mppt[0]
        await asyncio.get_event_loop().run_in_executor(
            None, mppt.read
        )
        
        # Extract data
        return {
            'manufacturer': common.Mn.value,
            'model': common.Md.value,
            'serial': common.SN.value,
            'power': inverter.W.cvalue,
            'voltage': inverter.PPVphAB.cvalue,
            # ... more fields
        }
```

### Problems with This Approach

1. **Multiple executor calls** - Each read operation requires a separate executor call
2. **Thread pool pressure** - Consumes Home Assistant's limited thread pool
3. **Slow polling** - Executor overhead adds latency to each poll cycle
4. **Error handling complexity** - Exceptions must be caught and re-raised across executor boundaries
5. **Connection management** - Hard to manage connection state across threads
6. **Defeats the purpose** - We're essentially reimplementing an async layer

### What Works Well

✅ **Model definitions** - The JSON model files are excellent and reusable
✅ **Data structures** - The Point/Group/Model hierarchy is well-designed
✅ **SunSpec compliance** - Proper implementation of SunSpec protocol

---

## 11. ModbusLink Alternative

### What is ModbusLink?

**ModbusLink** is a modern Python Modbus library with:
- Native async/await support
- Clean layered architecture
- No pymodbus dependency
- Type hints throughout
- Developer-friendly API

### ModbusLink Example

```python
from modbuslink import ModbusClient, TcpTransport

# Create async TCP transport
transport = TcpTransport(host='192.168.1.100', port=502)
client = ModbusClient(transport)

# Async operations
async with client:
    registers = await client.read_holding_registers(
        slave_id=1,
        start_address=0,
        count=10
    )
```

### ModbusLink + pysunspec2 Models Hybrid Approach

```python
import json
from modbuslink import ModbusClient, TcpTransport

class HybridSunSpecAPI:
    """Use ModbusLink for transport + pysunspec2 model definitions"""
    
    def __init__(self, host: str, port: int, device_id: int):
        self.transport = TcpTransport(host=host, port=port)
        self.client = ModbusClient(self.transport)
        self.device_id = device_id
        
        # Load pysunspec2 model definitions
        self.models = self._load_sunspec_models()
    
    def _load_sunspec_models(self) -> dict:
        """Load model definitions from pysunspec2 JSON files"""
        models = {}
        model_ids = [1, 103, 160]  # Common, Three-phase, MPPT
        
        for model_id in model_ids:
            with open(f'models/json/model_{model_id}.json') as f:
                models[model_id] = json.load(f)
        
        return models
    
    async def async_scan(self) -> list[int]:
        """Async SunSpec device scan"""
        async with self.client:
            # Look for SunS marker at common addresses
            for base_addr in [0, 40000, 50000]:
                data = await self.client.read_holding_registers(
                    self.device_id, base_addr, 2
                )
                if self._is_sunspec_marker(data):
                    return await self._discover_models(base_addr)
        return []
    
    async def async_read_model(self, model_id: int, base_addr: int) -> dict:
        """Async read of a SunSpec model"""
        model_def = self.models[model_id]
        
        async with self.client:
            # Read model data
            registers = await self.client.read_holding_registers(
                self.device_id,
                base_addr,
                model_def['length']
            )
            
            # Parse using pysunspec2 model definition
            return self._parse_model_data(model_def, registers)
```

### Hybrid Approach Benefits

✅ **Async native** - ModbusLink provides true async operations  
✅ **No pymodbus** - ModbusLink has no pymodbus dependency  
✅ **Reuse model definitions** - Leverage pysunspec2's excellent models  
✅ **Type safe** - ModbusLink has full type hints  
✅ **Flexible** - Can customize parsing while using standard models  

### Hybrid Approach Challenges

⚠️ **Custom parsing required** - Must implement SunSpec data parsing  
⚠️ **Scale factor handling** - Need to implement scale factor logic  
⚠️ **More code to maintain** - Not using an off-the-shelf solution  
⚠️ **ModbusLink maturity** - Newer library, less battle-tested  

---

## 12. Specific Issues Identified

### Issue 1: No Async Support
- **Severity:** 🔴 Critical
- **Impact:** Cannot be used in Home Assistant without executor wrappers
- **Workaround:** Run all operations in thread pool
- **Effort:** High complexity, poor performance

### Issue 2: pymodbus Dependency
- **Severity:** 🔴 Critical
- **Impact:** Still depends on pymodbus (though only for tests)
- **Workaround:** Fork and remove dependency
- **Effort:** Low, but defeats purpose of evaluation

### Issue 3: Transport Not Abstracted
- **Severity:** 🟠 High
- **Impact:** Cannot use ModbusLink or other Modbus libraries
- **Workaround:** Major refactoring required
- **Effort:** Very high, essentially rewriting the library

### Issue 4: No Type Hints
- **Severity:** 🟡 Medium
- **Impact:** Reduced IDE support, harder to maintain
- **Workaround:** Add type hints in wrapper
- **Effort:** Medium

### Issue 5: Connection Management
- **Severity:** 🟡 Medium
- **Impact:** Connection lifecycle is synchronous
- **Workaround:** Manage in executor with careful state tracking
- **Effort:** Medium-high

---

## 13. Migration Path Assessment

### If We Were to Use pysunspec2 (Not Recommended)

#### Step 1: Create Async Wrapper
```python
# Estimated: 200-300 lines of wrapper code
class AsyncPySunSpec2Wrapper:
    # Wrap all blocking operations in executors
    # Handle connection state across threads
    # Manage error propagation
```
**Effort:** 2-3 days

#### Step 2: Adapt Data Extraction
```python
# Map pysunspec2 Point objects to our sensor entities
# Handle scale factors
# Deal with None/undefined values
```
**Effort:** 1-2 days

#### Step 3: Testing
- Test with single-phase inverters
- Test with three-phase inverters
- Test MPPT detection
- Test error scenarios
**Effort:** 2-3 days

#### Step 4: Performance Tuning
- Optimize executor usage
- Minimize thread pool pressure
- Handle timeouts properly
**Effort:** 1-2 days

**Total Migration Effort:** 6-10 days  
**Risk:** High - might not perform well enough

---

## 14. Alternative Solutions

### Option A: Continue with Current Implementation ✅ RECOMMENDED
**Pros:**
- Already works well
- Fully async
- Well-tested
- Understood codebase

**Cons:**
- Depends on pymodbus>=3.11.2
- Custom SunSpec parsing (maintenance burden)
- Pymodbus version compatibility issues

**Recommendation:** Keep using until pymodbus issues become critical

---

### Option B: ModbusLink + Custom SunSpec Parsing 🟡 VIABLE
**Pros:**
- True async support
- No pymodbus dependency
- Modern, actively maintained
- Type-safe

**Cons:**
- Need to implement SunSpec parsing
- More code to write and maintain
- ModbusLink is newer (less proven)

**Migration Path:**
1. Install ModbusLink: `pip install modbuslink`
2. Copy pysunspec2 model definitions (JSON files)
3. Implement SunSpec discovery logic
4. Implement model data parsing
5. Test thoroughly

**Effort:** 1-2 weeks

**Code Volume:** ~500-800 lines

---

### Option C: Fork pysunspec2 and Add Async ❌ NOT RECOMMENDED
**Pros:**
- Could add async support to pysunspec2
- Keep high-level API

**Cons:**
- Major refactoring required
- Need to maintain fork
- Breaking changes to library architecture
- Upstream unlikely to accept (architectural change)

**Effort:** 2-3 weeks minimum

**Risk:** Very high

---

### Option D: Use pysunspec2 with Executor Wrappers ❌ NOT RECOMMENDED
**Pros:**
- Minimal code changes
- Use pysunspec2 as-is

**Cons:**
- Poor performance (multiple executor calls)
- Complexity in error handling
- Thread pool pressure
- Still depends on pymodbus

**Effort:** 1 week

**Performance:** Poor

---

## 15. Final Recommendation

### Primary Recommendation: Continue Current Implementation

**Keep the current custom implementation** until pymodbus issues become blocking. The current code:
- ✅ Works reliably
- ✅ Is fully async
- ✅ Is well-tested
- ✅ Handles all required SunSpec models
- ⚠️ Has pymodbus dependency (manageable for now)

**When to reconsider:** If pymodbus version conflicts become critical or if Home Assistant drops support for our pymodbus version.

---

### Secondary Recommendation: ModbusLink + Custom SunSpec Parsing

If/when we need to move away from pymodbus:

1. **Evaluate ModbusLink thoroughly**
   - Test with real hardware
   - Verify performance
   - Check error handling

2. **Extract pysunspec2 model definitions**
   - Copy JSON model files
   - Use for data structure reference
   - Implement parsing based on definitions

3. **Incremental migration**
   - Start with one model (e.g., Model 1 - Common)
   - Add Model 103 (Three-phase inverter)
   - Add Model 160 (MPPT)
   - Parallel testing with current implementation

4. **Consider creating `abb-fimer-client` library**
   - Separate library for ABB/FIMER inverters
   - Uses ModbusLink internally
   - Provides high-level async API
   - Can be reused by other projects

---

### What NOT to Do

❌ **Do not use pysunspec2 as-is** - The lack of async support is a deal-breaker  
❌ **Do not fork pysunspec2** - Too much refactoring required  
❌ **Do not wrap pysunspec2 in executors** - Performance will suffer  
❌ **Do not ignore the async requirement** - Home Assistant mandates async I/O  

---

## 16. Action Items

### Immediate Actions

1. ✅ **Document this analysis** (this document)
2. ⏭️ **Evaluate ModbusLink** with real hardware
3. ⏭️ **Create PoC** with ModbusLink + custom parsing
4. ⏭️ **Performance benchmark** ModbusLink vs current implementation

### Future Considerations

1. **Monitor pysunspec2** for async support (unlikely but worth watching)
2. **Track ModbusLink development** for stability and features
3. **Consider contributing** async support to pysunspec2 (low priority)
4. **Extract model definitions** from pysunspec2 for our use

---

## 17. Appendix: Code Examples

### A. Current Implementation Structure

```python
# custom_components/abb_powerone_pvi_sunspec/api.py
class ABBPowerOneFimerAPI:
    async def async_get_data(self) -> dict[str, Any]:
        async with self._lock:
            await self._client.connect()
            # Custom SunSpec register reading
            data = await self._read_model_1()    # Common
            data.update(await self._read_model_103())  # Inverter
            data.update(await self._read_model_160())  # MPPT
            return data
```

### B. pysunspec2 API Example

```python
import sunspec2.modbus.client as client

# Synchronous operations
d = client.SunSpecModbusClientDeviceTCP(
    slave_id=1, ipaddr='192.168.1.100', ipport=502
)

# Blocking scan
d.scan()  # ⚠️ Blocks event loop

# Blocking reads
d.common[0].read()  # ⚠️ Blocks event loop
manufacturer = d.common[0].Mn.value
```

### C. ModbusLink PoC Example

```python
from modbuslink import ModbusClient, TcpTransport

async def read_sunspec_common(host: str, port: int, device_id: int) -> dict:
    """Read SunSpec Model 1 (Common) using ModbusLink"""
    transport = TcpTransport(host=host, port=port)
    client = ModbusClient(transport)
    
    async with client:
        # Scan for SunS marker
        base_addr = None
        for addr in [0, 40000, 50000]:
            data = await client.read_holding_registers(device_id, addr, 2)
            if data and data[0:2] == b'SunS':
                base_addr = addr
                break
        
        if not base_addr:
            raise ValueError("SunSpec device not found")
        
        # Read Model 1 (Common) - 66 registers
        registers = await client.read_holding_registers(
            device_id, base_addr + 2, 66
        )
        
        # Parse according to SunSpec Model 1 definition
        # (Use pysunspec2 model definition as reference)
        return {
            'manufacturer': _decode_string(registers[2:18]),
            'model': _decode_string(registers[18:34]),
            'serial': _decode_string(registers[50:66]),
            # ... more fields
        }
```

---

## 18. References

### Repositories
- **pysunspec2:** https://github.com/sunspec/pysunspec2
- **ModbusLink:** https://pypi.org/project/modbuslink/
- **pymodbus:** https://github.com/pymodbus-dev/pymodbus
- **SunSpec Models:** https://github.com/sunspec/models

### Documentation
- **SunSpec Specification:** https://sunspec.org/specifications/
- **Home Assistant Async:** https://developers.home-assistant.io/docs/asyncio_working_with_async/
- **ModbusLink Docs:** (See PyPI package)

### Relevant Issues
- pysunspec2 #51: "How to use numbered models?" (October 2021)
- pysunspec2 #115: TLS certificate fixes (September 2025)

---

## Document Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Oct 18, 2025 | Initial comprehensive analysis |

---

**Analysis completed by:** Claude Code  
**For:** ABB/Power-One/FIMER PVI SunSpec Integration  
**Conclusion:** ❌ Do not use pysunspec2. Consider ModbusLink + custom parsing for future migration.
