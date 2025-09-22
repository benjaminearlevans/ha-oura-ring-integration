"""Switch platform for Oura Ring integration."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import OuraControlEntity

_LOGGER = logging.getLogger(__name__)

SWITCH_DESCRIPTIONS = [
    SwitchEntityDescription(
        key="ai_insights_enabled",
        name="AI Insights",
        icon="mdi:brain",
        entity_category=EntityCategory.CONFIG,
    ),
    SwitchEntityDescription(
        key="mqtt_bridge_enabled",
        name="MQTT Bridge",
        icon="mdi:transit-connection-variant",
        entity_category=EntityCategory.CONFIG,
    ),
    SwitchEntityDescription(
        key="webhooks_enabled",
        name="Webhooks",
        icon="mdi:webhook",
        entity_category=EntityCategory.CONFIG,
    ),
    SwitchEntityDescription(
        key="smart_lighting_enabled",
        name="Smart Lighting Control",
        icon="mdi:lightbulb-auto",
    ),
    SwitchEntityDescription(
        key="temperature_automation",
        name="Temperature Automation",
        icon="mdi:thermostat-auto",
    ),
    SwitchEntityDescription(
        key="sleep_sanctuary_mode",
        name="Sleep Sanctuary Mode",
        icon="mdi:bed",
    ),
    SwitchEntityDescription(
        key="recovery_protocol_enabled",
        name="Recovery Protocol",
        icon="mdi:restore",
    ),
    SwitchEntityDescription(
        key="stress_response_enabled",
        name="Stress Response System",
        icon="mdi:emoticon-stressed-outline",
    ),
    SwitchEntityDescription(
        key="activity_motivation",
        name="Activity Motivation",
        icon="mdi:run",
    ),
    SwitchEntityDescription(
        key="circadian_optimization",
        name="Circadian Optimization",
        icon="mdi:sun-clock",
    ),
    SwitchEntityDescription(
        key="nap_intelligence",
        name="Nap Intelligence",
        icon="mdi:power-sleep",
    ),
    SwitchEntityDescription(
        key="workout_optimization",
        name="Workout Optimization",
        icon="mdi:dumbbell",
    ),
    SwitchEntityDescription(
        key="privacy_mode",
        name="Privacy Mode",
        icon="mdi:incognito",
        entity_category=EntityCategory.CONFIG,
    ),
    SwitchEntityDescription(
        key="debug_logging",
        name="Debug Logging",
        icon="mdi:bug",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
]


class OuraSwitch(OuraControlEntity, SwitchEntity):
    """Representation of an Oura switch entity."""

    entity_description: SwitchEntityDescription

    def __init__(
        self,
        coordinator,
        description: SwitchEntityDescription,
        entry_id: str,
        device_info: Dict,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator, entry_id, description.key)
        self.entity_description = description
        self._attr_device_info = device_info
        self._attr_has_entity_name = True
        
        # Initialize state from coordinator or config
        self._is_on = self._get_initial_state()

    def _get_initial_state(self) -> bool:
        """Get initial state from coordinator or config."""
        key = self.entity_description.key
        
        # Check coordinator settings first
        if hasattr(self.coordinator, 'switch_states'):
            return self.coordinator.switch_states.get(key, False)
        
        # Default states based on switch type
        defaults = {
            "ai_insights_enabled": self.coordinator.enable_ai,
            "mqtt_bridge_enabled": self.coordinator.enable_mqtt,
            "webhooks_enabled": False,
            "smart_lighting_enabled": True,
            "temperature_automation": True,
            "sleep_sanctuary_mode": True,
            "recovery_protocol_enabled": True,
            "stress_response_enabled": True,
            "activity_motivation": True,
            "circadian_optimization": True,
            "nap_intelligence": False,
            "workout_optimization": True,
            "privacy_mode": False,
            "debug_logging": False,
        }
        
        return defaults.get(key, False)

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._async_set_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._async_set_state(False)

    async def _async_set_state(self, state: bool) -> None:
        """Set the switch state and handle side effects."""
        self._is_on = state
        key = self.entity_description.key
        
        # Store state in coordinator
        if not hasattr(self.coordinator, 'switch_states'):
            self.coordinator.switch_states = {}
        self.coordinator.switch_states[key] = state
        
        # Handle specific switch logic
        if key == "ai_insights_enabled":
            await self._handle_ai_insights(state)
        elif key == "mqtt_bridge_enabled":
            await self._handle_mqtt_bridge(state)
        elif key == "webhooks_enabled":
            await self._handle_webhooks(state)
        elif key == "smart_lighting_enabled":
            await self._handle_smart_lighting(state)
        elif key == "temperature_automation":
            await self._handle_temperature_automation(state)
        elif key == "sleep_sanctuary_mode":
            await self._handle_sleep_sanctuary(state)
        elif key == "recovery_protocol_enabled":
            await self._handle_recovery_protocol(state)
        elif key == "stress_response_enabled":
            await self._handle_stress_response(state)
        elif key == "activity_motivation":
            await self._handle_activity_motivation(state)
        elif key == "circadian_optimization":
            await self._handle_circadian_optimization(state)
        elif key == "nap_intelligence":
            await self._handle_nap_intelligence(state)
        elif key == "workout_optimization":
            await self._handle_workout_optimization(state)
        elif key == "privacy_mode":
            await self._handle_privacy_mode(state)
        elif key == "debug_logging":
            await self._handle_debug_logging(state)
        
        # Update state
        self.async_write_ha_state()
        
        # Fire event for automations
        self.hass.bus.async_fire(
            f"{DOMAIN}_switch_changed",
            {
                "entity_id": self.entity_id,
                "switch": key,
                "state": state,
            },
        )

    async def _handle_ai_insights(self, enabled: bool) -> None:
        """Handle AI insights toggle."""
        self.coordinator.enable_ai = enabled
        
        if enabled:
            # Generate insights immediately
            await self.coordinator.async_generate_ai_insights()
            await self._create_notification(
                "AI Insights Enabled",
                "AI-powered wellness insights are now active."
            )
        else:
            # Clear existing insights
            self.coordinator.ai_insights.clear()
            await self._create_notification(
                "AI Insights Disabled",
                "AI insights have been turned off."
            )

    async def _handle_mqtt_bridge(self, enabled: bool) -> None:
        """Handle MQTT bridge toggle."""
        self.coordinator.enable_mqtt = enabled
        
        if enabled:
            # Initialize MQTT bridge
            try:
                from .mqtt_bridge import OuraMqttBridge
                if not hasattr(self.coordinator, 'mqtt_bridge'):
                    mqtt_bridge = OuraMqttBridge(
                        hass=self.hass,
                        coordinator=self.coordinator,
                        topic_prefix="anima/wellness/oura"
                    )
                    await mqtt_bridge.async_setup()
                    self.coordinator.mqtt_bridge = mqtt_bridge
                
                await self._create_notification(
                    "MQTT Bridge Enabled",
                    "Oura data is now being published to MQTT."
                )
            except Exception as err:
                _LOGGER.error("Failed to enable MQTT bridge: %s", err)
                self._is_on = False
        else:
            # Disable MQTT bridge
            if hasattr(self.coordinator, 'mqtt_bridge'):
                await self.coordinator.mqtt_bridge.async_cleanup()
                delattr(self.coordinator, 'mqtt_bridge')
            
            await self._create_notification(
                "MQTT Bridge Disabled",
                "MQTT publishing has been stopped."
            )

    async def _handle_webhooks(self, enabled: bool) -> None:
        """Handle webhooks toggle."""
        if enabled:
            try:
                from .webhooks import OuraWebhookHandler
                if not hasattr(self.coordinator, 'webhook_handler'):
                    webhook_handler = OuraWebhookHandler(self.hass, self.coordinator)
                    await webhook_handler.async_setup()
                    self.coordinator.webhook_handler = webhook_handler
                
                await self._create_notification(
                    "Webhooks Enabled",
                    "Real-time webhook updates are now active."
                )
            except Exception as err:
                _LOGGER.error("Failed to enable webhooks: %s", err)
                self._is_on = False
        else:
            if hasattr(self.coordinator, 'webhook_handler'):
                await self.coordinator.webhook_handler.async_cleanup()
                delattr(self.coordinator, 'webhook_handler')
            
            await self._create_notification(
                "Webhooks Disabled",
                "Webhook updates have been disabled."
            )

    async def _handle_smart_lighting(self, enabled: bool) -> None:
        """Handle smart lighting automation."""
        await self._fire_automation_event("smart_lighting", enabled)

    async def _handle_temperature_automation(self, enabled: bool) -> None:
        """Handle temperature automation."""
        await self._fire_automation_event("temperature_automation", enabled)

    async def _handle_sleep_sanctuary(self, enabled: bool) -> None:
        """Handle sleep sanctuary mode."""
        await self._fire_automation_event("sleep_sanctuary", enabled)

    async def _handle_recovery_protocol(self, enabled: bool) -> None:
        """Handle recovery protocol."""
        await self._fire_automation_event("recovery_protocol", enabled)

    async def _handle_stress_response(self, enabled: bool) -> None:
        """Handle stress response system."""
        await self._fire_automation_event("stress_response", enabled)

    async def _handle_activity_motivation(self, enabled: bool) -> None:
        """Handle activity motivation."""
        await self._fire_automation_event("activity_motivation", enabled)

    async def _handle_circadian_optimization(self, enabled: bool) -> None:
        """Handle circadian optimization."""
        await self._fire_automation_event("circadian_optimization", enabled)

    async def _handle_nap_intelligence(self, enabled: bool) -> None:
        """Handle nap intelligence."""
        await self._fire_automation_event("nap_intelligence", enabled)

    async def _handle_workout_optimization(self, enabled: bool) -> None:
        """Handle workout optimization."""
        await self._fire_automation_event("workout_optimization", enabled)

    async def _handle_privacy_mode(self, enabled: bool) -> None:
        """Handle privacy mode."""
        if enabled:
            # Disable certain automations when guests are present
            await self._fire_automation_event("privacy_mode_enabled", True)
            await self._create_notification(
                "Privacy Mode Enabled",
                "Certain automations are disabled for privacy."
            )
        else:
            await self._fire_automation_event("privacy_mode_disabled", True)
            await self._create_notification(
                "Privacy Mode Disabled",
                "All automations are now active."
            )

    async def _handle_debug_logging(self, enabled: bool) -> None:
        """Handle debug logging."""
        import logging
        
        logger = logging.getLogger("custom_components.oura_full")
        
        if enabled:
            logger.setLevel(logging.DEBUG)
            _LOGGER.info("Debug logging enabled for Oura integration")
        else:
            logger.setLevel(logging.INFO)
            _LOGGER.info("Debug logging disabled for Oura integration")

    async def _fire_automation_event(self, automation_type: str, enabled: bool) -> None:
        """Fire event for automation systems."""
        self.hass.bus.async_fire(
            f"{DOMAIN}_automation_toggle",
            {
                "automation_type": automation_type,
                "enabled": enabled,
                "readiness_score": self.coordinator.readiness_data[0].score if self.coordinator.readiness_data else None,
                "wellness_phase": self.coordinator.wellness_phase,
            },
        )

    async def _create_notification(self, title: str, message: str) -> None:
        """Create a notification."""
        # Check if notifications are enabled
        notification_preference = getattr(self.coordinator, 'notification_preference', 'all')
        
        if notification_preference != "none":
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": title,
                    "message": message,
                    "notification_id": f"{DOMAIN}_{self.entity_description.key}",
                },
            )

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        attributes = super().extra_state_attributes
        key = self.entity_description.key
        
        # Add context-specific attributes
        if key == "ai_insights_enabled":
            attributes["last_insight_generated"] = str(
                max(self.coordinator.ai_insights.values(), default="Never")
            ) if self.coordinator.ai_insights else "Never"
        
        elif key == "recovery_protocol_enabled":
            if self.coordinator.readiness_data:
                attributes["current_readiness"] = self.coordinator.readiness_data[0].score
                attributes["recovery_needed"] = self.coordinator.readiness_data[0].score < 70
        
        elif key == "stress_response_enabled":
            if self.coordinator.stress_data:
                attributes["current_stress"] = self.coordinator.stress_data[0].score
                attributes["high_stress_active"] = self.coordinator.stress_data[0].score > 60
        
        elif key == "circadian_optimization":
            attributes.update(self.coordinator.circadian_alignment)
        
        elif key == "privacy_mode":
            attributes["automations_affected"] = [
                "smart_lighting", "temperature_automation", "activity_motivation"
            ]
        
        return attributes


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Oura switch entities from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    device_info = hass.data[DOMAIN][config_entry.entry_id]["device_info"]
    
    entities = []
    for description in SWITCH_DESCRIPTIONS:
        entities.append(
            OuraSwitch(
                coordinator=coordinator,
                description=description,
                entry_id=config_entry.entry_id,
                device_info=device_info,
            )
        )
    
    async_add_entities(entities, True)
