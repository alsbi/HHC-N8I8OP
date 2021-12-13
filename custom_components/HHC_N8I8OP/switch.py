import logging
import socket

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNKNOWN
from homeassistant.helpers.config_validation import (PLATFORM_SCHEMA)

_LOGGER = logging.getLogger(__name__)

CONF_NAME = "name"
CONF_IP = "ip"
CONF_PORT = "port"
CONF_INDEX = "index"
ICON = 'icon'

WAIT_TIMEOUT = 2
DEFAULT_PORT = 5000

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_IP): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.string,
    vol.Optional(ICON, default="mdi:lightbulb"): cv.string,
    vol.Required(CONF_INDEX): cv.string,
})


async def async_setup_platform(_hass, config, async_add_entities, _discovery_info=None):
    sensors = [Hhcn8I8opSwitch(config)]
    async_add_entities(sensors, update_before_add=True)


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
        self._icon = config.get(ICON)

        self._get_state()

        _LOGGER.debug(f'Start switch {self._unique_id}')

    @property
    def icon(self):
        """Icon of the entity."""
        return self._icon

    @property
    def available(self):
        """If light is available."""
        return self._state != STATE_UNKNOWN

    @property
    def extra_state_attributes(self):
        """Return the device state attributes."""
        attrs = {
            'friendly_name': self._name,
            'unique_id': self._unique_id,
            'index': self._index,
            "manufacturer": "HHC",
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

    def _execute_socket_command(self, command: str) -> str:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(WAIT_TIMEOUT)
            sock.connect((self._ip, self._port))
            sock.send(str(command).encode())
            return sock.recv(8192).decode()

    def _get_state(self):
        try:
            response = self._execute_socket_command('read')
            state = list(reversed(response.split('relay')[1]))[self._index - 1]
            self._state = STATE_ON if bool(int(state)) else STATE_OFF
        except socket.timeout:
            self._state = STATE_UNKNOWN

    async def async_update(self):
        """Retrieve latest state."""
        self._get_state()

    def _set_state(self, state: str):
        try:

            self._execute_socket_command(f'{state}{self._index}')
            self._state = state

        except socket.timeout:
            _LOGGER.debug(f'Set "{self.name}" state {state} fail, socket timeout')
            self._state = STATE_UNKNOWN

    @property
    def state(self):
        """Return the state of the entity."""
        return self._state

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state == STATE_ON

    def turn_on(self, **kwargs):
        self._set_state(STATE_ON)

    def turn_off(self, **kwargs):
        self._set_state(STATE_OFF)
