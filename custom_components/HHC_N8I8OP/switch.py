import logging
import socket
from collections import defaultdict

import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
import voluptuous as vol
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.config_validation import (PLATFORM_SCHEMA)
from homeassistant.helpers.event import track_point_in_time

_LOGGER = logging.getLogger(__name__)

CONF_NAME = "name"
CONF_IP = "ip"
CONF_PORT = "port"
CONF_INDEX = "index"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_IP): cv.string,
    vol.Optional(CONF_PORT, default=500): cv.string,
    vol.Required(CONF_INDEX): cv.string,
})

_LOGGER.warning('START MY SWITCH')

_registered_switch = defaultdict(list)


async def async_setup_platform(_hass, config, async_add_entities, _discovery_info=None):
    switches = [Hhcn8I8opSwitch(config)]
    async_add_entities(switches, True)


class Hhcn8I8opSwitch(SwitchEntity):
    def __init__(self, config):
        self._name = config.get(CONF_NAME)

        self.no_domain_ = self._name.startswith("!")
        if self.no_domain_:
            self._name = self.name[1:]
        self._unique_id = self._name.lower().replace(' ', '_')

        self._ip = config.get(CONF_IP)
        self._port = int(config.get(CONF_PORT))
        self._index = int(config.get(CONF_INDEX))

    def _execute(self, command):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect((self._ip, self._port))
        c = str(command).encode()
        sock.settimeout(5)
        sock.send(c)
        data = sock.recv(8192)
        data = data.decode()
        sock.close()
        return data

    @property
    def device_state_attributes(self):
        """Return the device state attributes."""
        attrs = {
            'friendly_name': self._name,
            'unique_id': self._unique_id,
        }
        return attrs

    @property
    def name(self):
        if self.no_domain_:
            return self._name
        else:
            return super().name

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._get_state()

    def turn_on(self, **kwargs):
        self._set_state(True)

    def turn_off(self, **kwargs):
        self._set_state(False)

    def _parse_state(self, responce):
        return [bool(int(state)) for index, state in
                enumerate(reversed(responce.split('relay')[1]))]

    def _get_state(self):
        return self._parse_state(self._execute('read'))[self._index - 1]

    def _set_state(self, state):
        state = f'{"on" if state else "off"}'

        self._execute(f'{state}{self._index}')

        track_point_in_time(self.hass, self.async_update_ha_state, dt_util.utcnow())
        _LOGGER.debug(f'Set "{self.name}" state {state}')

        self.async_schedule_update_ha_state()
