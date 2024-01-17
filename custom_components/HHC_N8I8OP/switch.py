import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.config_validation import (PLATFORM_SCHEMA)
from tuya_connector import TuyaOpenAPI

from .const import *

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(ACCESS_ID): cv.string,
    vol.Required(ACCESS_KEY): cv.string,
    vol.Required(DEVICE_ID): cv.string,
    vol.Optional(CONF_NAME, default="dorrbell"): cv.string,
})


async def async_setup_platform(
        hass,
        config,
        async_add_entities,
        discovery_info=None,
) -> None:
    button = TuyaDoorBellOpen(config.get(ACCESS_ID),
                              config.get(ACCESS_KEY),
                              config.get(DEVICE_ID),
                              name=config.get(CONF_NAME)
                              )

    async_add_entities([button], update_before_add=False)


class TuyaDoorBellOpen(ButtonEntity):
    def __init__(self, access_id, access_key, device_id, name='dorrbell'):
        self.access_id = access_id
        self.access_key = access_key
        self.device_id = device_id

        self._name = name
        self._unique_id = self._name.lower().replace(' ', '_')
        _LOGGER.debug(f'Init {self._unique_id}')

    def press(self) -> None:
        openapi = TuyaOpenAPI(API_ENDPOINT, self.access_id, self.access_key)
        openapi.connect()
        response = openapi.post(
            f"/v2.0/cloud/thing/{self.device_id}/shadow/properties/issue", {
                "properties": {
                    "accessory_lock": True
                }
            }
        )
        _LOGGER.debug(f'Press button {self._unique_id}')
