DOMAIN = "abb_sunspec_modbus"
DEFAULT_NAME = "abb_sunspec"
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_PORT = 502
DEFAULT_UNITID = 2
CONF_ABB_SUNSPEC_HUB = "abb_sunspec_hub"
ATTR_STATUS_DESCRIPTION = "status_description"
ATTR_MANUFACTURER = "ABB"

SENSOR_TYPES = {
    "AC_Current": ["AC Current", "accurrent", "A", "mdi:current-ac"],
    "AC_CurrentA": ["AC Current A", "accurrenta", "A", "mdi:current-ac"],
    "AC_CurrentB": ["AC Current B", "accurrentb", "A", "mdi:current-ac"],
    "AC_CurrentC": ["AC Current C", "accurrentc", "A", "mdi:current-ac"],
    "AC_VoltageAB": ["AC Voltage AB", "acvoltageab", "V", None],
    "AC_VoltageBC": ["AC Voltage BC", "acvoltagebc", "V", None],
    "AC_VoltageCA": ["AC Voltage CA", "acvoltageca", "V", None],
    "AC_VoltageAN": ["AC Voltage AN", "acvoltagean", "V", None],
    "AC_VoltageBN": ["AC Voltage BN", "acvoltagebn", "V", None],
    "AC_VoltageCN": ["AC Voltage CN", "acvoltagecn", "V", None],
    "AC_Power": ["AC Power", "acpower", "W", "mdi:solar-power"],
    "AC_Frequency": ["AC Frequency", "acfreq", "Hz", None],
    "AC_Energy_KWH": ["AC Energy KWH", "acenergy", "kWh", "mdi:solar-power"],
    "DC_Power": ["DC Power", "dcpower", "W", "mdi:solar-power"],
    "Temp_Cab": ["Temp Cabinet", "tempcab", "°C", None],
    "Temp_Oth": ["Temp Booster", "tempoth", "°C", None],
    "Status": ["Status", "status", None, None],
    "Status_Vendor": ["Status Vendor", "statusvendor", None, None],
}

DEVICE_STATUSSES = {
    1: "Off",
    2: "Sleeping (auto-shutdown) – Night mode",
    3: "Grid Monitoring/wake-up",
    4: "Inverter is ON and producing power",
    5: "Production (curtailed)",
    6: "Shutting down",
    7: "Fault",
    8: "Maintenance/setup",
}
