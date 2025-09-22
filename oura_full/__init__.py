"""Oura Ring Integration for Home Assistant."""
import asyncio
import logging
from datetime import timedelta
from typing import Any, Dict, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
    EVENT_HOMEASSISTANT_STOP,
    Platform,
)
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import (
    config_validation as cv,
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import async_track_time_interval
import voluptuous as vol

from .api import OuraApiClient
from .const import (
    CONF_ENABLE_WEBHOOKS,
    CONF_ENABLE_AI_INSIGHTS,
    CONF_ENABLE_MQTT_BRIDGE,
    CONF_SCAN_INTERVAL,
    CONF_TOKEN,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    SERVICE_REFRESH_DATA,
    SERVICE_GET_WELLNESS_INSIGHT,
    SERVICE_SET_WELLNESS_MODE,
    SERVICE_EXPORT_DATA,
    SERVICE_TRIGGER_RECOVERY,
    SERVICE_CREATE_AUTOMATION,
)
from .coordinator import OuraDataUpdateCoordinator
from .services import OuraServices

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.BUTTON,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Oura Ring integration."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault("devices", {})
    hass.data[DOMAIN].setdefault("entities", {})
    hass.data[DOMAIN].setdefault("services", None)
    
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Oura Ring from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Create API client
    session = async_get_clientsession(hass)
    api_client = OuraApiClient(
        session=session,
        token=entry.data[CONF_TOKEN],
        auth_type="pat",  # Always use PAT since OAuth2 was removed
        base_url=entry.options.get("api_base_url"),
    )
    
    # Verify API connection
    try:
        user_info = await api_client.get_user_info()
        if not user_info:
            raise ConfigEntryNotReady("Unable to fetch user information")
    except Exception as err:
        _LOGGER.error("Error connecting to Oura API: %s", err)
        raise ConfigEntryNotReady(f"Error connecting to Oura API: {err}") from err
    
    # Create update coordinator
    coordinator = OuraDataUpdateCoordinator(
        hass=hass,
        api_client=api_client,
        update_interval=timedelta(
            minutes=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        ),
        enable_ai=entry.options.get(CONF_ENABLE_AI_INSIGHTS, False),
        enable_mqtt=entry.options.get(CONF_ENABLE_MQTT_BRIDGE, False),
        user_info=user_info,
    )
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator and API client
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api_client": api_client,
        "user_info": user_info,
        "services": None,
        "unsub_listeners": [],
    }
    
    # Register device
    await _async_register_device(hass, entry, user_info)
    
    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Set up services
    services = OuraServices(hass, coordinator, entry)
    await services.async_register_services()
    hass.data[DOMAIN][entry.entry_id]["services"] = services
    
    # Set up webhook if enabled
    if entry.options.get(CONF_ENABLE_WEBHOOKS, False):
        await _async_setup_webhooks(hass, entry, coordinator)
    
    # Set up MQTT bridge if enabled
    if entry.options.get(CONF_ENABLE_MQTT_BRIDGE, False):
        await _async_setup_mqtt_bridge(hass, entry, coordinator)
    
    # Register update listener
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    
    # Set up background tasks
    await _async_setup_background_tasks(hass, entry, coordinator)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Cancel background tasks
    for unsub in hass.data[DOMAIN][entry.entry_id].get("unsub_listeners", []):
        unsub()
    
    # Unload services
    if services := hass.data[DOMAIN][entry.entry_id].get("services"):
        await services.async_unregister_services()
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def _async_register_device(
    hass: HomeAssistant,
    entry: ConfigEntry,
    user_info: dict,
) -> None:
    """Register device in device registry."""
    device_registry = dr.async_get(hass)
    
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, user_info["id"])},
        manufacturer="Oura Health",
        model=f"Ring Gen {user_info.get('ring_generation', '3')}",
        name=entry.data.get(CONF_NAME, f"Oura Ring ({user_info.get('email', 'User')})"),
        sw_version=user_info.get("app_version", "Unknown"),
        configuration_url="https://cloud.ouraring.com",
    )
    
    # Store device info for use by entities
    hass.data[DOMAIN][entry.entry_id]["device_info"] = DeviceInfo(
        identifiers={(DOMAIN, user_info["id"])},
        name=entry.data.get(CONF_NAME, f"Oura Ring ({user_info.get('email', 'User')})"),
        manufacturer="Oura Health",
        model=f"Ring Gen {user_info.get('ring_generation', '3')}",
        sw_version=user_info.get("app_version"),
        configuration_url="https://cloud.ouraring.com",
    )


async def _async_setup_webhooks(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: OuraDataUpdateCoordinator,
) -> None:
    """Set up webhook support."""
    from .webhooks import OuraWebhookHandler
    
    webhook_handler = OuraWebhookHandler(hass, coordinator)
    await webhook_handler.async_setup()
    
    hass.data[DOMAIN][entry.entry_id]["webhook_handler"] = webhook_handler


async def _async_setup_mqtt_bridge(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: OuraDataUpdateCoordinator,
) -> None:
    """Set up MQTT bridge for Anima ecosystem."""
    from .mqtt_bridge import OuraMqttBridge
    
    mqtt_bridge = OuraMqttBridge(
        hass=hass,
        coordinator=coordinator,
        topic_prefix=entry.options.get("mqtt_topic_prefix", "anima/wellness/oura"),
    )
    await mqtt_bridge.async_setup()
    
    hass.data[DOMAIN][entry.entry_id]["mqtt_bridge"] = mqtt_bridge


async def _async_setup_background_tasks(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: OuraDataUpdateCoordinator,
) -> None:
    """Set up background tasks."""
    
    # AI insight generation task (runs every 4 hours)
    if entry.options.get(CONF_ENABLE_AI_INSIGHTS, False):
        async def generate_insights(_):
            """Generate AI insights periodically."""
            await coordinator.async_generate_ai_insights()
        
        unsub = async_track_time_interval(
            hass,
            generate_insights,
            timedelta(hours=4),
        )
        hass.data[DOMAIN][entry.entry_id]["unsub_listeners"].append(unsub)
    
    # Trend calculation task (runs every hour)
    async def calculate_trends(_):
        """Calculate trends periodically."""
        await coordinator.async_calculate_trends()
    
    unsub = async_track_time_interval(
        hass,
        calculate_trends,
        timedelta(hours=1),
    )
    hass.data[DOMAIN][entry.entry_id]["unsub_listeners"].append(unsub)
    
    # Cleanup old data task (runs daily)
    async def cleanup_old_data(_):
        """Clean up old data periodically."""
        await coordinator.async_cleanup_old_data()
    
    unsub = async_track_time_interval(
        hass,
        cleanup_old_data,
        timedelta(days=1),
    )
    hass.data[DOMAIN][entry.entry_id]["unsub_listeners"].append(unsub)


class OuraDevice:
    """Representation of an Oura device for entity management."""
    
    def __init__(self, user_info: dict):
        """Initialize the device."""
        self.user_info = user_info
        self.id = user_info["id"]
        self.name = f"Oura Ring ({user_info.get('email', 'User')})"
    
    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.id)},
            name=self.name,
            manufacturer="Oura Health",
            model=f"Ring Gen {self.user_info.get('ring_generation', '3')}",
            sw_version=self.user_info.get("app_version"),
            configuration_url="https://cloud.ouraring.com",
        )