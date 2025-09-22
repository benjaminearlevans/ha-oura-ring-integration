"""Sensor platform for Oura ring integration."""
import logging
from typing import Any, Dict, Optional, Union

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN
from .entity import OuraEntityBase

_LOGGER = logging.getLogger(__name__)

# Sensor descriptions with UI-friendly configurations
SENSOR_DESCRIPTIONS = [
    # Sleep Sensors
    SensorEntityDescription(
        key="sleep_score",
        name="Sleep Score",
        icon="mdi:sleep",
        native_unit_of_measurement="points",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    SensorEntityDescription(
        key="sleep_total_hours",
        name="Total Sleep",
        icon="mdi:clock-time-eight",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="sleep_efficiency",
        name="Sleep Efficiency",
        icon="mdi:percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="sleep_latency",
        name="Sleep Latency",
        icon="mdi:timer-sand",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="sleep_rem_hours",
        name="REM Sleep",
        icon="mdi:brain",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="sleep_deep_hours",
        name="Deep Sleep",
        icon="mdi:power-sleep",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="sleep_light_hours",
        name="Light Sleep",
        icon="mdi:weather-night",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="sleep_awake_time",
        name="Awake Time",
        icon="mdi:eye-outline",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="sleep_restless_periods",
        name="Restless Periods",
        icon="mdi:motion-sensor",
        native_unit_of_measurement="periods",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    
    # Readiness Sensors
    SensorEntityDescription(
        key="readiness_score",
        name="Readiness Score",
        icon="mdi:heart-pulse",
        native_unit_of_measurement="points",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="temperature_deviation",
        name="Temperature Deviation",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="temperature_trend",
        name="Temperature Trend",
        icon="mdi:trending-up",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="hrv_balance",
        name="HRV Balance",
        icon="mdi:pulse",
        native_unit_of_measurement="ms",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="recovery_index",
        name="Recovery Index",
        icon="mdi:restore",
        native_unit_of_measurement="points",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="resting_heart_rate",
        name="Resting Heart Rate",
        icon="mdi:heart",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    
    # Activity Sensors
    SensorEntityDescription(
        key="activity_score",
        name="Activity Score",
        icon="mdi:run",
        native_unit_of_measurement="points",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="activity_steps",
        name="Steps",
        icon="mdi:walk",
        native_unit_of_measurement="steps",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="activity_total_calories",
        name="Total Calories",
        icon="mdi:fire",
        native_unit_of_measurement="kcal",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="activity_active_calories",
        name="Active Calories",
        icon="mdi:run-fast",
        native_unit_of_measurement="kcal",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="activity_met_minutes",
        name="MET Minutes",
        icon="mdi:heart-flash",
        native_unit_of_measurement="minutes",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="activity_inactive_time",
        name="Inactive Time",
        icon="mdi:seat-recline-normal",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="activity_low_time",
        name="Low Activity Time",
        icon="mdi:walk",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="activity_medium_time",
        name="Medium Activity Time",
        icon="mdi:bike",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="activity_high_time",
        name="High Activity Time",
        icon="mdi:run-fast",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    
    # Physiological Sensors
    SensorEntityDescription(
        key="hrv_average",
        name="Average HRV",
        icon="mdi:pulse",
        native_unit_of_measurement="ms",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="respiratory_rate",
        name="Respiratory Rate",
        icon="mdi:lungs",
        native_unit_of_measurement="breaths/min",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="spo2_average",
        name="Blood Oxygen",
        icon="mdi:water-percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="stress_score",
        name="Stress Score",
        icon="mdi:emoticon-stressed-outline",
        native_unit_of_measurement="points",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="stress_high_periods",
        name="High Stress Periods",
        icon="mdi:alert",
        native_unit_of_measurement="periods",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    
    # Trend Sensors
    SensorEntityDescription(
        key="sleep_trend_7d",
        name="Sleep Trend (7 days)",
        icon="mdi:trending-up",
        native_unit_of_measurement="points",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="readiness_trend_7d",
        name="Readiness Trend (7 days)",
        icon="mdi:trending-up",
        native_unit_of_measurement="points",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="activity_trend_7d",
        name="Activity Trend (7 days)",
        icon="mdi:trending-up",
        native_unit_of_measurement="steps",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    
    # Wellness Phase & Recommendations
    SensorEntityDescription(
        key="wellness_phase",
        name="Wellness Phase",
        icon="mdi:state-machine",
    ),
    SensorEntityDescription(
        key="optimal_bedtime",
        name="Optimal Bedtime",
        icon="mdi:bed-clock",
    ),
    SensorEntityDescription(
        key="recovery_time_needed",
        name="Recovery Time Needed",
        icon="mdi:timer-outline",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
    ),
    SensorEntityDescription(
        key="circadian_score",
        name="Circadian Alignment Score",
        icon="mdi:sun-clock",
        native_unit_of_measurement="points",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    
    # Workout Sensors
    SensorEntityDescription(
        key="workout_count_today",
        name="Workouts Today",
        icon="mdi:dumbbell",
        native_unit_of_measurement="workouts",
        state_class=SensorStateClass.TOTAL,
    ),
    SensorEntityDescription(
        key="workout_intensity",
        name="Last Workout Intensity",
        icon="mdi:speedometer",
    ),
    
    # System Sensors
    SensorEntityDescription(
        key="api_rate_limit",
        name="API Rate Limit Remaining",
        icon="mdi:api",
        native_unit_of_measurement="requests",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="last_sync",
        name="Last Sync",
        icon="mdi:sync-clock",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
]


class OuraSensor(OuraEntityBase, SensorEntity):
    """Representation of an Oura sensor."""

    entity_description: SensorEntityDescription

    def __init__(
        self,
        coordinator,
        description: SensorEntityDescription,
        entry_id: str,
        device_info: Dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry_id)
        self.entity_description = description
        self._attr_device_info = device_info
        self._attr_unique_id = f"{coordinator.user_info['id']}_{description.key}"
        self._attr_has_entity_name = True

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        key = self.entity_description.key
        
        # Handle different data sources
        if key == "sleep_score":
            if self.coordinator.sleep_data:
                return self.coordinator.sleep_data[0].score
        elif key == "sleep_total_hours":
            if self.coordinator.sleep_data:
                return self.coordinator.sleep_data[0].hours_slept
        elif key == "sleep_efficiency":
            if self.coordinator.sleep_data:
                return self.coordinator.sleep_data[0].efficiency
        elif key == "sleep_latency":
            if self.coordinator.sleep_data:
                return self.coordinator.sleep_data[0].latency
        elif key == "sleep_rem_hours":
            if self.coordinator.sleep_data and self.coordinator.sleep_data[0].rem_duration:
                return round(self.coordinator.sleep_data[0].rem_duration / 3600, 2)
        elif key == "sleep_deep_hours":
            if self.coordinator.sleep_data and self.coordinator.sleep_data[0].deep_duration:
                return round(self.coordinator.sleep_data[0].deep_duration / 3600, 2)
        elif key == "sleep_light_hours":
            if self.coordinator.sleep_data and self.coordinator.sleep_data[0].light_duration:
                return round(self.coordinator.sleep_data[0].light_duration / 3600, 2)
        elif key == "sleep_awake_time":
            if self.coordinator.sleep_data and self.coordinator.sleep_data[0].awake_duration:
                return round(self.coordinator.sleep_data[0].awake_duration / 60, 1)
        elif key == "sleep_restless_periods":
            if self.coordinator.sleep_data:
                return self.coordinator.sleep_data[0].restless_periods
        
        # Readiness sensors
        elif key == "readiness_score":
            if self.coordinator.readiness_data:
                return self.coordinator.readiness_data[0].score
        elif key == "temperature_deviation":
            if self.coordinator.readiness_data:
                return self.coordinator.readiness_data[0].temperature_deviation
        elif key == "temperature_trend":
            if self.coordinator.readiness_data:
                return self.coordinator.readiness_data[0].temperature_trend
        elif key == "hrv_balance":
            if self.coordinator.readiness_data:
                return self.coordinator.readiness_data[0].contributors.get("hrv_balance")
        elif key == "recovery_index":
            if self.coordinator.readiness_data:
                return self.coordinator.readiness_data[0].contributors.get("recovery_index")
        elif key == "resting_heart_rate":
            if self.coordinator.readiness_data:
                return self.coordinator.readiness_data[0].contributors.get("resting_heart_rate")
        
        # Activity sensors
        elif key == "activity_score":
            if self.coordinator.activity_data:
                return self.coordinator.activity_data[0].score
        elif key == "activity_steps":
            if self.coordinator.activity_data:
                return self.coordinator.activity_data[0].steps
        elif key == "activity_total_calories":
            if self.coordinator.activity_data:
                return self.coordinator.activity_data[0].total_calories
        elif key == "activity_active_calories":
            if self.coordinator.activity_data:
                return self.coordinator.activity_data[0].active_calories
        elif key == "activity_met_minutes":
            if self.coordinator.activity_data:
                met_data = self.coordinator.activity_data[0].met_minutes
                return sum(met_data.values()) if met_data else 0
        elif key == "activity_inactive_time":
            if self.coordinator.activity_data and self.coordinator.activity_data[0].inactive_time:
                return round(self.coordinator.activity_data[0].inactive_time / 3600, 1)
        elif key == "activity_low_time":
            if self.coordinator.activity_data and self.coordinator.activity_data[0].low_activity_time:
                return round(self.coordinator.activity_data[0].low_activity_time / 3600, 1)
        elif key == "activity_medium_time":
            if self.coordinator.activity_data and self.coordinator.activity_data[0].medium_activity_time:
                return round(self.coordinator.activity_data[0].medium_activity_time / 3600, 1)
        elif key == "activity_high_time":
            if self.coordinator.activity_data and self.coordinator.activity_data[0].high_activity_time:
                return round(self.coordinator.activity_data[0].high_activity_time / 3600, 1)
        
        # Physiological sensors
        elif key == "hrv_average":
            if self.coordinator.sleep_data:
                return self.coordinator.sleep_data[0].average_hrv
        elif key == "respiratory_rate":
            if self.coordinator.sleep_data:
                return self.coordinator.sleep_data[0].respiratory_rate
        elif key == "spo2_average":
            spo2_data = self.coordinator.data.get("spo2", [])
            if spo2_data and spo2_data[0].get("spo2_percentage"):
                return spo2_data[0]["spo2_percentage"]["average"]
        elif key == "stress_score":
            if self.coordinator.stress_data:
                return self.coordinator.stress_data[0].score
        elif key == "stress_high_periods":
            if self.coordinator.stress_data:
                return self.coordinator.stress_data[0].high_periods
        
        # Trend sensors
        elif key == "sleep_trend_7d":
            trends = self.coordinator.trends.get("sleep", {})
            return trends.get("current")
        elif key == "readiness_trend_7d":
            trends = self.coordinator.trends.get("readiness", {})
            return trends.get("current")
        elif key == "activity_trend_7d":
            trends = self.coordinator.trends.get("activity", {})
            return trends.get("current")
        
        # Wellness sensors
        elif key == "wellness_phase":
            return self.coordinator.wellness_phase
        elif key == "optimal_bedtime":
            return self.coordinator.circadian_alignment.get("optimal_bedtime")
        elif key == "recovery_time_needed":
            if self.coordinator.readiness_data and self.coordinator.readiness_data[0].score:
                score = self.coordinator.readiness_data[0].score
                if score < 60:
                    return 12
                elif score < 70:
                    return 8
                elif score < 80:
                    return 4
                else:
                    return 0
        elif key == "circadian_score":
            return self.coordinator.circadian_alignment.get("score")
        
        # Workout sensors
        elif key == "workout_count_today":
            if self.coordinator.workout_data:
                from datetime import date
                today = date.today()
                return sum(1 for w in self.coordinator.workout_data if w.day == today.isoformat())
            return 0
        elif key == "workout_intensity":
            if self.coordinator.workout_data:
                return self.coordinator.workout_data[0].intensity
        
        # System sensors
        elif key == "api_rate_limit":
            return self.coordinator.rate_limit_remaining
        elif key == "last_sync":
            return self.coordinator.last_update
        
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        attributes = {}
        key = self.entity_description.key
        
        # Add relevant attributes based on sensor type
        if "sleep" in key and self.coordinator.sleep_data:
            sleep = self.coordinator.sleep_data[0]
            attributes.update({
                "quality": sleep.sleep_quality,
                "bedtime_start": str(sleep.bedtime_start) if sleep.bedtime_start else None,
                "bedtime_end": str(sleep.bedtime_end) if sleep.bedtime_end else None,
                "day": sleep.day,
            })
            
            # Add AI insight if available
            if self.coordinator.ai_insights.get("sleep"):
                attributes["ai_insight"] = self.coordinator.ai_insights["sleep"]
        
        elif "readiness" in key and self.coordinator.readiness_data:
            readiness = self.coordinator.readiness_data[0]
            attributes.update({
                "level": readiness.readiness_level.value,
                "recommendation": readiness.recovery_recommendation,
                "contributors": readiness.contributors,
                "day": readiness.day,
            })
            
            # Add AI insight if available
            if self.coordinator.ai_insights.get("daily"):
                attributes["ai_insight"] = self.coordinator.ai_insights["daily"]
        
        elif "activity" in key and self.coordinator.activity_data:
            activity = self.coordinator.activity_data[0]
            attributes.update({
                "level": activity.activity_level.value,
                "met_breakdown": activity.met_minutes,
                "day": activity.day,
            })
        
        elif key == "wellness_phase":
            attributes.update({
                "description": self._get_phase_description(self.coordinator.wellness_phase),
                "recommendations": self._get_phase_recommendations(self.coordinator.wellness_phase),
            })
        
        elif key == "circadian_score":
            attributes.update(self.coordinator.circadian_alignment)
        
        # Add trend information for trend sensors
        if "trend" in key:
            trend_key = key.split("_")[0]
            if trend_key in self.coordinator.trends:
                trend_data = self.coordinator.trends[trend_key]
                attributes.update({
                    "previous": trend_data.get("previous"),
                    "direction": trend_data.get("direction"),
                    "change": round(
                        trend_data.get("current", 0) - trend_data.get("previous", 0), 1
                    ),
                })
        
        return attributes

    def _get_phase_description(self, phase: str) -> str:
        """Get description for wellness phase."""
        descriptions = {
            "recovery": "Focus on rest and recovery. Your body needs time to recharge.",
            "maintenance": "Maintain current activity levels. Balance activity with recovery.",
            "challenge": "Good time for challenging activities. Your body is ready for more.",
            "peak": "Optimal performance state. Take advantage of high readiness.",
        }
        return descriptions.get(phase, "")

    def _get_phase_recommendations(self, phase: str) -> list:
        """Get recommendations for wellness phase."""
        recommendations = {
            "recovery": [
                "Prioritize sleep (8+ hours)",
                "Gentle movement only",
                "Stress reduction activities",
                "Hydration and nutrition focus",
            ],
            "maintenance": [
                "Maintain regular sleep schedule",
                "Moderate exercise",
                "Balance work and rest",
                "Continue healthy habits",
            ],
            "challenge": [
                "Increase workout intensity",
                "Try new activities",
                "Push comfort zone",
                "Track progress",
            ],
            "peak": [
                "Maximum training load",
                "Competition or PR attempts",
                "Complex skill learning",
                "Leverage high energy",
            ],
        }
        return recommendations.get(phase, [])


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Oura sensors from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    device_info = hass.data[DOMAIN][config_entry.entry_id]["device_info"]
    
    entities = []
    for description in SENSOR_DESCRIPTIONS:
        entities.append(
            OuraSensor(
                coordinator=coordinator,
                description=description,
                entry_id=config_entry.entry_id,
                device_info=device_info,
            )
        )
    
    async_add_entities(entities, True)