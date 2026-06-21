# Open-Meteo Enhanced

[![HACS](https://img.shields.io/badge/hacs-default-blue)](https://hacs.xyz/)
[![HACS Validation](https://github.com/sayurin/open_meteo_local/actions/workflows/validate.yml/badge.svg)](https://github.com/sayurin/open_meteo_local/actions/workflows/validate.yml)
[![License](https://img.shields.io/github/license/sayurin/open_meteo_local)](https://github.com/sayurin/open_meteo_local/blob/master/LICENSE.md)
[![Version](https://img.shields.io/github/v/release/sayurin/open_meteo_local)](https://github.com/sayurin/open_meteo_local/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/sayurin/open_meteo_local/latest/total)](https://github.com/sayurin/open_meteo_local/releases/latest)
[![Stars](https://img.shields.io/github/stars/sayurin/open_meteo_local?style=flat&color=gold)](https://github.com/sayurin/open_meteo_local)

A custom [Home Assistant](https://www.home-assistant.io/) integration for [Open-Meteo](https://open-meteo.com/) weather forecasting. Provides more accurate forecasts and richer weather data than the built-in `open_meteo` integration — no cloud account or API key required.

## Why use this instead of the built-in Open-Meteo integration?

The most significant difference is the timezone handling. The built-in integration uses UTC as the day boundary for daily forecasts. This means that "today's" forecast is aggregated over a UTC day (00:00–23:59 UTC), not your local day. For example, in JST (UTC+9), the daily high temperature would be calculated from 09:00–32:59 local time, mixing two calendar days. This integration uses the local timezone (`auto`), so daily forecasts correctly represent local calendar days.

In addition, this integration exposes many more weather attributes and uses more efficient API communication.

### Key improvements

- **Local timezone**: Daily forecast aggregation uses local calendar days instead of UTC days.
- **FlatBuffers format**: Uses `openmeteo-sdk` for efficient binary parsing instead of the JSON-based `open-meteo` library.
- **Faster updates**: Polls every 15 minutes (built-in is 30 minutes).

### Attribute comparison

| Feature | Built-in `open_meteo` | `open_meteo_local` | Non-obvious details |
|---|---|---|---|
| **Current: Cloud coverage** | No | **Yes** | - |
| **Current: Condition** | Partial | **Yes** | See **Weather condition accuracy** below |
| **Current: Humidity** | No | **Yes** | 2m |
| **Current: Apparent temperature** | No | **Yes** | 2m |
| **Current: Dew point** | No | **Yes** | 2m |
| **Current: Pressure** | No | **Yes** | Sea level pressure |
| **Current: Temperature** | Yes | Yes | 2m |
| **Current: Visibility** | No | **Yes** | - |
| **Current: Wind gust speed** | No | **Yes** | 10m |
| **Current: Wind speed** | Yes | Yes | 10m |
| **Current: Ozone** | No | No | TBD |
| **Current: UV index** | No | **Yes** | - |
| **Current: Wind bearing** | Yes | Yes | 10m |
| **Daily: Cloud coverage** | No | **Yes** | `mean` |
| **Daily: Condition** | Partial | **Yes** | See **Weather condition accuracy** below |
| **Daily: Humidity** | No | **Yes** | 2m `mean` |
| **Daily: Apparent temperature** | No | **Yes** | 2m `mean` |
| **Daily: Dew point** | No | **Yes** | 2m `mean` |
| **Daily: Precipitation** | Yes | Yes | `sum` |
| **Daily: Pressure** | No | **Yes** | sea level pressure `mean` |
| **Daily: Higher temperature** | Yes | Yes | 2m `max` |
| **Daily: Lower temperature** | Yes | Yes | 2m `min` |
| **Daily: Wind gust speed** | No | **Yes** | 10m `max` |
| **Daily: Wind speed** | Yes | Yes | 10m `max` |
| **Daily: Precipitation probability** | No | **Yes** | daily `max` |
| **Daily: UV index** | No | **Yes** | daily `max` |
| **Daily: Wind bearing** | Yes | Yes | 10m `dominant` |
| **Hourly: Cloud coverage** | No | **Yes** | - |
| **Hourly: Condition** | Partial | **Yes** | See **Weather condition accuracy** below |
| **Hourly: Humidity** | No | **Yes** | 2m |
| **Hourly: Apparent temperature** | No | **Yes** | 2m |
| **Hourly: Dew point** | No | **Yes** | 2m |
| **Hourly: Precipitation** | Yes | Yes | - |
| **Hourly: Pressure** | No | **Yes** | sea level pressure |
| **Hourly: Temperature** | Yes | Yes | 2m |
| **Hourly: Wind gust speed** | No | **Yes** | 10m |
| **Hourly: Wind speed** | No | **Yes** | 10m |
| **Hourly: Precipitation probability** | No | **Yes** | - |
| **Hourly: UV index** | No | **Yes** | - |
| **Hourly: Wind bearing** | No | **Yes** | 10m |

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

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=sayurin&repository=open_meteo_local&category=integration)

1. Select the button above, or search for **"Open-Meteo Enhanced"** in HACS.
2. Install the integration.
3. Restart Home Assistant.

### Manual

1. Copy the `custom_components/open_meteo_local` directory to your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

## Prerequisites

- Home Assistant with [HACS](https://hacs.xyz/) installed (for HACS installation) or access to the `custom_components` directory (for manual installation)
- Internet access to reach the [Open-Meteo API](https://open-meteo.com/) — no account or API key required
- At least one zone configured in Home Assistant to use as the weather location (**Settings → Areas, labels & zones**)

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**.
2. Search for **Open-Meteo Enhanced**.
3. Select a zone to use for the weather location.

The integration creates a weather entity bound to the selected zone. The location (latitude/longitude) is read from the zone entity, so updating the zone coordinates will automatically update the weather data location.

Multiple instances can be added to get forecasts for different locations — one instance per zone.

## Known Limitations

- Requires internet access; there is no local or offline mode.
- Each configuration entry covers a single zone. Add multiple instances for multiple locations.
- Ozone is intentionally not fetched to keep all data on a single weather forecast API call.
- Forecast history is not retained — only current and future forecasts are available.

## Troubleshooting

### Weather entity shows as unavailable

The weather entity appears as unavailable after setup.

1. Check that Home Assistant has internet access and can reach `api.open-meteo.com`.
2. Verify the selected zone exists and has valid coordinates set in **Settings → Areas, labels & zones**.
3. Check **Settings → System → Logs** for any error messages related to `open_meteo_local`.
4. Try reloading the integration from **Settings → Devices & Services → Open-Meteo Enhanced → ⋮ → Reload**.

### Daily forecast temperatures look incorrect

Daily high or low temperatures seem wrong, especially around midnight.

This is the exact problem this integration solves — the built-in `open_meteo` integration uses UTC day boundaries. Confirm you are using **Open-Meteo Enhanced** and not the built-in integration. If the issue persists, verify the zone's latitude and longitude are correct.

### Weather condition shows "sunny" at night

Make sure day/night awareness is working by checking that the zone's coordinates are correct. This integration uses the `is_day` flag from the Open-Meteo API based on the zone's location.

## Removing the Integration

To remove the integration, go to **Settings → Devices & Services**, select **Open-Meteo Enhanced**, and select **Delete**.

## Acknowledgments

- [Open-Meteo](https://open-meteo.com/) for the free, open-source weather API
- [openmeteo-sdk](https://github.com/open-meteo/sdk) for the FlatBuffers parsing library

## License

See [LICENSE](LICENSE.md).
