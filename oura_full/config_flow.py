"""Config flow for Oura Ring integration."""
import asyncio
import logging
from typing import Any, Dict, Optional
from urllib.parse import urlencode

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
    CONF_AUTH_TYPE,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_ENABLE_AI_INSIGHTS,
    CONF_ENABLE_MQTT_BRIDGE,
    CONF_ENABLE_WEBHOOKS,
    CONF_SCAN_INTERVAL,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# OAuth2 Configuration
OAUTH_AUTHORIZE_URL = "https://cloud.ouraring.com/oauth/authorize"
OAUTH_TOKEN_URL = "https://api.ouraring.com/oauth/token"

# Data schemas
DATA_SCHEMA_AUTH_TYPE = vol.Schema({
    vol.Required("auth_type", default="pat"): vol.In(["pat", "oauth2"])
})

DATA_SCHEMA_PAT = vol.Schema({
    vol.Required(CONF_TOKEN): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})

DATA_SCHEMA_OAUTH2 = vol.Schema({
    vol.Required(CONF_CLIENT_ID): cv.string,
    vol.Required(CONF_CLIENT_SECRET): cv.string,
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
        self.auth_type = None
        self.oauth_data = {}
        self.user_info = None

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            self.auth_type = user_input["auth_type"]
            
            if self.auth_type == "pat":
                return await self.async_step_pat()
            else:
                return await self.async_step_oauth2()

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA_AUTH_TYPE,
            description_placeholders={
                "docs_url": "https://cloud.ouraring.com/docs/authentication"
            },
        )

    async def async_step_pat(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle Personal Access Token authentication."""
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
                        CONF_AUTH_TYPE: "pat",
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
            step_id="pat",
            data_schema=DATA_SCHEMA_PAT,
            errors=errors,
            description_placeholders={
                "token_url": "https://cloud.ouraring.com/personal-access-tokens"
            },
        )

    async def async_step_oauth2(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle OAuth2 authentication setup."""
        errors = {}

        if user_input is not None:
            # Store OAuth2 credentials
            self.oauth_data = {
                CONF_CLIENT_ID: user_input[CONF_CLIENT_ID],
                CONF_CLIENT_SECRET: user_input[CONF_CLIENT_SECRET],
                CONF_NAME: user_input.get(CONF_NAME, DEFAULT_NAME),
            }
            
            # Start OAuth2 flow
            return await self.async_step_oauth2_authorize()

        return self.async_show_form(
            step_id="oauth2",
            data_schema=DATA_SCHEMA_OAUTH2,
            errors=errors,
            description_placeholders={
                "app_url": "https://cloud.ouraring.com/oauth/applications"
            },
        )

    async def async_step_oauth2_authorize(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle OAuth2 authorization."""
        if user_input is not None:
            # This step is handled by the external auth flow
            return await self.async_step_oauth2_token(user_input)

        # Generate OAuth2 authorization URL
        redirect_uri = f"{self.hass.config.external_url}/auth/external/callback"
        
        auth_params = {
            "client_id": self.oauth_data[CONF_CLIENT_ID],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "daily",  # Oura API scope
            "state": self.flow_id,  # Use flow ID as state for security
        }
        
        auth_url = f"{OAUTH_AUTHORIZE_URL}?{urlencode(auth_params)}"
        
        return self.async_external_step(
            step_id="oauth2_authorize",
            url=auth_url,
        )

    async def async_step_oauth2_token(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle OAuth2 token exchange."""
        if "code" not in user_input:
            return self.async_abort(reason="oauth_error")
        
        try:
            # Exchange authorization code for access token
            session = async_get_clientsession(self.hass)
            
            token_data = {
                "grant_type": "authorization_code",
                "code": user_input["code"],
                "client_id": self.oauth_data[CONF_CLIENT_ID],
                "client_secret": self.oauth_data[CONF_CLIENT_SECRET],
                "redirect_uri": f"{self.hass.config.external_url}/auth/external/callback",
            }
            
            async with session.post(OAUTH_TOKEN_URL, data=token_data) as response:
                if response.status != 200:
                    _LOGGER.error("OAuth2 token exchange failed: %s", response.status)
                    return self.async_abort(reason="oauth_error")
                
                token_response = await response.json()
                access_token = token_response.get("access_token")
                refresh_token = token_response.get("refresh_token")
                
                if not access_token:
                    return self.async_abort(reason="oauth_error")
            
            # Test the token and get user info
            api_client = OuraApiClient(
                session=session,
                token=access_token,
                auth_type="oauth2"
            )
            
            user_info = await api_client.get_user_info()
            if not user_info:
                raise InvalidAuth("Unable to authenticate with OAuth2 token")
            
            self.user_info = user_info
            
            # Check for existing entries
            await self.async_set_unique_id(user_info.get("id"))
            self._abort_if_unique_id_configured()
            
            # Create the config entry
            return self.async_create_entry(
                title=self.oauth_data.get(CONF_NAME, f"Oura Ring ({user_info.get('email', 'User')})"),
                data={
                    CONF_AUTH_TYPE: "oauth2",
                    CONF_TOKEN: access_token,
                    "refresh_token": refresh_token,
                    CONF_CLIENT_ID: self.oauth_data[CONF_CLIENT_ID],
                    CONF_CLIENT_SECRET: self.oauth_data[CONF_CLIENT_SECRET],
                    CONF_NAME: self.oauth_data.get(CONF_NAME, DEFAULT_NAME),
                    "user_id": user_info.get("id"),
                    "email": user_info.get("email"),
                },
            )
            
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception("OAuth2 token exchange error: %s", err)
            return self.async_abort(reason="oauth_error")

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
        auth_type=data.get(CONF_AUTH_TYPE, "pat")
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