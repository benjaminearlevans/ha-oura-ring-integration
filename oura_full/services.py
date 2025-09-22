"""Service handlers for Oura Ring integration."""
import logging
from datetime import datetime, timedelta
import csv
import json
from typing import Any, Dict

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
import voluptuous as vol

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_services(
    hass: HomeAssistant,
    coordinator: "OuraDataUpdateCoordinator"
) -> None:
    """Set up Oura services."""
    
    async def handle_refresh_data(call: ServiceCall) -> None:
        """Handle data refresh service call."""
        include_historical = call.data.get("include_historical", False)
        
        if include_historical:
            # Temporarily extend date range
            coordinator.api.default_lookback_days = 7
        
        await coordinator.async_request_refresh()
        
    async def handle_get_wellness_insight(call: ServiceCall) -> Dict[str, Any]:
        """Generate wellness insight."""
        insight_type = call.data["insight_type"]
        context_days = call.data.get("context_days", 7)
        
        # Gather context data
        context = await _prepare_insight_context(coordinator, context_days)
        
        # Generate insight based on type
        insight = await _generate_insight(hass, insight_type, context)
        
        # Store in coordinator for access by entities
        coordinator.ai_insights[f"manual_{insight_type}"] = insight
        
        return {"insight": insight}
    
    async def handle_set_wellness_mode(call: ServiceCall) -> None:
        """Set wellness mode override."""
        mode = call.data["mode"]
        duration = call.data.get("duration_hours", 24)
        
        # Set override in coordinator
        coordinator.wellness_mode_override = {
            "mode": mode,
            "expires": datetime.now() + timedelta(hours=duration)
        }
        
        # Fire event for automations
        hass.bus.async_fire(
            f"{DOMAIN}_wellness_mode_changed",
            {"mode": mode, "duration": duration}
        )
        
    async def handle_export_data(call: ServiceCall) -> Dict[str, str]:
        """Export wellness data."""
        format_type = call.data["format"]
        date_range = call.data.get("date_range", 30)
        destination = call.data.get("destination", f"/config/oura_export_{datetime.now().strftime('%Y%m%d')}")
        
        # Gather data for export
        export_data = await _prepare_export_data(coordinator, date_range)
        
        # Export based on format
        if format_type == "csv":
            file_path = f"{destination}.csv"
            await _export_csv(export_data, file_path)
        elif format_type == "json":
            file_path = f"{destination}.json"
            await _export_json(export_data, file_path)
        elif format_type == "influxdb":
            await _export_influxdb(hass, export_data)
            file_path = "influxdb"
        
        return {"file": file_path, "records": len(export_data)}
    
    async def handle_trigger_recovery_protocol(call: ServiceCall) -> None:
        """Trigger recovery protocol."""
        level = call.data["protocol_level"]
        components = call.data.get("components", ["lighting", "temperature"])
        
        # Fire events for each component
        for component in components:
            hass.bus.async_fire(
                f"{DOMAIN}_recovery_protocol",
                {
                    "level": level,
                    "component": component,
                    "readiness_score": coordinator.data.get("readiness", [{}])[0].get("score")
                }
            )
        
        # Create persistent notification
        await hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "Recovery Protocol Activated",
                "message": f"Recovery level: {level}\nComponents: {', '.join(components)}",
                "notification_id": f"{DOMAIN}_recovery_protocol"
            }
        )
    
    # Register services
    hass.services.async_register(
        DOMAIN,
        "refresh_data",
        handle_refresh_data,
    )
    
    hass.services.async_register(
        DOMAIN,
        "get_wellness_insight",
        handle_get_wellness_insight,
        supports_response="optional",
    )
    
    hass.services.async_register(
        DOMAIN,
        "set_wellness_mode",
        handle_set_wellness_mode,
    )
    
    hass.services.async_register(
        DOMAIN,
        "export_wellness_data",
        handle_export_data,
        supports_response="optional",
    )
    
    hass.services.async_register(
        DOMAIN,
        "trigger_recovery_protocol",
        handle_trigger_recovery_protocol,
    )

async def _generate_insight(
    hass: HomeAssistant,
    insight_type: str,
    context: Dict[str, Any]
) -> str:
    """Generate AI-powered insight."""
    
    prompts = {
        "sleep_optimization": """
        Based on the sleep data showing {sleep_trend} trend with average score of {avg_sleep_score},
        bedtime variance of {bedtime_variance} hours, and {sleep_debt} hours of sleep debt,
        provide specific recommendations for improving sleep quality.
        """,
        "recovery_plan": """
        With readiness at {readiness_score}%, HRV trending {hrv_trend}, 
        and {workout_count} workouts in the past week,
        suggest a recovery plan for the next 24 hours.
        """,
    }
    
    prompt = prompts.get(insight_type, "").format(**context)
    
    # Call AI service if available
    if hass.services.has_service("conversation", "process"):
        response = await hass.services.async_call(
            "conversation",
            "process",
            {"text": prompt},
            blocking=True,
            return_response=True
        )
        return response.get("response", {}).get("text", "Unable to generate insight")
    
    # Fallback to rule-based insights
    return _generate_rule_based_insight(insight_type, context)