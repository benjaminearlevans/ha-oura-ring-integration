"""Config flow for Oura Ring integration."""
import asyncio
import logging
from typing import Any, Dict, Optional

import aiohttp
import voluptuous as vol
from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_NAME, CONF_TOKEN
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .api import OuraApiClient
from .const import (
    CONF_ENABLE_AI_INSIGHTS,
    CONF_ENABLE_MQTT_BRIDGE,
    CONF_ENABLE_WEBHOOKS,
    CONF_SCAN_INTERVAL,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# Data schemas
DATA_SCHEMA_USER = vol.Schema({
    vol.Required(CONF_TOKEN): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})

OPTIONS_SCHEMA = vol.Schema({
    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
        vol.Coerce(int), vol.Range(min=5, max=120)
    ),
    vol.Optional(CONF_ENABLE_WEBHOOKS, default=False): cv.boolean,
    vol.Optional(CONF_ENABLE_AI_INSIGHTS, default=False): cv.boolean,
    vol.Optional(CONF_ENABLE_MQTT_BRIDGE, default=False): cv.boolean,
})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Oura Ring."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.user_info = None

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # Validate the token
                session = async_get_clientsession(self.hass)
                api_client = OuraApiClient(
                    session=session,
                    token=user_input[CONF_TOKEN],
                    auth_type="pat"
                )
                
                # Test connection and get user info
                user_info = await api_client.get_user_info()
                if not user_info:
                    raise InvalidAuth("Unable to authenticate with provided token")
                
                self.user_info = user_info
                
                # Check for existing entries
                await self.async_set_unique_id(user_info.get("id"))
                self._abort_if_unique_id_configured()
                
                # Create the config entry
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, f"Oura Ring ({user_info.get('email', 'User')})"),
                    data={
                        CONF_TOKEN: user_input[CONF_TOKEN],
                        CONF_NAME: user_input.get(CONF_NAME, DEFAULT_NAME),
                        "user_id": user_info.get("id"),
                        "email": user_info.get("email"),
                    },
                )
                
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA_USER,
            errors=errors,
            description_placeholders={
                "token_url": "https://cloud.ouraring.com/personal-access-tokens"
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Oura Ring."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Pre-fill with current options
        current_options = self.config_entry.options
        
        options_schema = vol.Schema({
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=current_options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ): vol.All(vol.Coerce(int), vol.Range(min=5, max=120)),
            vol.Optional(
                CONF_ENABLE_WEBHOOKS,
                default=current_options.get(CONF_ENABLE_WEBHOOKS, False)
            ): cv.boolean,
            vol.Optional(
                CONF_ENABLE_AI_INSIGHTS,
                default=current_options.get(CONF_ENABLE_AI_INSIGHTS, False)
            ): cv.boolean,
            vol.Optional(
                CONF_ENABLE_MQTT_BRIDGE,
                default=current_options.get(CONF_ENABLE_MQTT_BRIDGE, False)
            ): cv.boolean,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""


async def validate_input(hass: core.HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    session = async_get_clientsession(hass)
    api_client = OuraApiClient(
        session=session,
        token=data[CONF_TOKEN],
        auth_type="pat"
    )

    try:
        user_info = await api_client.get_user_info()
        if not user_info:
            raise InvalidAuth("Cannot retrieve user information")
    except Exception as err:
        _LOGGER.error("Error connecting to Oura API: %s", err)
        raise CannotConnect("Cannot connect to Oura API") from err

    # Return info that you want to store in the config entry.
    return {
        "title": f"Oura Ring ({user_info.get('email', 'User')})",
        "user_info": user_info,
    }