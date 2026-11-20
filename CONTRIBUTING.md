# Contributing

Use English Conventional Commit subjects and PR titles, for example
`fix: handle a failed request` or `chore(deps): update dependencies`. Use the
PR title as the squash-merge commit subject. A breaking change uses `!`.
Use one of `feat`, `fix`, `perf`, `deps`, `revert`, `docs`, `style`, `chore`,
`refactor`, `test`, `build`, or `ci`. CI checks the title and non-merge commit
subjects.

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

## Pre-release recovery

Release Please creates a public pre-release and tag when its release PR is
merged. Before merging, review the release notes and state that pre-releases
may be delivered to HACS users who enable them. Do not mark the release as
latest; promote it to a stable release only after human verification.

To recover a missing ZIP, manually run the Release workflow on `master` with
the existing published pre-release tag (for example, `v0.1.6`). The workflow
checks out that tag and verifies its revision, version, and pre-release status
before building. It adds `open_meteo_local.zip` only when missing; an existing
asset must match byte-for-byte or recovery fails. Never run recovery while
someone is promoting the release.
