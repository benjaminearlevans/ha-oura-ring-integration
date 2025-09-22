"""Binary sensor platform for Oura Ring integration."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .entity import OuraEntityBase

_LOGGER = logging.getLogger(__name__)

BINARY_SENSOR_DESCRIPTIONS = [
    BinarySensorEntityDescription(
        key="in_bed",
        name="In Bed",
        device_class=BinarySensorDeviceClass.OCCUPANCY,
        icon="mdi:bed",
    ),
    BinarySensorEntityDescription(
        key="sleeping",
        name="Sleeping",
        device_class=BinarySensorDeviceClass.OCCUPANCY,
        icon="mdi:sleep",
    ),
    BinarySensorEntityDescription(
        key="activity_goal_met",
        name="Activity Goal Met",
        icon="mdi:target",
    ),
    BinarySensorEntityDescription(
        key="recovery_needed",
        name="Recovery Needed",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:alert-circle",
    ),
    BinarySensorEntityDescription(
        key="workout_active",
        name="Workout Active",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:run",
    ),
    BinarySensorEntityDescription(
        key="high_stress",
        name="High Stress",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:emoticon-stressed",
    ),
    BinarySensorEntityDescription(
        key="optimal_readiness",
        name="Optimal Readiness",
        icon="mdi:check-circle",
    ),
    BinarySensorEntityDescription(
        key="circadian_aligned",
        name="Circadian Aligned",
        icon="mdi:sun-clock",
    ),
    BinarySensorEntityDescription(
        key="temperature_elevated",
        name="Temperature Elevated",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:thermometer-alert",
    ),
    BinarySensorEntityDescription(
        key="sleep_debt",
        name="Sleep Debt",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:sleep-off",
    ),
    BinarySensorEntityDescription(
        key="rest_mode_active",
        name="Rest Mode Active",
        icon="mdi:pause-circle",
    ),
    BinarySensorEntityDescription(
        key="data_synced",
        name="Data Synced",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:sync",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
]


class OuraBinarySensor(OuraEntityBase, BinarySensorEntity):
    """Representation of an Oura binary sensor."""

    entity_description: BinarySensorEntityDescription

    def __init__(
        self,
        coordinator,
        description: BinarySensorEntityDescription,
        entry_id: str,
        device_info: Dict,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry_id)
        self.entity_description = description
        self._attr_device_info = device_info
        self._attr_unique_id = f"{coordinator.user_info['id']}_{description.key}"
        self._attr_has_entity_name = True

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if the binary sensor is on."""
        key = self.entity_description.key
        
        if key == "in_bed":
            return self._check_in_bed()
        elif key == "sleeping":
            return self._check_sleeping()
        elif key == "activity_goal_met":
            return self._check_activity_goal()
        elif key == "recovery_needed":
            return self._check_recovery_needed()
        elif key == "workout_active":
            return self._check_workout_active()
        elif key == "high_stress":
            return self._check_high_stress()
        elif key == "optimal_readiness":
            return self._check_optimal_readiness()
        elif key == "circadian_aligned":
            return self._check_circadian_aligned()
        elif key == "temperature_elevated":
            return self._check_temperature_elevated()
        elif key == "sleep_debt":
            return self._check_sleep_debt()
        elif key == "rest_mode_active":
            return self._check_rest_mode()
        elif key == "data_synced":
            return self._check_data_synced()
        
        return None

    def _check_in_bed(self) -> bool:
        """Check if user is currently in bed."""
        if not self.coordinator.sleep_data:
            return False
        
        latest_sleep = self.coordinator.sleep_data[0]
        
        # Check if we have bedtime data
        if not latest_sleep.bedtime_start or not latest_sleep.bedtime_end:
            return False
        
        # Check if current time is between bedtime start and end
        now = dt_util.now()
        
        # Handle timezone-aware comparison
        if latest_sleep.bedtime_start.tzinfo is None:
            bedtime_start = dt_util.as_local(latest_sleep.bedtime_start)
            bedtime_end = dt_util.as_local(latest_sleep.bedtime_end)
        else:
            bedtime_start = latest_sleep.bedtime_start
            bedtime_end = latest_sleep.bedtime_end
        
        # Check if we're in the sleep window
        if bedtime_start <= now <= bedtime_end:
            return True
        
        # Check if it's within reasonable bedtime hours (10 PM - 10 AM)
        current_hour = now.hour
        if 22 <= current_hour or current_hour <= 10:
            # Check if last sleep ended less than 2 hours ago
            time_since_wake = now - bedtime_end
            if time_since_wake.total_seconds() < 7200:  # 2 hours
                return False
            # Might be starting new sleep period
            return self._is_heart_rate_sleeping()
        
        return False

    def _check_sleeping(self) -> bool:
        """Check if user is currently sleeping."""
        # Must be in bed first
        if not self._check_in_bed():
            return False
        
        # Check heart rate pattern indicates sleep
        return self._is_heart_rate_sleeping()

    def _is_heart_rate_sleeping(self) -> bool:
        """Check if heart rate pattern indicates sleep."""
        if not self.coordinator.heart_rate_data:
            return False
        
        # Get recent heart rate data
        recent_hr = self.coordinator.heart_rate_data[0]
        
        # Check if heart rate is near resting rate
        if recent_hr.resting and recent_hr.average:
            # During sleep, HR should be close to resting rate
            return recent_hr.average <= recent_hr.resting * 1.1
        
        return False

    def _check_activity_goal(self) -> bool:
        """Check if daily activity goal is met."""
        if not self.coordinator.activity_data:
            return False
        
        activity = self.coordinator.activity_data[0]
        
        # Check if activity score indicates goal met
        if activity.score:
            return activity.score >= 85
        
        # Fallback to step goal (default 10,000)
        if activity.steps:
            return activity.steps >= 10000
        
        return False

    def _check_recovery_needed(self) -> bool:
        """Check if recovery is needed."""
        if not self.coordinator.readiness_data:
            return False
        
        readiness = self.coordinator.readiness_data[0]
        
        # Recovery needed if readiness is low
        if readiness.score:
            return readiness.score < 70
        
        # Also check temperature deviation
        if readiness.temperature_deviation:
            return abs(readiness.temperature_deviation) > 0.5
        
        return False

    def _check_workout_active(self) -> bool:
        """Check if workout is currently active."""
        if not self.coordinator.workout_data:
            return False
        
        # Check if any workout was logged today
        from datetime import date
        today = date.today().isoformat()
        
        for workout in self.coordinator.workout_data:
            if workout.day == today:
                # Check if workout is recent (within last 2 hours)
                if workout.end_datetime:
                    time_since_workout = dt_util.now() - workout.end_datetime
                    if time_since_workout.total_seconds() < 7200:  # 2 hours
                        return True
        
        # Also check heart rate for exercise pattern
        if self.coordinator.heart_rate_data:
            recent_hr = self.coordinator.heart_rate_data[0]
            if recent_hr.maximum and recent_hr.resting:
                # High HR indicates possible workout
                return recent_hr.maximum > recent_hr.resting * 1.5
        
        return False

    def _check_high_stress(self) -> bool:
        """Check if stress is high."""
        if not self.coordinator.stress_data:
            return False
        
        stress = self.coordinator.stress_data[0]
        
        # Check stress score
        if stress.score:
            return stress.score > 60
        
        # Check high stress periods
        if stress.high_periods:
            return stress.high_periods > 3
        
        return False

    def _check_optimal_readiness(self) -> bool:
        """Check if readiness is optimal."""
        if not self.coordinator.readiness_data:
            return False
        
        readiness = self.coordinator.readiness_data[0]
        
        # Optimal if score is 85+
        if readiness.score:
            return readiness.score >= 85
        
        return False

    def _check_circadian_aligned(self) -> bool:
        """Check if circadian rhythm is aligned."""
        return self.coordinator.circadian_alignment.get("aligned", False)

    def _check_temperature_elevated(self) -> bool:
        """Check if body temperature is elevated."""
        if not self.coordinator.readiness_data:
            return False
        
        readiness = self.coordinator.readiness_data[0]
        
        # Check temperature deviation
        if readiness.temperature_deviation:
            return readiness.temperature_deviation > 0.5
        
        return False

    def _check_sleep_debt(self) -> bool:
        """Check if there is accumulated sleep debt."""
        if not self.coordinator.readiness_data:
            return False
        
        readiness = self.coordinator.readiness_data[0]
        
        # Check sleep balance contributor
        sleep_balance = readiness.contributors.get("sleep_balance")
        if sleep_balance:
            return sleep_balance < 70
        
        # Check recent sleep duration
        if self.coordinator.sleep_data:
            recent_sleep = [s.hours_slept for s in self.coordinator.sleep_data[:7] if s.hours_slept]
            if recent_sleep:
                avg_sleep = sum(recent_sleep) / len(recent_sleep)
                return avg_sleep < 7  # Less than 7 hours average
        
        return False

    def _check_rest_mode(self) -> bool:
        """Check if rest mode is active."""
        # This would need to check the rest_mode_periods endpoint
        # For now, check if recovery is needed
        return self._check_recovery_needed()

    def _check_data_synced(self) -> bool:
        """Check if data is recently synced."""
        if not self.coordinator.last_update:
            return False
        
        # Check if last update was within 30 minutes
        time_since_update = dt_util.now() - self.coordinator.last_update
        return time_since_update.total_seconds() < 1800  # 30 minutes

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        attributes = super().extra_state_attributes
        key = self.entity_description.key
        
        # Add specific attributes based on sensor type
        if key == "in_bed" and self.coordinator.sleep_data:
            sleep = self.coordinator.sleep_data[0]
            if sleep.bedtime_start:
                attributes["bedtime_start"] = str(sleep.bedtime_start)
            if sleep.bedtime_end:
                attributes["bedtime_end"] = str(sleep.bedtime_end)
        
        elif key == "recovery_needed" and self.coordinator.readiness_data:
            readiness = self.coordinator.readiness_data[0]
            attributes["readiness_score"] = readiness.score
            attributes["recommendation"] = readiness.recovery_recommendation
        
        elif key == "high_stress" and self.coordinator.stress_data:
            stress = self.coordinator.stress_data[0]
            attributes["stress_score"] = stress.score
            attributes["high_periods"] = stress.high_periods
        
        elif key == "circadian_aligned":
            attributes.update(self.coordinator.circadian_alignment)
        
        elif key == "temperature_elevated" and self.coordinator.readiness_data:
            readiness = self.coordinator.readiness_data[0]
            attributes["deviation"] = readiness.temperature_deviation
            attributes["trend"] = readiness.temperature_trend
        
        elif key == "data_synced":
            attributes["last_update"] = str(self.coordinator.last_update)
            attributes["update_errors"] = self.coordinator.update_errors
        
        return attributes


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Oura binary sensors from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    device_info = hass.data[DOMAIN][config_entry.entry_id]["device_info"]
    
    entities = []
    for description in BINARY_SENSOR_DESCRIPTIONS:
        entities.append(
            OuraBinarySensor(
                coordinator=coordinator,
                description=description,
                entry_id=config_entry.entry_id,
                device_info=device_info,
            )
        )
    
    async_add_entities(entities, True)