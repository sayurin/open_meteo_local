"""Fixtures for Open-Meteo Enhanced tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import flatbuffers
import pytest
from pytest_homeassistant.common import MockConfigEntry

from custom_components.open_meteo_local.const import DOMAIN


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    """Allow Home Assistant to load this custom integration."""


@pytest.fixture
def mock_config_entry():
    return MockConfigEntry(
        title="Home", domain=DOMAIN, data={"zone": "zone.home"}, unique_id="zone.home"
    )


def _section(builder, values, start, interval, count=2, missing=()):
    variables = []
    for index, value in enumerate(values):
        if isinstance(value, tuple):
            builder.StartVector(4, count, 4)
            for i in reversed(range(count)):
                item = (
                    float("nan")
                    if i == count - 1 and index in missing
                    else value[i % len(value)]
                )
                builder.PrependFloat32(item)
            array = builder.EndVector()
            builder.StartObject(13)
            builder.PrependUOffsetTRelativeSlot(3, array, 0)
        else:
            builder.StartObject(13)
            builder.PrependFloat32Slot(2, value, 0)
        variables.append(builder.EndObject())
    builder.StartVector(4, len(variables), 4)
    for variable in reversed(variables):
        builder.PrependUOffsetTRelative(variable)
    vector = builder.EndVector()
    builder.StartObject(4)
    builder.PrependInt64Slot(0, start, 0)
    builder.PrependInt64Slot(1, start + interval * count, 0)
    builder.PrependInt32Slot(2, interval, 0)
    builder.PrependUOffsetTRelativeSlot(3, vector, 0)
    return builder.EndObject()


@pytest.fixture
def forecast_payload(request):
    """Build a real size-prefixed FlatBuffers response with local-day boundaries."""
    options = getattr(request, "param", {})
    weather_code = options.get("weather_code", 0)
    builder = flatbuffers.Builder(1024)
    current = _section(
        builder,
        [weather_code, 0, 30, 65, 18, 12, 1010, 20, 10000, 25, 10, 4, 180],
        0,
        3600,
    )
    daily = _section(
        builder,
        [
            (weather_code, 3),
            (30, 40),
            (65, 70),
            (18, 19),
            (12, 13),
            (2, 3),
            (1010, 1011),
            (25, 26),
            (15, 16),
            (25, 26),
            (10, 11),
            (30, 40),
            (4, 5),
            (180, 190),
        ],
        1735657200,
        86400,
        count=options.get("daily_steps", 2),
        missing=options.get("daily_missing", ()),
    )
    hourly = _section(
        builder,
        [
            (weather_code, 0),
            (0, 1),
            (30, 40),
            (65, 70),
            (18, 19),
            (12, 13),
            (2, 3),
            (1010, 1011),
            (20, 21),
            (25, 26),
            (10, 11),
            (30, 40),
            (4, 5),
            (180, 190),
        ],
        1735686000,
        3600,
        count=options.get("hourly_steps", 2),
        missing=options.get("hourly_missing", ()),
    )
    builder.StartObject(15)
    builder.PrependUOffsetTRelativeSlot(9, current, 0)
    builder.PrependUOffsetTRelativeSlot(10, daily, 0)
    builder.PrependUOffsetTRelativeSlot(11, hourly, 0)
    builder.FinishSizePrefixed(builder.EndObject())
    return bytes(builder.Output())


@pytest.fixture
def mock_open_meteo(forecast_payload):
    response = MagicMock()
    response.read = AsyncMock(return_value=forecast_payload)
    response.raise_for_status = MagicMock()
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=response)
    context.__aexit__ = AsyncMock(return_value=False)
    session = MagicMock()
    session.get.return_value = context
    with patch(
        "custom_components.open_meteo_local.coordinator.async_get_clientsession",
        return_value=session,
    ):
        yield session, response
