import logging
import socket

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from cachetools.func import ttl_cache
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNKNOWN
from homeassistant.helpers.config_validation import (PLATFORM_SCHEMA)

from .const import *

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_IP): cv.string,
    vol.Optional(CONF_NAME): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.string,
    vol.Optional(ICON, default="mdi:lightbulb"): cv.string,
    vol.Required(CONF_LIGHTS): cv.positive_int,
})


async def async_setup_platform(
        hass,
        config,
        async_add_entities,
        discovery_info=None,
) -> None:
    devices = []

    switch = Hhcn8I8opSwitch(config.get(CONF_IP), config.get(CONF_PORT), name=config.get(CONF_NAME))

    for index in range(config[CONF_LIGHTS]):
        devices.append(
            Hhcn8I8opEntity(switch, index, icon=config.get(ICON))
        )

    async_add_entities(devices, update_before_add=True)


class Hhcn8I8opSwitch:
    def __init__(self, ip, port, name=None):
        self.name = name
        self.ip = ip
        self.port = int(port)
        self.collection = {}

    def execute_socket_command(self, command: str) -> str:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(WAIT_TIMEOUT)
            sock.connect((self.ip, self.port))
            sock.send(str(command).encode())
            return sock.recv(8192).decode()

    @ttl_cache(1, 1)
    def update_state(self):

        try:
            response = self.execute_socket_command('read')
            state = [STATE_ON if bool(int(s)) else STATE_OFF for s in list(reversed(response.split('relay')[1]))]
        except socket.timeout:
            state = [STATE_UNKNOWN] * len(self.collection)

        for i, switch in self.collection.items():
            switch._state = state[i]


class Hhcn8I8opEntity(SwitchEntity):
    def __init__(self, switch: Hhcn8I8opSwitch, index: int, icon=None):
        self.switch = switch
        self._index = index

        self.switch.collection[self._index] = self

        if self.switch.name:
            self._name = '{}_{}'.format(self.switch.name, self.index)
        else:
            self._name = '{}'.format(self.index)

        self.no_domain_ = self._name.startswith("!")
        if self.no_domain_:
            self._name = self.name[1:]
        self._unique_id = self._name.lower().replace(' ', '_')

        self._state = STATE_UNKNOWN
        self._icon = icon

        _LOGGER.debug(f'Start switch {self._unique_id}')

    @property
    def index(self):
        return self._index + 1

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
            'index': self.index,
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

    def update(self):
        self.switch.update_state()

    def _set_state(self, state: str):
        try:

            self.switch.execute_socket_command(f'{state}{self.index}')
            self._state = state

        except socket.timeout:
            _LOGGER.debug(f'Set "{self.name}" state {state} fail, socket timeout')
            self._state = STATE_UNKNOWN

        self.schedule_update_ha_state()

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
