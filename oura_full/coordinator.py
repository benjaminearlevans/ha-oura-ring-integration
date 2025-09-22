"""Data update coordinator for Oura ring integration."""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import OuraApiClient
from .const import DOMAIN
from .models import (
    ActivityData,
    HeartRateData,
    ReadinessData,
    SleepData,
    StressData,
    WorkoutData,
)

_LOGGER = logging.getLogger(__name__)


class OuraDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Oura data from API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: OuraApiClient,
        update_interval: timedelta,
        enable_ai: bool = False,
        enable_mqtt: bool = False,
        user_info: dict = None,
    ) -> None:
        """Initialize the data update coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.api = api_client
        self.enable_ai = enable_ai
        self.enable_mqtt = enable_mqtt
        self.user_info = user_info or {}
        
        # Data storage
        self.sleep_data: List[SleepData] = []
        self.readiness_data: List[ReadinessData] = []
        self.activity_data: List[ActivityData] = []
        self.heart_rate_data: List[HeartRateData] = []
        self.stress_data: List[StressData] = []
        self.workout_data: List[WorkoutData] = []
        
        # Derived data
        self.wellness_phase = "maintenance"
        self.circadian_alignment = {}
        self.ai_insights = {}
        self.trends = {}
        self.predictions = {}
        
        # State tracking
        self.last_update = dt_util.now()
        self.update_errors = 0
        self.rate_limit_remaining = 100
        
    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from API and calculate derived metrics."""
        try:
            # Reset error counter on successful update
            self.update_errors = 0
            
            # Determine date range for fetching
            end_date = dt_util.now().date()
            start_date = end_date - timedelta(days=7)
            
            # Fetch all data types in parallel
            tasks = {
                "sleep": self._fetch_sleep_data(start_date, end_date),
                "readiness": self._fetch_readiness_data(start_date, end_date),
                "activity": self._fetch_activity_data(start_date, end_date),
                "heart_rate": self._fetch_heart_rate_data(start_date, end_date),
                "stress": self._fetch_stress_data(start_date, end_date),
                "workouts": self._fetch_workout_data(start_date, end_date),
                "spo2": self._fetch_spo2_data(start_date, end_date),
                "temperature": self._fetch_temperature_data(start_date, end_date),
            }
            
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            
            # Process results
            data = {}
            for key, result in zip(tasks.keys(), results):
                if isinstance(result, Exception):
                    if "401" in str(result) or "authentication" in str(result).lower():
                        raise ConfigEntryAuthFailed("Authentication failed") from result
                    _LOGGER.error("Error fetching %s data: %s", key, result)
                    data[key] = self._get_cached_data(key)
                else:
                    data[key] = result
                    self._cache_data(key, result)
            
            # Calculate derived metrics
            await self._calculate_derived_metrics(data)
            
            # Generate AI insights if enabled
            if self.enable_ai:
                await self.async_generate_ai_insights(data)
            
            # Publish to MQTT if enabled
            if self.enable_mqtt:
                await self._publish_mqtt_updates(data)
            
            # Update last successful update time
            self.last_update = dt_util.now()
            
            # Add metadata
            data["last_update"] = self.last_update
            data["wellness_phase"] = self.wellness_phase
            data["circadian_alignment"] = self.circadian_alignment
            data["ai_insights"] = self.ai_insights
            data["trends"] = self.trends
            data["predictions"] = self.predictions
            data["rate_limit_remaining"] = self.rate_limit_remaining
            
            return data
            
        except ConfigEntryAuthFailed:
            raise
        except Exception as err:
            self.update_errors += 1
            if self.update_errors > 3:
                _LOGGER.error("Multiple update failures: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
    
    async def _fetch_sleep_data(self, start_date, end_date) -> List[SleepData]:
        """Fetch sleep data from API."""
        try:
            raw_data = await self.api.get_daily_sleep(
                start_date.isoformat(),
                end_date.isoformat()
            )
            
            # Also fetch detailed sleep periods for today
            sleep_periods = await self.api.get_sleep_periods(
                end_date.isoformat(),
                end_date.isoformat()
            )
            
            # Convert to data models
            sleep_data = []
            for item in raw_data:
                sleep = SleepData.from_api_response(item)
                # Add detailed period data if available
                if sleep_periods and sleep.day == end_date.isoformat():
                    sleep.add_period_details(sleep_periods[0])
                sleep_data.append(sleep)
            
            self.sleep_data = sleep_data
            return sleep_data
            
        except Exception as err:
            _LOGGER.error("Error fetching sleep data: %s", err)
            raise
    
    async def _fetch_readiness_data(self, start_date, end_date) -> List[ReadinessData]:
        """Fetch readiness data from API."""
        try:
            raw_data = await self.api.get_daily_readiness(
                start_date.isoformat(),
                end_date.isoformat()
            )
            
            readiness_data = [
                ReadinessData.from_api_response(item) for item in raw_data
            ]
            self.readiness_data = readiness_data
            return readiness_data
            
        except Exception as err:
            _LOGGER.error("Error fetching readiness data: %s", err)
            raise
    
    async def _fetch_activity_data(self, start_date, end_date) -> List[ActivityData]:
        """Fetch activity data from API."""
        try:
            raw_data = await self.api.get_daily_activity(
                start_date.isoformat(),
                end_date.isoformat()
            )
            
            activity_data = [
                ActivityData.from_api_response(item) for item in raw_data
            ]
            self.activity_data = activity_data
            return activity_data
            
        except Exception as err:
            _LOGGER.error("Error fetching activity data: %s", err)
            raise
    
    async def _fetch_heart_rate_data(self, start_date, end_date) -> List[HeartRateData]:
        """Fetch heart rate data from API."""
        try:
            raw_data = await self.api.get_heart_rate(
                start_datetime=f"{start_date}T00:00:00",
                end_datetime=f"{end_date}T23:59:59"
            )
            
            # Process heart rate data
            heart_rate_data = []
            if raw_data:
                # Group by day and calculate daily stats
                daily_hr = {}
                for item in raw_data:
                    day = item.get("timestamp", "")[:10]
                    if day not in daily_hr:
                        daily_hr[day] = []
                    daily_hr[day].append(item.get("bpm", 0))
                
                for day, values in daily_hr.items():
                    if values:
                        hr_data = HeartRateData(
                            day=day,
                            average=sum(values) / len(values),
                            minimum=min(values),
                            maximum=max(values),
                            resting=min(values),  # Simplified, should use morning values
                            samples=values
                        )
                        heart_rate_data.append(hr_data)
            
            self.heart_rate_data = heart_rate_data
            return heart_rate_data
            
        except Exception as err:
            _LOGGER.error("Error fetching heart rate data: %s", err)
            raise
    
    async def _fetch_stress_data(self, start_date, end_date) -> List[StressData]:
        """Fetch stress data from API."""
        try:
            raw_data = await self.api.get_daily_stress(
                start_date.isoformat(),
                end_date.isoformat()
            )
            
            stress_data = [
                StressData.from_api_response(item) for item in raw_data
            ]
            self.stress_data = stress_data
            return stress_data
            
        except Exception as err:
            _LOGGER.error("Error fetching stress data: %s", err)
            raise
    
    async def _fetch_workout_data(self, start_date, end_date) -> List[WorkoutData]:
        """Fetch workout data from API."""
        try:
            raw_data = await self.api.get_workouts(
                start_date.isoformat(),
                end_date.isoformat()
            )
            
            workout_data = [
                WorkoutData.from_api_response(item) for item in raw_data
            ]
            self.workout_data = workout_data
            return workout_data
            
        except Exception as err:
            _LOGGER.error("Error fetching workout data: %s", err)
            raise
    
    async def _fetch_spo2_data(self, start_date, end_date) -> List[Dict]:
        """Fetch SpO2 data from API."""
        try:
            return await self.api.get_daily_spo2(
                start_date.isoformat(),
                end_date.isoformat()
            )
        except Exception as err:
            _LOGGER.error("Error fetching SpO2 data: %s", err)
            return []
    
    async def _fetch_temperature_data(self, start_date, end_date) -> List[Dict]:
        """Fetch temperature data from readiness data."""
        # Temperature is included in readiness data
        return []
    
    async def _calculate_derived_metrics(self, data: Dict[str, Any]) -> None:
        """Calculate derived metrics from raw data."""
        # Calculate wellness phase
        self.wellness_phase = self._calculate_wellness_phase(data)
        
        # Calculate circadian alignment
        self.circadian_alignment = self._calculate_circadian_alignment(data)
        
        # Calculate trends
        self.trends = await self.async_calculate_trends()
        
        # Generate predictions
        if self.enable_ai:
            self.predictions = await self._generate_predictions(data)
    
    def _calculate_wellness_phase(self, data: Dict[str, Any]) -> str:
        """Determine current wellness phase based on recent data."""
        readiness = data.get("readiness", [])
        sleep = data.get("sleep", [])
        activity = data.get("activity", [])
        
        if not readiness or not sleep:
            return "maintenance"
        
        # Calculate 7-day averages
        recent_readiness = [r.score for r in readiness[:7] if r.score]
        recent_sleep = [s.score for s in sleep[:7] if s.score]
        recent_activity = [a.score for a in activity[:7] if a.score]
        
        avg_readiness = sum(recent_readiness) / len(recent_readiness) if recent_readiness else 0
        avg_sleep = sum(recent_sleep) / len(recent_sleep) if recent_sleep else 0
        avg_activity = sum(recent_activity) / len(recent_activity) if recent_activity else 0
        
        # Determine phase
        if avg_readiness < 60 or avg_sleep < 60:
            return "recovery"
        elif avg_readiness > 85 and avg_sleep > 80 and avg_activity > 75:
            return "peak"
        elif avg_readiness > 75 and avg_sleep > 70:
            return "challenge"
        else:
            return "maintenance"
    
    def _calculate_circadian_alignment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate circadian rhythm alignment metrics."""
        sleep = data.get("sleep", [])
        
        if not sleep:
            return {"aligned": False, "score": 0, "optimal_bedtime": "22:00"}
        
        # Analyze bedtime consistency
        bedtimes = []
        wake_times = []
        
        for s in sleep[:14]:  # Look at 2 weeks
            if s.bedtime_start:
                bedtimes.append(s.bedtime_start.hour + s.bedtime_start.minute / 60)
            if s.bedtime_end:
                wake_times.append(s.bedtime_end.hour + s.bedtime_end.minute / 60)
        
        if len(bedtimes) < 3:
            return {"aligned": False, "score": 0, "optimal_bedtime": "22:00"}
        
        # Calculate consistency
        avg_bedtime = sum(bedtimes) / len(bedtimes)
        bedtime_variance = sum((bt - avg_bedtime) ** 2 for bt in bedtimes) / len(bedtimes)
        
        avg_wake = sum(wake_times) / len(wake_times) if wake_times else 7
        wake_variance = sum((wt - avg_wake) ** 2 for wt in wake_times) / len(wake_times) if wake_times else 1
        
        # Score based on consistency (lower variance = better)
        bedtime_score = max(0, 100 - (bedtime_variance * 20))
        wake_score = max(0, 100 - (wake_variance * 20))
        overall_score = (bedtime_score + wake_score) / 2
        
        # Format optimal times
        optimal_bedtime_hour = int(avg_bedtime)
        optimal_bedtime_minute = int((avg_bedtime % 1) * 60)
        optimal_wake_hour = int(avg_wake)
        optimal_wake_minute = int((avg_wake % 1) * 60)
        
        return {
            "aligned": overall_score > 70,
            "score": round(overall_score),
            "optimal_bedtime": f"{optimal_bedtime_hour:02d}:{optimal_bedtime_minute:02d}",
            "optimal_wake": f"{optimal_wake_hour:02d}:{optimal_wake_minute:02d}",
            "bedtime_consistency": round(bedtime_score),
            "wake_consistency": round(wake_score),
        }
    
    async def async_calculate_trends(self) -> Dict[str, Any]:
        """Calculate trends from historical data."""
        trends = {}
        
        # Sleep trend
        if self.sleep_data:
            recent = [s.score for s in self.sleep_data[:7] if s.score]
            older = [s.score for s in self.sleep_data[7:14] if s.score]
            if recent and older:
                trends["sleep"] = {
                    "current": sum(recent) / len(recent),
                    "previous": sum(older) / len(older),
                    "direction": "up" if sum(recent) / len(recent) > sum(older) / len(older) else "down",
                }
        
        # Readiness trend
        if self.readiness_data:
            recent = [r.score for r in self.readiness_data[:7] if r.score]
            older = [r.score for r in self.readiness_data[7:14] if r.score]
            if recent and older:
                trends["readiness"] = {
                    "current": sum(recent) / len(recent),
                    "previous": sum(older) / len(older),
                    "direction": "up" if sum(recent) / len(recent) > sum(older) / len(older) else "down",
                }
        
        # Activity trend
        if self.activity_data:
            recent = [a.steps for a in self.activity_data[:7] if a.steps]
            older = [a.steps for a in self.activity_data[7:14] if a.steps]
            if recent and older:
                trends["activity"] = {
                    "current": sum(recent) / len(recent),
                    "previous": sum(older) / len(older),
                    "direction": "up" if sum(recent) / len(recent) > sum(older) / len(older) else "down",
                }
        
        return trends
    
    async def async_generate_ai_insights(self, data: Optional[Dict] = None) -> None:
        """Generate AI-powered insights from data patterns."""
        if not self.hass.services.has_service("conversation", "process"):
            _LOGGER.debug("AI conversation service not available")
            return
        
        try:
            # Prepare context
            context = self._prepare_ai_context(data or self.data)
            
            # Generate different types of insights
            insights = {}
            
            # Daily insight
            daily_prompt = f"""
            Based on today's Oura data:
            - Readiness score: {context.get('readiness_today', 'N/A')}
            - Sleep score: {context.get('sleep_today', 'N/A')}
            - Sleep duration: {context.get('sleep_hours', 'N/A')} hours
            - Activity: {context.get('steps_today', 'N/A')} steps
            - Wellness phase: {self.wellness_phase}
            
            Provide a brief personalized wellness insight and recommendation for today.
            """
            
            response = await self.hass.services.async_call(
                "conversation",
                "process",
                {"text": daily_prompt},
                blocking=True,
                return_response=True,
            )
            
            if response:
                insights["daily"] = response.get("response", {}).get("speech", {}).get("plain", {}).get("speech", "")
            
            # Sleep optimization insight
            if context.get("sleep_today"):
                sleep_prompt = f"""
                Analyze sleep pattern:
                - Recent average: {context.get('sleep_avg', 'N/A')} hours
                - Bedtime variance: {context.get('bedtime_variance', 'N/A')} hours
                - Deep sleep: {context.get('deep_sleep_percent', 'N/A')}%
                - REM sleep: {context.get('rem_sleep_percent', 'N/A')}%
                
                Suggest specific improvements for better sleep quality.
                """
                
                response = await self.hass.services.async_call(
                    "conversation",
                    "process",
                    {"text": sleep_prompt},
                    blocking=True,
                    return_response=True,
                )
                
                if response:
                    insights["sleep"] = response.get("response", {}).get("speech", {}).get("plain", {}).get("speech", "")
            
            self.ai_insights = insights
            
        except Exception as err:
            _LOGGER.error("Error generating AI insights: %s", err)
    
    def _prepare_ai_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context for AI insight generation."""
        context = {}
        
        # Today's data
        if self.readiness_data:
            context["readiness_today"] = self.readiness_data[0].score
        if self.sleep_data:
            context["sleep_today"] = self.sleep_data[0].score
            context["sleep_hours"] = round(self.sleep_data[0].hours_slept, 1)
            
            # Calculate sleep stage percentages
            if self.sleep_data[0].total_duration:
                total = self.sleep_data[0].total_duration
                context["deep_sleep_percent"] = round(
                    (self.sleep_data[0].deep_duration or 0) / total * 100, 1
                )
                context["rem_sleep_percent"] = round(
                    (self.sleep_data[0].rem_duration or 0) / total * 100, 1
                )
        
        if self.activity_data:
            context["steps_today"] = self.activity_data[0].steps
        
        # Trends and averages
        context.update(self.trends)
        
        # Circadian data
        context["bedtime_consistency"] = self.circadian_alignment.get("bedtime_consistency")
        context["optimal_bedtime"] = self.circadian_alignment.get("optimal_bedtime")
        
        return context
    
    async def _generate_predictions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate predictive insights."""
        predictions = {}
        
        # Predict tomorrow's readiness based on today's activity and sleep
        if self.readiness_data and self.sleep_data and self.activity_data:
            # Simple prediction model (could be enhanced with ML)
            today_readiness = self.readiness_data[0].score or 70
            today_sleep = self.sleep_data[0].score or 70
            today_activity = self.activity_data[0].score or 70
            
            # Weighted prediction
            predicted_readiness = (
                today_readiness * 0.3 +
                today_sleep * 0.5 +
                (100 - today_activity * 0.2)  # High activity reduces next day readiness
            )
            
            predictions["tomorrow_readiness"] = round(predicted_readiness)
            
            # Predict optimal bedtime
            if today_readiness < 70:
                predictions["recommended_bedtime_adjustment"] = -30  # Go to bed 30 min earlier
            elif today_readiness > 85:
                predictions["recommended_bedtime_adjustment"] = 0
            else:
                predictions["recommended_bedtime_adjustment"] = -15
        
        return predictions
    
    async def _publish_mqtt_updates(self, data: Dict[str, Any]) -> None:
        """Publish updates to MQTT for ecosystem integration."""
        if not self.hass.services.has_service("mqtt", "publish"):
            return
        
        try:
            # Publish key metrics
            topics = {
                "sleep/score": self.sleep_data[0].score if self.sleep_data else None,
                "sleep/duration": self.sleep_data[0].hours_slept if self.sleep_data else None,
                "readiness/score": self.readiness_data[0].score if self.readiness_data else None,
                "readiness/temperature": self.readiness_data[0].temperature_deviation if self.readiness_data else None,
                "activity/steps": self.activity_data[0].steps if self.activity_data else None,
                "activity/calories": self.activity_data[0].total_calories if self.activity_data else None,
                "wellness/phase": self.wellness_phase,
                "circadian/score": self.circadian_alignment.get("score"),
            }
            
            for topic_suffix, value in topics.items():
                if value is not None:
                    await self.hass.services.async_call(
                        "mqtt",
                        "publish",
                        {
                            "topic": f"anima/wellness/oura/{topic_suffix}",
                            "payload": str(value),
                            "retain": True,
                        },
                    )
            
        except Exception as err:
            _LOGGER.error("Error publishing to MQTT: %s", err)
    
    def _get_cached_data(self, key: str) -> Any:
        """Get cached data for a specific key."""
        cache_map = {
            "sleep": self.sleep_data,
            "readiness": self.readiness_data,
            "activity": self.activity_data,
            "heart_rate": self.heart_rate_data,
            "stress": self.stress_data,
            "workouts": self.workout_data,
        }
        return cache_map.get(key, [])
    
    def _cache_data(self, key: str, data: Any) -> None:
        """Cache data for a specific key."""
        cache_map = {
            "sleep": "sleep_data",
            "readiness": "readiness_data",
            "activity": "activity_data",
            "heart_rate": "heart_rate_data",
            "stress": "stress_data",
            "workouts": "workout_data",
        }
        
        if key in cache_map:
            setattr(self, cache_map[key], data)
    
    async def async_cleanup_old_data(self) -> None:
        """Clean up old data to prevent memory bloat."""
        max_days = 30
        
        # Clean up each data type
        if self.sleep_data:
            self.sleep_data = self.sleep_data[:max_days]
        if self.readiness_data:
            self.readiness_data = self.readiness_data[:max_days]
        if self.activity_data:
            self.activity_data = self.activity_data[:max_days]
        if self.heart_rate_data:
            self.heart_rate_data = self.heart_rate_data[:max_days]
        if self.stress_data:
            self.stress_data = self.stress_data[:max_days]
        if self.workout_data:
            self.workout_data = self.workout_data[:max_days * 3]  # Keep more workout history