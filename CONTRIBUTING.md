# Contributing

Use English Conventional Commit subjects and PR titles, for example
`fix: handle a failed request` or `chore(deps): update dependencies`. Use the
PR title as the squash-merge commit subject. A breaking change uses `!`.

The development project is not a distributable Python package; `version.txt`
and the integration manifest are managed by Release Please. Python 3.14.10 and
uv 0.13.1 or later are required. Bootstrap the workspace after changing
dependencies or switching branches. Run the independent test environment via:

```shell
bash scripts/hass-dev.sh run open_meteo_local uv run --locked --extra dev --extra ha-minimum pytest
bash scripts/hass-dev.sh run open_meteo_local uv run --locked --extra dev --extra ha-latest pytest
bash scripts/hass-dev.sh run open_meteo_local uv run --locked --extra dev --extra ha-latest prek run --all-files
```

The Home Assistant extras are mutually exclusive. Each pins an official
`pytest-homeassistant` version and its matching Home Assistant version. The
offline tests do not establish that the real Open-Meteo API works.

The lifecycle, configuration, weather and diagnostics tests are adapted from
Home Assistant's `tests/components/open_meteo`. This integration retains its
zone-based unique IDs and does not implement Core's connection check,
reconfiguration flow or unique-ID migration. Its tests use FlatBuffers rather
than Core's JSON forecast fixture.

Mypy currently checks the constants, diagnostics and weather modules; the
configuration flow and coordinator require further type work. Prek runs with
`--no-sync` to preserve the selected HA environment; sync the selected extras
before running it. Install `gh actions-lock` v0.4.1 to update the workflow lock
and never edit the generated lock manually.

## Draft releases

Release Please creates a PR and a draft release using the repository GitHub
App. `APP_ID` and `APP_PRIVATE_KEY` must be configured before this can work.
Review the draft and its ZIP before publishing a stable release manually.
Draft creation also creates a tag: verify HACS tag discovery before merging a
release PR. To recover a draft attachment, run the Release workflow with its
existing tag. The workflow verifies the tag, committed versions and draft
status and replaces the same-named asset. Do not recover while publishing.
Published releases are not recovery targets.
