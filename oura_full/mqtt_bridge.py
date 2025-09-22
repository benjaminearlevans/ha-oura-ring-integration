"""MQTT bridge for Oura Full integration."""
import asyncio
import json
import logging
from typing import Any, Dict, Optional

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .const import DOMAIN, MQTT_TOPICS

_LOGGER = logging.getLogger(__name__)


class OuraMqttBridge:
    """MQTT bridge for publishing Oura wellness data to ecosystem."""

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator,
        topic_prefix: str = "anima/wellness/oura",
    ) -> None:
        """Initialize the MQTT bridge."""
        self.hass = hass
        self.coordinator = coordinator
        self.topic_prefix = topic_prefix.rstrip("/")
        self._listeners = []
        self._active = False

    async def async_setup(self) -> None:
        """Set up the MQTT bridge."""
        if not self.hass.services.has_service("mqtt", "publish"):
            _LOGGER.error("MQTT integration not available")
            return False

        try:
            # Set up state change listeners
            await self._setup_state_listeners()
            
            # Publish initial state
            await self._publish_initial_state()
            
            # Set up periodic publishing
            await self._setup_periodic_publishing()
            
            self._active = True
            _LOGGER.info("MQTT bridge setup complete with prefix: %s", self.topic_prefix)
            return True
            
        except Exception as err:
            _LOGGER.error("Failed to setup MQTT bridge: %s", err)
            return False

    async def async_cleanup(self) -> None:
        """Clean up the MQTT bridge."""
        if self._active:
            # Remove listeners
            for unsub in self._listeners:
                unsub()
            self._listeners.clear()
            
            # Publish offline status
            await self._publish_status("offline")
            
            self._active = False
            _LOGGER.info("MQTT bridge cleaned up")

    async def _setup_state_listeners(self) -> None:
        """Set up listeners for entity state changes."""
        # Listen for coordinator updates
        @callback
        def coordinator_updated(event):
            """Handle coordinator updates."""
            if self._active:
                asyncio.create_task(self._publish_all_data())

        # Listen for specific entity changes
        entity_patterns = [
            f"sensor.{DOMAIN}_*",
            f"binary_sensor.{DOMAIN}_*",
        ]
        
        for pattern in entity_patterns:
            unsub = async_track_state_change_event(
                self.hass,
                pattern,
                self._handle_entity_change
            )
            self._listeners.append(unsub)

    @callback
    def _handle_entity_change(self, event) -> None:
        """Handle entity state changes."""
        if not self._active:
            return
            
        entity_id = event.data.get("entity_id")
        new_state = event.data.get("new_state")
        
        if not new_state:
            return
        
        # Publish specific entity updates
        asyncio.create_task(self._publish_entity_update(entity_id, new_state))

    async def _publish_entity_update(self, entity_id: str, state) -> None:
        """Publish individual entity update."""
        try:
            # Extract entity type and key from entity_id
            parts = entity_id.split(".")
            if len(parts) != 2:
                return
                
            domain, entity_name = parts
            
            # Map entity to MQTT topic
            topic = self._map_entity_to_topic(entity_name)
            if not topic:
                return
            
            # Prepare payload
            payload = {
                "value": state.state,
                "attributes": dict(state.attributes),
                "timestamp": dt_util.now().isoformat(),
                "entity_id": entity_id,
            }
            
            # Publish to MQTT
            await self._publish_mqtt(topic, payload)
            
        except Exception as err:
            _LOGGER.error("Error publishing entity update: %s", err)

    def _map_entity_to_topic(self, entity_name: str) -> Optional[str]:
        """Map entity name to MQTT topic."""
        # Remove domain prefix if present
        if entity_name.startswith(f"{DOMAIN}_"):
            entity_name = entity_name[len(f"{DOMAIN}_"):]
        
        # Map common entities to topics
        topic_mappings = {
            # Sleep entities
            "sleep_score": "sleep/score",
            "sleep_total_hours": "sleep/duration",
            "sleep_efficiency": "sleep/efficiency",
            "sleep_deep_hours": "sleep/stages/deep",
            "sleep_rem_hours": "sleep/stages/rem",
            "sleep_light_hours": "sleep/stages/light",
            "average_hrv": "sleep/hrv",
            
            # Readiness entities
            "readiness_score": "readiness/score",
            "temperature_deviation": "readiness/temperature",
            "hrv_balance": "readiness/hrv_balance",
            "resting_heart_rate": "readiness/resting_hr",
            
            # Activity entities
            "activity_steps": "activity/steps",
            "activity_total_calories": "activity/calories",
            "activity_score": "activity/score",
            "activity_met_minutes": "activity/met_minutes",
            
            # Wellness entities
            "wellness_phase": "wellness/phase",
            "optimal_bedtime": "wellness/optimal_bedtime",
            "recovery_time_needed": "wellness/recovery_time",
            
            # Binary sensors
            "in_bed": "status/in_bed",
            "sleeping": "status/sleeping",
            "recovery_needed": "status/recovery_needed",
            "high_stress": "status/high_stress",
            "optimal_readiness": "status/optimal_readiness",
            
            # Real-time data (when available)
            "current_heart_rate": "realtime/heart_rate",
            "stress_score": "realtime/stress",
        }
        
        return topic_mappings.get(entity_name)

    async def _publish_initial_state(self) -> None:
        """Publish initial state of all entities."""
        await self._publish_status("online")
        await self._publish_all_data()

    async def _publish_all_data(self) -> None:
        """Publish all current Oura data to MQTT."""
        try:
            # Sleep data
            if self.coordinator.sleep_data:
                sleep = self.coordinator.sleep_data[0]
                await self._publish_sleep_data(sleep)
            
            # Readiness data
            if self.coordinator.readiness_data:
                readiness = self.coordinator.readiness_data[0]
                await self._publish_readiness_data(readiness)
            
            # Activity data
            if self.coordinator.activity_data:
                activity = self.coordinator.activity_data[0]
                await self._publish_activity_data(activity)
            
            # Wellness data
            await self._publish_wellness_data()
            
            # Trends
            await self._publish_trends()
            
        except Exception as err:
            _LOGGER.error("Error publishing all data: %s", err)

    async def _publish_sleep_data(self, sleep) -> None:
        """Publish sleep data to MQTT."""
        base_topic = f"{self.topic_prefix}/sleep"
        
        # Main sleep metrics
        await self._publish_mqtt(f"{base_topic}/score", {
            "value": sleep.score,
            "quality": sleep.sleep_quality,
            "day": sleep.day,
            "timestamp": dt_util.now().isoformat(),
        })
        
        await self._publish_mqtt(f"{base_topic}/duration", {
            "value": sleep.hours_slept,
            "total_seconds": sleep.total_duration,
            "efficiency": sleep.efficiency,
            "timestamp": dt_util.now().isoformat(),
        })
        
        # Sleep stages
        stages_topic = f"{base_topic}/stages"
        await self._publish_mqtt(f"{stages_topic}/deep", {
            "value": round(sleep.deep_duration / 3600, 2) if sleep.deep_duration else 0,
            "seconds": sleep.deep_duration,
            "timestamp": dt_util.now().isoformat(),
        })
        
        await self._publish_mqtt(f"{stages_topic}/rem", {
            "value": round(sleep.rem_duration / 3600, 2) if sleep.rem_duration else 0,
            "seconds": sleep.rem_duration,
            "timestamp": dt_util.now().isoformat(),
        })
        
        await self._publish_mqtt(f"{stages_topic}/light", {
            "value": round(sleep.light_duration / 3600, 2) if sleep.light_duration else 0,
            "seconds": sleep.light_duration,
            "timestamp": dt_util.now().isoformat(),
        })
        
        # HRV data
        if sleep.average_hrv:
            await self._publish_mqtt(f"{base_topic}/hrv", {
                "value": sleep.average_hrv,
                "lowest_hr": sleep.lowest_heart_rate,
                "respiratory_rate": sleep.respiratory_rate,
                "timestamp": dt_util.now().isoformat(),
            })

    async def _publish_readiness_data(self, readiness) -> None:
        """Publish readiness data to MQTT."""
        base_topic = f"{self.topic_prefix}/readiness"
        
        await self._publish_mqtt(f"{base_topic}/score", {
            "value": readiness.score,
            "level": readiness.readiness_level.value,
            "recommendation": readiness.recovery_recommendation,
            "day": readiness.day,
            "timestamp": dt_util.now().isoformat(),
        })
        
        await self._publish_mqtt(f"{base_topic}/temperature", {
            "value": readiness.temperature_deviation,
            "trend": readiness.temperature_trend,
            "timestamp": dt_util.now().isoformat(),
        })
        
        # Contributors
        if readiness.contributors:
            await self._publish_mqtt(f"{base_topic}/hrv_balance", {
                "value": readiness.contributors.get("hrv_balance"),
                "timestamp": dt_util.now().isoformat(),
            })

    async def _publish_activity_data(self, activity) -> None:
        """Publish activity data to MQTT."""
        base_topic = f"{self.topic_prefix}/activity"
        
        await self._publish_mqtt(f"{base_topic}/steps", {
            "value": activity.steps,
            "goal_progress": (activity.steps / 10000 * 100) if activity.steps else 0,
            "timestamp": dt_util.now().isoformat(),
        })
        
        await self._publish_mqtt(f"{base_topic}/calories", {
            "value": activity.total_calories,
            "active_calories": activity.active_calories,
            "timestamp": dt_util.now().isoformat(),
        })
        
        await self._publish_mqtt(f"{base_topic}/score", {
            "value": activity.score,
            "level": activity.activity_level.value,
            "day": activity.day,
            "timestamp": dt_util.now().isoformat(),
        })

    async def _publish_wellness_data(self) -> None:
        """Publish wellness and derived data."""
        base_topic = f"{self.topic_prefix}/wellness"
        
        await self._publish_mqtt(f"{base_topic}/phase", {
            "value": self.coordinator.wellness_phase,
            "circadian_score": self.coordinator.circadian_alignment.get("score", 0),
            "timestamp": dt_util.now().isoformat(),
        })
        
        # Circadian data
        if self.coordinator.circadian_alignment:
            await self._publish_mqtt(f"{base_topic}/circadian", {
                "aligned": self.coordinator.circadian_alignment.get("aligned", False),
                "score": self.coordinator.circadian_alignment.get("score", 0),
                "optimal_bedtime": self.coordinator.circadian_alignment.get("optimal_bedtime"),
                "optimal_wake": self.coordinator.circadian_alignment.get("optimal_wake"),
                "timestamp": dt_util.now().isoformat(),
            })

    async def _publish_trends(self) -> None:
        """Publish trend data."""
        if not self.coordinator.trends:
            return
            
        base_topic = f"{self.topic_prefix}/trends"
        
        for trend_type, trend_data in self.coordinator.trends.items():
            await self._publish_mqtt(f"{base_topic}/{trend_type}", {
                "current": trend_data.get("current"),
                "previous": trend_data.get("previous"),
                "direction": trend_data.get("direction"),
                "change": trend_data.get("current", 0) - trend_data.get("previous", 0),
                "timestamp": dt_util.now().isoformat(),
            })

    async def _publish_status(self, status: str) -> None:
        """Publish integration status."""
        await self._publish_mqtt(f"{self.topic_prefix}/status", {
            "status": status,
            "last_update": str(self.coordinator.last_update) if self.coordinator.last_update else None,
            "wellness_phase": self.coordinator.wellness_phase,
            "timestamp": dt_util.now().isoformat(),
        })

    async def _setup_periodic_publishing(self) -> None:
        """Set up periodic publishing of data."""
        async def periodic_publish():
            """Periodically publish data."""
            while self._active:
                try:
                    await asyncio.sleep(300)  # Every 5 minutes
                    if self._active:
                        await self._publish_all_data()
                except asyncio.CancelledError:
                    break
                except Exception as err:
                    _LOGGER.error("Error in periodic publishing: %s", err)
        
        # Start periodic publishing task
        asyncio.create_task(periodic_publish())

    async def _publish_mqtt(self, topic: str, payload: Dict[str, Any]) -> None:
        """Publish data to MQTT topic."""
        try:
            # Ensure topic starts with prefix
            if not topic.startswith(self.topic_prefix):
                topic = f"{self.topic_prefix}/{topic}"
            
            # Convert payload to JSON
            json_payload = json.dumps(payload, default=str)
            
            # Publish to MQTT
            await self.hass.services.async_call(
                "mqtt",
                "publish",
                {
                    "topic": topic,
                    "payload": json_payload,
                    "retain": True,
                    "qos": 1,
                },
            )
            
            _LOGGER.debug("Published to MQTT: %s", topic)
            
        except Exception as err:
            _LOGGER.error("Error publishing to MQTT topic %s: %s", topic, err)

    @property
    def is_active(self) -> bool:
        """Return if bridge is active."""
        return self._active

    @property
    def bridge_info(self) -> Dict[str, Any]:
        """Return bridge information."""
        return {
            "active": self._active,
            "topic_prefix": self.topic_prefix,
            "listeners_count": len(self._listeners),
            "mqtt_available": self.hass.services.has_service("mqtt", "publish"),
        }
