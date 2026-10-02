# Error handling and Volkswagen comparison

Checked on 2026-09-14 using public source only. The target is Core 2.2.3 at
`3ced7f9cef3c70980ee1fab670f0d0717d1809ca`. The current public `master` was resolved through GitHub to
`09fd69358bf91965a112c71a9cd713a5b7dd616b`. No VW client, live account or wallbox was used.

## What Volkswagen does

The exact 2.2.3 target contains `vwid`. It raises errors for failed login,
missing vehicles and unsuccessful data retrieval. Its adapter uses the shared
`ConfigurableVehicle` wrapper. The optional `calculate_soc` setting (default
`False`) selects calculation while charging, bypassing API queries during that
period. It is not a special outage or automatic-stop setting.

- [Target VW adapter](https://github.com/openWB/core/blob/3ced7f9cef3c70980ee1fab670f0d0717d1809ca/packages/modules/vehicles/vwid/soc.py)
- [Target VW configuration](https://github.com/openWB/core/blob/3ced7f9cef3c70980ee1fab670f0d0717d1809ca/packages/modules/vehicles/vwid/config.py)
- [Target VW query errors](https://github.com/openWB/core/blob/3ced7f9cef3c70980ee1fab670f0d0717d1809ca/packages/modules/vehicles/vwid/libvwid.py)

The current `vweuda` module uses EUDataAct retrieval and the same optional
calculation setting. It additionally keeps vehicle results on disk and in
memory. If no result is found, its return path can use the stored result; with
no stored result it starts with zero values and an epoch timestamp. This is a
cache strategy, not proof that the returned SoC is current. No dedicated
charging interlock was found in either VW adapter.

- [Current VW adapter](https://github.com/openWB/core/blob/09fd69358bf91965a112c71a9cd713a5b7dd616b/packages/modules/vehicles/vweuda/soc.py)
- [Current VW result and cache handling](https://github.com/openWB/core/blob/09fd69358bf91965a112c71a9cd713a5b7dd616b/packages/modules/vehicles/vweuda/libeuda.py)

## Shared openWB behavior

Both inspected versions use the shared wrapper to calculate SoC after an API
failure when the vehicle is plugged in, a previous SoC is available from the
current connection, and charging-meter data permits calculation. Old API data
can also trigger calculation when additional energy has been metered. Successful
fallback produces a warning, rather than the error state used by the scheduler.
The calculation depends on configured battery capacity and charging efficiency.

If fallback fails, the error reaches the normal vehicle fault handling. When
the scheduler's consecutive-error counter reaches three, it publishes SoC zero
before the next update. This counts failed module updates, which may include
updates deferred by a client cooldown; it is not necessarily three HTTP calls.
The wrapper and scheduler files on current master matched the locally inspected
development sources. Their relevant behavior also exists in the exact target.

The SoC-limit branches in instant, PV and eco charging stop only when the
supplied SoC reaches the configured target. Zero does not represent an unknown
value there. Inference from these control paths: this error policy can permit
charging beyond the intended SoC target; with PV minimum-SoC charging configured,
zero can also request charging up to that minimum. Other charge limits and the
vehicle's own protection remain separate. This was source analysis, not a live
charging test.

- [Target fallback](https://github.com/openWB/core/blob/3ced7f9cef3c70980ee1fab670f0d0717d1809ca/packages/modules/common/configurable_vehicle.py)
- [Target error counter](https://github.com/openWB/core/blob/3ced7f9cef3c70980ee1fab670f0d0717d1809ca/packages/modules/update_soc.py)
- [Target charge limits](https://github.com/openWB/core/blob/3ced7f9cef3c70980ee1fab670f0d0717d1809ca/packages/control/ev/charge_template.py)
- [Current charge limits](https://github.com/openWB/core/blob/09fd69358bf91965a112c71a9cd713a5b7dd616b/packages/control/ev/charge_template.py)

## Nissan implementation and remaining decision

Nissan already participates in the same shared fallback, without requiring a
new setting. Its adapter keeps the original Nissan measurement timestamp and
does not turn missing or invalid data into a fabricated zero. Bounded retry
pauses now cover transport, authentication, service and response errors; see
the README. Paused updates preserve the error category and report the remaining
pause without sending another request. Success resets the backoff.

The retry changes do not alter charging control, scheduler error counting or
shared fallback. In particular, they cannot guarantee that the last SoC remains
published. The shared fallback also treats a previous SoC of zero as absent,
and uses truthiness for meter baselines; these are upstream limitations, not
fixed by the Nissan retry change.

The user subsequently clarified that development must remain within the new
module and its normal integration. Shared Core behavior must not be changed,
and the controller must not need Nissan-specific handling. The earlier charging
interlock proposal is therefore outside this scope. The standard zero policy
remains in effect when neither a query nor the existing fallback succeeds.

A compatible improvement is an optional `calculate_soc` setting connected to
the existing `calc_while_charging` parameter, with the same default (`False`) as
VW. While charging with this setting enabled, the wrapper calculates from
metered energy instead of calling the API. This avoids API failures during that
period, provided a useful starting SoC and the calculation inputs are available.
It does not guarantee a current starting value, validate the quality of the
configured capacity/efficiency, or prevent failures outside that period. VW,
HTTP and JSON already expose this option; PSA enables calculation while charging
unconditionally. No change to the common calculation is required.

- [Target HTTP module](https://github.com/openWB/core/blob/3ced7f9cef3c70980ee1fab670f0d0717d1809ca/packages/modules/vehicles/http/soc.py)
- [Target JSON module](https://github.com/openWB/core/blob/3ced7f9cef3c70980ee1fab670f0d0717d1809ca/packages/modules/vehicles/json/soc.py)
- [Target PSA module](https://github.com/openWB/core/blob/3ced7f9cef3c70980ee1fab670f0d0717d1809ca/packages/modules/vehicles/psa/soc.py)

Returning cached data after a transport error is not unprecedented, as the
current VW implementation shows. However, converting failed queries into
apparently successful updates merely to avoid the error counter changes how
the shared fault handling sees the outage. An unchanged value can become wrong
after driving; replacing its measurement timestamp with query time makes that
worse. A cache with an original timestamp and an explicit warning is different
from a fresh measurement, but still cannot resolve missing reliable data.
It is not proposed as a way to defeat the standard zero policy.

The calculation option is a recommendation, not yet implemented or enabled.
No new policy, error-counter manipulation, VW cache code or persistent account
data was added. Existing Nissan retry pauses protect the backend only; deferred
updates can still contribute to the standard error counter when fallback fails.

## Diagnostics

The module now logs a selected DEBUG summary of actual attempts, deferred calls,
last success, Nissan measurement times, battery values and retry delays. The
settings connection test returns a separate passive result without publishing
it into charging control. Neither changes the shared fallback or zero policy.
See [query diagnostics and the test endpoint](diagnostics.md) for confidentiality,
separate cooldowns and exact timestamp meanings.

## Verification limits

Synthetic module tests cover timeouts, malformed or invalid responses, HTTP
429/503, both Retry-After forms, repeated outages, recovery and absence of new
requests during a pause. The exact-target contract checks separately cover the
real wrapper's fallback and the scheduler's zero policy using in-memory stores
and publication. They do not run a full charging system. Sustained private
authentication, Linux/ARM execution and separately approved device tests remain
necessary. The deferred source/API license and terms review is still open.

## Optional odometer and explicit refresh commands

A cockpit GET follows battery success in module/connection-test/probe calls.
Invalid or missing totalMileage yields no odometer. A cockpit HTTP/transport
failure retains the valid SoC and pauses only cockpit attempts for five minutes.
Rate limiting and explicit provider Retry-After advice retain the client-wide
pause, even when the current battery result succeeded. No old odometer is
retained as a fresh reading. The normal Core timestamp/charging policy is unchanged.

In the pinned 2.2.3 VW ID implementation, the executed path is
`VwGroup.request_data -> libvwid.get_status -> Connection.update -> Vehicle.update`
and selective-status GET requests. The library also defines `set_refresh` and
`wakeUpVehicle`, the latter posting to `vehiclewakeuptrigger`, but that normal
SoC path does not call them. A repository-wide search at that revision found
no caller of set_refresh; wakeUpVehicle is referenced only inside that method.
Its success branch also calls wait_for_data_refresh, whose definition is absent
from the checked tree, so the unused helper is not proven ready to enable.
Token refresh renews authentication, not vehicle data. The shared manual-refresh flag schedules the same updater; the VW adapter
does not distinguish it as a wake command. This source finding makes no claim
about current VW service availability. The newer development checkout instead
contains `vweuda`, which polls data-portal datasets and likewise exposes no
vehicle wake action in its module adapter.

The Nissan module also has no wake command, including from the Color-theme
refresh button. Passive retrieval must not be described as forcing the car to
send a new measurement. The theme's pending indicator issue is documented in
[diagnostics](diagnostics.md); it is separate from wake support.
