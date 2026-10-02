# License and service-terms review

Reviewed on **2026-10-02** for the European MyNISSAN integration, with German
service terms. Code basis: Core contribution `72c4786`, settings `776a60d`,
target Core `3ced7f9cef3c70980ee1fab670f0d0717d1809ca` and target settings
`e8de268fa25f7efca2b5ffc005a757a2f36b530f`.

**Result:** the reviewed adapted source has a GPLv3-compatible licensing path.
The existing MIT text is correct; its provenance and modification notice are
now explicit in [NOTICE.md](NOTICE.md). This finding does not establish
permission for the unofficial service client. Final distribution packaging
and the service-access question below remain open. This is a documented source
review, not legal certification or a release approval.

## Source provenance

| Source | Pinned evidence | Use and license conclusion |
| --- | --- | --- |
| openWB Core and settings | Each repository's `LICENSE`, GNU GPL version 3; revisions above | Native integration and UI contribution follow GPLv3, preserving existing notices. No new runtime or UI dependency. |
| HomeAssistant-NissanConnect | [MIT license](https://github.com/dan-r/HomeAssistant-NissanConnect/blob/b0bafe9108d4574e243aa182324584dbc68369ad/LICENSE.md), [client](https://github.com/dan-r/HomeAssistant-NissanConnect/blob/b0bafe9108d4574e243aa182324584dbc68369ad/custom_components/nissan_connect/kamereon/kamereon.py), [constants](https://github.com/dan-r/HomeAssistant-NissanConnect/blob/b0bafe9108d4574e243aa182324584dbc68369ad/custom_components/nissan_connect/kamereon/kamereon_const.py) | Direct reference for the HTML login-form parser, OneID/PKCE and token exchange/renewal flow, EU endpoints and battery fields. Our standard-library transport, validation, error policy and openWB adapter differ. Daniel Raper's 2024 MIT notice is retained verbatim. |
| mitchellrj/kamereon-python | [Apache-2.0 license](https://github.com/mitchellrj/kamereon-python/blob/146904802301aa0b0008e2bdb3a88ed10ff50acf/LICENSE.md), [client header](https://github.com/mitchellrj/kamereon-python/blob/146904802301aa0b0008e2bdb3a88ed10ff50acf/kamereon/kamereon.py) credits Richard Mitchell, 2020 | Indirect reference chain. Crucially, the direct HA client's header states that Apache portions were relicensed with permission. We rely on that published MIT grant, not an assumption that Apache attribution vanished. No separate Apache source was copied into this contribution during this review. |
| Tobiaswk/dartnissanconnect | [MIT license](https://github.com/Tobiaswk/dartnissanconnect/blob/5e34e8c573d34dc4d3d48e63052f015f99080d2d/LICENSE), Tobias Westergaard Kjeldsen, 2021 | Research reference and upstream credit. No Dart package or application assets are shipped. Credit is retained; do not confuse this library's license with another application's license. |

The HA relicensing statement is upstream evidence; its private permission
correspondence was not inspected. That is an ordinary reliance on the stated
source license, not independent verification of every author's rights.
If future work directly incorporates Apache-licensed code, preserve its
copyright/attribution and any upstream NOTICE, include Apache-2.0, and mark
modified files as required by [section 4](https://www.apache.org/licenses/LICENSE-2.0).
Apache-2.0 is compatible with GPLv3 according to the
[Apache Software Foundation](https://apache.org/licenses/GPL-compatibility.html);
MIT/Expat compatibility is documented by the
[Free Software Foundation](https://www.gnu.org/licenses/license-list.html#Expat).

## Distribution obligations and dependencies

For the proposed source contributions, preserve both repository GPL texts,
the module NOTICE and existing third-party notices. The dated adaptation notice
identifies the openWB changes; do not present the complete contribution as MIT.
GPLv3 sections 4-6 cover notices, modified source and corresponding source for
non-source distributions. For a compiled UI release, supply its matching
preferred source, lockfile and necessary build material through a compliant
distribution route. Local private use does not itself require public posting.
The repository `LICENSE` is the applicable license text; the
[GPLv3 guide](https://www.gnu.org/licenses/quick-guide-gplv3.en.html) supplies context.

**BP-LIC-01 resolved (correction):** the earlier report overlooked lowercase
`readme.md` in `urlsafe-base64` 1.0.0. It contains the MIT notice, copyright
2014 RGBboy. The [pinned upstream README](https://github.com/RGBboy/urlsafe-base64/blob/4438da5b18040af1c1789dd3c53b6595b3bea512/readme.md)
and the exact [npm tarball](https://registry.npmjs.org/urlsafe-base64/-/urlsafe-base64-1.0.0.tgz)
confirm it. Tarball SHA-512 matches both UI lockfiles; its README, package.json
and two JavaScript files match the installed copies byte for byte. No
dependency replacement or update was necessary. Missing lockfile metadata is
not a missing license. The other previously identified metadata gaps have MIT
notices in the existing packages; see [the inventory](contribution-review.md).

**BP-LIC-02 open, release packaging only:** 699 target/662 development lock
entries include build-only and optional packages; they are not a shipped SBOM.
The frozen overlay archive has 367 members and only the module NOTICE among
license-named files. This does not establish absence of embedded notices, and
the overlay relies on an existing installation with its GPL text. It is not
evidence of a complete distributable license bundle. Before distributing a
final compiled UI, map included JavaScript/CSS/fonts/icons to their actual
package versions, preserve required MIT/BSD/Apache notices and applicable
asset attribution, and verify GPL corresponding source. Do this against the
final build once; do not modify shared dependencies or rebuild the frozen
device candidate merely for this review.

## Nissan service access: BP-TERMS-01 open

The [official German terms index](https://www.nissan.de/rechtliches/agb.html)
links the [NissanConnect Services terms, May 2026](https://www.nissan.de/content/dam/Nissan/nissan_europe/services/Ownership/NissanConnectServices_FULL/PDF/TermsOfUse/NissanConnect%20Services%20Terms%20and%20Conditions%20-%20Germany.pdf).
This public version explicitly includes MyNISSAN. Relevant provisions:

- Section 1.2, p. 4: applications supplied by Nissan or third parties on its behalf.
- Sections 6.1 and 7.3-7.4, pp. 23, 25-26: technology/content restrictions,
  reverse engineering and permitted service use; section 7.2 addresses credentials.
- Sections 5.2 and 5.7, pp. 19, 21: data access/sharing and lawful user reuse,
  subject to restrictions. Read these together with the broader content clauses.
- Section 2.6, p. 7: service suspension/termination, including for breaches.

Our assessment: these provisions neither establish a specific permission for
the present client nor justify declaring every local use unlawful. The module
reuses a public official-app client identifier, performs scheduled owner-account
queries and stores/displays values for charge control. Copyright permission
from an independent library author does not resolve this service relationship.
The user's accepted account/app version and any additional OneID/Kamereon
conditions were not inspected. No separate public developer grant for the exact
login/BFF endpoints or numeric permitted polling interval was established.
Backoff and cooldown are engineering safeguards, not contractual permission.

German copyright law also limits blanket conclusions: interface ideas are
addressed by [UrhG section 69a(2)](https://www.gesetze-im-internet.de/urhg/__69a.html),
lawful observation/testing by [69d(3)](https://www.gesetze-im-internet.de/urhg/__69d.html),
and necessary interoperability decompilation by
[69e](https://www.gesetze-im-internet.de/urhg/__69e.html).
[69g(2)](https://www.gesetze-im-internet.de/urhg/__69g.html) invalidates specified
contrary contractual terms. These conditional rules are not a blanket license
to access a hosted service or bypass access controls. Their application to this
implementation requires a case-specific assessment.

## Official alternative worth evaluating

Nissan's [German vehicle-data page](https://www.nissan.de/vernetzte-fahrzeugdaten.html)
lists LEAF production from May 2019 for its data-access route. The precise
eligibility of an individual 2019 vehicle remains unverified.
The [German FAQ](https://www.nissan.de/kundenservice/faq.html) links public
[MyNISSANdata developer documentation](https://mynissandata.com/developer-documentation).
It describes registered business integrations, owner consent, separate credentials,
payment/billing and read-only pull/webhook delivery. Its charging reference
includes state of charge and update time. This is a different API from our
current MyNISSAN app endpoints. Documentation is not proof that our vehicle,
private-use deployment, pricing or freshness requirements qualify.

The public [platform terms page](https://mynissandata.com/terms-of-service)
returned navigation without substantive terms in this review; those platform
and Data Terms remain unreviewed. No account, consent request, paid operation
or live API call was made. No migration is included in this license pass.

## Concrete remaining decision

Before declaring the service-terms item closed, obtain a documented disposition
based on the applicable terms and qualified interpretation or provider
clarification. The following is a prepared inquiry, **not sent**:

> Does Nissan permit a vehicle owner to use an open-source, locally operated
> openWB integration for periodic read-only battery queries through the
> MyNISSAN EU app's OneID/Kamereon endpoints and public app client identifier,
> with local storage/display for charging control? Which access terms and query
> limits apply? If this access path is not supported, can an independently
> registered MyNISSANdata integration serve that private-use purpose, with
> which eligibility, data-freshness, redistribution and fee conditions?

The inquiry needs no password, VIN, private response or account screenshot.
Separate authorization is required before sending it. Final privacy/security
review remains tracked separately in [privacy.md](privacy.md) and the project
Bulletproof record; this license pass does not close those findings.

## Reproducible public evidence

Exact fetched SHA-256 digests, in addition to the immutable URLs above:

| Artifact | SHA-256 |
| --- | --- |
| HA LICENSE.md | `b7dc3fcde759bb78fd2e22b8725c6d384ced62a612c1c73b579f5a82cbdb05e2` |
| HA client | `f6360df94a70a6f51d49fbc5ba37ba3f5c89f9af7865360cb5022acf1573d743` |
| kamereon-python LICENSE.md | `43070e2d4e532684de521b885f385d0841030efa2b1a20bafb76133a5e1379c1` |
| Dart library LICENSE | `e7b839ced10822fbc7f0eb1655f0a8070c4b1b541769c600e3567c0d2e136d17` |
| urlsafe-base64 npm tarball | `c0a12871ac0a9dc23d79a701be42da557b8a31ad3e45820628576f9e5f7be0f4` |

Public source/license downloads were audit inputs only; no package was installed.
Nissan pages are mutable and must be rechecked for the final service decision.

## Odometer field provenance (2026-10-02)

The same MIT-licensed HA revision supplies the additional field mapping:
[OdometerSensor](https://github.com/dan-r/HomeAssistant-NissanConnect/blob/b0bafe9108d4574e243aa182324584dbc68369ad/custom_components/nissan_connect/sensor.py)
uses `total_mileage` with kilometre units; its already-reviewed client maps that
attribute from cockpit `totalMileage`. The new parser/transport/error policy
are implemented locally, and the existing MIT notice remains applicable.
No new package or license is introduced. Live Leaf availability and service
access remain separate acceptance and terms questions.

## Updated build notice evidence (2026-10-02)

The [offline release review](release-review.md) records a rebuilt odometer/UI
candidate with full notice text for all 126 npm package locations found in its
Vite output/CSS graph, plus the exact prepared source archive. BP-LIC-02 remains
partly open for independent prebuilt legacy vendor bundles and final publication
packaging. No service-access permission or legal approval follows from this
artifact check. The frozen installed candidate is unchanged.
