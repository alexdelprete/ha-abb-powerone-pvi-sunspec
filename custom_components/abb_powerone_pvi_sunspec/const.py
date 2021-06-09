from homeassistant.const import (
    DEVICE_CLASS_CURRENT,
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_VOLTAGE,
)

DOMAIN = "abb_powerone_pvi_sunspec"
DEFAULT_NAME = "abb_p1"
DEFAULT_PORT = 502
DEFAULT_SCAN_INTERVAL = 30
MANUFACTURER = "ABB Power-One"
ATTR_STATUS_DESCRIPTION = "status_description"
ATTR_MANUFACTURER = "ABB Power-One"


SENSOR_TYPES = {
    "Manufacturer": ["Manufacturer", "comm_manufact", None, "mdi:information-outline", None],
    "Model": ["Model", "comm_model", None, "mdi:information-outline", None],
    "Options": ["Options", "comm_options", None, "mdi:information-outline", None],
    "Version": ["Firmware Version", "comm_version", None, "mdi:information-outline", None],
    "Serial": ["Serial", "comm_sernum", None, "mdi:information-outline", None],
    "Device_Addr": ["Modbus Address", "comm_devaddr", None, "mdi:information-outline", None],
    "AC_Current": ["AC Current", "accurrent", "A", "mdi:current-ac", DEVICE_CLASS_CURRENT],
    "AC_CurrentA": ["AC Current A", "accurrenta", "A", "mdi:current-ac", DEVICE_CLASS_CURRENT],
    "AC_CurrentB": ["AC Current B", "accurrentb", "A", "mdi:current-ac", DEVICE_CLASS_CURRENT],
    "AC_CurrentC": ["AC Current C", "accurrentc", "A", "mdi:current-ac", DEVICE_CLASS_CURRENT],
    "AC_VoltageAB": ["AC Voltage AB", "acvoltageab", "V", "mdi:lightning-bolt", DEVICE_CLASS_VOLTAGE],
    "AC_VoltageBC": ["AC Voltage BC", "acvoltagebc", "V", "mdi:lightning-bolt", DEVICE_CLASS_VOLTAGE],
    "AC_VoltageCA": ["AC Voltage CA", "acvoltageca", "V", "mdi:lightning-bolt", DEVICE_CLASS_VOLTAGE],
    "AC_VoltageAN": ["AC Voltage AN", "acvoltagean", "V", "mdi:lightning-bolt", DEVICE_CLASS_VOLTAGE],
    "AC_VoltageBN": ["AC Voltage BN", "acvoltagebn", "V", "mdi:lightning-bolt", DEVICE_CLASS_VOLTAGE],
    "AC_VoltageCN": ["AC Voltage CN", "acvoltagecn", "V", "mdi:lightning-bolt", DEVICE_CLASS_VOLTAGE],
    "AC_Power": ["AC Power", "acpower", "W", "mdi:solar-power", DEVICE_CLASS_POWER],
    "AC_Frequency": ["AC Frequency", "acfreq", "Hz", "mdi:sine-wave", None],
    "AC_Energy": ["AC Energy", "acenergy", "kWh", "mdi:solar-power", DEVICE_CLASS_ENERGY],
    "DC_Power": ["DC Power", "dcpower", "W", "mdi:solar-power", DEVICE_CLASS_POWER],
    "DC1_Curr": ["DC1 current", "dc1curr", "A", "mdi:current-ac", DEVICE_CLASS_CURRENT],
    "DC1_Volt": ["DC1 voltage", "dc1volt", "V", "mdi:lightning-bolt", DEVICE_CLASS_VOLTAGE],
    "DC1_Power": ["DC1 power", "dc1power", "W", "mdi:solar-power", DEVICE_CLASS_POWER],
    "DC2_Curr": ["DC2 current", "dc2curr", "A", "mdi:current-ac", DEVICE_CLASS_CURRENT],
    "DC2_Volt": ["DC2 voltage", "dc2volt", "V", "mdi:lightning-bolt", DEVICE_CLASS_VOLTAGE],
    "DC2_Power": ["DC2 power", "dc2power", "W", "mdi:solar-power", DEVICE_CLASS_POWER],
    "Status": ["Operating State", "status", None, "mdi:information-outline", None],
    "Status_Vendor": ["Vendor Operating State", "statusvendor", None, "mdi:information-outline", None],
    "Temp_Cab": ["Cabinet Temperature", "tempcab", "°C", "mdi:temperature-celsius", DEVICE_CLASS_TEMPERATURE],
    "Temp_Oth": ["Booster Temperature", "tempoth", "°C", "mdi:temperature-celsius", DEVICE_CLASS_TEMPERATURE],
}

DEVICE_STATUS = {
    1: "Off",
    2: "Sleeping (auto-shutdown) – Night mode",
    3: "Grid Monitoring/wake-up",
    4: "Inverter is ON and producing power",
    5: "Production (curtailed)",
    6: "Shutting down",
    7: "Fault",
    8: "Maintenance/setup",
}
