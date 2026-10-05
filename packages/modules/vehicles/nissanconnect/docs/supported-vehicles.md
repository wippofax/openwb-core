# Vehicle and regional scope

Reviewed on 2026-10-04. This is an unofficial European MyNISSAN integration,
not a promise of support for every Nissan model or region.

## Evidence and naming

Nissan [describes MyNISSAN](https://www.nissan.de/kunden/mynissan-app.html)
as the successor branding for NissanConnect Services and You+Nissan, with a
shared app/portal login. The desktop portal does not provide the app's remote
vehicle functions. A shared account or app does not prove that every model uses
the same battery endpoint, response schema, units or service entitlement.

The [European Android listing maintained by Nissan Automotive Europe](https://play.google.com/store/apps/details?id=eu.nissan.nissanconnect.services&hl=de)
lists these electric vehicles by production date, among other vehicles:

| Vehicle | Official app listing | Evidence for this openWB module |
| --- | --- | --- |
| LEAF | From May 2019 | Positive private Leaf ZE1 account, wallbox and everyday-use reports; not every year/variant tested |
| ARIYA | From July 2022 | Unverified |
| Townstar EV | Townstar/Townstar EV grouped from September/October 2022 | Unverified |
| MICRA electric | From September 2025 | Unverified |
| Interstar EV | Interstar/Interstar EV grouped from April/May 2026 | Unverified |

The listing qualifies availability by equipment and country. Its dates describe
app compatibility, not this module's test coverage. Do not extend the Leaf report
to every ZE1 produced from 2017, to a later Leaf generation, or to older
NissanConnect EV/CarWings vehicles. Those are not established by this evidence.
The same app name in another region is not evidence for the European backend.
Other manufacturers and non-plug-in e-POWER models are outside this module's
intended openWB traction-battery SoC use.

## Technical compatibility boundary

The client uses the European OneID/Kamereon endpoints. It selects an account's
vehicle by VIN and contains no Leaf model-code filter or fixed battery capacity.
It requires `batteryLevel` and a valid timezone-aware `lastUpdateTime` from
`v1/cars/<vin>/battery-status`. Optional range uses `rangeHvacOn`/`rangeHvacOff`;
optional odometer uses `totalMileage` from the separate `cockpit` endpoint in km.
A different required response schema fails rather than manufacturing a SoC.
Missing odometer data does not discard a valid battery measurement.

It is therefore plausible that additional European Nissan EVs work unchanged,
but that is an inference from the client structure, not verified compatibility.
App membership alone cannot establish endpoint support, freshness or units.
There are no vehicle wakeup or charging commands.

## Public-facing name and further reports

Use **Nissan – MyNISSAN EU (experimental)** with the separate visible statement:
**Tested with the Leaf ZE1; other models are unverified.** The internal module
type remains `nissanconnect`, so the name change needs no configuration migration.

For another model, a voluntary qualitative report should distinguish successful
login/vehicle selection, plausible SoC, measurement freshness, automatic queries
and optional odometer units. Do not request credentials, VINs, raw API responses,
private logs or screenshots. Do not mark an entire model range verified from one
successful login. Service-access/legal review is separate from compatibility;
see [license and service terms](license-review.md).
