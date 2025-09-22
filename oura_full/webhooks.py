"""Webhook handler for Oura Full integration."""
import asyncio
import hashlib
import hmac
import json
import logging
from typing import Any, Dict, Optional

from aiohttp import web
from homeassistant.components.webhook import (
    async_register as webhook_register,
    async_unregister as webhook_unregister,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.network import get_url
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

WEBHOOK_EVENTS = {
    "create.daily_sleep": "sleep_data_updated",
    "update.daily_sleep": "sleep_data_updated", 
    "create.daily_readiness": "readiness_data_updated",
    "update.daily_readiness": "readiness_data_updated",
    "create.daily_activity": "activity_data_updated",
    "update.daily_activity": "activity_data_updated",
    "create.workout": "workout_created",
    "update.workout": "workout_updated",
    "create.session": "session_created",
    "update.session": "session_updated",
    "create.tag": "tag_created",
    "update.tag": "tag_updated",
    "create.daily_stress": "stress_data_updated",
    "update.daily_stress": "stress_data_updated",
    "create.daily_spo2": "spo2_data_updated",
    "update.daily_spo2": "spo2_data_updated",
}


class OuraWebhookHandler:
    """Handle Oura API webhooks for real-time updates."""

    def __init__(self, hass: HomeAssistant, coordinator) -> None:
        """Initialize the webhook handler."""
        self.hass = hass
        self.coordinator = coordinator
        self.webhook_id = None
        self.webhook_url = None
        self._webhook_secret = None
        self._registered = False

    async def async_setup(self) -> None:
        """Set up the webhook handler."""
        try:
            # Generate webhook ID and secret
            self.webhook_id = self._generate_webhook_id()
            self._webhook_secret = self._generate_webhook_secret()
            
            # Register webhook with Home Assistant
            webhook_register(
                self.hass,
                DOMAIN,
                "Oura Webhook",
                self.webhook_id,
                self._handle_webhook,
            )
            
            # Generate webhook URL
            self.webhook_url = self._get_webhook_url()
            
            # Register webhook with Oura API (if supported)
            await self._register_with_oura_api()
            
            self._registered = True
            _LOGGER.info("Webhook handler setup complete: %s", self.webhook_url)
            
        except Exception as err:
            _LOGGER.error("Failed to setup webhook handler: %s", err)
            raise

    async def async_cleanup(self) -> None:
        """Clean up the webhook handler."""
        if self._registered:
            try:
                # Unregister from Oura API
                await self._unregister_from_oura_api()
                
                # Unregister from Home Assistant
                webhook_unregister(self.hass, self.webhook_id)
                
                self._registered = False
                _LOGGER.info("Webhook handler cleaned up")
                
            except Exception as err:
                _LOGGER.error("Error during webhook cleanup: %s", err)

    def _generate_webhook_id(self) -> str:
        """Generate a unique webhook ID."""
        import uuid
        return f"oura_{uuid.uuid4().hex[:8]}"

    def _generate_webhook_secret(self) -> str:
        """Generate a webhook secret for verification."""
        import secrets
        return secrets.token_urlsafe(32)

    def _get_webhook_url(self) -> str:
        """Get the webhook URL."""
        try:
            base_url = get_url(self.hass, prefer_external=True)
            return f"{base_url}/api/webhook/{self.webhook_id}"
        except Exception:
            # Fallback if external URL not available
            return f"http://localhost:8123/api/webhook/{self.webhook_id}"

    async def _register_with_oura_api(self) -> None:
        """Register webhook with Oura API."""
        # Note: Oura API webhook registration would typically be done through their developer portal
        # This is a placeholder for when/if they support programmatic webhook registration
        
        _LOGGER.info("Webhook URL ready for Oura API registration: %s", self.webhook_url)
        
        # For now, we'll just log the webhook URL for manual registration
        # In the future, this could make an API call to register the webhook
        
        # Example of what the API call might look like:
        # webhook_data = {
        #     "callback_url": self.webhook_url,
        #     "verification_token": self._webhook_secret,
        #     "event_type": "create.daily_sleep,update.daily_sleep,create.daily_readiness"
        # }
        # 
        # response = await self.coordinator.api._request(
        #     "POST", 
        #     "v2/webhook", 
        #     data=webhook_data
        # )

    async def _unregister_from_oura_api(self) -> None:
        """Unregister webhook from Oura API."""
        # Placeholder for webhook unregistration
        _LOGGER.info("Webhook unregistered from Oura API")

    async def _handle_webhook(self, hass: HomeAssistant, webhook_id: str, request: web.Request) -> web.Response:
        """Handle incoming webhook requests."""
        try:
            # Get request data
            body = await request.read()
            headers = dict(request.headers)
            
            _LOGGER.debug("Received webhook: %s", {
                "webhook_id": webhook_id,
                "headers": headers,
                "body_length": len(body)
            })
            
            # Verify webhook signature if present
            if not await self._verify_webhook_signature(headers, body):
                _LOGGER.warning("Webhook signature verification failed")
                return web.Response(status=401, text="Unauthorized")
            
            # Parse JSON payload
            try:
                payload = json.loads(body.decode('utf-8'))
            except json.JSONDecodeError as err:
                _LOGGER.error("Invalid JSON in webhook payload: %s", err)
                return web.Response(status=400, text="Invalid JSON")
            
            # Process the webhook event
            await self._process_webhook_event(payload)
            
            return web.Response(status=200, text="OK")
            
        except Exception as err:
            _LOGGER.error("Error handling webhook: %s", err)
            return web.Response(status=500, text="Internal Server Error")

    async def _verify_webhook_signature(self, headers: Dict[str, str], body: bytes) -> bool:
        """Verify webhook signature for security."""
        # Check for signature header (format may vary by API)
        signature_header = headers.get('x-oura-signature') or headers.get('x-hub-signature-256')
        
        if not signature_header or not self._webhook_secret:
            # If no signature expected or configured, skip verification
            return True
        
        try:
            # Extract signature from header
            if signature_header.startswith('sha256='):
                signature = signature_header[7:]
            else:
                signature = signature_header
            
            # Calculate expected signature
            expected_signature = hmac.new(
                self._webhook_secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as err:
            _LOGGER.error("Error verifying webhook signature: %s", err)
            return False

    async def _process_webhook_event(self, payload: Dict[str, Any]) -> None:
        """Process incoming webhook event."""
        try:
            # Extract event information
            event_type = payload.get('event_type')
            data_type = payload.get('data_type')
            user_id = payload.get('user_id')
            timestamp = payload.get('timestamp')
            
            _LOGGER.info("Processing webhook event: %s for user %s", event_type, user_id)
            
            # Verify this webhook is for our user
            if user_id != self.coordinator.user_info.get('id'):
                _LOGGER.warning("Webhook for different user: %s", user_id)
                return
            
            # Map event type to internal event
            internal_event = WEBHOOK_EVENTS.get(event_type)
            if not internal_event:
                _LOGGER.debug("Unhandled webhook event type: %s", event_type)
                return
            
            # Process based on data type
            await self._handle_data_update(data_type, payload.get('data', {}))
            
            # Fire Home Assistant event
            self.hass.bus.async_fire(
                f"{DOMAIN}_webhook_received",
                {
                    "event_type": event_type,
                    "data_type": data_type,
                    "internal_event": internal_event,
                    "timestamp": timestamp,
                    "user_id": user_id,
                }
            )
            
            # Trigger coordinator update for affected data
            await self._trigger_selective_update(data_type)
            
        except Exception as err:
            _LOGGER.error("Error processing webhook event: %s", err)

    async def _handle_data_update(self, data_type: str, data: Dict[str, Any]) -> None:
        """Handle specific data type updates."""
        if data_type == "daily_sleep":
            await self._handle_sleep_update(data)
        elif data_type == "daily_readiness":
            await self._handle_readiness_update(data)
        elif data_type == "daily_activity":
            await self._handle_activity_update(data)
        elif data_type == "workout":
            await self._handle_workout_update(data)
        elif data_type == "session":
            await self._handle_session_update(data)
        elif data_type == "tag":
            await self._handle_tag_update(data)
        elif data_type == "daily_stress":
            await self._handle_stress_update(data)
        elif data_type == "daily_spo2":
            await self._handle_spo2_update(data)
        else:
            _LOGGER.debug("Unhandled data type: %s", data_type)

    async def _handle_sleep_update(self, data: Dict[str, Any]) -> None:
        """Handle sleep data update."""
        _LOGGER.info("Sleep data updated via webhook")
        
        # Fire specific event for sleep updates
        self.hass.bus.async_fire(
            f"{DOMAIN}_sleep_updated",
            {
                "score": data.get('score'),
                "total_sleep": data.get('total_sleep'),
                "efficiency": data.get('efficiency'),
                "day": data.get('day'),
            }
        )
        
        # Check for sleep quality alerts
        score = data.get('score')
        if score and score < 70:
            await self._create_notification(
                "Poor Sleep Alert",
                f"Last night's sleep score was {score}. Consider recovery activities today."
            )

    async def _handle_readiness_update(self, data: Dict[str, Any]) -> None:
        """Handle readiness data update."""
        _LOGGER.info("Readiness data updated via webhook")
        
        score = data.get('score')
        temperature_deviation = data.get('temperature_deviation')
        
        # Fire specific event
        self.hass.bus.async_fire(
            f"{DOMAIN}_readiness_updated",
            {
                "score": score,
                "temperature_deviation": temperature_deviation,
                "day": data.get('day'),
            }
        )
        
        # Check for readiness alerts
        if score and score < 60:
            await self._create_notification(
                "Low Readiness Alert",
                f"Readiness score is {score}. Consider taking it easy today."
            )
        
        # Check for temperature alerts
        if temperature_deviation and abs(temperature_deviation) > 0.5:
            await self._create_notification(
                "Temperature Alert",
                f"Body temperature deviation: {temperature_deviation:.1f}°C"
            )

    async def _handle_activity_update(self, data: Dict[str, Any]) -> None:
        """Handle activity data update."""
        _LOGGER.info("Activity data updated via webhook")
        
        # Fire specific event
        self.hass.bus.async_fire(
            f"{DOMAIN}_activity_updated",
            {
                "score": data.get('score'),
                "steps": data.get('steps'),
                "total_calories": data.get('total_calories'),
                "day": data.get('day'),
            }
        )

    async def _handle_workout_update(self, data: Dict[str, Any]) -> None:
        """Handle workout data update."""
        _LOGGER.info("Workout data updated via webhook")
        
        # Fire specific event
        self.hass.bus.async_fire(
            f"{DOMAIN}_workout_updated",
            {
                "activity": data.get('activity'),
                "calories": data.get('calories'),
                "duration": data.get('duration'),
                "intensity": data.get('intensity'),
            }
        )

    async def _handle_session_update(self, data: Dict[str, Any]) -> None:
        """Handle session data update."""
        _LOGGER.info("Session data updated via webhook")
        
        # Fire specific event
        self.hass.bus.async_fire(
            f"{DOMAIN}_session_updated",
            {
                "type": data.get('type'),
                "day": data.get('day'),
            }
        )

    async def _handle_tag_update(self, data: Dict[str, Any]) -> None:
        """Handle tag data update."""
        _LOGGER.info("Tag data updated via webhook")
        
        # Fire specific event
        self.hass.bus.async_fire(
            f"{DOMAIN}_tag_updated",
            {
                "tag": data.get('tag'),
                "day": data.get('day'),
            }
        )

    async def _handle_stress_update(self, data: Dict[str, Any]) -> None:
        """Handle stress data update."""
        _LOGGER.info("Stress data updated via webhook")
        
        score = data.get('day_summary', {}).get('score')
        
        # Fire specific event
        self.hass.bus.async_fire(
            f"{DOMAIN}_stress_updated",
            {
                "score": score,
                "day": data.get('day'),
            }
        )
        
        # Check for high stress alerts
        if score and score > 70:
            await self._create_notification(
                "High Stress Alert",
                f"Stress level is elevated ({score}). Consider relaxation techniques."
            )

    async def _handle_spo2_update(self, data: Dict[str, Any]) -> None:
        """Handle SpO2 data update."""
        _LOGGER.info("SpO2 data updated via webhook")
        
        # Fire specific event
        self.hass.bus.async_fire(
            f"{DOMAIN}_spo2_updated",
            {
                "average": data.get('spo2_percentage', {}).get('average'),
                "day": data.get('day'),
            }
        )

    async def _trigger_selective_update(self, data_type: str) -> None:
        """Trigger selective coordinator update based on data type."""
        # Instead of full refresh, we could implement selective updates
        # For now, trigger a full refresh but with shorter delay
        
        async def delayed_refresh():
            await asyncio.sleep(5)  # Short delay to allow for multiple updates
            await self.coordinator.async_request_refresh()
        
        # Cancel any pending refresh and schedule new one
        if hasattr(self, '_refresh_task') and not self._refresh_task.done():
            self._refresh_task.cancel()
        
        self._refresh_task = asyncio.create_task(delayed_refresh())

    async def _create_notification(self, title: str, message: str) -> None:
        """Create a notification for webhook events."""
        # Check notification preferences
        notification_preference = getattr(self.coordinator, 'notification_preference', 'all')
        
        if notification_preference in ['all', 'important']:
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": title,
                    "message": message,
                    "notification_id": f"{DOMAIN}_webhook_{dt_util.now().timestamp()}",
                },
            )

    @property
    def is_registered(self) -> bool:
        """Return if webhook is registered."""
        return self._registered

    @property
    def webhook_info(self) -> Dict[str, Any]:
        """Return webhook information for configuration."""
        return {
            "webhook_id": self.webhook_id,
            "webhook_url": self.webhook_url,
            "registered": self._registered,
            "secret_configured": bool(self._webhook_secret),
        }
