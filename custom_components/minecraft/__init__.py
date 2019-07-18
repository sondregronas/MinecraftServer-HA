"""
The "minecraft" custom components.
Sensor to check the status of a Minecraft server.

minecraft:
"""
import os
from datetime import timedelta
import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import discovery
from homeassistant.util import Throttle

from .const import (
    DOMAIN, 
    DOMAIN_DATA,
    STARTUP,
    VERSION,
    PLATFORMS,
    REQUIRED_FILES,
    ISSUE_URL,
    CONF_HOST, 			DEFAULT_HOST,
    CONF_QUERY_PORT, 	DEFAULT_QUERY_PORT,
    CONF_RCON_PORT,
    CONF_RCON_PASSWORD,
    CONF_NAME, 			DEFAULT_NAME,
    CONF_ICON, 			DEFAULT_ICON,
    CONF_SENSORS,		DEFAULT_SENSORS,
    CONF_ENABLED,
    CONF_SENSOR,
    ATTR_SEED,
    ATTR_MANSION_LOCATION,
    SENSOR_TYPES,
)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional(DOMAIN): vol.Schema(
            {
                vol.Optional(CONF_HOST,				default=DEFAULT_HOST): 				cv.string,
                vol.Optional(CONF_QUERY_PORT,		default=DEFAULT_QUERY_PORT): 		cv.port,
                vol.Optional(CONF_RCON_PORT): 											cv.port,
                vol.Optional(CONF_RCON_PASSWORD):										cv.string,
                vol.Optional(CONF_NAME, 			default=DEFAULT_NAME): 				cv.string,
                vol.Optional(CONF_ICON,				default=DEFAULT_ICON):				cv.string,
                vol.Optional(CONF_SENSOR,			default=DEFAULT_SENSOR):			vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
            }
        )
    },
	extra=vol.ALLOW_EXTRA,
)

# pylint: disable=unused-argument
async def async_setup(hass, config):
    """Setup the Minecraft server platform."""
    hass.data[DOMAIN_DATA] = {}

    # Print startup message
    startup = STARTUP.format(name=DOMAIN, version=VERSION, issueurl=ISSUE_URL)
    _LOGGER.info(startup)

    # Check that all required files are present
    file_check = await check_files(hass)
    if not file_check:
        return False

    # Grab the config
    host 		= config[DOMAIN].get(CONF_HOST)
    query_port	= config[DOMAIN].get(CONF_QUERY_PORT)
    rcon_port	= config[DOMAIN].get(CONF_RCON_PORT)
    rcon_pw		= config[DOMAIN].get(CONF_RCON_PASSWORD)
    name		= config[DOMAIN].get(CONF_NAME)
    icon		= config[DOMAIN].get(CONF_ICON)

    # Store config in hass.data
    hass.data[DOMAIN_DATA][CONF_HOST] 			= host
    hass.data[DOMAIN_DATA][CONF_QUERY_PORT] 	= query_port
    hass.data[DOMAIN_DATA][CONF_RCON_PORT] 		= rcon_port
    hass.data[DOMAIN_DATA][CONF_RCON_PASSWORD] 	= rcon_pw
    hass.data[DOMAIN_DATA][CONF_NAME] 			= name
    hass.data[DOMAIN_DATA][CONF_ICON] 			= icon

    # Initiate the component
    hass.data[DOMAIN_DATA]["client"] = MinecraftServerSensor(hass, host, query_port, rcon_port, rcon_pw)

    # Load platforms
    for platform in PLATFORMS:
        # Get platform specific configuration
        platform_config = config[DOMAIN].get(platform, {})

        # If platform is not enabled, skip.
        if not platform_config:
            continue

        hass.async_create_task(
            discovery.async_load_platform(hass, platform, DOMAIN, platform_config, config)
        )


    """RCON Notify Services"""
    if rcon_pw is not None and rcon_port is not None:
        from mcipc.rcon import Client as RCON

        async def minecraft_notify(call):
            """Broadcast Messages within Minecraft Server"""
            call_message = call.data.get('message')
            call_title = call.data.get('title', 'Home Assistant')
            call_target = call.data.get('target', '@a')

            with RCON(host, rcon_port) as client:
                client.login(rcon_pw)
                if call_title == "":
                    return client.run('tellraw', call_target, '["" ,{"text":"%s"}]' %(call_message))
                elif call_title != "":
                    return client.run('tellraw', call_target, '["[%s] " ,{"text":"%s"}]' %(call_title, call_message))

        async def minecraft_notify_title(call):
            """Broadcast Titles within Minecraft Server"""
            call_message = call.data.get('message')
            call_title = call.data.get('title', 'title')
            call_target = call.data.get('target', '@a')

            with RCON(host, rcon_port) as client:
                client.login(rcon_pw)
                return client.run('title', call_target + ' %s {"text":"%s"}' %(call_title, call_message))

        hass.services.async_register('notify', 'minecraft_server', minecraft_notify)
        hass.services.async_register('notify', 'minecraft_server_title', minecraft_notify_title)

    return True

class MinecraftServerSensor:
    """A class for the Minecraft Server Sensor."""

    def __init__(self, hass, host, query_port, rcon_port, rcon_pw):
        self._hass 			= hass
        self._host 			= host
        self._query_port	= query_port
        self._rcon_port		= rcon_port
        self._rcon_pw       = rcon_pw

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def update_data(self):
        """Update data."""
        from mcipc.query import Client as QUERY
        from mcipc.rcon import Client as RCON
        try:
            # Get Query clients "full_stats" value
            with QUERY(self._host, self._query_port) as client:
                self._hass.data[DOMAIN_DATA]["data"] = client.full_stats

            # Get RCON client data, if possible
            try:
                with RCON(self._host, self._rcon_port) as client:
                    client.login(self._rcon_pw)
                    self._hass.data[DOMAIN_DATA][ATTR_SEED] 			= client.seed
                    self._hass.data[DOMAIN_DATA][ATTR_MANSION_LOCATION] = client.locate('Mansion')
            except:
                _LOGGER.info('Retrieving RCON data failed')

        # Server offline or failed to authenticate
        except Exception as error:  # pylint: disable=broad-except
            self._hass.data[DOMAIN_DATA]["data"] = 'UNAVAILABLE'
            _LOGGER.error("Could not update data - %s, is query enabled in server.properties?", error)

async def check_files(hass):
    """Return bool that indicates if all files are present."""
    # Verify that the user downloaded all files.
    base = "{}/custom_components/{}/".format(hass.config.path(), DOMAIN)
    missing = []
    for file in REQUIRED_FILES:
        fullpath = "{}{}".format(base, file)
        if not os.path.exists(fullpath):
            missing.append(file)

    if missing:
        _LOGGER.critical("The following files are missing: %s", str(missing))
        returnvalue = False
    else:
        returnvalue = True

    return returnvalue