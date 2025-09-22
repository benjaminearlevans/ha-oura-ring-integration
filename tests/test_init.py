"""Test the Oura Ring integration initialization."""
import pytest
from unittest.mock import patch, MagicMock

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN
from homeassistant.exceptions import ConfigEntryNotReady

from custom_components.oura_full.const import DOMAIN


@pytest.mark.integration
async def test_setup_entry_success(hass: HomeAssistant, mock_config_entry, mock_oura_api):
    """Test successful setup of config entry."""
    mock_config_entry.add_to_hass(hass)
    
    with patch("custom_components.oura_full.OuraDataUpdateCoordinator") as mock_coordinator:
        mock_coordinator_instance = MagicMock()
        mock_coordinator.return_value = mock_coordinator_instance
        mock_coordinator_instance.async_config_entry_first_refresh.return_value = None
        
        with patch("custom_components.oura_full.OuraServices") as mock_services:
            mock_services_instance = MagicMock()
            mock_services.return_value = mock_services_instance
            mock_services_instance.async_register_services.return_value = None
            
            assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
            await hass.async_block_till_done()
            
            # Verify coordinator was created and refreshed
            mock_coordinator.assert_called_once()
            mock_coordinator_instance.async_config_entry_first_refresh.assert_called_once()
            
            # Verify services were registered
            mock_services_instance.async_register_services.assert_called_once()
            
            # Verify integration data is stored
            assert DOMAIN in hass.data
            assert mock_config_entry.entry_id in hass.data[DOMAIN]


@pytest.mark.integration
async def test_setup_entry_api_failure(hass: HomeAssistant, mock_config_entry):
    """Test setup failure when API connection fails."""
    mock_config_entry.add_to_hass(hass)
    
    with patch("custom_components.oura_full.api.OuraApiClient") as mock_api:
        mock_api.return_value.get_user_info.side_effect = Exception("API Error")
        
        # Setup should fail with ConfigEntryNotReady
        assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)


@pytest.mark.integration
async def test_setup_entry_no_user_info(hass: HomeAssistant, mock_config_entry):
    """Test setup failure when user info is None."""
    mock_config_entry.add_to_hass(hass)
    
    with patch("custom_components.oura_full.api.OuraApiClient") as mock_api:
        mock_api.return_value.get_user_info.return_value = None
        
        # Setup should fail with ConfigEntryNotReady
        assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)


@pytest.mark.integration
async def test_unload_entry(hass: HomeAssistant, mock_setup_integration):
    """Test unloading a config entry."""
    config_entry = mock_setup_integration
    
    with patch("custom_components.oura_full.OuraServices") as mock_services:
        mock_services_instance = MagicMock()
        mock_services.return_value = mock_services_instance
        mock_services_instance.async_unregister_services.return_value = None
        
        # Store services in hass data to simulate setup
        hass.data[DOMAIN][config_entry.entry_id]["services"] = mock_services_instance
        
        assert await hass.config_entries.async_unload(config_entry.entry_id)
        await hass.async_block_till_done()
        
        # Verify services were unregistered
        mock_services_instance.async_unregister_services.assert_called_once()
        
        # Verify data was cleaned up
        assert config_entry.entry_id not in hass.data[DOMAIN]


@pytest.mark.integration
async def test_device_registration(hass: HomeAssistant, mock_config_entry, mock_oura_api):
    """Test that device is properly registered."""
    mock_config_entry.add_to_hass(hass)
    
    with patch("custom_components.oura_full.OuraDataUpdateCoordinator") as mock_coordinator:
        mock_coordinator_instance = MagicMock()
        mock_coordinator.return_value = mock_coordinator_instance
        mock_coordinator_instance.async_config_entry_first_refresh.return_value = None
        
        with patch("homeassistant.helpers.device_registry.async_get") as mock_device_registry:
            mock_registry = MagicMock()
            mock_device_registry.return_value = mock_registry
            
            assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
            await hass.async_block_till_done()
            
            # Verify device was registered
            mock_registry.async_get_or_create.assert_called_once()
            call_args = mock_registry.async_get_or_create.call_args
            
            # Check device registration parameters
            assert call_args.kwargs["config_entry_id"] == mock_config_entry.entry_id
            assert call_args.kwargs["manufacturer"] == "Oura Health"
            assert "Oura Ring" in call_args.kwargs["name"]


@pytest.mark.integration
async def test_platforms_setup(hass: HomeAssistant, mock_config_entry, mock_oura_api):
    """Test that all platforms are set up correctly."""
    mock_config_entry.add_to_hass(hass)
    
    with patch("custom_components.oura_full.OuraDataUpdateCoordinator") as mock_coordinator:
        mock_coordinator_instance = MagicMock()
        mock_coordinator.return_value = mock_coordinator_instance
        mock_coordinator_instance.async_config_entry_first_refresh.return_value = None
        
        with patch("homeassistant.config_entries.ConfigEntries.async_forward_entry_setups") as mock_forward:
            mock_forward.return_value = True
            
            assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
            await hass.async_block_till_done()
            
            # Verify platforms were set up
            mock_forward.assert_called_once()
            call_args = mock_forward.call_args
            
            # Check that expected platforms are included
            platforms = call_args[0][1]  # Second argument is the platforms list
            expected_platforms = ["sensor", "binary_sensor", "select", "switch", "number", "button"]
            
            for platform in expected_platforms:
                assert platform in platforms
