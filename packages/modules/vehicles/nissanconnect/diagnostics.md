# Query diagnostics and settings connection test

## Regular SoC queries

The Nissan adapter emits one DEBUG record per updater invocation using the
existing openWB logger. The normal SoC logging context routes these records to
`soc.log`; the existing SoC log level must permit DEBUG. No separate log file or
global logging configuration is introduced. The standalone private probe and
settings worker do not emit these records.

The JSON summary deliberately includes only these diagnostic fields:

| Fields | Meaning |
| --- | --- |
| `outcome`, `phase` | Success, failure or deferred call; authentication, vehicle selection, battery or idle phase |
| `request_started_at` | Start of the first actual HTTP transport attempt in this invocation; null if deferred |
| `completed_at`, `duration_seconds` | Invocation completion time and monotonic elapsed duration |
| `http_requests`, `last_http_status` | Attempt count and most recent response status, when available |
| `last_contact_at` | Most recent HTTP transport attempt, including failed attempts; preserved during backoff |
| `last_success_at` | Most recent successful battery query, preserved after failure |
| `measurement_at`, `data_age_seconds` | Nissan's original measurement time and its age at completion, for a successful result |
| `last_measurement_at` | Original measurement time from the most recent successful battery query |
| `soc`, `range_km` | Battery percentage and optional range accepted by the client parser; null when the client has no valid result |
| `retry_after_seconds` | Remaining client pause; zero when no pause applies |
| `provider_retry_after_seconds` | Separate remaining provider advice; excludes the scheduled client's local error pause |
| `source` | `nissan_cached_api`, identifying passive server data |

Times are ISO 8601 UTC. A deferred call has zero HTTP requests, no new request
start and unchanged last-contact/last-success times. Recent retrieval does not
make an old measurement fresh. A small negative age can expose clock skew;
measurements more than five minutes ahead are already rejected by the parser.
Authentication is reused within the normal module client, so an update need not
repeat every login request.

These logs describe Nissan retrieval, not the SoC subsequently calculated by the
shared openWB wrapper. They do not change scheduler timestamps, fallback, error
counters or charging policy. See [error handling](error-handling.md).

In the pinned 2.2.3 Core, the Status card displays `soc_timestamp`, which this
module sets to Nissan's measurement time. It is independent of percentage
changes. Core's `soc_request_timestamp` records an updater attempt before it
runs; it does not itself prove that an HTTP request was sent. Use
`request_started_at` and `measurement_at` to distinguish the two times.

The module emits `outcome=success` before the shared wrapper decides whether
to store the returned value. That wrapper rejects a measurement more than
60 seconds older than the previously stored one and logs
`Not updating SoC, because timestamp is older.` at DEBUG. A recent manual
entry can therefore remain displayed after a successful cached Nissan query.
The module deliberately preserves the real measurement time.

Saving a different module does not force an immediate first query or reset the
vehicle's existing request timestamp. Normal scheduling applies the currently
saved interval to that timestamp; reducing the interval does not retain a
separate timer for the old interval. A normal manual refresh bypasses the
scheduler interval, while client retry delays and the timestamp guard still
apply. These mechanisms do not prove the cause of any particular past trial.

Username, password, VIN, tokens, cookies, URLs, raw bodies and transport exception
messages are excluded. Battery values and times can still reveal vehicle usage:
keep real logs private, and do not copy them into Git, issue reports or cloud
agent sessions without a separately considered disclosure decision.

## Test from the settings page

The Nissan page's **Test connection** button uses the currently entered username,
password and optional VIN, including unsaved edits. It starts one passive battery
query, including the login and selection requests it requires. The result shows
SoC, optional range, query start, completion, original measurement time and data
age. Times use the browser's local time zone. Age continues to increase while the
result is visible. The result is cleared when the input changes or the component
is closed. An in-flight request finishes so its original account's cooldown can
be retained; its displayed result is discarded after an input change.

The test does not save configuration, publish MQTT values, update charging
control, wake the vehicle or issue vehicle commands. The ordinary Save operation
retains its normal behavior. A success proves retrieval of valid stored battery
data, not that the vehicle is awake or that the data was measured just now.

The UI posts JSON to the module-owned endpoint
`web/settings/modules/vehicles/nissanconnect/test_connection.php`. Its helper
`connection_test_lib.php` requires PHP 7.4 or newer with `proc_open`; deployment
expects Linux and `/usr/bin/python3` with Python 3.9 or newer. The worker is
`packages/modules/vehicles/nissanconnect/connection_test.py`. All three backend
files must accompany the Python module and matching settings build. A UI-only
installation cannot run the test. No shared Core handler is modified.

The endpoint requires same-origin JSON POST requests and inherits the settings
web server's access policy. Origin validation is not authentication. It expects
the web server to report the actual scheme and host; reverse-proxy setups must
preserve that relationship. The browser-to-wallbox connection uses the existing
settings transport. The worker-to-Nissan connection verifies HTTPS certificates.

Credentials travel in the POST body and then through worker stdin, never in
process arguments, shell interpolation, module files or module logs. Responses
use `no-store`; worker stderr is discarded, and failures expose fixed error codes
and bounded messages. The worker refuses recognizable cloud-agent environments,
but that precaution cannot detect screen sharing, browser recording or every
agent. Run live tests privately, outside agents, and keep the results private.

At most one settings test runs at a time. A complete successful battery result
starts a five-minute pause for that account, measured from completion; zero SoC
counts as success. A different account can be tested immediately. Returning to
the first account retains its pause, including after password or VIN changes.
An authentication failure, incomplete battery result or other ordinary failure
allows an immediate retry. A busy response creates no cooldown.

Provider restrictions are independent. HTTP 429 without usable Retry-After
defaults to five minutes; valid Retry-After advice on HTTP 429/503 is bounded to
24 hours. HTTP 503 without usable advice adds no manual-test pause. Since these
responses do not establish an account-only scope, the endpoint conservatively
holds provider advice across accounts. Changing accounts cannot bypass it.
The scheduled SoC client's existing error backoff is unchanged and independent.

The private temporary directory `openwb-nissanconnect-test` stores a bounded
state file with expiry times, a random local HMAC key and keyed digests of
normalized account names. It contains no raw username, password, VIN or vehicle
response. The digests remain account-related: a party holding the state and
its key can check candidate account names against them, so keep this state
private too. Expired account entries are removed when state is next loaded. Failure
to persist state prevents a query. The browser retains account countdowns only
in component memory; after a reload or in another tab, the server remains
authoritative and reports any applicable delay when a test is requested.

The hardened endpoint validates the Linux process UID, a trusted temporary
parent, a real 0700 directory and a regular 0600 state file owned by that UID.
It rejects symlinks, multiply linked files and unsafe existing permissions.
Exclusive creation and descriptor/path identity checks happen before state is
read or written. Reopening does not truncate an unverified file; permissions
are never silently repaired and rejected paths are not removed. Competing
first-time creation can return unavailable safely; no Nissan query is started.
The boundary excludes a hostile root process or another process with the same
UID. A missing POSIX extension uses the bounded Linux `/proc/self/status` UID
record; there is no new package dependency. Windows ACLs are not inferred from
Unix-style stat values, and production endpoint use is limited to Linux.

The worker has a 60-second request-start budget and per-socket limits. The PHP
parent terminates a still-running worker after 70 seconds; the browser abandons
its request after 75 seconds. Closing the page does not guarantee cancellation
of an already running server query. Process termination on target Linux remains
part of the pending device validation.

## Offline evidence and remaining work

Before the 2026-10-02 private-state hardening, the exact Core target
`3ced7f9ce` passed 122 synthetic module/PHP tests under
Python 3.9.2 on Windows. The preceding 11 native-interface checks remain valid;
the adapter and shared interfaces were not changed in this extension. PHP helper
checks ran with PHP 7.4.33 and cover origin/input checks, subprocess limits,
stderr exclusion, cooldown persistence and concurrent lock exclusion.

The module suite now includes a complete loopback HTTP contract test with 25
checks. Two owned PHP servers share isolated temporary state. The endpoint and
helper are copied from the module; only the fixed Python interpreter path is
adapted for the host, and a synthetic worker replaces the real Nissan client.
Checks cover response codes/headers, rejection before worker startup, corrected
login, zero SoC, account and provider cooldowns, concurrent requests through two
servers, invalid worker output, private state and expired fixture state. This
tests actual HTTP/PHP/process boundaries without a Nissan or wallbox connection.

Sixteen UI tests passed on development and the pinned 2.2.3 source. Additional
cases cover network failure, invalid JSON, an incomplete success response and
the actual 75-second browser deadline using a controlled clock. A browser timeout
now reports an explicit timeout message and releases the test button. Exceptions
and raw response details are not shown. Flake8, ESLint and the pinned build passed.
The isolated browser preview offers selectable synthetic success/error scenarios,
including provider delay and a real 75-second wait; its reset clears only demo
state. No real account or wallbox was used.

The owner subsequently reported an Apache/PHP/Python runtime check, candidate
installation, an unsaved settings connection test, a regular module query and
unsaved-test removal on the wallbox. The displayed battery data matched the
official app. Overnight logs and GUI changes are also reported; precise
automatic cadence, charging with this SoC module, sustained token renewal and
saved-settings removal still need their own acceptance evidence.

The private-state hardening and its additional tests are local source changes
after the frozen pre-Bulletproof candidate. They have not been deployed or
validated by PHP yet. Installation of a local PHP test runtime is deferred at
the owner's request until an unmetered network is available. Linux ownership
and full endpoint tests must additionally run in a Linux environment; Windows
PHP covers syntax, pure metadata predicates and the other portable helpers.
Earlier endpoint/PHP passes do not validate the new hardening.

This is not a full Core regression or completed security/privacy review.
Any wallbox change still requires an explicit warning and the owner's express
approval. License/API terms and privacy checks remain open under the
Bulletproof plan; the project remains open.
