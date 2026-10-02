# Contribution and source review

Inventory dated 2026-10-02, updated after the authorized public-source license
review. See [license-review.md](license-review.md) for the source-license result,
dated evidence and unresolved service-access/release-packaging questions.
Dependency advisories and final privacy review remain separate work.

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
| HomeAssistant-NissanConnect | `NOTICE.md` records `dan-r/HomeAssistant-NissanConnect` revision `b0bafe9108d4574e243aa182324584dbc68369ad` and an MIT notice for Daniel Raper (2024) | Adapted EU/OneID protocol/login flow in `api.py`. Pinned source and MIT text verified; provenance and modification notice retained in NOTICE.md. |
| `Tobiaswk/dartnissanconnect`, mitchellrj work | Original research reference; the recorded primary reference credits these authors | No Dart package is imported/bundled by this module. MIT Dart license and Apache-2.0 Python origin verified. The direct HA client explicitly states permission to relicense Apache portions; see the detailed review. |
| Python/PHP/runtime libraries | Python standard library imports in the API/worker/probe; existing openWB helper imports in the adapter; PHP built-ins | No new Python package, requirements-file change or mandatory PHP extension. Runtime/OpenSSL/distribution updates and licenses remain inherited platform responsibilities. |
| Vue/build dependencies | Existing UI `package.json` and `package-lock.json` at both revisions above | The Nissan component adds no dependency. Transitive licenses/notices and final build artifacts still require review. |

`NOTICE.md` preserves the original MIT text and now records upstream relicensing
and the dated openWB adaptation. Public source/license texts and one small npm
tarball were retrieved for verification, without installing packages. No
unofficial service-access permission is inferred from a software license.

## Dependency metadata gaps

The pinned target lockfile contains **699 package entries**; the development
lockfile contains **662**. Counts include development, optional and platform
packages, not only code shipped to a browser. Labels include MIT/MIT-0, ISC,
Apache-2.0, BSD variants, BlueOak-1.0.0, CC0/CC-BY and composite expressions.
This enumeration is metadata, not an artifact-level license audit or an SBOM.

Four target entries have no `license` field: `console-browserify` 1.2.0,
`querystring-es3` 0.2.1, `timers-browserify` 1.4.2 and `urlsafe-base64` 1.0.0.
The development lock additionally lacks the field for `vue-color` 3.3.3.
Existing local package metadata/license files supply MIT notices for all five.
The earlier statement that `urlsafe-base64` lacked a license was incorrect:
the lowercase `readme.md` contains its MIT notice. The exact registry tarball
matches the target/development lockfile integrity and the inspected installed
files. The other four packages' local license evidence was not independently
reauthenticated against registry tarballs in this pass.

**BP-LIC-01 resolved:** the apparent provenance gap was a search error.
**BP-LIC-02 remains open for a final binary release:** verify shipped third-party
notices and corresponding source against that actual build. Missing metadata
does not establish incompatibility. No dependency upgrade or replacement was
necessary; the Nissan component adds no dependency. See the detailed license
review for the bounded artifact inspection and the remaining release check.

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

On 2026-10-02 the full affected module suite passed **142 tests** using
Python 3.9.2 and an already present portable Windows PHP 7.4.33 interpreter.
This includes the 102 Python cases and 40 portable PHP cases; both module-owned
PHP files also pass syntax checking. No download or installation was needed.
**12 Linux-only cases remain skipped**, including actual ownership/mode checks
and the hardened HTTP contract. BP-SEC-01 remains open until those checks run.
The unchanged UI has prior 16-test/ESLint and pinned-build evidence. These are
affected-area checks, not complete openWB regression or release validation.

A tester reports matching data in private account, unsaved settings and normal
module queries, with overnight log/GUI activity. Precise automatic cadence,
sustained token renewal, charging acceptance and saved-settings removal remain
open. No captured responses, screenshots or credentials belong in a contribution.

Before submission, close or explicitly disposition the PHP hardening, inherited
logging issue, final distribution notices, service terms/privacy review and
device acceptance; then refresh this summary for the actual final revisions.
No fork, hosted request, push or upstream communication was performed by this
offline review.
