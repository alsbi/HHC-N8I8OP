import logging
import socket

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

WAIT_TIMEOUT = 10
DEFAULT_PORT = 5000

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_IP): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.string,
    vol.Required(CONF_INDEX): cv.string,
})


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

        _LOGGER.debug(f'Start switch {self._unique_id}')

    @property
    def icon(self):
        """Icon of the entity."""
        return "mdi:Lightbulb"

    def _execute(self, command):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(WAIT_TIMEOUT)
            sock.connect((self._ip, self._port))
            sock.send(str(command).encode())
            return sock.recv(8192).decode()

    @property
    def available(self):
        """Return availability."""
        return True if self._get_state() is not None else False

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

    def _get_state(self):
        try:
            response = self._execute('read')
            state = list(reversed(response.split('relay')[1]))[self._index - 1]
            return bool(int(state))
        except socket.timeout:
            return

    def _set_state(self, state):
        state = f'{"on" if state else "off"}'

        try:
            self._execute(f'{state}{self._index}')
        except socket.timeout:
            _LOGGER.debug(f'Set "{self.name}" state {state} fail, socket timeout')
            return

        track_point_in_time(self.hass, self.async_update_ha_state, dt_util.utcnow())
        _LOGGER.debug(f'Set "{self.name}" state {state}')

        self.async_schedule_update_ha_state()

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._get_state()

    def turn_on(self, **kwargs):
        self._set_state(True)

    def turn_off(self, **kwargs):
        self._set_state(False)
