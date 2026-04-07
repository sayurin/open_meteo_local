"""DataUpdateCoordinator for the Open-Meteo integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from openmeteo_sdk.WeatherApiResponse import WeatherApiResponse

from homeassistant.components.weather import (
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_NATIVE_PRECIPITATION,
    ATTR_FORECAST_NATIVE_TEMP,
    ATTR_FORECAST_NATIVE_TEMP_LOW,
    ATTR_FORECAST_NATIVE_WIND_SPEED,
    ATTR_FORECAST_WIND_BEARING,
    Forecast,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE, CONF_ZONE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    FLATBUFFERS_ERROR_MARKER,
    FLATBUFFERS_PREFIX,
    LOGGER,
    OPEN_METEO_URL,
    SCAN_INTERVAL,
    WMO_TO_HA_CONDITION_MAP,
)

type OpenMeteoConfigEntry = ConfigEntry[OpenMeteoDataUpdateCoordinator]


@dataclass
class OpenMeteoData:
    """Dataclass for Open-Meteo weather data."""

    condition: str | None
    temperature: float | None
    wind_speed: float | None
    wind_bearing: float | None
    daily_forecast: list[Forecast] = field(default_factory=list)
    hourly_forecast: list[tuple[int, Forecast]] = field(default_factory=list)


class OpenMeteoDataUpdateCoordinator(DataUpdateCoordinator[OpenMeteoData]):
    """A Open-Meteo Data Update Coordinator."""

    config_entry: OpenMeteoConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: OpenMeteoConfigEntry) -> None:
        """Initialize the Open-Meteo coordinator."""
        super().__init__(
            hass,
            LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN}_{config_entry.data[CONF_ZONE]}",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> OpenMeteoData:
        """Fetch data from Open-Meteo."""
        if (zone := self.hass.states.get(self.config_entry.data[CONF_ZONE])) is None:
            raise UpdateFailed(f"Zone '{self.config_entry.data[CONF_ZONE]}' not found")

        params = {
            "latitude": zone.attributes[ATTR_LATITUDE],
            "longitude": zone.attributes[ATTR_LONGITUDE],
            "current": "temperature_2m,weather_code,wind_speed_10m,wind_direction_10m",
            "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min,weather_code,wind_direction_10m_dominant,wind_speed_10m_max",
            "hourly": "precipitation,temperature_2m,weather_code",
            "format": "flatbuffers",
            "precipitation_unit": "mm",
            "temperature_unit": "celsius",
            "timezone": "auto",
            "wind_speed_unit": "kmh",
        }

        try:
            session = async_get_clientsession(self.hass)
            async with session.get(OPEN_METEO_URL, params=params) as http_response:
                http_response.raise_for_status()
                data = await http_response.read()
        except Exception as err:
            raise UpdateFailed("Open-Meteo API communication error") from err

        # Parse length-prefixed FlatBuffers frames
        responses: list[WeatherApiResponse] = []
        total = len(data)
        pos = 0
        while pos < total:
            length = int.from_bytes(
                data[pos : pos + FLATBUFFERS_PREFIX], byteorder="little"
            )
            if length == FLATBUFFERS_ERROR_MARKER:
                raise UpdateFailed(data[pos:total].decode())
            responses.append(
                WeatherApiResponse.GetRootAs(data, pos + FLATBUFFERS_PREFIX)
            )
            pos += length + FLATBUFFERS_PREFIX

        response = responses[0]
        tz = timezone(timedelta(seconds=response.UtcOffsetSeconds()))

        # Current weather — variable order matches "current" list above
        condition: str | None = None
        temperature: float | None = None
        wind_speed: float | None = None
        wind_bearing: float | None = None
        if (current := response.Current()) is not None:
            temperature = current.Variables(0).Value()
            condition = WMO_TO_HA_CONDITION_MAP.get(int(current.Variables(1).Value()))
            wind_speed = current.Variables(2).Value()
            wind_bearing = current.Variables(3).Value()

        # Daily forecast — variable order matches "daily" list above
        daily_forecast: list[Forecast] = []
        if (daily := response.Daily()) is not None:
            precip_sum = daily.Variables(0)
            temp_max = daily.Variables(1)
            temp_min = daily.Variables(2)
            weather_code = daily.Variables(3)
            wind_dir = daily.Variables(4)
            wind_spd = daily.Variables(5)
            for i, ts in enumerate(
                range(daily.Time(), daily.TimeEnd(), daily.Interval())
            ):
                _dt = datetime.fromtimestamp(ts, tz=tz)
                entry: Forecast = Forecast(datetime=_dt.isoformat())
                entry[ATTR_FORECAST_CONDITION] = WMO_TO_HA_CONDITION_MAP.get(
                    int(weather_code.Values(i))
                )
                entry[ATTR_FORECAST_NATIVE_PRECIPITATION] = precip_sum.Values(i)
                entry[ATTR_FORECAST_NATIVE_TEMP] = temp_max.Values(i)
                entry[ATTR_FORECAST_NATIVE_TEMP_LOW] = temp_min.Values(i)
                entry[ATTR_FORECAST_WIND_BEARING] = wind_dir.Values(i)
                entry[ATTR_FORECAST_NATIVE_WIND_SPEED] = wind_spd.Values(i)
                daily_forecast.append(entry)

        # Hourly forecast — variable order matches "hourly" list above
        hourly_forecast: list[tuple[int, Forecast]] = []
        if (hourly := response.Hourly()) is not None:
            precipitation = hourly.Variables(0)
            temperature_2m = hourly.Variables(1)
            weather_code_h = hourly.Variables(2)
            for i, ts in enumerate(
                range(hourly.Time(), hourly.TimeEnd(), hourly.Interval())
            ):
                _dt = datetime.fromtimestamp(ts, tz=tz)
                entry = Forecast(datetime=_dt.isoformat())
                entry[ATTR_FORECAST_CONDITION] = WMO_TO_HA_CONDITION_MAP.get(
                    int(weather_code_h.Values(i))
                )
                entry[ATTR_FORECAST_NATIVE_PRECIPITATION] = precipitation.Values(i)
                entry[ATTR_FORECAST_NATIVE_TEMP] = temperature_2m.Values(i)
                hourly_forecast.append((ts, entry))

        return OpenMeteoData(
            condition=condition,
            temperature=temperature,
            wind_speed=wind_speed,
            wind_bearing=wind_bearing,
            daily_forecast=daily_forecast,
            hourly_forecast=hourly_forecast,
        )
