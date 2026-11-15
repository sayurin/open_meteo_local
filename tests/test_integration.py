"""Lifecycle and weather tests adapted from Core's Open-Meteo tests."""

import flatbuffers
import pytest
from homeassistant.components.weather import DOMAIN as WEATHER_DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_ENTITY_ID
from pytest_homeassistant.components.diagnostics import get_diagnostics_for_config_entry


async def test_load_forecasts_and_unload(hass, mock_config_entry, mock_open_meteo):
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED
    state = hass.states.get("weather.home")
    assert state is not None
    assert state.state == "clear-night"
    assert state.attributes["temperature"] == 20
    assert state.attributes["visibility"] == 10
    for forecast_type, first_condition in (
        ("daily", "sunny"),
        ("hourly", "clear-night"),
    ):
        response = await hass.services.async_call(
            WEATHER_DOMAIN,
            "get_forecasts",
            {ATTR_ENTITY_ID: "weather.home", "type": forecast_type},
            blocking=True,
            return_response=True,
        )
        forecasts = response["weather.home"]["forecast"]
        assert len(forecasts) == 2
        assert forecasts[0]["condition"] == first_condition
        assert forecasts[0]["temperature"] == (25 if forecast_type == "daily" else 20)
        if forecast_type == "daily":
            assert forecasts[0]["datetime"] == "2024-12-31T15:00:00+00:00"
        else:
            assert forecasts[1]["condition"] == "sunny"
    _, kwargs = mock_open_meteo[0].get.call_args
    assert kwargs["params"]["timezone"] == "auto"
    assert kwargs["params"]["format"] == "flatbuffers"
    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


async def test_connection_failure_and_recovery(
    hass, mock_config_entry, mock_open_meteo
):
    mock_open_meteo[1].raise_for_status.side_effect = OSError("offline")
    mock_config_entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY
    mock_open_meteo[1].raise_for_status.side_effect = None
    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    assert mock_config_entry.state is ConfigEntryState.LOADED


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"\x00\x00\x00\x00",
        b"\x10\x00\x00\x00x",
        b"\x04\x00\x00\x00\xff\xff\xff\xff",
    ],
)
async def test_invalid_frame_causes_setup_retry(
    hass, mock_config_entry, mock_open_meteo, payload
):
    mock_open_meteo[1].read.return_value = payload
    mock_config_entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_zone_removed_before_setup(hass, mock_config_entry):
    hass.states.async_remove("zone.home")
    mock_config_entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_weather_without_data(hass, mock_config_entry, mock_open_meteo):
    builder = flatbuffers.Builder(32)
    builder.StartObject(15)
    builder.FinishSizePrefixed(builder.EndObject())
    mock_open_meteo[1].read.return_value = bytes(builder.Output())
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    state = hass.states.get("weather.home")
    assert state is not None
    assert state.state == "unknown"
    assert "temperature" not in state.attributes
    for forecast_type in ("daily", "hourly"):
        response = await hass.services.async_call(
            WEATHER_DOMAIN,
            "get_forecasts",
            {ATTR_ENTITY_ID: "weather.home", "type": forecast_type},
            blocking=True,
            return_response=True,
        )
        assert response == {"weather.home": {"forecast": []}}


async def test_diagnostics(hass, hass_client, mock_config_entry, mock_open_meteo):
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    diagnostics = await get_diagnostics_for_config_entry(
        hass, hass_client, mock_config_entry
    )
    assert diagnostics["condition"] == "clear-night"
    assert diagnostics["native_temperature"] == 20
    assert "latitude" not in diagnostics
    assert "longitude" not in diagnostics
