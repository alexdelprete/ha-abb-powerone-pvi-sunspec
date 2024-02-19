"""Constants for ABB Power-One PVI SunSpec.

https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec
"""

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)

# Base component constants
NAME = "ABB/Power-One/FIMER PVI SunSpec ModBus TCP"
DOMAIN = "abb_powerone_pvi_sunspec"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "3.0.0"
ATTRIBUTION = "by @alexdelprete"
ISSUE_URL = "https://github.com/alexdelprete/ha-abb-powerone-pvi-sunspec/issues"

# Icons
ICON = "mdi:format-quote-close"

# Device classes
BINARY_SENSOR_DEVICE_CLASS = "connectivity"

# Platforms
SENSOR = "sensor"
PLATFORMS = [
    "sensor",
]
UPDATE_LISTENER = "update_listener"
DATA = "data"

# Configuration and options
CONF_NAME = "name"
CONF_HOST = "host"
CONF_PORT = "port"
CONF_SLAVE_ID = "slave_id"
CONF_BASE_ADDR = "base_addr"
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_NAME = "ABB Inverter"
DEFAULT_PORT = 502
DEFAULT_SLAVE_ID = 2
DEFAULT_BASE_ADDR = 0
DEFAULT_SCAN_INTERVAL = 60
MIN_SCAN_INTERVAL = 30
STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
{ATTRIBUTION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""

# Sensors for all inverters
SENSOR_TYPES_COMMON = {
    "Manufacturer": [
        "Manufacturer",
        "comm_manufact",
        None,
        "mdi:information-outline",
        None,
        None,
    ],
    "Model": ["Model", "comm_model", None, "mdi:information-outline", None, None],
    "Options": ["Options", "comm_options", None, "mdi:information-outline", None, None],
    "Version": [
        "Firmware Version",
        "comm_version",
        None,
        "mdi:information-outline",
        None,
        None,
    ],
    "Serial": ["Serial", "comm_sernum", None, "mdi:information-outline", None, None],
    "Inverter_Type": [
        "Inverter Type",
        "invtype",
        None,
        "mdi:information-outline",
        None,
        None,
    ],
    "AC_Current": [
        "AC Current",
        "accurrent",
        UnitOfElectricCurrent.AMPERE,
        "mdi:current-ac",
        SensorDeviceClass.CURRENT,
        SensorStateClass.MEASUREMENT,
    ],
    "AC_VoltageAN": [
        "AC Voltage AN",
        "acvoltagean",
        UnitOfElectricPotential.VOLT,
        "mdi:lightning-bolt",
        SensorDeviceClass.VOLTAGE,
        SensorStateClass.MEASUREMENT,
    ],
    "AC_Power": [
        "AC Power",
        "acpower",
        UnitOfPower.WATT,
        "mdi:solar-power",
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
    ],
    "AC_Frequency": [
        "AC Frequency",
        "acfreq",
        UnitOfFrequency.HERTZ,
        "mdi:sine-wave",
        SensorDeviceClass.FREQUENCY,
        SensorStateClass.MEASUREMENT,
    ],
    "DC_Power": [
        "DC Power",
        "dcpower",
        UnitOfPower.WATT,
        "mdi:solar-power",
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
    ],
    "Total_Energy": [
        "Total Energy",
        "totalenergy",
        UnitOfEnergy.WATT_HOUR,
        "mdi:solar-power",
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
    ],
    "Status": [
        "Operating State",
        "status",
        None,
        "mdi:information-outline",
        None,
        None,
    ],
    "Status_Vendor": [
        "Vendor Operating State",
        "statusvendor",
        None,
        "mdi:information-outline",
        None,
        None,
    ],
    "Temp_Cab": [
        "Ambient Temperature",
        "tempcab",
        UnitOfTemperature.CELSIUS,
        "mdi:temperature-celsius",
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ],
    "Temp_Oth": [
        "Inverter Temperature",
        "tempoth",
        UnitOfTemperature.CELSIUS,
        "mdi:temperature-celsius",
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ],
    "MPPT_Count": [
        "MPPT Count",
        "mppt_nr",
        None,
        "mdi:information-outline",
        None,
        None,
    ],
}

# Sensors for single phase inverters, apparently does not have any specific sensors
SENSOR_TYPES_SINGLE_PHASE = {}

# Sensors for three phase inverters
SENSOR_TYPES_THREE_PHASE = {
    "AC_CurrentA": [
        "AC Current A",
        "accurrenta",
        UnitOfElectricCurrent.AMPERE,
        "mdi:current-ac",
        SensorDeviceClass.CURRENT,
        SensorStateClass.MEASUREMENT,
    ],
    "AC_CurrentB": [
        "AC Current B",
        "accurrentb",
        UnitOfElectricCurrent.AMPERE,
        "mdi:current-ac",
        SensorDeviceClass.CURRENT,
        SensorStateClass.MEASUREMENT,
    ],
    "AC_CurrentC": [
        "AC Current C",
        "accurrentc",
        UnitOfElectricCurrent.AMPERE,
        "mdi:current-ac",
        SensorDeviceClass.CURRENT,
        SensorStateClass.MEASUREMENT,
    ],
    "AC_VoltageAB": [
        "AC Voltage AB",
        "acvoltageab",
        UnitOfElectricPotential.VOLT,
        "mdi:lightning-bolt",
        SensorDeviceClass.VOLTAGE,
        SensorStateClass.MEASUREMENT,
    ],
    "AC_VoltageBC": [
        "AC Voltage BC",
        "acvoltagebc",
        UnitOfElectricPotential.VOLT,
        "mdi:lightning-bolt",
        SensorDeviceClass.VOLTAGE,
        SensorStateClass.MEASUREMENT,
    ],
    "AC_VoltageCA": [
        "AC Voltage CA",
        "acvoltageca",
        UnitOfElectricPotential.VOLT,
        "mdi:lightning-bolt",
        SensorDeviceClass.VOLTAGE,
        SensorStateClass.MEASUREMENT,
    ],
    "AC_VoltageBN": [
        "AC Voltage BN",
        "acvoltagebn",
        UnitOfElectricPotential.VOLT,
        "mdi:lightning-bolt",
        SensorDeviceClass.VOLTAGE,
        SensorStateClass.MEASUREMENT,
    ],
    "AC_VoltageCN": [
        "AC Voltage CN",
        "acvoltagecn",
        UnitOfElectricPotential.VOLT,
        "mdi:lightning-bolt",
        SensorDeviceClass.VOLTAGE,
        SensorStateClass.MEASUREMENT,
    ],
}

# Sensors for single mppt inverters
SENSOR_TYPES_SINGLE_MPPT = {
    "DC_Curr": [
        "DC Current",
        "dccurr",
        UnitOfElectricCurrent.AMPERE,
        "mdi:current-ac",
        SensorDeviceClass.CURRENT,
        SensorStateClass.MEASUREMENT,
    ],
    "DC_Volt": [
        "DC Voltage",
        "dcvolt",
        UnitOfElectricPotential.VOLT,
        "mdi:lightning-bolt",
        SensorDeviceClass.VOLTAGE,
        SensorStateClass.MEASUREMENT,
    ],
}

# Sensors for single dual inverters
SENSOR_TYPES_DUAL_MPPT = {
    "DC1_Curr": [
        "DC1 Current",
        "dc1curr",
        UnitOfElectricCurrent.AMPERE,
        "mdi:current-ac",
        SensorDeviceClass.CURRENT,
        SensorStateClass.MEASUREMENT,
    ],
    "DC1_Volt": [
        "DC1 Voltage",
        "dc1volt",
        UnitOfElectricPotential.VOLT,
        "mdi:lightning-bolt",
        SensorDeviceClass.VOLTAGE,
        SensorStateClass.MEASUREMENT,
    ],
    "DC1_Power": [
        "DC1 Power",
        "dc1power",
        UnitOfPower.WATT,
        "mdi:solar-power",
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
    ],
    "DC2_Curr": [
        "DC2 Current",
        "dc2curr",
        UnitOfElectricCurrent.AMPERE,
        "mdi:current-ac",
        SensorDeviceClass.CURRENT,
        SensorStateClass.MEASUREMENT,
    ],
    "DC2_Volt": [
        "DC2 Voltage",
        "dc2volt",
        UnitOfElectricPotential.VOLT,
        "mdi:lightning-bolt",
        SensorDeviceClass.VOLTAGE,
        SensorStateClass.MEASUREMENT,
    ],
    "DC2_Power": [
        "DC2 Power",
        "dc2power",
        UnitOfPower.WATT,
        "mdi:solar-power",
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
    ],
}

INVERTER_TYPE = {101: "Single Phase", 103: "Three Phase", 999: "Unknown"}

DEVICE_GLOBAL_STATUS = {
    0: "Sending Parameters",
    1: "Wait Sun/Grid",
    2: "Checking Grid",
    3: "Measuring Riso",
    4: "DcDc Start",
    5: "Inverter Start",
    6: "Run",
    7: "Recovery",
    8: "Pause",
    9: "Ground Fault",
    10: "OTH Fault",
    11: "Address Setting",
    12: "Self Test",
    13: "Self Test Fail",
    14: "Sensor Test + Measure Riso",
    15: "Leak Fault",
    16: "Waiting for manual reset",
    17: "Internal Error E026",
    18: "Internal Error E027",
    19: "Internal Error E028",
    20: "Internal Error E029",
    21: "Internal Error E030",
    22: "Sending Wind Table",
    23: "Failed Sending table",
    24: "UTH Fault",
    25: "Remote OFF",
    26: "Interlock Fail",
    27: "Executing Autotest",
    30: "Waiting Sun",
    31: "Temperature Fault",
    32: "Fan Staucked",
    33: "Int. Com. Fault",
    34: "Slave Insertion",
    35: "DC Switch Open",
    36: "TRAS Switch Open",
    37: "MASTER Exclusion",
    38: "Auto Exclusion",
    98: "Erasing Internal EEprom",
    99: "Erasing External EEprom",
    100: "Counting EEprom",
    101: "Freeze",
    116: "Standby",
    200: "Dsp Programming",
    999: "Unknown",
}

DEVICE_STATUS = {
    0: "Stand By",
    1: "Checking Grid",
    2: "Run",
    3: "Bulk OV",
    4: "Out OC",
    5: "IGBT Sat",
    6: "Bulk UV",
    7: "Degauss Error",
    8: "No Parameters",
    9: "Bulk Low",
    10: "Grid OV",
    11: "Communication Error",
    12: "Degaussing",
    13: "Starting",
    14: "Bulk Cap Fail",
    15: "Leak Fail",
    16: "DcDc Fail",
    17: "Ileak Sensor Fail",
    18: "SelfTest: relay inverter",
    19: "SelfTest: wait for sensor test",
    20: "SelfTest: test relay DcDc + sensor",
    21: "SelfTest: relay inverter fail",
    22: "SelfTest timeout fail",
    23: "SelfTest: relay DcDc fail",
    24: "Self Test 1",
    25: "Waiting self test start",
    26: "Dc Injection",
    27: "Self Test 2",
    28: "Self Test 3",
    29: "Self Test 4",
    30: "Internal Error",
    31: "Internal Error",
    40: "Forbidden State",
    41: "Input UC",
    42: "Zero Power",
    43: "Grid Not Present",
    44: "Waiting Start",
    45: "MPPT",
    46: "Grid Fail",
    47: "Input OC",
    255: "Inverter Dsp not programmed",
    999: "Unkown",
}

DEVICE_MODEL = {
    0: "UNO-DM-3.3-TL-PLUS",
    1: "UNO-DM-4.0-TL-PLUS",
    3: "UNO-DM-4.6-TL-PLUS",
    4: "UNO-DM-5.0-TL-PLUS",
    5: "UNO-DM-6.0-TL-PLUS",
    10: "UNO-DM-1.2-TL-PLUS",
    11: "UNO-DM-2.0-TL-PLUS",
    12: "UNO-DM-3.0-TL-PLUS",
    13: "REACT2-UNO-5.0-TL",
    14: "REACT2-UNO-3.6-TL",
    15: "UNO-DM-5.0-TL-PLUS",
    16: "UNO-DM-6.0-TL-PLUS",
    19: "REACT2-5.0-TL",
    49: "PVI-3.0-OUTD",
    50: "PVI-3.3-OUTD",
    51: "PVI-3.6-OUTD",
    52: "PVI-4.2-OUTD",
    53: "PVI-5000-OUTD",
    54: "PVI-6000-OUTD",
    65: "PVI-CENTRAL-350",
    66: "PVI-CENTRAL-350",
    67: "PVI-CENTRAL-50",
    68: "PVI-12.5-OUTD",
    69: "PVI-CENTRAL-67",
    70: "TRIO-27.6-TL-OUTD",
    71: "UNO-2.5-OUTD",
    72: "PVI-4.6-OUTD-I",
    74: "PVI-1700-OUTD",
    76: "PVI-CENTRAL-350",
    77: "PVI-CENTRAL-250",
    78: "PVI-12.5-OUTD",
    79: "PVI-3600-OUTD",
    80: "3-phase interface (3G74)",
    81: "PVI-8.0-OUTD-PLUS",
    82: "TRIO-8.5-TL-OUTD-S",
    83: "PVS-12.5-TL",
    84: "PVI-12.5-OUTD-I",
    85: "PVI-12.5-OUTD-I",
    86: "PVI-12.5-OUTD-I",
    88: "PVI-10.0-OUTD",
    89: "TRIO-27.6-TL-OUTD",
    90: "PVI-12.5-OUTD-I",
    99: "CDD",
    102: "TRIO-20-TL-OUTD",
    103: "UNO-2.0-OUTD",
    104: "PVI-3.8-OUTD-I",
    105: "PVI-2000-IND",
    106: "PVI-1700-IND",
    107: "TRIO-7.5-OUTD",
    108: "PVI-3600-IND",
    110: "PVI-10.0-OUTD",
    111: "PVI-2000-OUTD",
    113: "PVI-8.0-OUTD",
    114: "TRIO-5.8-OUTD",
    116: "PVI-10.0-OUTD-I",
    117: "PVI-10.0-OUTD-I",
    118: "PVI-10.0-OUTD-I",
    119: "PVI-10.0-I-OUTD",
    121: "TRIO-20-TL-OUTD",
    122: "PVI-10.0-OUTD-I",
    224: "UNO-2.0-TL-OUTD",
    242: "UNO-3.0-TL-OUTD",
}
