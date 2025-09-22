"""Button platform for Oura Full integration."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import OuraControlEntity

_LOGGER = logging.getLogger(__name__)

BUTTON_DESCRIPTIONS = [
    ButtonEntityDescription(
        key="refresh_data",
        name="Refresh Data",
        icon="mdi:refresh",
    ),
    ButtonEntityDescription(
        key="force_sync",
        name="Force Ring Sync",
        icon="mdi:sync",
    ),
    ButtonEntityDescription(
        key="generate_ai_insight",
        name="Generate AI Insight",
        icon="mdi:brain",
    ),
    ButtonEntityDescription(
        key="trigger_recovery_light",
        name="Light Recovery Protocol",
        icon="mdi:restore",
    ),
    ButtonEntityDescription(
        key="trigger_recovery_moderate",
        name="Moderate Recovery Protocol",
        icon="mdi:restore-alert",
    ),
    ButtonEntityDescription(
        key="trigger_recovery_intensive",
        name="Intensive Recovery Protocol",
        icon="mdi:medical-bag",
    ),
    ButtonEntityDescription(
        key="activate_sleep_sanctuary",
        name="Activate Sleep Sanctuary",
        icon="mdi:bed",
    ),
    ButtonEntityDescription(
        key="start_stress_response",
        name="Start Stress Response",
        icon="mdi:emoticon-stressed-outline",
    ),
    ButtonEntityDescription(
        key="optimize_circadian",
        name="Optimize Circadian Rhythm",
        icon="mdi:sun-clock",
    ),
    ButtonEntityDescription(
        key="suggest_nap",
        name="Suggest Optimal Nap",
        icon="mdi:power-sleep",
    ),
    ButtonEntityDescription(
        key="prepare_workout",
        name="Prepare for Workout",
        icon="mdi:dumbbell",
    ),
    ButtonEntityDescription(
        key="export_wellness_data",
        name="Export Wellness Data",
        icon="mdi:download",
        entity_category=EntityCategory.CONFIG,
    ),
    ButtonEntityDescription(
        key="clear_cache",
        name="Clear API Cache",
        icon="mdi:cached",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ButtonEntityDescription(
        key="test_connection",
        name="Test API Connection",
        icon="mdi:connection",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ButtonEntityDescription(
        key="reset_wellness_phase",
        name="Reset Wellness Phase",
        icon="mdi:restart",
        entity_category=EntityCategory.CONFIG,
    ),
]


class OuraButton(OuraControlEntity, ButtonEntity):
    """Representation of an Oura button entity."""

    entity_description: ButtonEntityDescription

    def __init__(
        self,
        coordinator,
        description: ButtonEntityDescription,
        entry_id: str,
        device_info: Dict,
    ) -> None:
        """Initialize the button entity."""
        super().__init__(coordinator, entry_id, description.key)
        self.entity_description = description
        self._attr_device_info = device_info
        self._attr_has_entity_name = True

    async def async_press(self) -> None:
        """Handle button press."""
        key = self.entity_description.key
        
        _LOGGER.info("Button pressed: %s", key)
        
        try:
            if key == "refresh_data":
                await self._refresh_data()
            elif key == "force_sync":
                await self._force_sync()
            elif key == "generate_ai_insight":
                await self._generate_ai_insight()
            elif key == "trigger_recovery_light":
                await self._trigger_recovery_protocol("light")
            elif key == "trigger_recovery_moderate":
                await self._trigger_recovery_protocol("moderate")
            elif key == "trigger_recovery_intensive":
                await self._trigger_recovery_protocol("intensive")
            elif key == "activate_sleep_sanctuary":
                await self._activate_sleep_sanctuary()
            elif key == "start_stress_response":
                await self._start_stress_response()
            elif key == "optimize_circadian":
                await self._optimize_circadian()
            elif key == "suggest_nap":
                await self._suggest_nap()
            elif key == "prepare_workout":
                await self._prepare_workout()
            elif key == "export_wellness_data":
                await self._export_wellness_data()
            elif key == "clear_cache":
                await self._clear_cache()
            elif key == "test_connection":
                await self._test_connection()
            elif key == "reset_wellness_phase":
                await self._reset_wellness_phase()
            
            # Fire event for automations
            self.hass.bus.async_fire(
                f"{DOMAIN}_button_pressed",
                {
                    "entity_id": self.entity_id,
                    "button": key,
                    "timestamp": self.hass.loop.time(),
                },
            )
            
        except Exception as err:
            _LOGGER.error("Error executing button action %s: %s", key, err)
            await self._create_notification(
                f"Button Action Failed",
                f"Failed to execute {key}: {str(err)}"
            )

    async def _refresh_data(self) -> None:
        """Refresh all Oura data."""
        await self.coordinator.async_request_refresh()
        
        await self._create_notification(
            "Data Refresh",
            "Oura data has been refreshed from the API."
        )

    async def _force_sync(self) -> None:
        """Force ring synchronization."""
        # This would typically trigger a notification to sync the ring
        # Since we can't directly control the ring, we'll refresh data and notify
        await self.coordinator.async_request_refresh()
        
        await self._create_notification(
            "Sync Requested",
            "Please sync your Oura Ring in the mobile app for latest data."
        )

    async def _generate_ai_insight(self) -> None:
        """Generate AI-powered wellness insight."""
        if not self.coordinator.enable_ai:
            await self._create_notification(
                "AI Insights Disabled",
                "Please enable AI insights in the integration settings."
            )
            return
        
        await self.coordinator.async_generate_ai_insights()
        
        # Get the latest insight
        latest_insight = ""
        if self.coordinator.ai_insights:
            latest_insight = list(self.coordinator.ai_insights.values())[-1]
        
        await self._create_notification(
            "AI Insight Generated",
            latest_insight[:200] + "..." if len(latest_insight) > 200 else latest_insight
        )

    async def _trigger_recovery_protocol(self, level: str) -> None:
        """Trigger recovery protocol at specified level."""
        if not self.coordinator.readiness_data:
            await self._create_notification(
                "No Readiness Data",
                "Cannot trigger recovery protocol without readiness data."
            )
            return
        
        readiness_score = self.coordinator.readiness_data[0].score
        
        # Define recovery actions based on level
        recovery_actions = {
            "light": {
                "components": ["lighting", "notifications"],
                "duration": 2,  # hours
                "description": "Gentle lighting adjustment and reduced notifications"
            },
            "moderate": {
                "components": ["lighting", "temperature", "notifications"],
                "duration": 4,
                "description": "Environmental optimization and activity suggestions"
            },
            "intensive": {
                "components": ["lighting", "temperature", "notifications", "calendar_blocking"],
                "duration": 8,
                "description": "Full recovery mode with calendar blocking"
            }
        }
        
        protocol = recovery_actions.get(level, recovery_actions["light"])
        
        # Fire recovery protocol event
        self.hass.bus.async_fire(
            f"{DOMAIN}_recovery_protocol",
            {
                "level": level,
                "components": protocol["components"],
                "duration_hours": protocol["duration"],
                "readiness_score": readiness_score,
                "wellness_phase": self.coordinator.wellness_phase,
            },
        )
        
        await self._create_notification(
            f"{level.title()} Recovery Protocol",
            f"Activated {protocol['description']} for {protocol['duration']} hours."
        )

    async def _activate_sleep_sanctuary(self) -> None:
        """Activate sleep sanctuary mode."""
        # Check if it's appropriate time for sleep
        from datetime import datetime
        current_hour = datetime.now().hour
        
        if not (20 <= current_hour or current_hour <= 6):
            await self._create_notification(
                "Sleep Sanctuary",
                "Sleep sanctuary is typically used during evening/night hours."
            )
        
        # Fire sleep sanctuary event
        self.hass.bus.async_fire(
            f"{DOMAIN}_sleep_sanctuary_activated",
            {
                "bedtime_suggestion": self.coordinator.circadian_alignment.get("optimal_bedtime", "22:00"),
                "temperature_target": 18,  # Celsius
                "light_level": 5,  # Percent
            },
        )
        
        await self._create_notification(
            "Sleep Sanctuary Activated",
            "Environment optimized for sleep. Sweet dreams!"
        )

    async def _start_stress_response(self) -> None:
        """Start stress response protocol."""
        if not self.coordinator.stress_data:
            await self._create_notification(
                "No Stress Data",
                "Cannot start stress response without stress data."
            )
            return
        
        current_stress = self.coordinator.stress_data[0].score or 0
        
        # Fire stress response event
        self.hass.bus.async_fire(
            f"{DOMAIN}_stress_response_activated",
            {
                "stress_level": current_stress,
                "breathing_exercise": True,
                "ambient_adjustment": True,
                "notification_reduction": True,
            },
        )
        
        await self._create_notification(
            "Stress Response Activated",
            f"Stress management protocol started (stress level: {current_stress})"
        )

    async def _optimize_circadian(self) -> None:
        """Optimize circadian rhythm."""
        alignment = self.coordinator.circadian_alignment
        
        if not alignment:
            await self._create_notification(
                "No Circadian Data",
                "Cannot optimize without circadian alignment data."
            )
            return
        
        # Fire circadian optimization event
        self.hass.bus.async_fire(
            f"{DOMAIN}_circadian_optimization",
            {
                "current_score": alignment.get("score", 0),
                "optimal_bedtime": alignment.get("optimal_bedtime", "22:00"),
                "optimal_wake": alignment.get("optimal_wake", "07:00"),
                "light_therapy": alignment.get("score", 0) < 70,
            },
        )
        
        await self._create_notification(
            "Circadian Optimization",
            f"Rhythm optimization started (current score: {alignment.get('score', 0)})"
        )

    async def _suggest_nap(self) -> None:
        """Suggest optimal nap timing."""
        from datetime import datetime, timedelta
        
        current_time = datetime.now()
        current_hour = current_time.hour
        
        # Check if nap is appropriate
        if not (13 <= current_hour <= 16):  # 1-4 PM
            await self._create_notification(
                "Nap Suggestion",
                "Optimal nap window is between 1-4 PM."
            )
            return
        
        # Check sleep debt
        sleep_debt = 0
        if self.coordinator.sleep_data:
            recent_sleep = self.coordinator.sleep_data[0].hours_slept
            if recent_sleep:
                sleep_debt = max(0, 8 - recent_sleep)  # Assuming 8h target
        
        if sleep_debt < 1:
            await self._create_notification(
                "Nap Not Needed",
                "Your sleep debt is low. A nap may interfere with tonight's sleep."
            )
            return
        
        # Suggest nap duration based on sleep debt
        nap_duration = min(20, int(sleep_debt * 10))  # Max 20 minutes
        
        # Fire nap suggestion event
        self.hass.bus.async_fire(
            f"{DOMAIN}_nap_suggested",
            {
                "duration_minutes": nap_duration,
                "sleep_debt_hours": sleep_debt,
                "optimal_start": current_time.isoformat(),
                "wake_time": (current_time + timedelta(minutes=nap_duration)).isoformat(),
            },
        )
        
        await self._create_notification(
            "Nap Suggestion",
            f"Optimal nap: {nap_duration} minutes (sleep debt: {sleep_debt:.1f}h)"
        )

    async def _prepare_workout(self) -> None:
        """Prepare environment for workout."""
        if not self.coordinator.readiness_data:
            await self._create_notification(
                "No Readiness Data",
                "Cannot prepare workout without readiness data."
            )
            return
        
        readiness = self.coordinator.readiness_data[0].score or 0
        
        # Determine workout intensity based on readiness
        if readiness >= 85:
            intensity = "high"
            recommendation = "Great day for intense training!"
        elif readiness >= 70:
            intensity = "moderate"
            recommendation = "Good for moderate exercise."
        elif readiness >= 60:
            intensity = "light"
            recommendation = "Light activity recommended."
        else:
            intensity = "recovery"
            recommendation = "Focus on recovery activities."
        
        # Fire workout preparation event
        self.hass.bus.async_fire(
            f"{DOMAIN}_workout_preparation",
            {
                "readiness_score": readiness,
                "recommended_intensity": intensity,
                "environment_prep": True,
                "music_playlist": intensity,
            },
        )
        
        await self._create_notification(
            "Workout Preparation",
            f"Environment prepared for {intensity} workout. {recommendation}"
        )

    async def _export_wellness_data(self) -> None:
        """Export wellness data."""
        try:
            # Call the export service
            await self.hass.services.async_call(
                DOMAIN,
                "export_wellness_data",
                {
                    "format": "json",
                    "date_range": 30,
                },
                blocking=True,
            )
            
            await self._create_notification(
                "Data Export",
                "Wellness data exported successfully."
            )
            
        except Exception as err:
            _LOGGER.error("Failed to export data: %s", err)
            await self._create_notification(
                "Export Failed",
                f"Failed to export data: {str(err)}"
            )

    async def _clear_cache(self) -> None:
        """Clear API cache."""
        self.coordinator.api.clear_cache()
        
        await self._create_notification(
            "Cache Cleared",
            "API cache has been cleared. Next update will fetch fresh data."
        )

    async def _test_connection(self) -> None:
        """Test API connection."""
        try:
            success = await self.coordinator.api.test_connection()
            
            if success:
                await self._create_notification(
                    "Connection Test",
                    "✅ API connection is working properly."
                )
            else:
                await self._create_notification(
                    "Connection Test",
                    "❌ API connection failed. Check your token."
                )
                
        except Exception as err:
            await self._create_notification(
                "Connection Test",
                f"❌ Connection test failed: {str(err)}"
            )

    async def _reset_wellness_phase(self) -> None:
        """Reset wellness phase to auto-calculation."""
        # Clear any manual overrides
        if hasattr(self.coordinator, 'wellness_mode_override'):
            self.coordinator.wellness_mode_override = None
        
        # Recalculate wellness phase
        await self.coordinator.async_request_refresh()
        
        await self._create_notification(
            "Wellness Phase Reset",
            f"Wellness phase reset to auto-calculated: {self.coordinator.wellness_phase}"
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
                    "notification_id": f"{DOMAIN}_{self.entity_description.key}_{self.hass.loop.time()}",
                },
            )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Oura button entities from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    device_info = hass.data[DOMAIN][config_entry.entry_id]["device_info"]
    
    entities = []
    for description in BUTTON_DESCRIPTIONS:
        entities.append(
            OuraButton(
                coordinator=coordinator,
                description=description,
                entry_id=config_entry.entry_id,
                device_info=device_info,
            )
        )
    
    async_add_entities(entities, True)
