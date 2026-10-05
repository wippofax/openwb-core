# Nissan module source map

This map describes the current files in this module. All paths in the tree
are relative to the Core repository root. It covers production code, offline
tests, the manual diagnostic tool and documentation; it is not a proposed
folder layout or a deployment inventory.

## Directory and file responsibilities

```text
packages/modules/vehicles/nissanconnect/
├── __init__.py                 # Python package marker
├── api.py                      # Authentication, transport, parsing and retry policy
├── config.py                   # Native openWB configuration and defaults
├── soc.py                      # openWB adapter: client measurements to CarState
├── connection_test.py          # Production stdin worker used by the PHP endpoint
├── probe.py                    # Optional manual query in a private local terminal
├── conftest.py                 # Automatic network denial for offline tests
├── api_test.py                 # API tests; also currently supplies shared test helpers
├── diagnostics_test.py         # Query diagnostics and connection-worker tests
├── odometer_test.py            # Optional odometer parsing and query tests
├── probe_test.py               # Private-terminal guard and direct-start tests
├── soc_test.py                 # Native adapter and configuration-change tests
├── README.md                   # Module introduction, setup and test commands
├── source-map.md               # This directory map and integration boundaries
├── NOTICE.md                   # Source attribution and license notices
├── COMPATIBILITY.md            # Pinned openWB 2.2.3 compatibility evidence
├── supported-vehicles.md       # Vehicle, account and regional support boundaries
├── user-information.md         # Short service-access and privacy notice
├── diagnostics.md              # Log fields and connection-test behavior
├── error-handling.md           # Failures, stale data and existing Core behavior
├── privacy.md                  # Reviewed data flows, storage and privacy limits
├── license-review.md           # License and service-terms review in English
├── license-review.de.md        # German translation of that review
├── contribution-review.md      # Upstream contribution review and integration notes
└── release-review.md           # Release checks, evidence and remaining limitations
```

## Integration boundaries

- `soc.py` must remain available as `modules.vehicles.nissanconnect.soc`:
  Core dynamically imports the vehicle type's `soc` module. It delegates
  scheduling and charge policy to existing Core interfaces.
- `config.py` follows the existing vehicle-module configuration convention.
- `connection_test.py` is a production stdin worker, despite its name. The
  companion settings PHP endpoint invokes this exact path:
  `packages/modules/vehicles/nissanconnect/connection_test.py`.
- `probe.py` is an optional manual tool for a private terminal. Automated
  tests exercise it with synthetic inputs; they do not need account data.
- `conftest.py` blocks network access for the offline tests. Shared synthetic
  transport/data helpers currently live in `api_test.py` and are reused by
  the diagnostics and odometer tests.

## Companion repository and reading guide

`openWB/openwb-ui-settings` owns the Vue form and both PHP endpoint sources,
including their UI/PHP tests. Its directory overview is
`docs/nissanconnect-source-map.md`. Core owns the Python API, adapter and worker.

Start with [README.md](README.md) for setup and test commands,
[user-information.md](user-information.md) for the short user notice and
[diagnostics.md](diagnostics.md) for the query/connection-test contract.
The tree labels identify the detailed compatibility, privacy and license reviews.

Keep this map and affected imports, test commands and companion worker paths
consistent when moving files. This documentation does not change module layout,
behavior or an installed wallbox.
