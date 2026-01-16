"""Constants for the Helty VMC integration."""

DOMAIN = "helty_vmc"
DEFAULT_PORT = 5001
DEFAULT_TIMEOUT = 15
DEFAULT_SCAN_INTERVAL = 30

# VMC Commands
CMD_GET_STATUS = "VMGH?"
CMD_GET_SENSORS = "VMGI?"
CMD_GET_NAME = "VMNM?"
CMD_GET_LAN = "VMSL?"

# Speed commands - format: VMWH0000XXX where XXX is speed code
CMD_SET_SPEED_0 = "VMWH0000000"
CMD_SET_SPEED_1 = "VMWH0000001"
CMD_SET_SPEED_2 = "VMWH0000002"
CMD_SET_SPEED_3 = "VMWH0000003"
CMD_SET_SPEED_4 = "VMWH0000004"
CMD_SET_BOOST = "VMWH0000005"
CMD_SET_NIGHT = "VMWH0000006"
CMD_SET_FREE_COOLING = "VMWH0000007"

# Control commands
CMD_SENSORS_ON = "VMWH0300000"
CMD_SENSORS_OFF = "VMWH0300002"
CMD_LED_ON = "VMWH0100010"
CMD_LED_OFF = "VMWH0100000"
CMD_RESET_FILTER = "VMWH0417744"

# Speed modes mapping
SPEED_MODES = {
    0: "off",
    1: "speed_1",
    2: "speed_2",
    3: "speed_3",
    4: "speed_4",
    5: "boost",
    6: "night",
    7: "free_cooling",
}

SPEED_COMMANDS = {
    "off": CMD_SET_SPEED_0,
    "speed_1": CMD_SET_SPEED_1,
    "speed_2": CMD_SET_SPEED_2,
    "speed_3": CMD_SET_SPEED_3,
    "speed_4": CMD_SET_SPEED_4,
    "boost": CMD_SET_BOOST,
    "night": CMD_SET_NIGHT,
    "free_cooling": CMD_SET_FREE_COOLING,
}

# Airflow rates in m³/h for each speed (typical values for Helty Flow Plus)
AIRFLOW_RATES = {
    0: 0,
    1: 15,
    2: 30,
    3: 45,
    4: 60,
    5: 80,  # boost
    6: 10,  # night
    7: 60,  # free cooling
}

CONF_HOST = "host"
CONF_PORT = "port"
CONF_NAME = "name"
CONF_SCAN_INTERVAL = "scan_interval"
