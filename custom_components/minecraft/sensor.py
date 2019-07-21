"""Sensor platform for blueprint."""
from homeassistant.helpers.entity import Entity
from .const import (
DOMAIN,
DOMAIN_DATA, 

CONF_NAME, 
CONF_ICON,
CONF_HOST,
CONF_RCON_PORT,
CONF_RCON_PASSWORD,

ATTR_TYPE,
ATTR_SESSION_ID,
ATTR_MOTD,
ATTR_GAME_TYPE,
ATTR_GAME_ID,
ATTR_VERSION,
ATTR_PLUGINS,
ATTR_MAP,
ATTR_NUM_PLAYERS,
ATTR_MAX_PLAYERS,
ATTR_HOST_PORT,
ATTR_HOST_IP,
ATTR_PLAYERS,

ATTR_SEED,
ATTR_MANSION_LOCATION,
)

async def async_setup_platform(
    hass, config, async_add_entities, discovery_info=None
):  # pylint: disable=unused-argument
    """Setup sensor platform."""

    name = hass.data[DOMAIN_DATA][CONF_NAME]
    icon = hass.data[DOMAIN_DATA][CONF_ICON]

    async_add_entities([MinecraftSensor(hass, discovery_info, name, icon)], True)

    host        = hass.data[DOMAIN_DATA][CONF_HOST]
    rcon_port   = hass.data[DOMAIN_DATA][CONF_RCON_PORT]
    rcon_pw     = hass.data[DOMAIN_DATA][CONF_RCON_PASSWORD]

    """RCON Sensor Services"""
    if rcon_pw is not None and rcon_port is not None:
        from mcipc.rcon import Client as RCON

        async def minecraft_send_command(call):
            """Execute any Minecraft Server Command"""
            call_command = call.data.get('command')
            call_data = call.data.get('data', str(''))

            if call_data != '':
                call_command = '%s %s' %(call_command, call_data)

            with RCON(host, rcon_port) as client:
                client.login(rcon_pw)
                return client.run(call_command)
                # TODO: Ideally create a response attribute

        async def minecraft_turn_off(call):
            """Stops the server"""
            with RCON(host, rcon_port) as client:
                client.login(rcon_pw)
                return client.run('stop')

        async def minecraft_reload(call):
            """Reloads loot tables, advancements, and functions from disk."""
            with RCON(host, rcon_port) as client:
                client.login(rcon_pw)
                return client.run('reload')

        async def minecraft_save(call):
            """Saves the server to disk."""
            with RCON(host, rcon_port) as client:
                client.login(rcon_pw)
                return client.run('save-all')

        hass.services.async_register(DOMAIN, 'send_command', minecraft_send_command)
        hass.services.async_register(DOMAIN, 'turn_off', minecraft_turn_off)
        hass.services.async_register(DOMAIN, 'reload', minecraft_reload)
        hass.services.async_register(DOMAIN, 'save', minecraft_save)

class MinecraftSensor(Entity):
    """Minecraft Sensor class."""
    def __init__(self, hass, config, name, icon):
        self._hass     = hass
        self._attr     = config
        self._state    = 'Unavailable'
        self._name     = name
        self._icon     = icon

    async def async_update(self):
        """Update the sensor."""

        # Issue update command
        await self._hass.data[DOMAIN_DATA]["client"].update_data()

        # Get mcipc.query updates
        try:
            updated = self.hass.data[DOMAIN_DATA]["data"]

            self._type                = str(updated.type)
            self._session_id          = str(updated.session_id)
            self._motd                = str(updated.host_name)
            self._game_type           = str(updated.game_type)
            self._game_id             = str(updated.game_id)
            self._version             = str(updated.version)
            self._plugins             = updated.plugins
            self._map                 = str(updated.map)
            self._num_players         = str(updated.num_players)
            self._max_players         = str(updated.max_players)
            self._host_port           = str(updated.host_port)
            self._host_ip             = str(updated.host_ip)
            self._players             = updated.players

            self._state = str(updated.num_players) + '/' + str(updated.max_players)

        except:
            # Query is either disabled or server is offline
            self._state = 'Unavailable'
            self._players = ''
            return

        # Get mcipc.rcon updates
        try:
            self._seed                = self._hass.data[DOMAIN_DATA][ATTR_SEED]
            self._mansion_location    = self._hass.data[DOMAIN_DATA][ATTR_MANSION_LOCATION]

        except:
            # RCON credentials missing
            pass


    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self._icon

    @property
    def device_state_attributes(self):
        """Return the state attributes."""  

        # Try for query metrics
        try:
            attributes = {
                ATTR_TYPE: self._type,
                ATTR_SESSION_ID: self._session_id,
                ATTR_MOTD: self._motd,
                ATTR_GAME_TYPE: self._game_type,
                ATTR_GAME_ID: self._game_id,
                ATTR_VERSION: self._version,
                ATTR_PLUGINS: self._plugins,
                ATTR_MAP: self._map,
                ATTR_NUM_PLAYERS: self._num_players,
                ATTR_MAX_PLAYERS: self._max_players,
                ATTR_HOST_PORT: self._host_port,
                ATTR_HOST_IP: self._host_ip,
                ATTR_PLAYERS: self._players,
                }
        except:
            # Query is either disabled or server is offline
            return

        # Try for rcon metrics
        try:
            attributes.update({
                ATTR_SEED: self._seed,
                ATTR_MANSION_LOCATION: self._mansion_location,
            })
        except:
            # RCON credentials missing
            pass

        # Return only the configured metrics
        return {x:attributes[x] for x in self._attr}
