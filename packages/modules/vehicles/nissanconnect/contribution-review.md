# Contribution and source review

Offline inventory dated 2026-10-02. This prepares review; it is not a license
compatibility opinion, permission to use an API or authorization to publish.
Current legal/service terms and dependency advisories remain separate work.

## Contribution split

| Repository | Proposed content | Scope retained |
| --- | --- | --- |
| `openWB/core` | `packages/modules/vehicles/nissanconnect/` and the two module-owned PHP files in `web/settings/modules/vehicles/nissanconnect/` | Native configuration factory, `DeviceDescriptor`, `ConfigurableVehicle` and `CarState`; no shared scheduler/controller, MQTT, log-filter or recovery changes |
| `openWB/openwb-ui-settings` | Nissan Vue component and synthetic tests; the existing minimal console-payload removals need explicit explanation in review | Existing module selection, configuration store/save path and form components; no new UI dependency |
| Local project records | Candidate manifest, installation/recovery tools, acceptance and Bulletproof findings | Outside these product contributions unless maintainers explicitly request them |

Use the upstream branches and submission instructions current at contribution
time. The recorded targets are Core `master` and settings `main`; the 2.2.3
compatibility build is a separate pinned test artifact. Cross-reference the
two changes so maintainers can review endpoint and UI together. Do not commit
the locally compiled settings assets in the Core source contribution. Check
upstream expectations for the two PHP files before submitting; they must survive
the chosen UI build/deployment process.

The existing pinned preparation script also removes payload values from three
debug statements in `App.vue`, `ComponentState.vue` and
`VehicleConfiguration.vue`. Those narrowly scoped existing UI edits protect
editing/saving account details. They do not modify the Python Core or resolve
its inherited MQTT log-redaction finding. Do not silently enlarge them.

## Local provenance inventory

| Source/component | Evidence available offline | Use and open check |
| --- | --- | --- |
| openWB Core | Repository `LICENSE` contains GPL version 3 text; target `3ced7f9cef3c70980ee1fab670f0d0717d1809ca` | Integration APIs and neighboring-module conventions. Confirm final licensing notices and contribution requirements before publication. |
| openWB settings | Repository `LICENSE` contains GPL version 3 text; development overlay `776a60d762b59be12b147ca4e37cb715fcfb0c82` | Vue component, inherited UI and build chain. A LICENSE file alone does not resolve every bundled asset's terms. |
| Pinned 2.2.3 settings | `e8de268fa25f7efca2b5ffc005a757a2f36b530f`, recorded maintainer fork `Brett-S-OWB/openwb-ui-settings_BS_folk`; preparation script and compatibility guide | Build basis for the candidate. Use this lockfile for candidate review, not the newer development dependency versions. |
| HomeAssistant-NissanConnect | `NOTICE.md` records `dan-r/HomeAssistant-NissanConnect` revision `b0bafe9108d4574e243aa182324584dbc68369ad` and an MIT notice for Daniel Raper (2024) | Adapted EU/OneID protocol/login flow in `api.py`. Recheck upstream revision, actual reused portions, notice accuracy and modification obligations against the original source before closure. |
| `Tobiaswk/dartnissanconnect`, mitchellrj work | Original research reference; the recorded primary reference credits these authors | No Dart package is imported/bundled by this module. Do not infer absence of indirect derivation: confirm attribution chain and applicable source licenses during the online provenance review. |
| Python/PHP/runtime libraries | Python standard library imports in the API/worker/probe; existing openWB helper imports in the adapter; PHP built-ins | No new Python package, requirements-file change or mandatory PHP extension. Runtime/OpenSSL/distribution updates and licenses remain inherited platform responsibilities. |
| Vue/build dependencies | Existing UI `package.json` and `package-lock.json` at both revisions above | The Nissan component adds no dependency. Transitive licenses/notices and final build artifacts still require review. |

`NOTICE.md` is retained unchanged. The inventory does not relabel third-party
code, remove attribution or claim that public source permits unofficial service
access. No source package was downloaded in this pass.

## Dependency metadata gaps

The pinned target lockfile contains **699 package entries**; the development
lockfile contains **662**. Counts include development, optional and platform
packages, not only code shipped to a browser. Labels include MIT/MIT-0, ISC,
Apache-2.0, BSD variants, BlueOak-1.0.0, CC0/CC-BY and composite expressions.
This enumeration is metadata, not an artifact-level license audit or an SBOM.

Four target entries have no `license` field: `console-browserify` 1.2.0,
`querystring-es3` 0.2.1, `timers-browserify` 1.4.2 and `urlsafe-base64` 1.0.0.
The development lock additionally lacks the field for `vue-color` 3.3.3.
Existing local package metadata/license files supply MIT notices for the first
three and `vue-color`. Their local contents have not been reauthenticated
against registry tarball integrity in this pass. No license declaration/file
was found in the inspected local `urlsafe-base64` package or its README.

**BP-LIC-01 (open):** resolve `urlsafe-base64` provenance/license and verify the
notices actually required by the final distributed bundle. Missing metadata
does not establish either prohibition or permission. Do not update or replace
shared dependencies merely to make this inventory appear complete. Current
advisory checks and relevant authoritative license texts require the later
online pass. Inherited dependency changes between the two UI bases are not
changes introduced by the Nissan component.

## Coding conventions and interface review

The explicit Core checks are `.flake8` (120 columns, `__init__.py` F401
exemption) and the repository Python CI (Python 3.9, Flake8, pytest). The UI
uses its checked-in ESLint/Prettier rules and Vitest. No extra product
`AGENTS.md` or `CONTRIBUTING*` was found in the prior inspected trees.

The neighboring HTTP and Volkswagen adapters use a `create_vehicle` factory,
a nested updater, `CarState`, `ConfigurableVehicle` and `DeviceDescriptor`.
Volkswagen configuration uses ordinary classes with a configuration object;
the Nissan module follows that shape. This is an inferred convention, not a
new formal coding rule. Keep the deliberate private `urllib` transport:
the usual request hook can log authentication response data. Native error
and charging fallback policies remain unchanged; see [error handling](error-handling.md).

English interface documentation now states units, measurement/request-time
semantics, serialized client use, configuration lifetime, credential storage,
token renewal/backoff, worker/cooldown ownership and the proxy/trust boundary.
Small internal helpers are explained where their safety behavior needs context;
comments that merely restate assignments are unnecessary.

## Prepared reviewer summary

The existing Leaf module uses an incompatible service. This experimental EU
MyNISSAN module reads cached Nissan battery status for the ZE1 and supplies SoC,
optional range and the original measurement timestamp through the existing
vehicle wrapper. Its settings page offers an unsaved passive connection test
with separate query and measurement times. It sends no wake or charge commands.

The Python suite passes **102 tests** after correcting malformed destination
and numeric-overflow error paths. The new cases also verify refresh-token
rotation and no password-login retry on a refresh service outage. **52 PHP/
platform tests remain skipped** pending the separately planned runtime setup;
earlier PHP passes do not validate the new private-state hardening. The unchanged
UI has prior 16-test/ESLint and pinned-build evidence. These are affected-area
checks, not complete openWB regression or release validation.

A tester reports matching data in private account, unsaved settings and normal
module queries, with overnight log/GUI activity. Precise automatic cadence,
sustained token renewal, charging acceptance and saved-settings removal remain
open. No captured responses, screenshots or credentials belong in a contribution.

Before submission, close or explicitly disposition the PHP hardening, inherited
logging issue, source/dependency licenses, service terms/privacy review and
device acceptance; then refresh this summary for the actual final revisions.
No fork, hosted request, push or upstream communication was performed by this
offline review.
