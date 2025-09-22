"""Number platform for Oura Ring integration."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import OuraControlEntity

_LOGGER = logging.getLogger(__name__)

NUMBER_DESCRIPTIONS = [
    NumberEntityDescription(
        key="readiness_threshold",
        name="Readiness Alert Threshold",
        icon="mdi:heart-pulse",
        native_min_value=0,
        native_max_value=100,
        native_step=5,
        native_unit_of_measurement="points",
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
    ),
    NumberEntityDescription(
        key="sleep_score_threshold",
        name="Sleep Score Alert Threshold",
        icon="mdi:sleep",
        native_min_value=0,
        native_max_value=100,
        native_step=5,
        native_unit_of_measurement="points",
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
    ),
    NumberEntityDescription(
        key="activity_goal_steps",
        name="Daily Step Goal",
        icon="mdi:walk",
        native_min_value=1000,
        native_max_value=50000,
        native_step=500,
        native_unit_of_measurement="steps",
        mode=NumberMode.BOX,
    ),
    NumberEntityDescription(
        key="temperature_alert_threshold",
        name="Temperature Alert Threshold",
        icon="mdi:thermometer-alert",
        native_min_value=0.1,
        native_max_value=2.0,
        native_step=0.1,
        native_unit_of_measurement="°C",
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
    ),
    NumberEntityDescription(
        key="stress_alert_threshold",
        name="Stress Alert Threshold",
        icon="mdi:emoticon-stressed",
        native_min_value=0,
        native_max_value=100,
        native_step=5,
        native_unit_of_measurement="points",
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
    ),
    NumberEntityDescription(
        key="hrv_target_range_min",
        name="HRV Target Range (Min)",
        icon="mdi:pulse",
        native_min_value=10,
        native_max_value=200,
        native_step=5,
        native_unit_of_measurement="ms",
        mode=NumberMode.BOX,
    ),
    NumberEntityDescription(
        key="hrv_target_range_max",
        name="HRV Target Range (Max)",
        icon="mdi:pulse",
        native_min_value=10,
        native_max_value=200,
        native_step=5,
        native_unit_of_measurement="ms",
        mode=NumberMode.BOX,
    ),
    NumberEntityDescription(
        key="optimal_sleep_duration",
        name="Optimal Sleep Duration",
        icon="mdi:clock-time-eight",
        native_min_value=6.0,
        native_max_value=12.0,
        native_step=0.25,
        native_unit_of_measurement="hours",
        mode=NumberMode.SLIDER,
    ),
    NumberEntityDescription(
        key="bedtime_target_hour",
        name="Target Bedtime Hour",
        icon="mdi:bed-clock",
        native_min_value=19,
        native_max_value=26,
        native_step=1,
        native_unit_of_measurement="hour",
        mode=NumberMode.SLIDER,
    ),
    NumberEntityDescription(
        key="wake_target_hour",
        name="Target Wake Hour",
        icon="mdi:alarm",
        native_min_value=4,
        native_max_value=12,
        native_step=1,
        native_unit_of_measurement="hour",
        mode=NumberMode.SLIDER,
    ),
    NumberEntityDescription(
        key="inactive_alert_minutes",
        name="Inactive Time Alert",
        icon="mdi:seat-recline-normal",
        native_min_value=30,
        native_max_value=240,
        native_step=15,
        native_unit_of_measurement="minutes",
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
    ),
    NumberEntityDescription(
        key="recovery_time_target",
        name="Recovery Time Target",
        icon="mdi:restore-clock",
        native_min_value=4,
        native_max_value=24,
        native_step=1,
        native_unit_of_measurement="hours",
        mode=NumberMode.SLIDER,
    ),
    NumberEntityDescription(
        key="workout_intensity_target",
        name="Workout Intensity Target",
        icon="mdi:speedometer",
        native_min_value=1,
        native_max_value=10,
        native_step=1,
        native_unit_of_measurement="level",
        mode=NumberMode.SLIDER,
    ),
    NumberEntityDescription(
        key="data_retention_days",
        name="Data Retention Period",
        icon="mdi:database-clock",
        native_min_value=7,
        native_max_value=365,
        native_step=7,
        native_unit_of_measurement="days",
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
    ),
    NumberEntityDescription(
        key="polling_interval_minutes",
        name="Polling Interval",
        icon="mdi:clock-fast",
        native_min_value=5,
        native_max_value=120,
        native_step=5,
        native_unit_of_measurement="minutes",
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
    ),
]


class OuraNumber(OuraControlEntity, NumberEntity):
    """Representation of an Oura number entity."""

    entity_description: NumberEntityDescription

    def __init__(
        self,
        coordinator,
        description: NumberEntityDescription,
        entry_id: str,
        device_info: Dict,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, entry_id, description.key)
        self.entity_description = description
        self._attr_device_info = device_info
        self._attr_has_entity_name = True
        
        # Initialize value from coordinator or defaults
        self._native_value = self._get_initial_value()

    def _get_initial_value(self) -> float:
        """Get initial value from coordinator or defaults."""
        key = self.entity_description.key
        
        # Check coordinator settings first
        if hasattr(self.coordinator, 'number_values'):
            return self.coordinator.number_values.get(key, self._get_default_value())
        
        return self._get_default_value()

    def _get_default_value(self) -> float:
        """Get default value based on number type."""
        key = self.entity_description.key
        
        defaults = {
            "readiness_threshold": 70,
            "sleep_score_threshold": 70,
            "activity_goal_steps": 10000,
            "temperature_alert_threshold": 0.5,
            "stress_alert_threshold": 60,
            "hrv_target_range_min": 30,
            "hrv_target_range_max": 80,
            "optimal_sleep_duration": 8.0,
            "bedtime_target_hour": 22,
            "wake_target_hour": 7,
            "inactive_alert_minutes": 90,
            "recovery_time_target": 8,
            "workout_intensity_target": 5,
            "data_retention_days": 90,
            "polling_interval_minutes": 15,
        }
        
        return defaults.get(key, self.entity_description.native_min_value)

    @property
    def native_value(self) -> float:
        """Return the current value."""
        return self._native_value

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        self._native_value = value
        key = self.entity_description.key
        
        # Store value in coordinator
        if not hasattr(self.coordinator, 'number_values'):
            self.coordinator.number_values = {}
        self.coordinator.number_values[key] = value
        
        # Handle specific number logic
        await self._handle_value_change(key, value)
        
        # Update state
        self.async_write_ha_state()
        
        # Fire event for automations
        self.hass.bus.async_fire(
            f"{DOMAIN}_number_changed",
            {
                "entity_id": self.entity_id,
                "number": key,
                "value": value,
            },
        )

    async def _handle_value_change(self, key: str, value: float) -> None:
        """Handle value changes with specific logic."""
        if key == "readiness_threshold":
            await self._handle_readiness_threshold(value)
        elif key == "sleep_score_threshold":
            await self._handle_sleep_threshold(value)
        elif key == "activity_goal_steps":
            await self._handle_activity_goal(value)
        elif key == "temperature_alert_threshold":
            await self._handle_temperature_threshold(value)
        elif key == "stress_alert_threshold":
            await self._handle_stress_threshold(value)
        elif key in ["hrv_target_range_min", "hrv_target_range_max"]:
            await self._handle_hrv_target(key, value)
        elif key == "optimal_sleep_duration":
            await self._handle_sleep_duration_target(value)
        elif key in ["bedtime_target_hour", "wake_target_hour"]:
            await self._handle_sleep_schedule_target(key, value)
        elif key == "inactive_alert_minutes":
            await self._handle_inactive_alert(value)
        elif key == "recovery_time_target":
            await self._handle_recovery_target(value)
        elif key == "workout_intensity_target":
            await self._handle_workout_target(value)
        elif key == "data_retention_days":
            await self._handle_data_retention(value)
        elif key == "polling_interval_minutes":
            await self._handle_polling_interval(value)

    async def _handle_readiness_threshold(self, value: float) -> None:
        """Handle readiness threshold change."""
        self.coordinator.readiness_threshold = value
        
        # Check current readiness against new threshold
        if self.coordinator.readiness_data:
            current_score = self.coordinator.readiness_data[0].score
            if current_score and current_score < value:
                await self._create_notification(
                    "Readiness Alert",
                    f"Current readiness ({current_score}) is below threshold ({value})"
                )

    async def _handle_sleep_threshold(self, value: float) -> None:
        """Handle sleep score threshold change."""
        # Store threshold for alerts
        if not hasattr(self.coordinator, 'sleep_threshold'):
            self.coordinator.sleep_threshold = value
        
        # Check current sleep score
        if self.coordinator.sleep_data:
            current_score = self.coordinator.sleep_data[0].score
            if current_score and current_score < value:
                await self._create_notification(
                    "Sleep Alert",
                    f"Last night's sleep score ({current_score}) is below threshold ({value})"
                )

    async def _handle_activity_goal(self, value: float) -> None:
        """Handle activity goal change."""
        self.coordinator.activity_goal = int(value)
        
        # Fire event for activity tracking
        self.hass.bus.async_fire(
            f"{DOMAIN}_activity_goal_changed",
            {
                "new_goal": int(value),
                "current_steps": self.coordinator.activity_data[0].steps if self.coordinator.activity_data else 0,
            },
        )

    async def _handle_temperature_threshold(self, value: float) -> None:
        """Handle temperature alert threshold change."""
        # Check current temperature deviation
        if self.coordinator.readiness_data:
            current_deviation = self.coordinator.readiness_data[0].temperature_deviation
            if current_deviation and abs(current_deviation) > value:
                await self._create_notification(
                    "Temperature Alert",
                    f"Temperature deviation ({current_deviation:.1f}°C) exceeds threshold ({value}°C)"
                )

    async def _handle_stress_threshold(self, value: float) -> None:
        """Handle stress alert threshold change."""
        # Check current stress level
        if self.coordinator.stress_data:
            current_stress = self.coordinator.stress_data[0].score
            if current_stress and current_stress > value:
                await self._create_notification(
                    "Stress Alert",
                    f"Current stress level ({current_stress}) exceeds threshold ({value})"
                )

    async def _handle_hrv_target(self, key: str, value: float) -> None:
        """Handle HRV target range change."""
        if not hasattr(self.coordinator, 'hrv_targets'):
            self.coordinator.hrv_targets = {}
        
        self.coordinator.hrv_targets[key] = value
        
        # Check if we have both min and max values
        if 'hrv_target_range_min' in self.coordinator.hrv_targets and 'hrv_target_range_max' in self.coordinator.hrv_targets:
            min_val = self.coordinator.hrv_targets['hrv_target_range_min']
            max_val = self.coordinator.hrv_targets['hrv_target_range_max']
            
            # Validate range
            if min_val >= max_val:
                await self._create_notification(
                    "HRV Range Error",
                    "Minimum HRV target must be less than maximum target"
                )

    async def _handle_sleep_duration_target(self, value: float) -> None:
        """Handle optimal sleep duration target change."""
        self.coordinator.sleep_duration_target = value
        
        # Check recent sleep against target
        if self.coordinator.sleep_data:
            recent_sleep = self.coordinator.sleep_data[0].hours_slept
            if recent_sleep and abs(recent_sleep - value) > 1:  # More than 1 hour difference
                await self._create_notification(
                    "Sleep Duration",
                    f"Last night's sleep ({recent_sleep:.1f}h) differs from target ({value}h)"
                )

    async def _handle_sleep_schedule_target(self, key: str, value: float) -> None:
        """Handle sleep schedule target change."""
        if not hasattr(self.coordinator, 'sleep_schedule_targets'):
            self.coordinator.sleep_schedule_targets = {}
        
        self.coordinator.sleep_schedule_targets[key] = value
        
        # Fire event for circadian optimization
        self.hass.bus.async_fire(
            f"{DOMAIN}_sleep_schedule_changed",
            {
                "target_type": key,
                "target_hour": value,
                "circadian_score": self.coordinator.circadian_alignment.get("score", 0),
            },
        )

    async def _handle_inactive_alert(self, value: float) -> None:
        """Handle inactive time alert threshold change."""
        # This would typically integrate with activity monitoring
        self.coordinator.inactive_alert_threshold = int(value)

    async def _handle_recovery_target(self, value: float) -> None:
        """Handle recovery time target change."""
        self.coordinator.recovery_time_target = value

    async def _handle_workout_target(self, value: float) -> None:
        """Handle workout intensity target change."""
        self.coordinator.workout_intensity_target = int(value)

    async def _handle_data_retention(self, value: float) -> None:
        """Handle data retention period change."""
        self.coordinator.data_retention_days = int(value)
        
        # Trigger cleanup if retention period decreased
        await self.coordinator.async_cleanup_old_data()

    async def _handle_polling_interval(self, value: float) -> None:
        """Handle polling interval change."""
        from datetime import timedelta
        
        # Update coordinator polling interval
        new_interval = timedelta(minutes=int(value))
        self.coordinator.update_interval = new_interval
        
        await self._create_notification(
            "Polling Interval Updated",
            f"Data will now be fetched every {int(value)} minutes"
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
        if key == "readiness_threshold":
            if self.coordinator.readiness_data:
                attributes["current_readiness"] = self.coordinator.readiness_data[0].score
                attributes["threshold_met"] = (
                    self.coordinator.readiness_data[0].score >= self._native_value
                    if self.coordinator.readiness_data[0].score else False
                )
        
        elif key == "activity_goal_steps":
            if self.coordinator.activity_data:
                current_steps = self.coordinator.activity_data[0].steps
                attributes["current_steps"] = current_steps
                attributes["progress_percent"] = round(
                    (current_steps / self._native_value) * 100, 1
                ) if current_steps else 0
                attributes["remaining_steps"] = max(0, int(self._native_value - (current_steps or 0)))
        
        elif key == "optimal_sleep_duration":
            if self.coordinator.sleep_data:
                last_sleep = self.coordinator.sleep_data[0].hours_slept
                attributes["last_sleep_duration"] = last_sleep
                attributes["sleep_debt"] = round(self._native_value - (last_sleep or 0), 2)
        
        elif key in ["bedtime_target_hour", "wake_target_hour"]:
            attributes["circadian_alignment"] = self.coordinator.circadian_alignment
        
        elif key == "temperature_alert_threshold":
            if self.coordinator.readiness_data:
                current_deviation = self.coordinator.readiness_data[0].temperature_deviation
                attributes["current_deviation"] = current_deviation
                attributes["alert_active"] = (
                    abs(current_deviation) > self._native_value
                    if current_deviation else False
                )
        
        return attributes


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Oura number entities from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    device_info = hass.data[DOMAIN][config_entry.entry_id]["device_info"]
    
    entities = []
    for description in NUMBER_DESCRIPTIONS:
        entities.append(
            OuraNumber(
                coordinator=coordinator,
                description=description,
                entry_id=config_entry.entry_id,
                device_info=device_info,
            )
        )
    
    async_add_entities(entities, True)
