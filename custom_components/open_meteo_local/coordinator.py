"""DataUpdateCoordinator for the Open-Meteo integration."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import cache

from homeassistant.components.weather import (
    ATTR_FORECAST_CLOUD_COVERAGE,
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_HUMIDITY,
    ATTR_FORECAST_IS_DAYTIME,
    ATTR_FORECAST_NATIVE_APPARENT_TEMP,
    ATTR_FORECAST_NATIVE_DEW_POINT,
    ATTR_FORECAST_NATIVE_PRECIPITATION,
    ATTR_FORECAST_NATIVE_PRESSURE,
    ATTR_FORECAST_NATIVE_TEMP,
    ATTR_FORECAST_NATIVE_TEMP_LOW,
    ATTR_FORECAST_NATIVE_WIND_GUST_SPEED,
    ATTR_FORECAST_NATIVE_WIND_SPEED,
    ATTR_FORECAST_PRECIPITATION_PROBABILITY,
    ATTR_FORECAST_UV_INDEX,
    ATTR_FORECAST_WIND_BEARING,
    Forecast,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ZONE, EntityStateAttribute
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from openmeteo_sdk.WeatherApiResponse import WeatherApiResponse

from .const import (
    DOMAIN,
    FLATBUFFERS_ERROR_MARKER,
    FLATBUFFERS_PREFIX,
    LOGGER,
    OPEN_METEO_URL,
    SCAN_INTERVAL,
    resolve_condition,
)

type OpenMeteoConfigEntry = ConfigEntry[OpenMeteoDataUpdateCoordinator]

# The condition field must be first in the current and hourly map.
CONDITION_INDEX = 0

_CURRENT_MAP = (
    ("weather_code", None, int),
    ("is_day", ATTR_FORECAST_IS_DAYTIME, bool),
    ("cloud_cover", ATTR_FORECAST_CLOUD_COVERAGE, int),
    ("relative_humidity_2m", ATTR_FORECAST_HUMIDITY, float),
    ("apparent_temperature", ATTR_FORECAST_NATIVE_APPARENT_TEMP, float),
    ("dew_point_2m", ATTR_FORECAST_NATIVE_DEW_POINT, float),
    ("pressure_msl", ATTR_FORECAST_NATIVE_PRESSURE, float),
    ("temperature_2m", ATTR_FORECAST_NATIVE_TEMP, float),
    ("visibility", "native_visibility", lambda value: float(value) / 1000),
    ("wind_gusts_10m", ATTR_FORECAST_NATIVE_WIND_GUST_SPEED, float),
    ("wind_speed_10m", ATTR_FORECAST_NATIVE_WIND_SPEED, float),
    ("uv_index", ATTR_FORECAST_UV_INDEX, float),
    ("wind_direction_10m", ATTR_FORECAST_WIND_BEARING, float),
)

_DAILY_MAP = (
    (
        "weather_code",
        ATTR_FORECAST_CONDITION,
        lambda value: resolve_condition(int(value)),
    ),
    ("cloud_cover_mean", ATTR_FORECAST_CLOUD_COVERAGE, int),
    ("relative_humidity_2m_mean", ATTR_FORECAST_HUMIDITY, float),
    ("apparent_temperature_mean", ATTR_FORECAST_NATIVE_APPARENT_TEMP, float),
    ("dew_point_2m_mean", ATTR_FORECAST_NATIVE_DEW_POINT, float),
    ("precipitation_sum", ATTR_FORECAST_NATIVE_PRECIPITATION, float),
    ("pressure_msl_mean", ATTR_FORECAST_NATIVE_PRESSURE, float),
    ("temperature_2m_max", ATTR_FORECAST_NATIVE_TEMP, float),
    ("temperature_2m_min", ATTR_FORECAST_NATIVE_TEMP_LOW, float),
    ("wind_gusts_10m_max", ATTR_FORECAST_NATIVE_WIND_GUST_SPEED, float),
    ("wind_speed_10m_max", ATTR_FORECAST_NATIVE_WIND_SPEED, float),
    ("precipitation_probability_max", ATTR_FORECAST_PRECIPITATION_PROBABILITY, int),
    ("uv_index_max", ATTR_FORECAST_UV_INDEX, float),
    ("wind_direction_10m_dominant", ATTR_FORECAST_WIND_BEARING, float),
)

_HOURLY_MAP = (
    ("weather_code", None, int),
    ("is_day", ATTR_FORECAST_IS_DAYTIME, bool),
    ("cloud_cover", ATTR_FORECAST_CLOUD_COVERAGE, int),
    ("relative_humidity_2m", ATTR_FORECAST_HUMIDITY, float),
    ("apparent_temperature", ATTR_FORECAST_NATIVE_APPARENT_TEMP, float),
    ("dew_point_2m", ATTR_FORECAST_NATIVE_DEW_POINT, float),
    ("precipitation", ATTR_FORECAST_NATIVE_PRECIPITATION, float),
    ("pressure_msl", ATTR_FORECAST_NATIVE_PRESSURE, float),
    ("temperature_2m", ATTR_FORECAST_NATIVE_TEMP, float),
    ("wind_gusts_10m", ATTR_FORECAST_NATIVE_WIND_GUST_SPEED, float),
    ("wind_speed_10m", ATTR_FORECAST_NATIVE_WIND_SPEED, float),
    ("precipitation_probability", ATTR_FORECAST_PRECIPITATION_PROBABILITY, int),
    ("uv_index", ATTR_FORECAST_UV_INDEX, float),
    ("wind_direction_10m", ATTR_FORECAST_WIND_BEARING, float),
)


@cache
def _get_params(latitude: float, longitude: float) -> dict[str, float | str]:
    """Return cached Open-Meteo request parameters."""
    return {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join(field for field, *_ in _CURRENT_MAP),
        "daily": ",".join(field for field, *_ in _DAILY_MAP),
        "hourly": ",".join(field for field, *_ in _HOURLY_MAP),
        # Required by: https://github.com/open-meteo/open-meteo/issues/699
        "forecast_hours": "168",
        "format": "flatbuffers",
        "precipitation_unit": "mm",
        "temperature_unit": "celsius",
        "timezone": "auto",
        "wind_speed_unit": "kmh",
    }


@dataclass(slots=True)
class OpenMeteoData:
    """Dataclass for Open-Meteo weather data."""

    condition: str | None = None
    # Used to resolve the current condition; not exposed by the weather entity.
    is_daytime: bool | None = None
    native_temperature: float | None = None
    humidity: float | None = None
    native_dew_point: float | None = None
    native_apparent_temperature: float | None = None
    cloud_coverage: int | None = None
    native_pressure: float | None = None
    native_visibility: float | None = None
    native_wind_speed: float | None = None
    wind_bearing: float | None = None
    native_wind_gust_speed: float | None = None
    uv_index: float | None = None
    daily_forecast: list[Forecast] = field(default_factory=list)
    hourly_forecast: list[Forecast] = field(default_factory=list)


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

        params = _get_params(
            zone.attributes[EntityStateAttribute.LATITUDE],
            zone.attributes[EntityStateAttribute.LONGITUDE],
        )

        try:
            session = async_get_clientsession(self.hass)
            async with session.get(OPEN_METEO_URL, params=params) as http_response:
                http_response.raise_for_status()
                payload = await http_response.read()
        except Exception as err:
            raise UpdateFailed("Open-Meteo API communication error") from err

        # Parse the first length-prefixed FlatBuffers frame.
        # Additional frames are ignored with a warning.
        total = len(payload)
        if total < FLATBUFFERS_PREFIX:
            raise UpdateFailed("Malformed response frame header")

        length = int.from_bytes(payload[:FLATBUFFERS_PREFIX], byteorder="little")
        if length == FLATBUFFERS_ERROR_MARKER:
            raise UpdateFailed(payload.decode())
        if length <= 0:
            raise UpdateFailed("Malformed response frame length")

        frame_end = FLATBUFFERS_PREFIX + length
        if frame_end > total:
            raise UpdateFailed("Malformed response frame length")

        response = WeatherApiResponse.GetRootAs(payload, FLATBUFFERS_PREFIX)

        if frame_end < total:
            LOGGER.warning(
                "Received %s extra bytes from Open-Meteo for %s; using first frame only",
                total - frame_end,
                self.config_entry.data[CONF_ZONE],
            )

        data = OpenMeteoData()

        # Current weather
        if (current := response.Current()) is not None:
            for j, (_, data_key, conv) in enumerate(_CURRENT_MAP):
                if data_key is not None:
                    setattr(data, data_key, conv(current.Variables(j).Value()))
            data.condition = resolve_condition(
                int(current.Variables(CONDITION_INDEX).Value()), data.is_daytime
            )

        # Daily forecast
        daily_forecast: list[Forecast] = []
        if (daily := response.Daily()) is not None:
            daily_forecast = [
                Forecast(datetime=datetime.fromtimestamp(ts, tz=UTC).isoformat())
                for ts in range(daily.Time(), daily.TimeEnd(), daily.Interval())
            ]
            for j, (_, ha_key, conv) in enumerate(_DAILY_MAP):
                var = daily.Variables(j)
                for i, entry in enumerate(daily_forecast):
                    entry[ha_key] = conv(var.Values(i))

        # Hourly forecast
        hourly_forecast: list[Forecast] = []
        if (hourly := response.Hourly()) is not None:
            hourly_forecast = [
                Forecast(datetime=datetime.fromtimestamp(ts, tz=UTC).isoformat())
                for ts in range(hourly.Time(), hourly.TimeEnd(), hourly.Interval())
            ]
            for j, (_, ha_key, conv) in enumerate(_HOURLY_MAP):
                if ha_key is not None:
                    var = hourly.Variables(j)
                    for i, entry in enumerate(hourly_forecast):
                        entry[ha_key] = conv(var.Values(i))
            condition_var = hourly.Variables(CONDITION_INDEX)
            for i, entry in enumerate(hourly_forecast):
                entry[ATTR_FORECAST_CONDITION] = resolve_condition(
                    int(condition_var.Values(i)),
                    bool(entry[ATTR_FORECAST_IS_DAYTIME]),
                )

        data.daily_forecast = daily_forecast
        data.hourly_forecast = hourly_forecast
        return data
