# Nissan module source map

This map describes the implemented source layout. Paths in the tree are relative
to the Core repository root. Production code, synthetic tests, manual tools and
documentation have separate directories; native integration entry points remain
at the module root. This is not a deployment inventory.

## Directory and file responsibilities

```text
packages/modules/vehicles/nissanconnect/
├── __init__.py                 # Native Python package marker
├── config.py                   # openWB configuration and defaults
├── soc.py                      # openWB adapter: client measurements to CarState
├── connection_test.py          # Production stdin worker used by the PHP endpoint
├── README.md                   # Introduction, configuration and test commands
├── NOTICE.md                   # Source attribution and license notices
├── src/
│   ├── __init__.py             # Internal implementation package
│   └── api.py                  # Authentication, parsing, transport and retry policy
├── tests/
│   ├── __init__.py             # Offline-test package
│   ├── conftest.py             # Automatic network denial
│   ├── helpers.py              # Shared synthetic responses, transport and clocks
│   ├── api_test.py             # Authentication, validation and retry tests
│   ├── diagnostics_test.py     # Query diagnostics and stdin-worker contracts
│   ├── odometer_test.py        # Optional odometer parsing and query tests
│   ├── probe_test.py           # Terminal guards and both isolated script entry points
│   └── soc_test.py             # Native adapter and configuration-change tests
├── tools/
│   ├── __init__.py             # Optional manual-tool package
│   └── probe.py                # Query in a private local terminal
└── docs/
    ├── source-map.md           # This map and integration boundaries
    ├── compatibility.md        # Dated openWB 2.2.3 compatibility evidence
    ├── supported-vehicles.md   # Vehicle, account and regional coverage
    ├── user-information.md     # Short service-access and privacy notice
    ├── diagnostics.md          # Log fields and connection-test behavior
    ├── error-handling.md       # Failures, stale data and existing Core behavior
    ├── privacy.md              # Data flows, storage and privacy limits
    ├── license-review.md       # English license and service-terms review
    ├── license-review.de.md    # German review translation
    ├── contribution-review.md  # Dated source/contribution review
    └── release-review.md       # Dated release checks and limitations
```

## Integration boundaries

- `soc.py` remains `modules.vehicles.nissanconnect.soc`, the vehicle type's
  dynamic Core entry point. Scheduling and charge policy remain Core-owned.
- `config.py` retains the existing configuration import convention.
- `connection_test.py` is a production stdin worker despite its filename. The
  settings PHP endpoint calls this exact module-root path with isolated Python.
  It loads the internal `src.api` implementation without importing Core services.
- `tools/probe.py` supports both a package import and direct isolated execution.
  Its synthetic startup test cannot create a real API client.
- Tests import shared fixtures from `tests/helpers.py`, never another test file.
  `tests/conftest.py` denies network access within this test package.
- Timeout, size and dimensional constants live beside their implementation;
  names distinguish seconds, Unix seconds, milliseconds, bytes and characters.

## Companion repository and reading guide

`openWB/openwb-ui-settings` owns the Vue form and both PHP endpoint sources,
including their UI/PHP tests. Its overview is `docs/nissanconnect-source-map.md`.
Core owns the Python client, native adapter and production stdin worker.

Start with [README.md](../README.md) for setup and executable test commands,
[user-information.md](user-information.md) for the short user notice, and
[diagnostics.md](diagnostics.md) for the query/connection-test contract.
Detailed reviews retain their dates and historical scope; moving them does not
turn earlier test evidence into current validation or a release approval.

Keep this map, imports, test commands and companion paths synchronized with
source moves. Source layout changes do not update an installed wallbox.
