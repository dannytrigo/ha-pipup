import logging
import requests
from typing import List
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.const import CONF_HOST, ATTR_ENTITY_ID
from homeassistant.helpers import config_validation as cv, entity_platform
from .const import *

__LOGGER__ = logging.getLogger(__name__)

PIPUP_SERVICE_SCHEMA = {
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
}


class Services:

    def __init__(self, hass: HomeAssistant):
        self.hass = hass

    def register(self) -> bool:
        self.hass.services.register(DOMAIN, "pipup", self.handle_pipup_service_call,
                               schema=cv.make_entity_service_schema(PIPUP_SERVICE_SCHEMA), supports_response=SupportsResponse.OPTIONAL)
        self.hass.services.register(DOMAIN, "start_pipup", self.handle_start_pipup_service_call,
                               schema=cv.make_entity_service_schema({}), supports_response=SupportsResponse.OPTIONAL)
        self.hass.services.register(DOMAIN, "setup_pipup", self.handle_setup_pipup_service_call,
                               schema=cv.make_entity_service_schema({}), supports_response=SupportsResponse.OPTIONAL)
        return True

    def get_hosts(self, entity_ids: List[str]) -> List[str]:
        hosts = []
        androidtv_platforms = entity_platform.async_get_platforms(self.hass, ANDROIDTV_DOMAIN)
        for androidtv_platform in androidtv_platforms:
            for entity_id in entity_ids:
                if entity_id in androidtv_platform.entities:
                    __LOGGER__.info(androidtv_platform.config_entry.data)
                    __LOGGER__.info(androidtv_platform.config_entry.data[CONF_HOST])
                    hosts.append(androidtv_platform.config_entry.data[CONF_HOST])
        return hosts

    async def handle_pipup_service_call(self, call: ServiceCall):
        entity_ids = call.data[ATTR_ENTITY_ID]
        hosts = self.get_hosts(entity_ids)

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
        try:
            image_filename = call.data.get(ATTR_IMAGE_FILENAME, None)
            if image_filename:
                files = {}
                image_file = open(image_filename, 'rb')
                files['image'] = image_file
                # __LOGGER__.info(requests.Request('POST', f'http://host:7979/notify', files=files, data=data).prepare().body)
                post_req = lambda: requests.post(f'http://{host}:7979/notify', files=files, data=data)
            else:
                post_req = lambda: requests.post(f'http://{host}:7979/notify', json=data)

            __LOGGER__.info(data)
            for host in hosts:
                try:
                    r = await self.hass.async_add_executor_job(post_req)
                    if r.status_code != 200:
                        status_ok = False
                    __LOGGER__.info(r.status_code)
                except:
                    status_ok = False
                    __LOGGER__.info(f"Exception: {e}")
        finally:

            if image_file:
                image_file.close()
        if call.return_response:
            return {"status": status_ok}
        else:
            return None

    async def adb_command(self, entity_ids: List[str], command: str):
        for entity_id in entity_ids:
            await self.hass.services.async_call('androidtv', 'adb_command', {'entity_id': entity_id, 'command': command})

    async def handle_start_pipup_service_call(self, call: ServiceCall):
        entity_ids = call.data[ATTR_ENTITY_ID]
        await self.adb_command(entity_ids, 'ps -ef | grep -v grep | grep pipup || am start nl.rogro82.pipup/.MainActivity')
        if call.return_response:
            return {"status": True}
        else:
            return None

    async def handle_setup_pipup_service_call(self, call: ServiceCall):
        entity_ids = call.data[ATTR_ENTITY_ID]
        await self.adb_command(entity_ids, 'adb shell appops set nl.rogro82.pipup SYSTEM_ALERT_WINDOW allow')
        if call.return_response:
            return {"status": True}
        else:
            return None
