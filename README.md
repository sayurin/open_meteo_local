# Open-Meteo Enhanced

[![HACS Validation](https://github.com/sayurin/open_meteo_local/actions/workflows/validate.yml/badge.svg)](https://github.com/sayurin/open_meteo_local/actions/workflows/validate.yml)
[![License](https://img.shields.io/github/license/sayurin/open_meteo_local)](https://github.com/sayurin/open_meteo_local/blob/master/LICENSE.md)
[![Version](https://img.shields.io/github/v/release/sayurin/open_meteo_local)](https://github.com/sayurin/open_meteo_local/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/sayurin/open_meteo_local/latest/total)](https://github.com/sayurin/open_meteo_local/releases/latest)
[![Stars](https://img.shields.io/github/stars/sayurin/open_meteo_local?style=flat&color=gold)](https://github.com/sayurin/open_meteo_local)

A custom [Home Assistant](https://www.home-assistant.io/) integration for [Open-Meteo](https://open-meteo.com/) weather forecasting. Provides more accurate forecasts and richer weather data than the built-in `open_meteo` integration — no cloud account or API key required.

## Why use this instead of the built-in Open-Meteo integration?

The most significant difference is the timezone handling. The built-in integration uses UTC as the day boundary for daily forecasts. This means that "today's" forecast is aggregated over a UTC day (00:00–23:59 UTC), not your local day. For example, in JST (UTC+9), the daily high temperature would be calculated from 09:00–32:59 local time, mixing two calendar days. This integration uses the local timezone (`auto`), so daily forecasts correctly represent local calendar days.

In addition, this integration exposes additional weather attributes and uses more efficient API communication.

### Key improvements

- **Local timezone**: Daily forecast aggregation uses local calendar days instead of UTC days.
- **FlatBuffers format**: Uses `openmeteo-sdk` for efficient binary parsing instead of the JSON-based `open-meteo` library.
- **Faster updates**: Polls every 15 minutes (built-in is 30 minutes).

### Attribute comparison

Comparison with the built-in integration in Home Assistant 2026.11.

| Feature | Built-in | Enhanced | Height | Details |
|---|---|---|---|---|
| **Current: Cloud coverage** | ❌ | ✅ | — | |
| **Current: Condition** | Partial | ✅ | — | See **Weather condition accuracy** below |
| **Current: Humidity** | ❌ | ✅ | 2 m | |
| **Current: Apparent temperature** | ❌ | ✅ | 2 m | |
| **Current: Dew point** | ❌ | ✅ | 2 m | |
| **Current: Pressure** | ❌ | ✅ | Sea level | |
| **Current: Temperature** | ✅ | ✅ | 2 m | |
| **Current: Visibility** | ❌ | ✅ | — | |
| **Current: Wind gust speed** | ❌ | ✅ | 10 m | |
| **Current: Wind speed** | ✅ | ✅ | 10 m | |
| **Current: Ozone** | ❌ | ❌ | — | TBD |
| **Current: UV index** | ❌ | ✅ | — | |
| **Current: Wind bearing** | ✅ | ✅ | 10 m | |
| **Daily: Cloud coverage** | ❌ | ✅ | — | `mean` |
| **Daily: Condition** | Partial | ✅ | — | See **Weather condition accuracy** below |
| **Daily: Humidity** | ❌ | ✅ | 2 m | `mean` |
| **Daily: Apparent temperature** | Partial | ✅ | 2 m | `mean` (Built-in uses `max`) |
| **Daily: Dew point** | ❌ | ✅ | 2 m | `mean` |
| **Daily: Precipitation** | ✅ | ✅ | — | `sum` |
| **Daily: Pressure** | ❌ | ✅ | Sea level | `mean` |
| **Daily: Higher temperature** | ✅ | ✅ | 2 m | `max` |
| **Daily: Lower temperature** | ✅ | ✅ | 2 m | `min` |
| **Daily: Wind gust speed** | ✅ | ✅ | 10 m | `max` |
| **Daily: Wind speed** | ✅ | ✅ | 10 m | `max` |
| **Daily: Precipitation probability** | ❌ | ✅ | — | `max` |
| **Daily: UV index** | ❌ | ✅ | — | `max` |
| **Daily: Wind bearing** | ✅ | ✅ | 10 m | `dominant` |
| **Hourly: Cloud coverage** | ✅ | ✅ | — | |
| **Hourly: Condition** | Partial | ✅ | — | See **Weather condition accuracy** below |
| **Hourly: Humidity** | ✅ | ✅ | 2 m | |
| **Hourly: Apparent temperature** | ✅ | ✅ | 2 m | |
| **Hourly: Dew point** | ✅ | ✅ | 2 m | |
| **Hourly: Precipitation** | ✅ | ✅ | — | |
| **Hourly: Pressure** | ✅ | ✅ | Sea level | |
| **Hourly: Temperature** | ✅ | ✅ | 2 m | |
| **Hourly: Wind gust speed** | ✅ | ✅ | 10 m | |
| **Hourly: Wind speed** | ✅ | ✅ | 10 m | |
| **Hourly: Precipitation probability** | ❌ | ✅ | — | |
| **Hourly: UV index** | ❌ | ✅ | — | |
| **Hourly: Wind bearing** | ✅ | ✅ | 10 m | |

### Weather condition accuracy

The built-in integration maps WMO weather codes with limited granularity — for example, mapped thunderstorms are shown as `lightning`, and freezing drizzle/rain is treated as `rainy` or `pouring`.

This integration uses the following condition mapping:

| WMO Weather Code | Built-in | Enhanced |
|---|---|---|
| Freezing Drizzle / Rain | `rainy` / `pouring` | **`snowy-rainy`** |
| Thunderstorm | `lightning` | **`lightning-rainy`** |
| Heavy thunderstorm | Not mapped | **`lightning-rainy`** |
| Thunderstorm with hail | `lightning` | **`hail`** |
| Clear sky (at night) | `sunny` | **`clear-night`** |

The `snowy-rainy` condition highlights possible icing; freezing drizzle or rain does not necessarily mean snow is falling.

## Installation

[![Open your Home Assistant instance and open a repository in the Marketplace.](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=sayurin&repository=open_meteo_local&category=integration)

1. Select the button above, or go to **Settings → Marketplace** and search for **Open-Meteo Enhanced**.
2. Select **Install**, review the version, and confirm.
3. Follow the setup flow to select a zone. If Home Assistant requests a restart, restart it before configuring the integration.

## Prerequisites

- Home Assistant 2026.11.0 or later
- Internet access to reach the [Open-Meteo API](https://open-meteo.com/) — no account or API key required
- At least one zone configured in Home Assistant to use as the weather location (**Settings → Areas, labels & zones**)

## Configuration

If you closed the setup flow after installation:

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

In **Settings → Marketplace**, open **Open-Meteo Enhanced** and select **⋮ → Uninstall**. If it is still configured, the Marketplace offers to remove its setup as well.

## Acknowledgments

- [Open-Meteo](https://open-meteo.com/) for the free, open-source weather API
- [openmeteo-sdk](https://github.com/open-meteo/sdk) for the FlatBuffers parsing library

## License

See [LICENSE](LICENSE.md).
