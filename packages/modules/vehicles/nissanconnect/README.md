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
- **A tester has reported successful private account and wallbox tests:**
  installation, an unsaved settings connection test and a normal module query
  returned data matching the official app. Overnight logs and GUI changes were
  also reported. These are qualitative reports, not independently inspected
  private data. Exact automatic cadence, sustained token renewal, other account
  configurations, charging with the module's SoC and saved-settings removal
  remain open acceptance items.
- Only cached server data is read. No wakeup, `refresh-battery-status` or vehicle
  charging start/stop commands are sent. If Nissan's data is old, the reported
  SoC may also be old. The original timestamp is preserved so openWB can use
  its existing calculation.
- Status shows the stored SoC measurement time, not the last HTTP request time.
  A new request can return the same measurement without changing that display.
  An API success also does not guarantee that Core accepts the value: the
  pinned 2.2.3 wrapper rejects measurements more than 60 seconds older than the
  stored SoC, which can matter after switching from a recent manual value.
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

See [privacy and diagnostic data](privacy.md) for the reviewed configuration,
MQTT, logging, backup and removal paths, including an unresolved inherited
Core log-redaction limitation. Saved credentials are normal openWB
configuration; same-origin testing does not encrypt an HTTP connection.

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

## Query diagnostics and connection test

Regular module updates now log a selected DEBUG summary: actual HTTP attempt
times, success/failure/deferment, Nissan measurement time, data age, SoC, optional
range and retry delay. Credentials, VINs, tokens, URLs and raw responses are
excluded. Real battery values and times remain confidential.

The matching settings page includes **Test connection**. It displays a passive
query's battery values and separate query/measurement times using the current
form values, without saving settings or updating charging control. It requires
the module-owned PHP endpoint as well as the Python module and matching UI build.
See [diagnostics and connection-test behavior](diagnostics.md) for log fields,
the private cooldown metadata, access assumptions and testing limits.

## Offline validation

Use synthetic fixtures only. Optional PHP helper tests need `php` on PATH or
`NISSAN_TEST_PHP` pointing to a PHP CLI executable; otherwise those tests are
explicitly skipped. Their subprocesses use fixed synthetic programs only.
The state metadata predicates can be tested with PHP on Windows. Actual
ownership/mode checks and the hardened endpoint's loopback contract require
Linux; they are explicitly skipped on other platforms. The endpoint fails
closed outside Linux rather than treating Windows stat fields as ACL evidence.
The Python unit tests block socket connections, name resolution
and real vehicle queries through the replaced transport. The adapter test
replaces the service wrapper and verifies the values passed to the real
`CarState`; it does not test a running charging system.

The optional HTTP integration test runs in a child process with two temporary
PHP servers bound only to loopback. It copies the actual endpoint and helper,
substitutes the local Python interpreter path and installs a fixed synthetic
worker at the expected location. Redirects and proxies are disabled; no Nissan
client is imported. Private fixture directories contain only invented data and
are separate from live module state. The test stops its own servers when done.

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

See [NOTICE.md](NOTICE.md) for attribution and the dated adaptation notice,
[license and service-terms review](license-review.md) for the verified source
licenses and open service-access/distribution questions, and
[contribution/source review](contribution-review.md) for the repository split
and prepared reviewer summary. Software license compatibility does not establish
permission to use the unofficial API client.
