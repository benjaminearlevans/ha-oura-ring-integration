"""Test the Oura Ring sensor platform."""
import pytest
from unittest.mock import patch, MagicMock

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import STATE_UNAVAILABLE

from custom_components.oura_full.const import DOMAIN
from custom_components.oura_full.sensor import async_setup_entry


@pytest.mark.unit
async def test_sensor_setup(hass: HomeAssistant, mock_config_entry, mock_coordinator_data):
    """Test sensor platform setup."""
    mock_config_entry.add_to_hass(hass)
    
    # Mock coordinator
    with patch("custom_components.oura_full.sensor.OuraDataUpdateCoordinator") as mock_coordinator:
        mock_coordinator_instance = MagicMock()
        mock_coordinator_instance.data = mock_coordinator_data
        mock_coordinator_instance.user_info = {
            "id": "test_user_123",
            "email": "test@example.com",
            "ring_generation": "3"
        }
        
        # Mock add_entities callback
        mock_add_entities = MagicMock()
        
        # Store coordinator in hass data
        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "coordinator": mock_coordinator_instance
            }
        }
        
        # Test setup
        await async_setup_entry(hass, mock_config_entry, mock_add_entities)
        
        # Verify entities were added
        mock_add_entities.assert_called_once()
        entities = mock_add_entities.call_args[0][0]
        
        # Check that we have the expected number of entities
        assert len(entities) > 0
        
        # Verify some key entities exist
        entity_keys = [entity._key for entity in entities if hasattr(entity, '_key')]
        assert "sleep_score" in entity_keys
        assert "readiness_score" in entity_keys
        assert "activity_score" in entity_keys


@pytest.mark.unit
async def test_sensor_attributes(hass: HomeAssistant, mock_config_entry, mock_coordinator_data):
    """Test sensor entity attributes."""
    mock_config_entry.add_to_hass(hass)
    
    with patch("custom_components.oura_full.sensor.OuraDataUpdateCoordinator") as mock_coordinator:
        mock_coordinator_instance = MagicMock()
        mock_coordinator_instance.data = mock_coordinator_data
        mock_coordinator_instance.user_info = {
            "id": "test_user_123",
            "email": "test@example.com",
            "ring_generation": "3"
        }
        mock_coordinator_instance.last_update = "2024-01-01T12:00:00Z"
        
        # Mock add_entities callback
        mock_add_entities = MagicMock()
        
        # Store coordinator in hass data
        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "coordinator": mock_coordinator_instance
            }
        }
        
        await async_setup_entry(hass, mock_config_entry, mock_add_entities)
        entities = mock_add_entities.call_args[0][0]
        
        # Find sleep score entity
        sleep_score_entity = next(
            (e for e in entities if hasattr(e, '_key') and e._key == "sleep_score"), 
            None
        )
        
        if sleep_score_entity:
            # Test entity properties
            assert sleep_score_entity.unique_id == "test_user_123_sleep_score"
            assert sleep_score_entity.name == "Sleep Score"
            assert sleep_score_entity.native_value == 85
            assert sleep_score_entity.available is True
            
            # Test extra state attributes
            attributes = sleep_score_entity.extra_state_attributes
            assert "last_sync" in attributes
            assert "wellness_phase" in attributes


@pytest.mark.unit
async def test_sensor_unavailable_when_no_data(hass: HomeAssistant, mock_config_entry):
    """Test sensor is unavailable when coordinator has no data."""
    mock_config_entry.add_to_hass(hass)
    
    with patch("custom_components.oura_full.sensor.OuraDataUpdateCoordinator") as mock_coordinator:
        mock_coordinator_instance = MagicMock()
        mock_coordinator_instance.data = None
        mock_coordinator_instance.last_update = None
        mock_coordinator_instance.user_info = {
            "id": "test_user_123",
            "email": "test@example.com",
            "ring_generation": "3"
        }
        
        mock_add_entities = MagicMock()
        
        hass.data[DOMAIN] = {
            mock_config_entry.entry_id: {
                "coordinator": mock_coordinator_instance
            }
        }
        
        await async_setup_entry(hass, mock_config_entry, mock_add_entities)
        entities = mock_add_entities.call_args[0][0]
        
        # Test that entities are unavailable
        for entity in entities:
            if hasattr(entity, 'available'):
                assert entity.available is False
