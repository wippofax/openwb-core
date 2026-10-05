# Compatibility check: openWB 2.2.3

## Current evidence update (2026-10-04)

The historical offline checks below are retained with their dates. A tester has
since reported successful installation of the reviewed SoC/odometer candidate,
a successful settings-page connection test, and good operation in everyday use
on a Leaf ZE1. Saved-settings removal of the previous candidate also succeeded,
with energy/yield histories retained. No private results were inspected.
Specific odometer accuracy, sustained token renewal and charging-limit scenarios
remain unverified. No other vehicle model is confirmed; see
[vehicle and regional scope](supported-vehicles.md).

The publication source now uses the model-neutral MyNISSAN EU display name and
an explicit Leaf-only test-coverage notice. This copy-only change is not a new
API implementation or a change to the already installed private test package.

## Historical offline evidence

Checked on 2026-09-14 against public Core commit
[`3ced7f9cef3c70980ee1fab670f0d0717d1809ca`](https://github.com/openWB/core/commit/3ced7f9cef3c70980ee1fab670f0d0717d1809ca).
Its `web/version` file contains `2.2.3`. The exact commit, rather than a moving
branch or release label, defines this check.

## Result

The NissanConnect Python module passed the local compatibility checks without
implementation changes. This establishes compatibility with the exercised
Python interfaces, not a complete wallbox installation or charging-system test.
The target's original settings UI has no NissanConnect page. A matching local
UI candidate has now been prepared from the public 2.2.3 source, with synthetic
selection, credential-entry and save-path checks. It has not been installed.

## Validation scope

The exact public Core source was exported into an isolated directory and the
current NissanConnect module was added. Python tests ran under Python 3.9.2 on
Windows. No wallbox configuration, account credentials or captured vehicle
responses were used. Network connections were blocked in the tests.

| Check | Result |
| --- | --- |
| Module suite including retry, diagnostics and PHP helper cases against target Core source | 122 passed |
| Additional target-interface checks | 11 passed |
| Settings component and integration tests | 16 passed on development and pinned target source |
| Local settings UI build | Passed, including the pinned 2.2.3 candidate |
| Built UI loader, component chunk and configuration fields | Verified |

The additional checks exercised the real target `ConfigurableVehicle`,
`CarState`, fault handling, energy-based fallback and configuration serializer.
MQTT publication and storage were replaced with in-memory objects; the Nissan
client was synthetic. Cases covered valid SoC values including zero and 100,
unchanged measurement timestamps, rejection of older samples, client reuse,
configuration changes, stale data while charging and API errors with or without
sufficient fallback data. Module discovery was restricted to NissanConnect to
avoid initializing unrelated clients. A separate check executed the target
scheduler's unmodified `_get_threads` method with synthetic dependencies and
without starting workers. The additional harness and results are local test
evidence; they are not part of the regular module suite.

The initial check used module revision `555fe6e` and settings revision
`d0d5f23`. That development UI build included `./nissanconnect/vehicle.vue` in the dynamic module
map, generated its component chunk, and retained the masked password input and
the `user_id`, `password` and `vin` configuration fields.

## Existing openWB behavior relevant to charging

The target preserves the original measurement time and can calculate a new SoC
from metered charging energy when cached API data is old or an API query fails,
provided sufficient prior data exists. This calculated result has its own
timestamp and a warning state.

The scheduler also has a separate error policy: when its SoC error counter
reaches three, it publishes a SoC of zero before scheduling the next query. This
was confirmed with synthetic inputs. Consequently, rejecting an invalid API
response in this module does not guarantee that the overall openWB system will
retain the previous SoC indefinitely. A future charging test must account for
this upstream behavior and its effect on configured charge limits. This check
did not change that policy.

Relevant target sources:

- [Vehicle wrapper and fallback](https://github.com/openWB/core/blob/3ced7f9cef3c70980ee1fab670f0d0717d1809ca/packages/modules/common/configurable_vehicle.py)
- [SoC scheduler error handling](https://github.com/openWB/core/blob/3ced7f9cef3c70980ee1fab670f0d0717d1809ca/packages/modules/update_soc.py)
- [Module discovery](https://github.com/openWB/core/blob/3ced7f9cef3c70980ee1fab670f0d0717d1809ca/packages/modules/configuration.py)

The retry/error extension was checked again against a fresh export of the same
target: 76 module tests and all 11 additional interface checks passed. See
[the Volkswagen comparison and error-policy boundary](error-handling.md).
Request backoff does not change the scheduler's zero-SoC policy or stop charging.

## Settings UI installation boundary

The target's compiled `VehicleConfiguration` module map has no NissanConnect
entry. Its existing fallback offers raw JSON editing and displays
`vehicle.configuration` as formatted JSON, which can expose configured
credentials without masking. Adding only the Python module would therefore not
provide the intended credential-entry page.

A local candidate now uses the maintainer's public 2.2.3 UI source
[`e8de268fa25f7efca2b5ffc005a757a2f36b530f`](https://github.com/Brett-S-OWB/openwb-ui-settings_BS_folk/commit/e8de268fa25f7efca2b5ffc005a757a2f36b530f),
its exact dependency lockfile and the released build mode (`development`). An
unmodified local rebuild matched all 354 released files after normalizing asset
hashes, embedded source-root paths and scope-bound JavaScript identifiers in
parsed syntax trees. The 402 Vue source paths also matched. This establishes a
structurally matching base, not byte-for-byte reproduction or a full runtime test.

The candidate adds only the Nissan component and its tests, plus removes values
from three existing debug calls along the edit/save path. All 21 existing vehicle
modules remain, with NissanConnect added; the candidate contains 355 build files.
The current development UI's unrelated changes are not included.

The original three synthetic tests use the real text input, asynchronous vehicle proxy, Vuex
store and existing application save method. They cover module selection from a
synthetic Core descriptor, required username/password, masked input, optional VIN,
unchanged defaults and the expected configuration publication. Publication is
captured in memory; the application root and MQTT client are not started. The
checked debug calls do not contain the account values. A separate visible preview
uses the target proxy with disabled synthetic fields and blocked connections.

The UI repository contains `scripts/prepare-nissanconnect-2.2.3.py` and
`docs/nissanconnect-2.2.3.md` for repeatable source preparation, hashes, build steps
and validation limits. Raw JSON configuration is not the planned credential-entry
workflow. The existing fallback for other missing modules and normal credential
storage in openWB settings/backups are unchanged. A complete UI/security audit is
outside this check.

## Query diagnostics and settings test extension

The current candidate additionally includes a module-owned PHP test endpoint,
stdin-only Python worker, DEBUG query diagnostics and the settings test button.
The exact-target module suite now passes 122 tests. The preceding 11 native
interface checks remain valid; the adapter and shared interfaces did not change.
PHP 7.4.33 helper tests cover origin/input checks, subprocess I/O limits, stderr
exclusion and account-scoped cooldown storage. Sixteen UI tests pass on both
sources, and the pinned build succeeds with the existing warnings.

The suite includes 25 loopback HTTP checks through two owned PHP servers and a
synthetic Python worker. They exercise real HTTP, process and file-lock boundaries;
the endpoint copy changes only the interpreter path for the Windows host. The
browser preview offers selectable synthetic failures, and the UI reports an
explicit timeout after 75 seconds without a response. Apache deployment and
target Linux/ARM execution remain unverified.
See [the detailed behavior and limits](diagnostics.md).

## Linux PHP verification (2026-10-02)

After the owner's Windows restart, WSL 3.0.1 and Debian 13 (WSL2) started
successfully. The current module endpoint/test source was exported from Core
`d3f1cd3b355fd7e6fa3e3170c56f0ba8145f4c9c`; the eight-file public archive has
SHA-256 `652647f79766da7569d31e1b749da6129e52845b6128086560436ad8555d097f`.
It contains only the license, empty module initializer, fixture, three test
files and two PHP files. No account, wallbox or private runtime data is included.

Environment: Linux `6.18.40.1-microsoft-standard-WSL2`, x86_64, Python 3.13.5,
pytest 8.3.5, PHP CLI 8.4.26 with `-n`. Tests ran as an ordinary user in a fresh
Linux tmpfs directory, not as root or on the mounted Windows filesystem.
The three suites `connection_test_endpoint_test.py`,
`connection_test_state_test.py` and `connection_test_http_test.py` passed
**57 tests**. The one expected skip checks unsupported non-Linux platforms.
All 12 cases skipped in the earlier Windows run now pass, including real
permission/link checks and the two-server synthetic HTTP contract. Both PHP
files also pass `php -n -l`. No source/test correction was necessary.

BP-SEC-01 is corrected and locally verified. Windows PHP 7.4.33 portable checks
and Linux PHP 8.4.26 filesystem/HTTP checks are complementary evidence, not an
exact target-runtime matrix. This run does not establish ARM, Apache module,
full openWB, charging or real Nissan behavior. The hardened code and odometer
extension remain undeployed; the frozen candidate and wallbox are unchanged.

## Remaining validation

- Target ARM/Apache execution and a complete openWB runtime with real MQTT storage.
- Sustained authentication and token renewal with a real account.
- The prepared settings UI together with the real target Core, MQTT and storage.
- Controlled charging tests covering stale data, API outages, error-counter
  behavior and configured SoC limits.
- An explicit installation, backup and recovery plan approved before any
  wallbox change. No installation, device change or remote publication was
  performed or authorized by this compatibility check.

The UI build reported existing large vendor chunks and an `eval` warning from
`vm-browserify`. A first Python run encountered Windows write permissions in
the local snapshot directory; the successful run used its owner context. The
additional discovery test initially needed a correction to its synthetic path
stub; the final eleven checks passed. These are local validation limits and
tooling observations, not evidence of a successful device deployment.
