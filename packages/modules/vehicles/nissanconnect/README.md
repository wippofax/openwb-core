# Nissan Leaf ZE1 / MyNISSAN EU (experimental)

This module reads battery data stored by Nissan through MyNISSAN OneID and
Kamereon. It provides openWB with the SoC, range (if available) and actual
measurement timestamp. The existing openWB control system handles display,
query intervals, errors and charge limits.

## Requirements and limitations

- A European MyNISSAN account with a working login and an associated Leaf ZE1.
  The app and service used by the vehicle matter, not just its model year.
- NissanConnect EV and the existing `leaf` module use a different API.
  This module does not modify the existing Leaf module.
- This is an unofficial interface derived from public implementations. Nissan
  may change the login flow or data formats. Additional login steps, consent
  and MFA are not automated; complete them in the official app if required.
- **One successful manual account query has been reported by a tester:** the
  returned data matched the official Nissan app. Only the qualitative result
  was shared; it was not independently verified. Sustained token renewal,
  other account configurations and wallbox integration remain untested live.
- Only cached server data is read. No wakeup, `refresh-battery-status` or vehicle
  charging start/stop commands are sent. If Nissan's data is old, the reported
  SoC may also be old. The original timestamp is preserved so openWB can use
  its existing calculation.
- A missing or invalid SoC, or a measurement timestamp that is missing, has no
  time zone or is more than five minutes in the future, produces an error.
  A missing optional range does not invalidate an otherwise valid SoC.

See [the exact-version compatibility report](COMPATIBILITY.md) for the local
openWB 2.2.3 checks, UI requirements and existing error-handling behavior. The UI
repository now includes `docs/nissanconnect-2.2.3.md` and
`scripts/prepare-nissanconnect-2.2.3.py` for the locally verified target build.

## Configuration

The module type is `nissanconnect`. The corresponding settings page is in the
`openWB/openwb-ui-settings` repository at
`src/components/vehicles/nissanconnect/vehicle.vue`.

| Field | Meaning |
| --- | --- |
| `user_id` | MyNISSAN account email address |
| `password` | MyNISSAN account password |
| `vin` | Optional VIN; required if the account contains multiple vehicles |

The region is fixed to Europe. A single vehicle is selected automatically.
Ambiguous selection or an unknown VIN produces an error.

## Data flow and secrets

When run, the module communicates directly with the configured Nissan and
Kamereon HTTPS endpoints. No model provider is involved in client operation.
This code produces no telemetry and does not store API responses, cookies or
tokens on disk. Tokens are reused within the client object; restarting or
changing the configuration triggers a new login.

General openWB settings and backups may contain configured credentials.
Masking the password in the browser does not protect that storage. Such
configurations, backups, VINs and real API responses must not be included in
Git, issues, chat messages or model tool outputs. `.gitignore` alone does not
prevent transfer to a cloud model.

The transport therefore uses the Python standard library with certificate
verification, a response size limit and explicit redirect handling. It avoids
the usual `modules.common.req.get_http_session()` hook because that hook logs
complete responses. The standard library also avoids urllib3 debug URLs that
contain VINs or authorization codes. Exceptions contain only fixed messages
without personal data; original responses and underlying transport exceptions
are not displayed.

Each request uses a socket timeout of at most ten seconds. No further requests
are started after a 60-second budget. This is not a hard overall deadline for
a socket read already in progress. Redirects and retries after rejected
authentication are bounded. Failed queries trigger pauses of 5, 10, 20, 40 and
then at most 60 minutes. A successful query resets this sequence. HTTP 429 and
503 also honor `Retry-After` in seconds or HTTP-date form, bounded to 5 minutes
through 24 hours. A deferred update makes no HTTP request and does not extend
the pause. openWB's configured intervals can delay the next actual attempt
further. There are no unbounded retry loops or sleeps.

Authorization failures clear the rejected tokens. Network or service errors
keep the current authentication state for reuse or normal renewal. Pauses keep
only a bounded error message and its category, not an exception traceback;
all retry state is in memory and resets with the client.

See [error behavior and the Volkswagen comparison](error-handling.md) for the
shared energy fallback and the unresolved charging policy when it is unavailable.
These request pauses do not pause charging or override openWB's error counter.

## Offline validation

Use synthetic fixtures only. The tests block socket connections, name resolution
and real vehicle queries through the replaced transport. The adapter test
replaces the service wrapper and verifies the values passed to the real
`CarState`; it does not test a running charging system.

From the Core repository root, using a Python 3.9 test environment:

```sh
PYTHONPATH=packages python -m pytest -q packages/modules/vehicles/nissanconnect \
  --confcutdir=packages/modules/vehicles/nissanconnect
python -m flake8 packages/modules/vehicles/nissanconnect
```

For the UI in its separate repository:

```sh
npm ci --ignore-scripts
npx eslint src/components/vehicles/nissanconnect
npx vitest run src/components/vehicles/nissanconnect/vehicle.spec.js
npm run build
```

The normal build generates local UI files. The `build-dev` and `build-prod`
scripts write to an openWB installation path and are outside the scope of this
offline test procedure.

## Later testing on your own wallbox

1. First prepare an isolated test on a separate computer. Enter credentials
   locally using hidden input, run outside a cloud agent and compare results
   with the app locally. Do not transfer real values into the agent context.
   One successful initial query has been reported; see the limitations above.
2. Before installation, prepare a concrete plan covering the software version,
   backup, affected files, test window and recovery.
3. **Before every wallbox change, explicitly ask for permission with a warning
   about its effects and risks, and wait for explicit approval.** This also
   applies to backup files on the device, file transfers, restarts,
   configuration changes, and MQTT SoC or control values sent from another
   computer.
4. After an approved installation, first compare SoC and measurement timestamps,
   then observe the existing charging control with separately approved settings.
   A rollback is also a device change and must be covered by the approved plan.

For step 1, the module includes `probe.py`, which must be started manually in
a private local terminal outside Codex or cloud agents:

```sh
python packages/modules/vehicles/nissanconnect/probe.py
```

The probe asks for confirmation before the query, reads email, password and
optional VIN using hidden input, and displays SoC and measurement time only in
the terminal. It rejects pipes, output redirection and some detectable agent
environments. This is not a complete technical data loss prevention boundary:
terminal recording, screen sharing, other agents and operating system monitoring
cannot be ruled out. Never start a live test through model tools. The offline
tests of `probe.py` use a replaced client.

The module contains no installation, SSH, MQTT or restart scripts.

## Contributing

Prepare Core changes as a contribution against `openWB/core:master` and the
settings page as a separate contribution against `openWB/openwb-ui-settings:main`.
Cross-reference both contributions, state the testing limitations and API
reference, and do not include built UI files in the Core PR. Publication and
remote merges require separate authorization.

References:

- [openWB: developing a new module](https://github.com/openWB/core/blob/master/docs/Neues%20Modul%20programmieren.md)
- [openWB: creating a settings page](https://github.com/openWB/core/blob/master/docs/Einstellungs-Seite%20erstellen.md)
- [NissanConnect reference at the recorded revision](https://github.com/dan-r/HomeAssistant-NissanConnect/tree/b0bafe9108d4574e243aa182324584dbc68369ad)
- [OneID migration](https://github.com/dan-r/HomeAssistant-NissanConnect/pull/119)

See `NOTICE.md` for license information for the reference implementation.
