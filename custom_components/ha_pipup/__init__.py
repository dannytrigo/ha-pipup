import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import *
from .services import Services

__LOGGER__ = logging.getLogger(__name__)

# We don't need to set DEPENDENCIES because we're making the dependency optional
# But we can specify a list of dependencies that should be loaded first if they are available
SETUP_AFTER = ["androidtv"]


def setup(hass: HomeAssistant, config) -> bool:
    """Set up ha-pipup component."""
    __LOGGER__.info("Setting up ha-pipup services")

    # Check if androidtv is loaded
    if ANDROIDTV_DOMAIN in hass.config.components:
        __LOGGER__.info("AndroidTV integration is loaded")
    else:
        __LOGGER__.warning("AndroidTV integration is not loaded. Some functionality will be limited.")

    # Initialize services
    svcs = Services(hass)
    result = svcs.register()

    # Store services instance for potential use by config entries
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["services"] = svcs

    return result


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    # Make sure services are initialized
    if DOMAIN not in hass.data or "services" not in hass.data[DOMAIN]:
        __LOGGER__.info("Setting up ha-pipup services from config entry")
        services = Services(hass)
        services.register()
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN]["services"] = services

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Services stay registered until Home Assistant restarts
    return True
