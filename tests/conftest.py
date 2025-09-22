"""Fixtures for Oura Ring integration tests."""
import pytest
from unittest.mock import patch, MagicMock
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN, CONF_NAME

from custom_components.oura_full.const import DOMAIN


@pytest.fixture
def mock_oura_api():
    """Mock the Oura API client."""
    with patch("custom_components.oura_full.api.OuraApiClient") as mock_api:
        mock_instance = MagicMock()
        mock_api.return_value = mock_instance
        
        # Mock successful user info response
        mock_instance.get_user_info.return_value = {
            "id": "test_user_123",
            "email": "test@example.com",
            "ring_generation": "3",
            "app_version": "4.0.0"
        }
        
        # Mock successful data responses
        mock_instance.get_sleep_data.return_value = {
            "data": [{
                "id": "sleep_123",
                "day": "2024-01-01",
                "score": 85,
                "total_sleep_duration": 28800,  # 8 hours in seconds
                "efficiency": 92
            }]
        }
        
        mock_instance.get_readiness_data.return_value = {
            "data": [{
                "id": "readiness_123",
                "day": "2024-01-01",
                "score": 78,
                "temperature_deviation": 0.2
            }]
        }
        
        mock_instance.get_activity_data.return_value = {
            "data": [{
                "id": "activity_123",
                "day": "2024-01-01",
                "score": 82,
                "steps": 8500,
                "total_calories": 2200
            }]
        }
        
        yield mock_instance


@pytest.fixture
def mock_config_entry():
    """Mock a config entry."""
    return ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Test Oura Ring",
        data={
            CONF_TOKEN: "test_token_123",
            CONF_NAME: "Test Oura Ring",
            "user_id": "test_user_123",
            "email": "test@example.com",
        },
        options={
            "scan_interval": 15,
            "enable_webhooks": False,
            "enable_ai_insights": False,
            "enable_mqtt_bridge": False,
        },
        unique_id="test_user_123",
        source="user",
    )


@pytest.fixture
def mock_coordinator_data():
    """Mock coordinator data."""
    return {
        "sleep": {
            "score": 85,
            "total_hours": 8.0,
            "efficiency": 92,
            "deep_sleep_hours": 1.5,
            "rem_sleep_hours": 2.0,
            "light_sleep_hours": 4.5,
        },
        "readiness": {
            "score": 78,
            "temperature_deviation": 0.2,
            "hrv_balance": 0.1,
        },
        "activity": {
            "score": 82,
            "steps": 8500,
            "calories": 2200,
            "active_calories": 450,
        },
        "wellness_phase": "maintenance",
        "last_update": "2024-01-01T12:00:00Z",
    }


@pytest.fixture
async def mock_setup_integration(hass: HomeAssistant, mock_config_entry, mock_oura_api):
    """Set up the integration for testing."""
    mock_config_entry.add_to_hass(hass)
    
    with patch("custom_components.oura_full.OuraDataUpdateCoordinator") as mock_coordinator:
        mock_coordinator_instance = MagicMock()
        mock_coordinator.return_value = mock_coordinator_instance
        mock_coordinator_instance.async_config_entry_first_refresh.return_value = None
        mock_coordinator_instance.data = {
            "sleep": {"score": 85},
            "readiness": {"score": 78},
            "activity": {"score": 82},
        }
        
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        yield mock_config_entry
