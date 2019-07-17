"""
Sensor to check the status of a Minecraft server.
"""
import logging
from homeassistant.helpers.entity import Entity

DOMAIN = 'minecraft'

""" -- QUERY ATTRIBUTES -- """
ATTR_TYPE = 'type'
ATTR_SESSION_ID = 'session_id'
ATTR_MOTD = 'motd'
ATTR_GAME_TYPE = 'game_type'
ATTR_GAME_ID = 'game_id'
ATTR_VERSION = 'version'
ATTR_PLUGINS = 'plugins'
ATTR_MAP = 'map'
ATTR_NUM_PLAYERS = 'num_players'
ATTR_MAX_PLAYERS = 'max_players'
ATTR_HOST_PORT = 'host_port'
ATTR_HOST_IP = 'host_ip'
ATTR_PLAYERS = 'players_online'

""" -- RCON ATTRIBUTES -- """
ATTR_SEED = 'seed'
ATTR_MANSION_LOCATION = 'mansion_location'

# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Minecraft server platform."""
    from mcipc.query import Client as mcserver
    logger = logging.getLogger(__name__)

    host = config.get('host', '127.0.0.1')
    query_port = config.get('query_port', '25565')
    rcon_port = config.get('rcon_port', None)
    rcon_password = config.get('rcon_password', None)
    name = config.get('name', 'Minecraft Server')
    icon = config.get('icon', 'mdi:minecraft')
    monitored_conditions = config.get('monitored_conditions', ['motd','game_type','version','map','players_online'])

    if rcon_password is None and rcon_port is not None:
        logger.error('Rcon port found, missing rcon password')
        return False

    add_devices([
        MCServerSensor(host, query_port, rcon_port, rcon_password, monitored_conditions, name, icon)
    ])

    """ SERVICES """
    if rcon_password is not None and rcon_port is not None:
        from mcipc.rcon import Client as rconserver

        domain = name.lower().replace(' ', '_')

        def mcserver_send_command(call):
            """Execute Minecraft Server Commands"""
            rcon_command = call.data.get('command')
            rcon_data = call.data.get('data', str(''))

            if rcon_data != '':
                rcon_command = rcon_command + ' ' + rcon_data

            with rconserver(host, rcon_port) as client:
                client.login(rcon_password)
                response = client.run(rcon_command)
                hass.states.set(domain+'.send_command_response', response)

        def mcserver_turn_off(call):
            """Stops the server"""
            with rconserver(host, rcon_port) as client:
                client.login(rcon_password)
                response = client.run('stop')
                hass.states.set(domain+'.turn_off_response', response)

        def mcserver_reload(call):
            """Reloads loot tables, advancements, and functions from disk."""
            with rconserver(host, rcon_port) as client:
                client.login(rcon_password)
                response = client.run('reload')
                hass.states.set(domain+'.reload_response', response)

        def mcserver_save(call):
            """Saves the server to disk."""
            with rconserver(host, rcon_port) as client:
                client.login(rcon_password)
                response = client.run('save-all')
                hass.states.set(domain+'.save_response', response)

        def mcserver_notify(call):
            """Broadcast Messages within Minecraft Server"""
            rcon_message = call.data.get('message')
            rcon_title = call.data.get('title', 'Home Assistant')
            rcon_target = call.data.get('target', '@a')

            with rconserver(host, rcon_port) as client:
                client.login(rcon_password)
                if rcon_title == "":
                    response = client.run('tellraw', rcon_target, '["" ,{"text":"%s"}]' %(rcon_message))
                elif rcon_title != "":
                    response = client.run('tellraw', rcon_target, '["[%s] " ,{"text":"%s"}]' %(rcon_title, rcon_message))
                hass.states.set(domain+'.notify_response', response)

        def mcserver_notify_title(call):
            """Broadcast Titles within Minecraft Server"""
            rcon_message = call.data.get('message')
            rcon_title = call.data.get('title', 'title')
            rcon_target = call.data.get('target', '@a')

            with rconserver(host, rcon_port) as client:
                client.login(rcon_password)
                response = client.run('title', rcon_target + ' %s {"text":"%s"}' %(rcon_title, rcon_message))
                hass.states.set(domain+'.notify_title_response', response)
        
        hass.services.register(DOMAIN, 'send_command', mcserver_send_command)
        hass.services.register(DOMAIN, 'turn_off', mcserver_turn_off)
        hass.services.register(DOMAIN, 'reload', mcserver_reload)
        hass.services.register(DOMAIN, 'save', mcserver_save)
        hass.services.register('notify', 'minecraft_server', mcserver_notify)
        hass.services.register('notify', 'minecraft_server_title', mcserver_notify_title)

    return True


class MCServerSensor(Entity):
    """A class for the Minecraft server."""
    # pylint: disable=abstract-method
    def __init__(self, host, query_port, rcon_port, rcon_password, monitored_conditions, name, icon):
        """Initialize the sensor."""
        from mcipc.query import Client as query
        self._mcserver = query
        self._host = host
        self._query_port = query_port
        self._rcon_port = rcon_port
        self._rcon_password = rcon_password
        self._monitored_conditions = monitored_conditions
        if rcon_port is not None:
            from mcipc.rcon import Client as rcon
            self._rconserver = rcon
        self._name = name
        self._icon = icon
        self.update()

    @property
    def name(self):
        """Return the name of the server."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state
		
    # pylint: disable=no-member
    def update(self):
        """Update device state."""
        try: 
            with self._mcserver(self._host, self._query_port) as client:
                full_stats = client.full_stats

            """ -- QUERY DATA -- """
            self._type = str(full_stats.type)
            self._session_id = str(full_stats.session_id)
            self._motd = str(full_stats.host_name)
            self._game_type = str(full_stats.game_type)
            self._game_id = str(full_stats.game_id)
            self._version = str(full_stats.version)
            self._plugins = full_stats.plugins
            self._map = str(full_stats.map)
            self._num_players = str(full_stats.num_players)
            self._max_players = str(full_stats.max_players)
            self._host_port = str(full_stats.host_port)
            self._host_ip = str(full_stats.host_ip)
            self._players = full_stats.players

            
            if self._rcon_port is not None:
                with self._rconserver(self._host, self._rcon_port) as client:
                    client.login(self._rcon_password)

                    """ -- RCON DATA -- """
                    self._seed = client.seed
                    self._players_info = client.players
                    self._mansion_location = client.locate('Mansion')

            """ -- STATE -- """
            self._state = str(full_stats.num_players) + '/' + str(full_stats.max_players)

        except:
            logger = logging.getLogger(__name__)
            self._state = 'Unavailable'


    @property
    def device_state_attributes(self):
        logger = logging.getLogger(__name__)
        """Return the state attributes."""
        try: 
            with self._mcserver(self._host, self._query_port) as client:
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

            if self._rcon_port is not None:
                attributes.update({
                    ATTR_SEED: self._seed,
                    ATTR_MANSION_LOCATION: self._mansion_location
                })

            return {x:attributes[x] for x in self._monitored_conditions}

        except:
            pass

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return self._icon
