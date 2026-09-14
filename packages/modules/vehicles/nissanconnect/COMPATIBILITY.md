# Compatibility check: openWB 2.2.3

Checked on 2026-09-14 against public Core commit
[`3ced7f9cef3c70980ee1fab670f0d0717d1809ca`](https://github.com/openWB/core/commit/3ced7f9cef3c70980ee1fab670f0d0717d1809ca).
Its `web/version` file contains `2.2.3`. The exact commit, rather than a moving
branch or release label, defines this check.

## Result

The NissanConnect Python module passed the local compatibility checks without
implementation changes. This establishes compatibility with the exercised
Python interfaces, not a complete wallbox installation or charging-system test.
The target's bundled settings UI does not yet contain the NissanConnect page.
A coordinated, release-compatible UI build is needed before device testing.

## Validation scope

The exact public Core source was exported into an isolated directory and the
current NissanConnect module was added. Python tests ran under Python 3.9.2 on
Windows. No wallbox configuration, account credentials or captured vehicle
responses were used. Network connections were blocked in the tests.

| Check | Result |
| --- | --- |
| Existing module suite against target Core source | 60 passed |
| Additional target-interface checks | 11 passed |
| Settings component test | 1 passed |
| Local production settings UI build | Passed |
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

The checked module revision was `555fe6e`; the settings source revision was
`d0d5f23`. The UI build included `./nissanconnect/vehicle.vue` in the dynamic module
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

The current settings source builds successfully with the new page. This does
not establish that replacing the entire target UI with a newer development UI
is compatible with all other features of Core 2.2.3. Before installation,
prepare a settings build aligned with the target release and verify module
selection, credential masking and configuration delivery together. Raw JSON
configuration is not the planned credential-entry workflow.

## Remaining validation

- Linux/ARM execution and a complete openWB runtime with real MQTT storage.
- Sustained authentication and token renewal with a real account.
- A release-compatible settings UI combined with the target Core.
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
