# Offline publication and build review

## Subsequent private trial and publication preparation (2026-10-04)

The dated offline findings below remain the review evidence. The reviewed
369-file package was subsequently installed under separate private approval;
settings/connection tests and good operation were reported by its tester. Its
archive and recovery binding remain frozen. The publication sources now use
Nissan – MyNISSAN EU (experimental), with Leaf ZE1-only practical test coverage;
see [vehicle scope](supported-vehicles.md). That presentation change is not a
rebuild or modification of the installed private package. Source contributions
are being prepared; endpoint build placement, API terms and privacy disposition
remain open. No public binary release or PR has been created by this review.

## Original offline review

Review date: 2026-10-02. Public source and synthetic fixtures only. No wallbox,
Nissan account, captured response, private configuration, log or backup was read.
This review prepares a candidate; it does not authorize deployment or publication.

## Source scope and secret scan

Functional Core source: f4676e6729ebaeed4e8a328a4bf582e8da2d47e1; settings overlay:
0a55a3254665108a1f20afc9b7d8b0f8f9014745. Compatibility target: Core
3ced7f9cef3c70980ee1fab670f0d0717d1809ca and UI base
e8de268fa25f7efca2b5ffc005a757a2f36b530f.

The Core contribution starts at f2c50574ab46e45efc97223caadaac0662f7d50d:
15 commits and 25 changed files within the Nissan module and its PHP endpoints.
The settings contribution starts at daa2958fbd5a6738a7423a68cfa4dc3f0b45ed4e:
six commits and seven changed files, comprising the component/tests, preparation
guide/script and the three agreed debug-payload removals. Neither package.json
nor package-lock.json changes. Nissan introduces no dependency. Upstream refs
were not fetched; this is not a statement about current upstream mergeability.

[Gitleaks 8.30.1](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1),
verified against official release checksums, reported **zero findings** in
both contribution histories, current changed files, commit messages and the two
review archives below. Default rules and full redaction were used, without
repository ignore files or inline allow comments. This is bounded scanner
evidence, not proof that every possible confidential value is absent. Private
runtime folders and personalOS history are outside the product contributions.
Later source/history changes need a corresponding scan update.

## Validation and review package

The latest module was combined with the exact public 2.2.3 Core in a fresh
export. Python 3.9.2 / PHP 7.4.33: **182 passed, 12 Linux-only skips**. The same
PHP/test code already passed **57 Linux checks**, with one expected non-Linux
skip; see [the Linux record](COMPATIBILITY.md#linux-php-verification-2026-10-02).
The pinned settings overlay passed **24 synthetic tests** and its Vite build.
These are module/component checks, not full Core/Apache/ARM or live acceptance.

The pinned dependency tree was copied independently after matching its lockfile
and all 650 present package versions; absent entries were platform-optional.
No install script, upgrade or audit fix ran. Version comparison is not a fresh
tarball-integrity audit. Existing build warnings remain for large chunks,
vm-browserify eval and two discarded dependency annotations. An observation-only
Rollup plugin recorded rendered modules/CSS without changing application logic.

The **369-file** nissanconnect-2.2.3-offline-review.tar.gz contains the current
runtime module, complete pinned UI, both matching PHP endpoints, GPL text and
package notices. Its member names and bytes were read back against the manifest.
SHA-256: d66348f378d78dd809af3796b71007d31ee48c16d38fcf4281370302d751748e.
The accompanying source archive contains the exact prepared UI source, lockfile,
build configuration and complete Nissan contribution/tests/license.
SHA-256: 781c711f4f7037f2bc6fc9fbfcea713bead7c719e31d1a334df41bf607e29ede.

The archive is **not deployment-ready**: release decisions and a concrete update
procedure for the already configured installation remain. The existing installer
still binds the previous candidate hash and must not be used with this archive.
No installer/recovery file or frozen baseline changed. The endpoints are included
after the UI build; their durable upstream build placement remains to be agreed.

## Dependency advisory assessment: BP-DEP-01

Public package names/versions were queried against the
[npm bulk advisory endpoint](https://docs.npmjs.com/cli/v11/commands/npm-audit/#bulk-advisory-endpoint).
No source or private data was submitted. Results were matched to exact locked
versions with npm's semver parser and deduplicated by package/advisory URL.
These counts include build/test packages and are not counts of exploitable bugs.

| Lockfile | Matching packages | Package/advisory pairs | Unique advisory URLs |
| --- | ---: | ---: | ---: |
| Pinned 2.2.3 | 14 | 54 | 53 |
| Development | 4 | 17 | 17 |

The rendered pinned Vite graph contains affected **Axios 1.18.1** (12 advisories)
and **elliptic 6.6.1** (one). Other matched packages were not found in that graph
or CSS inventory. The npm dev flag alone was not used to infer browser inclusion.
This excludes transitive dependencies hidden inside independent prebuilt bundles.

- Six Axios matches concern the Node HTTP/HTTP2 adapter, proxy handling or Node
  data-URI helper. Those modules are absent from this browser build; the version
  match does not establish browser exposure.
- Six remaining Axios matches concern browser-capable/default/fetch/form paths.
  The [fetch-options issue](https://github.com/axios/axios/security/advisories/GHSA-vh66-26gq-q6x8),
  [form-options issue](https://github.com/axios/axios/security/advisories/GHSA-x97p-jq2g-jp4f)
  and [header/interceptor issue](https://github.com/axios/axios/security/advisories/GHSA-j8rh-479h-cp32)
  require additional conditions such as prior prototype pollution or particular
  API use. No application exploitability proof was performed. The development
  lock already uses Axios 1.20.0, outside these ranges. Nissan Test connection
  uses native fetch; the shared UI still imports Axios.
- Elliptic signing code is included via inherited polyfills. The
  [upstream signing report](https://github.com/indutny/elliptic/issues/321) and
  [reviewed advisory](https://github.com/advisories/GHSA-848j-6mx2-7j84) concern
  ECDSA correctness and conditional key exposure. No direct application signing
  call was found; Nissan adds none. This is not proof of global unreachability.
- The pinned [Vitest mock-path issue](https://github.com/vitest-dev/vitest/security/advisories/GHSA-82fw-gwwq-j7x9)
  concerns test tooling. Only trusted synthetic tests ran, without exposing a
  test server to other machines. The development lock already uses 4.1.11.

Direct queries for the static Bootstrap 4.4.1, jQuery 3.6.0, MQTT 5.14.1 and
normalize.css 8.0.1 copies returned no advisories on the review date. Their
embedded transitive packages are not covered by the current UI lock; this is
not a complete legacy-bundle vulnerability scan. Python/PHP platform advisories
and exact device distro patch status are not established by this npm review.

**Disposition:** inherited findings remain open for maintainer/release handling.
No blanket dependency upgrade or shared application change belongs to this
Nissan contribution. This is not a clean audit. Source contribution review can
assess inherited risk separately from distributing the rebuilt historical UI.

## Third-party notices: BP-LIC-02

The rendered output/CSS inventory identified 126 npm package locations. Supplied
license/notice files or complete grants in readmes were collected. Popper.js
1.16.1 carries its full MIT grant in the rendered header. The missing
@vue/devtools-api 6.6.4 grant was recovered from its npm-recorded gitHead:
[pinned MIT text](https://raw.githubusercontent.com/vuejs/vue-devtools/df6ab6bb7791a7a525a97990de73b3ea5e9a1941/LICENSE),
SHA-256 050bbca6960784db52ff387271bf2ecc5cbed7cf8581b415d528a6ecb6585015.
All 126 entries now have preserved notice text in the review package, including
composite licenses; this is not a substitute for their conditions.

The unchanged public/modules/legacy_smart_home contains independent prebuilt
MQTT, jQuery, Bootstrap and CSS assets. Headers and source maps are preserved,
but complete transitive notice/source coverage has not been established.
**BP-LIC-02 remains partly open** for that bundle and final publication packaging.
API terms (BP-TERMS-01), final privacy information, inherited Core logging
(BP-SEC-03) and device acceptance also remain open. No inquiry or issue was sent.
