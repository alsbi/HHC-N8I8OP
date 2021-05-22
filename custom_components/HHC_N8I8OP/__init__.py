import logging

__version__ = '0.1'

_LOGGER = logging.getLogger(__name__)


def setup(_hass, _config):
    _LOGGER.debug('setup')
    return True
