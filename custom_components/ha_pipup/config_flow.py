import logging
from typing import Any
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from .const import *

__LOGGER__ = logging.getLogger(__name__)


class PipupConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow"""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors = {}

        if user_input is not None:
            # Check if AndroidTV integration is available
            if ANDROIDTV_DOMAIN in self.hass.data:
                __LOGGER__.info("AndroidTV integration is available. Full functionality enabled.")
            else:
                # Just log a warning - the component will still work with direct host option
                __LOGGER__.warning(
                    "AndroidTV integration not detected. Some functionality will be limited. "
                    "You can still use the PiPUP service by specifying host IPs directly."
                )

            return self.async_create_entry(
                title=user_input.get(CONF_NAME, DEFAULT_NAME),
                data={},
            )

        # Show the configuration form
        data_schema = vol.Schema({
            vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_import(self, user_input: dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(user_input)
