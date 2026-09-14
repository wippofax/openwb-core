# Compatibility check: openWB 2.2.3

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
| Existing module suite against target Core source | 60 passed |
| Additional target-interface checks | 11 passed |
| Settings component and integration tests | 3 passed on development and pinned target source |
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

Three synthetic tests use the real text input, asynchronous vehicle proxy, Vuex
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

## Remaining validation

- Linux/ARM execution and a complete openWB runtime with real MQTT storage.
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
