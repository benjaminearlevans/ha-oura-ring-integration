"""Select platform for Oura Ring integration."""
import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ACTIVITY_INTENSITIES,
    DOMAIN,
    READINESS_LEVELS,
    WELLNESS_PHASES,
)
from .entity import OuraControlEntity

_LOGGER = logging.getLogger(__name__)

SELECT_DESCRIPTIONS = [
    SelectEntityDescription(
        key="wellness_phase_override",
        name="Wellness Phase Override",
        options=["auto"] + WELLNESS_PHASES,
        icon="mdi:state-machine",
    ),
    SelectEntityDescription(
        key="activity_intensity_target",
        name="Activity Intensity Target",
        options=ACTIVITY_INTENSITIES,
        icon="mdi:speedometer",
    ),
    SelectEntityDescription(
        key="readiness_threshold",
        name="Readiness Alert Threshold",
        options=READINESS_LEVELS,
        icon="mdi:alert",
        entity_category=EntityCategory.CONFIG,
    ),
    SelectEntityDescription(
        key="automation_mode",
        name="Automation Mode",
        options=["disabled", "minimal", "balanced", "full"],
        icon="mdi:home-automation",
        entity_category=EntityCategory.CONFIG,
    ),
    SelectEntityDescription(
        key="notification_preference",
        name="Notification Preference",
        options=["none", "critical", "important", "all"],
        icon="mdi:bell",
        entity_category=EntityCategory.CONFIG,
    ),
]


class OuraSelect(OuraControlEntity, SelectEntity):
    """Representation of an Oura select entity."""

    entity_description: SelectEntityDescription

    def __init__(
        self,
        coordinator,
        description: SelectEntityDescription,
        entry_id: str,
        device_info: Dict,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator, entry_id, description.key)
        self.entity_description = description
        self._attr_device_info = device_info
        self._attr_has_entity_name = True
        self._attr_options = list(description.options)
        
        # Store current selection in coordinator
        self._current_option = description.options[0]
        
        # Load saved preference if available
        self._load_preference()

    @property
    def current_option(self) -> Optional[str]:
        """Return the selected entity option."""
        key = self.entity_description.key
        
        if key == "wellness_phase_override":
            # Check if there's an active override
            if hasattr(self.coordinator, "wellness_mode_override"):
                override = self.coordinator.wellness_mode_override
                if override and override.get("mode"):
                    return override["mode"]
            return "auto"
        
        elif key == "activity_intensity_target":
            # Return current target based on wellness phase
            phase = self.coordinator.wellness_phase
            if phase == "recovery":
                return "rest"
            elif phase == "maintenance":
                return "low"
            elif phase == "challenge":
                return "medium"
            elif phase == "peak":
                return "high"
            return "medium"
        
        elif key == "readiness_threshold":
            # Return based on current readiness
            if self.coordinator.readiness_data:
                readiness = self.coordinator.readiness_data[0]
                return readiness.readiness_level.value.lower()
            return "medium"
        
        elif key == "automation_mode":
            return self._current_option
        
        elif key == "notification_preference":
            return self._current_option
        
        return self._current_option

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        self._current_option = option
        key = self.entity_description.key
        
        if key == "wellness_phase_override":
            await self._set_wellness_phase(option)
        
        elif key == "activity_intensity_target":
            await self._set_activity_target(option)
        
        elif key == "readiness_threshold":
            await self._set_readiness_threshold(option)
        
        elif key == "automation_mode":
            await self._set_automation_mode(option)
        
        elif key == "notification_preference":
            await self._set_notification_preference(option)
        
        # Save preference
        self._save_preference(option)
        
        # Update state
        self.async_write_ha_state()

    async def _set_wellness_phase(self, phase: str) -> None:
        """Set wellness phase override."""
        if phase == "auto":
            # Clear override
            self.coordinator.wellness_mode_override = None
        else:
            # Set override
            from datetime import datetime, timedelta
            self.coordinator.wellness_mode_override = {
                "mode": phase,
                "expires": datetime.now() + timedelta(hours=24),
            }
        
        # Fire event for automations
        self.hass.bus.async_fire(
            f"{DOMAIN}_wellness_mode_changed",
            {"mode": phase, "entity_id": self.entity_id},
        )

    async def _set_activity_target(self, intensity: str) -> None:
        """Set activity intensity target."""
        # Store in coordinator for use by automations
        self.coordinator.activity_target = intensity
        
        # Create notification
        await self._create_notification(
            f"Activity target set to {intensity}",
            "Automations will adjust recommendations accordingly.",
        )

    async def _set_readiness_threshold(self, level: str) -> None:
        """Set readiness alert threshold."""
        # Store threshold for alerts
        threshold_map = {
            "low": 60,
            "medium": 70,
            "high": 85,
            "optimal": 90,
        }
        
        self.coordinator.readiness_threshold = threshold_map.get(level, 70)
        
        await self._create_notification(
            f"Readiness alerts set to {level}",
            f"You'll be notified when readiness is below {threshold_map.get(level, 70)}%",
        )

    async def _set_automation_mode(self, mode: str) -> None:
        """Set automation mode."""
        # Update all automation entities based on mode
        mode_settings = {
            "disabled": {"enabled": False},
            "minimal": {"enabled": True, "aggressive": False, "ai": False},
            "balanced": {"enabled": True, "aggressive": False, "ai": True},
            "full": {"enabled": True, "aggressive": True, "ai": True},
        }
        
        settings = mode_settings.get(mode, {})
        
        # Apply settings
        self.coordinator.automation_settings = settings
        
        # Fire event for automations to reconfigure
        self.hass.bus.async_fire(
            f"{DOMAIN}_automation_mode_changed",
            {"mode": mode, "settings": settings},
        )

    async def _set_notification_preference(self, preference: str) -> None:
        """Set notification preference."""
        # Store preference
        self.coordinator.notification_preference = preference
        
        # Update notification service
        if preference == "none":
            _LOGGER.info("Notifications disabled")
        else:
            _LOGGER.info("Notification preference set to: %s", preference)

    async def _create_notification(self, title: str, message: str) -> None:
        """Create a notification."""
        if self.coordinator.notification_preference != "none":
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": title,
                    "message": message,
                    "notification_id": f"{DOMAIN}_{self.entity_description.key}",
                },
            )

    def _load_preference(self) -> None:
        """Load saved preference from storage."""
        # This would typically load from Home Assistant's storage
        # For now, use default
        pass

    def _save_preference(self, option: str) -> None:
        """Save preference to storage."""
        # This would typically save to Home Assistant's storage
        # For now, just log
        _LOGGER.debug("Saving preference %s = %s", self.entity_description.key, option)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        attributes = super().extra_state_attributes
        key = self.entity_description.key
        
        if key == "wellness_phase_override":
            if hasattr(self.coordinator, "wellness_mode_override"):
                override = self.coordinator.wellness_mode_override
                if override:
                    attributes["expires"] = str(override.get("expires"))
                    attributes["auto_phase"] = self.coordinator.wellness_phase
        
        elif key == "activity_intensity_target":
            attributes["recommended"] = self._get_recommended_intensity()
            attributes["current_activity_level"] = self._get_current_activity_level()
        
        elif key == "readiness_threshold":
            if self.coordinator.readiness_data:
                attributes["current_readiness"] = self.coordinator.readiness_data[0].score
                attributes["threshold_value"] = getattr(
                    self.coordinator, "readiness_threshold", 70
                )
        
        elif key == "automation_mode":
            attributes["settings"] = getattr(
                self.coordinator, "automation_settings", {}
            )
        
        return attributes

    def _get_recommended_intensity(self) -> str:
        """Get recommended intensity based on readiness."""
        if not self.coordinator.readiness_data:
            return "medium"
        
        readiness = self.coordinator.readiness_data[0]
        if readiness.score:
            if readiness.score >= 85:
                return "high"
            elif readiness.score >= 70:
                return "medium"
            elif readiness.score >= 60:
                return "low"
        return "rest"

    def _get_current_activity_level(self) -> str:
        """Get current activity level."""
        if self.coordinator.activity_data:
            return self.coordinator.activity_data[0].activity_level.value
        return "unknown"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Oura select entities from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    device_info = hass.data[DOMAIN][config_entry.entry_id]["device_info"]
    
    entities = []
    for description in SELECT_DESCRIPTIONS:
        entities.append(
            OuraSelect(
                coordinator=coordinator,
                description=description,
                entry_id=config_entry.entry_id,
                device_info=device_info,
            )
        )
    
    async_add_entities(entities, True)