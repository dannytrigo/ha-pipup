import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import *
from .services import Services

__LOGGER__ = logging.getLogger(__name__)


def setup(hass: HomeAssistant, config) -> bool:
    __LOGGER__.info("pipup register service")
    services = Services(hass)
    return services.register()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return True
