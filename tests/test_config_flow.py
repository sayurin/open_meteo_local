"""Config flow tests adapted from Home Assistant's Open-Meteo integration."""

from unittest.mock import patch

from homeassistant.components.zone import ENTITY_ID_HOME
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_ZONE
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component

from custom_components.open_meteo_local.const import DOMAIN


async def test_user_flow(hass):
    with patch(
        "custom_components.open_meteo_local.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_ZONE: ENTITY_ID_HOME}
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_ZONE: ENTITY_ID_HOME}
    assert result["result"].unique_id == ENTITY_ID_HOME


async def test_already_configured(hass, mock_config_entry):
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ZONE: ENTITY_ID_HOME}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_missing_zone_uses_fallback_title(hass):
    with patch(
        "custom_components.open_meteo_local.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_ZONE: "zone.gone"}
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Open-Meteo"
    assert result["result"].unique_id == "zone.gone"


async def test_user_form_serializes_for_frontend(hass, hass_client):
    assert await async_setup_component(hass, "config", {})
    client = await hass_client()
    response = await client.post(
        "/api/config/config_entries/flow", json={"handler": DOMAIN}
    )
    assert response.status == 200
    result = await response.json()
    assert result["type"] == "form"
    assert result["data_schema"][0]["name"] == CONF_ZONE
