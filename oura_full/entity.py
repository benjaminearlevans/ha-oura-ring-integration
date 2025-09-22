"""Base entity classes for Oura Ring integration."""
import logging
from typing import Any, Dict, Optional

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OuraDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class OuraEntityBase(CoordinatorEntity):
    """Base class for all Oura entities."""

    coordinator: OuraDataUpdateCoordinator
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OuraDataUpdateCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entry_id = entry_id
        self._attr_device_info = self._get_device_info()
        
    def _get_device_info(self) -> DeviceInfo:
        """Get device information."""
        user_info = self.coordinator.user_info
        return DeviceInfo(
            identifiers={(DOMAIN, user_info.get("id", "unknown"))},
            name=f"Oura Ring ({user_info.get('email', 'User')})",
            manufacturer="Oura Health",
            model=f"Ring Gen {user_info.get('ring_generation', '3')}",
            sw_version=user_info.get("app_version"),
            configuration_url="https://cloud.ouraring.com",
        )
    
    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update is not None
    
    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
    
    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return common attributes for all entities."""
        attributes = {
            "last_sync": self.coordinator.last_update,
            "wellness_phase": self.coordinator.wellness_phase,
        }
        
        # Add rate limit info for diagnostic purposes
        if hasattr(self.coordinator, "rate_limit_remaining"):
            attributes["api_rate_limit"] = self.coordinator.rate_limit_remaining
        
        return attributes


class OuraDeviceEntity(OuraEntityBase):
    """Base class for Oura device entities."""
    
    def __init__(
        self,
        coordinator: OuraDataUpdateCoordinator,
        entry_id: str,
        device_class: Optional[str] = None,
    ) -> None:
        """Initialize the device entity."""
        super().__init__(coordinator, entry_id)
        self._device_class = device_class
        
    @property
    def device_class(self) -> Optional[str]:
        """Return the device class."""
        return self._device_class


class OuraControlEntity(OuraEntityBase):
    """Base class for Oura control entities (switches, selects, etc)."""
    
    def __init__(
        self,
        coordinator: OuraDataUpdateCoordinator,
        entry_id: str,
        key: str,
    ) -> None:
        """Initialize the control entity."""
        super().__init__(coordinator, entry_id)
        self._key = key
        self._attr_unique_id = f"{coordinator.user_info['id']}_{key}"
        
    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        # Control entities are enabled by default
        return True