"""Oura API v2 client implementation."""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from aiohttp import ClientError, ClientSession
from asyncio import TimeoutError

from .const import (
    API_BASE_URL,
    API_TIMEOUT,
    MAX_RETRIES,
    RATE_LIMIT_DELAY,
)

_LOGGER = logging.getLogger(__name__)


class OuraApiClient:
    """Async Oura API v2 client."""

    def __init__(
        self,
        session: ClientSession,
        token: str,
        auth_type: str = "pat",
        base_url: Optional[str] = None,
    ) -> None:
        """Initialize the API client."""
        self.session = session
        self.token = token
        self.auth_type = auth_type
        self.base_url = base_url or API_BASE_URL
        
        # Rate limiting tracking
        self._rate_limit_remaining = 100
        self._rate_limit_reset = datetime.now()
        
        # Cache for reducing API calls
        self._cache = {}
        self._cache_expiry = {}

    @property
    def headers(self) -> Dict[str, str]:
        """Get request headers."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "User-Agent": "HomeAssistant-OuraFull/1.0",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        retries: int = 0,
    ) -> Any:
        """Make API request with error handling and rate limiting."""
        url = f"{self.base_url}/{endpoint}"
        
        # Check cache first
        cache_key = f"{method}:{endpoint}:{urlencode(params or {})}"
        if cache_key in self._cache:
            if self._cache_expiry.get(cache_key, datetime.min) > datetime.now():
                _LOGGER.debug("Using cached response for %s", endpoint)
                return self._cache[cache_key]
        
        # Rate limit check
        if self._rate_limit_remaining <= 5:
            wait_time = max(0, (self._rate_limit_reset - datetime.now()).seconds)
            if wait_time > 0:
                _LOGGER.info("Rate limit approaching, waiting %d seconds", wait_time)
                await asyncio.sleep(wait_time)
        
        try:
            async with self.session.request(
                method,
                url,
                headers=self.headers,
                params=params,
                json=data,
                timeout=API_TIMEOUT,
            ) as response:
                # Update rate limit info from headers
                if "X-RateLimit-Remaining" in response.headers:
                    self._rate_limit_remaining = int(response.headers["X-RateLimit-Remaining"])
                
                if "X-RateLimit-Reset" in response.headers:
                    self._rate_limit_reset = datetime.fromtimestamp(
                        int(response.headers["X-RateLimit-Reset"])
                    )
                
                # Handle rate limiting
                if response.status == 429:
                    if retries < MAX_RETRIES:
                        retry_after = int(response.headers.get("Retry-After", 60))
                        _LOGGER.warning("Rate limited, retrying after %d seconds", retry_after)
                        await asyncio.sleep(retry_after)
                        return await self._request(method, endpoint, params, data, retries + 1)
                    raise ClientError("Rate limit exceeded")
                
                # Handle authentication errors
                if response.status == 401:
                    raise ClientError("Authentication failed - token may be expired")
                
                # Handle not found
                if response.status == 404:
                    _LOGGER.debug("Endpoint not found: %s", endpoint)
                    return None
                
                # Raise for other HTTP errors
                response.raise_for_status()
                
                # Parse JSON response
                result = await response.json()
                
                # Cache successful responses
                self._cache[cache_key] = result
                self._cache_expiry[cache_key] = datetime.now() + timedelta(minutes=5)
                
                return result
                
        except TimeoutError:
            if retries < MAX_RETRIES:
                _LOGGER.debug("Request timeout, retry %d/%d", retries + 1, MAX_RETRIES)
                await asyncio.sleep(RATE_LIMIT_DELAY)
                return await self._request(method, endpoint, params, data, retries + 1)
            raise ClientError(f"Request timeout after {MAX_RETRIES} retries")
        except Exception as err:
            _LOGGER.error("API request failed for %s: %s", endpoint, err)
            raise

    async def _paginated_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
    ) -> List[Dict]:
        """Handle paginated API responses."""
        all_data = []
        next_token = None
        params = params or {}
        
        while True:
            if next_token:
                params["next_token"] = next_token
            
            response = await self._request("GET", endpoint, params)
            
            if response and "data" in response:
                all_data.extend(response["data"])
                
                # Check for next page
                next_token = response.get("next_token")
                if not next_token:
                    break
            else:
                break
        
        return all_data

    # User Information
    async def get_user_info(self) -> Dict[str, Any]:
        """Get user personal information."""
        response = await self._request("GET", "v2/usercollection/personal_info")
        
        # Extract user data from response
        if response and isinstance(response, list) and len(response) > 0:
            return response[0]
        elif response and isinstance(response, dict):
            return response
        
        return {}

    # Sleep Data
    async def get_daily_sleep(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict]:
        """Get daily sleep data."""
        params = self._prepare_date_params(start_date, end_date)
        return await self._paginated_request("v2/usercollection/daily_sleep", params)

    async def get_sleep_periods(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict]:
        """Get detailed sleep period data."""
        params = self._prepare_date_params(start_date, end_date)
        return await self._paginated_request("v2/usercollection/sleep", params)

    async def get_sleep_time(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict]:
        """Get recommended sleep time data."""
        params = self._prepare_date_params(start_date, end_date)
        return await self._paginated_request("v2/usercollection/sleep_time", params)

    # Readiness Data
    async def get_daily_readiness(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict]:
        """Get daily readiness data."""
        params = self._prepare_date_params(start_date, end_date)
        return await self._paginated_request("v2/usercollection/daily_readiness", params)

    async def get_daily_resilience(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict]:
        """Get daily resilience data."""
        params = self._prepare_date_params(start_date, end_date)
        return await self._paginated_request("v2/usercollection/daily_resilience", params)

    # Activity Data
    async def get_daily_activity(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict]:
        """Get daily activity data."""
        params = self._prepare_date_params(start_date, end_date)
        return await self._paginated_request("v2/usercollection/daily_activity", params)

    async def get_workouts(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict]:
        """Get workout data."""
        params = self._prepare_date_params(start_date, end_date)
        return await self._paginated_request("v2/usercollection/workout", params)

    async def get_sessions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict]:
        """Get session data (meditation, breathing, etc.)."""
        params = self._prepare_date_params(start_date, end_date)
        return await self._paginated_request("v2/usercollection/session", params)

    # Physiological Data
    async def get_heart_rate(
        self,
        start_datetime: Optional[str] = None,
        end_datetime: Optional[str] = None,
    ) -> List[Dict]:
        """Get heart rate data."""
        params = {}
        if start_datetime:
            params["start_datetime"] = start_datetime
        if end_datetime:
            params["end_datetime"] = end_datetime
        
        return await self._paginated_request("v2/usercollection/heartrate", params)

    async def get_daily_spo2(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict]:
        """Get daily blood oxygen (SpO2) data."""
        params = self._prepare_date_params(start_date, end_date)
        return await self._paginated_request("v2/usercollection/daily_spo2", params)

    async def get_daily_stress(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict]:
        """Get daily stress data."""
        params = self._prepare_date_params(start_date, end_date)
        return await self._paginated_request("v2/usercollection/daily_stress", params)

    async def get_vo2_max(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict]:
        """Get VO2 max data."""
        params = self._prepare_date_params(start_date, end_date)
        return await self._paginated_request("v2/usercollection/vo2_max", params)

    # Rest and Recovery
    async def get_rest_mode_periods(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict]:
        """Get rest mode period data."""
        params = self._prepare_date_params(start_date, end_date)
        return await self._paginated_request("v2/usercollection/rest_mode_period", params)

    # Tags and Enhanced Tags
    async def get_tags(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict]:
        """Get tag data."""
        params = self._prepare_date_params(start_date, end_date)
        return await self._paginated_request("v2/usercollection/tag", params)

    async def get_enhanced_tags(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict]:
        """Get enhanced tag data."""
        params = self._prepare_date_params(start_date, end_date)
        return await self._paginated_request("v2/usercollection/enhanced_tag", params)

    # Ring Configuration
    async def get_ring_configuration(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict]:
        """Get ring configuration data."""
        params = self._prepare_date_params(start_date, end_date)
        return await self._paginated_request("v2/usercollection/ring_configuration", params)

    # Cardiovascular Age
    async def get_daily_cardiovascular_age(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict]:
        """Get daily cardiovascular age data."""
        params = self._prepare_date_params(start_date, end_date)
        return await self._paginated_request("v2/usercollection/daily_cardiovascular_age", params)

    # Helper Methods
    def _prepare_date_params(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, str]:
        """Prepare date parameters for API requests."""
        params = {}
        
        if not end_date:
            end_date = datetime.now().date().isoformat()
        if not start_date:
            start_date = (datetime.now().date() - timedelta(days=7)).isoformat()
        
        params["start_date"] = start_date
        params["end_date"] = end_date
        
        return params

    async def test_connection(self) -> bool:
        """Test the API connection and authentication."""
        try:
            user_info = await self.get_user_info()
            return bool(user_info)
        except Exception as err:
            _LOGGER.error("Connection test failed: %s", err)
            return False

    def clear_cache(self) -> None:
        """Clear the response cache."""
        self._cache.clear()
        self._cache_expiry.clear()
        _LOGGER.debug("API cache cleared")