# Open-Meteo Enhanced

[![HACS Validation](https://github.com/sayurin/open_meteo_local/actions/workflows/validate.yml/badge.svg)](https://github.com/sayurin/open_meteo_local/actions/workflows/validate.yml)

A custom [Home Assistant](https://www.home-assistant.io/) integration for [Open-Meteo](https://open-meteo.com/) weather forecasting. Provides more accurate forecasts and richer weather data than the built-in `open_meteo` integration.

## Why use this instead of the built-in Open-Meteo integration?

The most significant difference is the timezone handling. The built-in integration uses UTC as the day boundary for daily forecasts. This means that "today's" forecast is aggregated over a UTC day (00:00–23:59 UTC), not your local day. For example, in JST (UTC+9), the daily high temperature would be calculated from 09:00–32:59 local time, mixing two calendar days. This integration uses the local timezone (`auto`), so daily forecasts correctly represent local calendar days.

In addition, this integration exposes many more weather attributes and uses more efficient API communication.

### Key improvements

- **Local timezone**: Daily forecast aggregation uses local calendar days instead of UTC days.
- **FlatBuffers format**: Uses `openmeteo-sdk` for efficient binary parsing instead of the JSON-based `open-meteo` library.
- **Faster updates**: Polls every 15 minutes (built-in is 30 minutes).

### Attribute comparison

| Feature | Built-in `open_meteo` | `open_meteo_local` |
|---|---|---|
| **Current: Temperature** | Yes | Yes |
| **Current: Humidity** | No | **Yes** |
| **Current: Dew point** | No | **Yes** |
| **Current: Apparent temperature** | No | **Yes** |
| **Current: Cloud coverage** | No | **Yes** |
| **Current: Pressure (MSL)** | No | **Yes** |
| **Current: Visibility** | No | **Yes** |
| **Current: Wind speed** | Yes | Yes |
| **Current: Wind bearing** | Yes | Yes |
| **Current: Wind gust speed** | No | **Yes** |
| **Current: UV index** | No | **Yes** |
| **Current: Ozone** | No | No |
| **Current: Day/Night awareness** | No | **Yes** |
| **Daily: Temperature max/min** | Yes | Yes |
| **Daily: Apparent temperature** | No | **Yes** |
| **Daily: Precipitation sum** | Yes | Yes |
| **Daily: Precipitation probability** | No | **Yes** |
| **Daily: Wind speed / direction** | Yes | Yes |
| **Daily: Wind gust speed** | No | **Yes** |
| **Daily: UV index** | No | **Yes** |
| **Daily: Humidity** | No | No |
| **Daily: Dew point** | No | No |
| **Daily: Cloud coverage** | No | No |
| **Daily: Pressure** | No | No |
| **Hourly: Temperature** | Yes | Yes |
| **Hourly: Precipitation** | Yes | Yes |
| **Hourly: Humidity** | No | **Yes** |
| **Hourly: Dew point** | No | **Yes** |
| **Hourly: Apparent temperature** | No | **Yes** |
| **Hourly: Precipitation probability** | No | **Yes** |
| **Hourly: Cloud coverage** | No | **Yes** |
| **Hourly: Pressure** | No | **Yes** |
| **Hourly: Wind speed / direction / gusts** | No | **Yes** |
| **Hourly: UV index** | No | **Yes** |
| **Hourly: Day/Night awareness** | No | **Yes** |

### Weather condition accuracy

The built-in integration maps WMO weather codes with limited granularity — for example, thunderstorms are all shown as `lightning`, and freezing drizzle/rain is treated as plain `rainy`.

This integration provides more accurate condition mapping:

| WMO Weather Code | Built-in `open_meteo` | `open_meteo_local` |
|---|---|---|
| Freezing Drizzle / Rain | `rainy` | **`snowy-rainy`** |
| Thunderstorm | `lightning` | **`lightning-rainy`** |
| Thunderstorm with hail | `lightning` | **`hail`** |
| Clear sky (at night) | `sunny` | **`clear-night`** |

## Installation

### HACS (recommended)

1. Open HACS in your Home Assistant instance.
2. Add this repository as a custom repository:
   - URL: `https://github.com/sayurin/open_meteo_local`
   - Category: Integration
3. Search for "Open-Meteo Enhanced" and install it.
4. Restart Home Assistant.

### Manual

1. Copy the `custom_components/open_meteo_local` directory to your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**.
2. Search for **Open-Meteo Enhanced**.
3. Select a zone to use for the weather location.

The integration creates a weather entity bound to the selected zone. The location (latitude/longitude) is read from the zone entity, so updating the zone will update the weather data location.

## Technical details

- Uses the [Open-Meteo API](https://open-meteo.com/) with FlatBuffers format (`openmeteo-sdk`) for efficient binary parsing, instead of the JSON-based `open-meteo` library used by the built-in integration.
- Polls every 15 minutes.
- Provides 48-hour hourly forecasts and 7-day daily forecasts.
- Timestamps use the local timezone (`auto`) for more intuitive forecast times.

## License

See [LICENSE](LICENSE.md).
