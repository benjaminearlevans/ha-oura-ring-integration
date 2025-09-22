"""Test the Oura Ring config flow."""
import pytest
from unittest.mock import patch, MagicMock

from homeassistant import config_entries
from homeassistant.const import CONF_TOKEN, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.oura_full.const import DOMAIN
from custom_components.oura_full.config_flow import CannotConnect, InvalidAuth


async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {}


async def test_form_invalid_auth(hass: HomeAssistant) -> None:
    """Test we handle invalid auth."""
    with patch(
        "custom_components.oura_full.config_flow.OuraApiClient.get_user_info",
        side_effect=InvalidAuth,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_TOKEN: "invalid_token",
                CONF_NAME: "Test Oura Ring",
            },
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect(hass: HomeAssistant) -> None:
    """Test we handle cannot connect error."""
    with patch(
        "custom_components.oura_full.config_flow.OuraApiClient.get_user_info",
        side_effect=CannotConnect,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_TOKEN: "test_token",
                CONF_NAME: "Test Oura Ring",
            },
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_success(hass: HomeAssistant) -> None:
    """Test successful config flow."""
    mock_user_info = {
        "id": "test_user_123",
        "email": "test@example.com",
        "ring_generation": "3"
    }
    
    with patch(
        "custom_components.oura_full.config_flow.OuraApiClient.get_user_info",
        return_value=mock_user_info,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_TOKEN: "valid_token",
                CONF_NAME: "Test Oura Ring",
            },
        )

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Test Oura Ring"
    assert result2["data"] == {
        CONF_TOKEN: "valid_token",
        CONF_NAME: "Test Oura Ring",
        "user_id": "test_user_123",
        "email": "test@example.com",
    }


async def test_form_already_configured(hass: HomeAssistant) -> None:
    """Test we handle already configured."""
    mock_user_info = {
        "id": "test_user_123",
        "email": "test@example.com",
        "ring_generation": "3"
    }
    
    # Create an existing entry
    entry = hass.config_entries.async_entries(DOMAIN)[0] if hass.config_entries.async_entries(DOMAIN) else None
    if not entry:
        hass.config_entries._entries.append(
            config_entries.ConfigEntry(
                version=1,
                domain=DOMAIN,
                title="Existing Oura Ring",
                data={CONF_TOKEN: "existing_token"},
                source=config_entries.SOURCE_USER,
                unique_id="test_user_123",
            )
        )
    
    with patch(
        "custom_components.oura_full.config_flow.OuraApiClient.get_user_info",
        return_value=mock_user_info,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_TOKEN: "another_token",
                CONF_NAME: "Another Oura Ring",
            },
        )

    assert result2["type"] == FlowResultType.ABORT
    assert result2["reason"] == "already_configured"
