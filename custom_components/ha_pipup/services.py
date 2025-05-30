import logging
import requests
from typing import List
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.const import CONF_HOST, ATTR_ENTITY_ID
from homeassistant.helpers import config_validation as cv, entity_platform
from .const import *

__LOGGER__ = logging.getLogger(__name__)

# Define schema without entity_id requirement to handle both direct host and entity-based calls
PIPUP_SERVICE_SCHEMA = vol.Schema({
    vol.Optional(ATTR_ENTITY_ID): cv.entity_id,  # Make entity_id optional
    vol.Optional(CONF_HOST): cv.string,  # Add direct host option
    vol.Optional(ATTR_DURATION): cv.positive_int,
    vol.Optional(ATTR_POSITION): cv.positive_int,
    vol.Optional(ATTR_TITLE): cv.string,
    vol.Optional(ATTR_TITLE_COLOUR): vol.All(
        vol.Coerce(tuple), vol.ExactSequence((cv.byte,) * 3)
    ),
    vol.Optional(ATTR_TITLE_SIZE): cv.positive_int,
    vol.Optional(ATTR_MESSAGE): cv.string,
    vol.Optional(ATTR_MESSAGE_COLOUR): vol.All(
        vol.Coerce(tuple), vol.ExactSequence((cv.byte,) * 3)
    ),
    vol.Optional(ATTR_MESSAGE_SIZE): cv.positive_int,
    vol.Optional(ATTR_BACKGROUND_COLOUR): vol.All(
        vol.Coerce(tuple), vol.ExactSequence((cv.byte,) * 3)
    ),
    vol.Optional(ATTR_MEDIA_IMAGE): cv.string,
    vol.Optional(ATTR_MEDIA_VIDEO): cv.string,
    vol.Optional(ATTR_MEDIA_WEB): cv.string,
    vol.Optional(ATTR_MEDIA_WIDTH): cv.positive_int,
    vol.Optional(ATTR_MEDIA_HEIGHT): cv.positive_int,
    vol.Optional(ATTR_IMAGE_FILENAME): cv.string,
})

# Simpler schema for ADB command services
ADB_SERVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.entity_ids
})


class Services:

    def __init__(self, hass: HomeAssistant):
        self.hass = hass

    def register(self) -> bool:
        # Register our services with appropriate schemas
        self.hass.services.register(
            DOMAIN,
            "pipup",
            self.handle_pipup_service_call,
            schema=PIPUP_SERVICE_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL
        )

        # These services still require androidtv entities
        self.hass.services.register(
            DOMAIN,
            "start_pipup",
            self.handle_start_pipup_service_call,
            schema=ADB_SERVICE_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL
        )

        self.hass.services.register(
            DOMAIN,
            "setup_pipup",
            self.handle_setup_pipup_service_call,
            schema=ADB_SERVICE_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL
        )

        return True

    def get_hosts(self, entity_id: str) -> List[str]:
        hosts = []
        try:
            # Check if androidtv integration is loaded
            # if ANDROIDTV_DOMAIN not in self.hass.data:
            #     __LOGGER__.warning(f"AndroidTV integration not found, cannot resolve entity_ids to hosts")
            #     return hosts

            androidtv_platforms = entity_platform.async_get_platforms(self.hass, ANDROIDTV_DOMAIN)
            for androidtv_platform in androidtv_platforms:
                if entity_id in androidtv_platform.entities:
                    try:
                        host = androidtv_platform.config_entry.data[CONF_HOST]
                        __LOGGER__.info(f"Resolved entity {entity_id} to host {host}")
                        hosts.append(host)
                    except KeyError:
                        __LOGGER__.warning(f"Could not find host for entity {entity_id}")
        except Exception as e:
            __LOGGER__.error(f"Error getting hosts for entity {entity_id}: {e}")
        return hosts

    async def handle_pipup_service_call(self, call: ServiceCall):
        # Get hosts either from direct specification or entity resolution
        hosts = []

        # First check if a direct host was provided
        direct_host = call.data.get(CONF_HOST)
        if direct_host:
            hosts = [direct_host]
            __LOGGER__.info(f"Using directly specified host: {direct_host}")
        elif ATTR_ENTITY_ID in call.data:
            # Only try to resolve entity_ids if provided
            entity_id = call.data.get(ATTR_ENTITY_ID, None)
            if entity_id:
                hosts = self.get_hosts(entity_id)
                __LOGGER__.info(f"Resolved entity IDs to hosts: {hosts}")

        if not hosts:
            error_msg = "No hosts found for PiPUP notification. Please provide either entity_ids or a direct host."
            __LOGGER__.warning(error_msg)
            if call.return_response:
                return {"status": False, "error": error_msg}
            return None

        data = {}
        for attr in POST_VARS.keys():
            val = call.data.get(attr, None)
            if val:
                if isinstance(val, tuple):
                    val = f'#{val[0]:02x}{val[1]:02x}{val[2]:02x}'
                data[POST_VARS[attr]] = val
        for attr in MEDIA_POST_VARS.keys():
            val = call.data.get(attr, None)
            if val:
                params = {"uri": val}
                for param in MEDIA_PARAM_VARS.keys():
                    param_val = call.data.get(param, None)
                    if param_val:
                        params[MEDIA_PARAM_VARS[param]] = param_val
                data["media"] = {MEDIA_POST_VARS[attr]: params}

        image_file = None
        status_ok = True
        results = {}
        try:
            image_filename = call.data.get(ATTR_IMAGE_FILENAME, None)
            if image_filename:
                files = {}
                image_file = open(image_filename, 'rb')
                files['image'] = image_file
                post_req = lambda host: requests.post(f'http://{host}:7979/notify', files=files, data=data)
            else:
                post_req = lambda host: requests.post(f'http://{host}:7979/notify', json=data)

            __LOGGER__.info(f"Sending PiPUP notification to hosts: {hosts}")
            __LOGGER__.debug(f"PiPUP notification data: {data}")

            for host in hosts:
                try:
                    r = await self.hass.async_add_executor_job(lambda: post_req(host))
                    results[host] = r.status_code
                    if r.status_code != 200:
                        status_ok = False
                    __LOGGER__.info(f"PiPUP notification to {host} returned status {r.status_code}")
                except Exception as e:
                    status_ok = False
                    results[host] = str(e)
                    __LOGGER__.error(f"Exception sending PiPUP notification to {host}: {e}")
        finally:
            if image_file:
                image_file.close()

        if call.return_response:
            return {"status": status_ok, "results": results}
        else:
            return None

    async def adb_command(self, entity_ids: List[str], command: str):
        # Check if androidtv integration is available before trying to use it
        if ANDROIDTV_DOMAIN not in self.hass.services.services:
            __LOGGER__.warning(f"AndroidTV integration not found, cannot execute ADB command: {command}")
            return False

        try:
            for entity_id in entity_ids:
                await self.hass.services.async_call('androidtv', 'adb_command',
                                                    {'entity_id': entity_id, 'command': command})
            return True
        except Exception as e:
            __LOGGER__.error(f"Error executing ADB command: {e}")
            return False

    async def handle_start_pipup_service_call(self, call: ServiceCall):
        entity_ids = call.data.get(ATTR_ENTITY_ID, [])
        success = await self.adb_command(entity_ids,
                                         'ps -ef | grep -v grep | grep pipup || am start nl.rogro82.pipup/.MainActivity')
        if call.return_response:
            return {"status": success}
        else:
            return None

    async def handle_setup_pipup_service_call(self, call: ServiceCall):
        entity_ids = call.data.get(ATTR_ENTITY_ID, [])
        success = await self.adb_command(entity_ids, 'adb shell appops set nl.rogro82.pipup SYSTEM_ALERT_WINDOW allow')
        if call.return_response:
            return {"status": success}
        else:
            return None
