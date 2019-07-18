"""Constants for minecraft."""
# Base component constants
DOMAIN = "minecraft"
DOMAIN_DATA = "{}_data".format(DOMAIN)
VERSION = "0.0.1"
PLATFORMS = ["sensor"]
REQUIRED_FILES = [
    "const.py",
    "manifest.json",
    "sensor.py",
    "services.yaml",
]
ISSUE_URL = "https://github.com/sondregronas/MinecraftServer-HA/issues"
ATTRIBUTION = "Data from this is provided by blueprint."
STARTUP = """
-------------------------------------------------------------------
{name}
Version: {version}
This is a custom component
If you have any issues with this you need to open an issue here:
{issueurl}
-------------------------------------------------------------------
"""

# Configuration
CONF_HOST              = 'host'
CONF_QUERY_PORT        = 'query_port'
CONF_RCON_PORT         = 'rcon_port'
CONF_RCON_PASSWORD     = 'rcon_password'
CONF_NAME              = 'name'
CONF_ICON              = 'icon'
CONF_SENSOR            = 'sensor'

# Defaults
DEFAULT_HOST           = '127.0.0.1'
DEFAULT_QUERY_PORT     = 25565
DEFAULT_NAME           = 'Minecraft Server'
DEFAULT_ICON           = "mdi:minecraft"
DEFAULT_SENSOR         = ['motd', 'game_type', 'version', 'map', 'players']

# Query sensors
ATTR_TYPE              = 'type'
ATTR_SESSION_ID        = 'session_id'
ATTR_MOTD              = 'motd'
ATTR_GAME_TYPE         = 'game_type'
ATTR_GAME_ID           = 'game_id'
ATTR_VERSION           = 'version'
ATTR_PLUGINS           = 'plugins'
ATTR_MAP               = 'map'
ATTR_NUM_PLAYERS       = 'num_players'
ATTR_MAX_PLAYERS       = 'max_players'
ATTR_HOST_PORT         = 'host_port'
ATTR_HOST_IP           = 'host_ip'
ATTR_PLAYERS           = 'players'

# Rcon sensors
ATTR_SEED              = 'seed'
ATTR_MANSION_LOCATION  = 'mansion_location'

# Sensor types
SENSOR_TYPES = {
    ATTR_TYPE:                 'type',
    ATTR_SESSION_ID:           'session_id',
    ATTR_MOTD:                 'motd',
    ATTR_GAME_TYPE:            'game_type',
    ATTR_GAME_ID:              'game_id',
    ATTR_VERSION:              'version',
    ATTR_PLUGINS:              'plugins',
    ATTR_MAP:                  'map',
    ATTR_NUM_PLAYERS:          'num_players',
    ATTR_MAX_PLAYERS:          'max_players',
    ATTR_HOST_PORT:            'host_port',
    ATTR_HOST_IP:              'host_ip',
    ATTR_PLAYERS:              'players',
    ATTR_SEED:                 'seed',
    ATTR_MANSION_LOCATION:     'mansion_location',
}