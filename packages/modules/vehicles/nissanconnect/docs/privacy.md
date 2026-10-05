# Privacy and diagnostic data

For the short user-facing version, see [Before using MyNISSAN EU](user-information.md).

Technical source review, 2026-10-02. This describes the module and the inherited
openWB data paths; it is not a legal compliance assessment or an inspection of
an installation. All checks used public source and invented test values.

The review starts from module commit `9b4ea4d`, settings commit `776a60d`,
Core target `3ced7f9cef3c70980ee1fab670f0d0717d1809ca` and settings target
`e8de268fa25f7efca2b5ffc005a757a2f36b530f`. Module changes accompanying this
document address the malformed-response findings below. These references
identify the initial review baseline. Target references describe that version,
not all openWB releases or the effective configuration of any particular wallbox.

## Information flows

| Data and purpose | Recipients and storage | Retention and boundary |
| --- | --- | --- |
| Username, password, optional VIN entered in settings | Browser inputs and the existing Vue configuration store; a connection test sends JSON to the same-origin PHP endpoint and worker stdin | The component does not use local/session storage. Parent configuration state and browser autofill are separate; input masking is not encryption. Changing test inputs clears the displayed result, not the parent form. |
| Saved account configuration for automatic queries | Standard `openWB/set/vehicle/<id>/soc_module/config` and retained `openWB/vehicle/<id>/soc_module/config`, Core memory, local broker persistence, permitted MQTT subscribers and the settings browser | Stored as ordinary configuration, without module-level encryption or automatic expiry. MQTT access control is inherited from the installation. |
| Login forms, credentials, cookies, identity/access/refresh tokens | Wallbox Python process and fixed HTTPS Nissan/OneID/Kamereon endpoints in `src/api.py` | Tokens and cookies stay in the client object. A new configuration creates a new client. Process exit/discard releases references; Python does not promise secure memory erasure. Host swap, crash dumps and monitoring are outside this guarantee. |
| Account ID and VIN returned by Nissan | Client memory and authenticated API requests to the fixed service origins | Used to select a vehicle and retrieve battery status; no module-written cache or diagnostic identifier. |
| SoC, optional range/odometer and battery measurement time | API response, `CarState`, existing Core state/MQTT topics and normal display | Core owns stored values and histories. A new request does not invent a new measurement time. Existing subscribers, histories and backups have their own lifecycle. |
| Query outcome, phase, HTTP status/count, query/measurement times, battery/odometer values and retry delays | `last_query` in memory; scheduled adapter writes its allowlisted summary at DEBUG; unsaved test returns the summary to PHP and selected fields to the browser | Still confidential vehicle/activity data even without a VIN or username. No complete response, URL, cookie or token is deliberately logged by this module. |
| Account cooldown digest, local HMAC key and expiry times | PHP temporary directory `openwb-nissanconnect-test/state`; browser account countdown map | Account digests are pseudonymous, not anonymous: the file also holds the key and permits testing guessed account names. Browser keys contain normalized account names in memory. |

The standalone `tools/probe.py` instead reads credentials with hidden terminal input
and prints battery/odometer values in that private terminal. It does not use MQTT or
the settings endpoint. Agent/TTY checks are precautions, not protection against
terminal recording, screen sharing or host inspection.

## Transport and access

Nissan requests use verified HTTPS. `urllib` can inherit environment/system
proxy configuration, and TLS trusts the host's configured certificate store.
The module adds no analytics or model-provider destination. That statement does
not cover existing openWB Cloud, MQTT bridges, remote support, backup services,
proxies or host monitoring.

The browser-to-wallbox connection uses the page's existing HTTP or HTTPS scheme;
same-origin POST does not encrypt an HTTP connection. The endpoint inherits the
web server's access policy and has no separate login. Origin, content-type and
Fetch Metadata checks prevent ordinary cross-site browser submissions; a direct
HTTP client can supply those headers. Installation access controls remain
necessary. Neither unsaved tests nor normal queries issue wake/charge commands.

The pinned local MQTT bridge explicitly exports `soc_module/#` and `get/#` to
the public broker. Its ACLs determine who can read these values. In
`runs/save_mqtt.php`, an ordinary external bridge with status transfer enabled
exports `openWB/vehicle/#`, which includes module configuration and battery data.
The openWB Cloud branch is different: the generator uses the cloud control
channel and does not generate that ordinary status export. This review does
not establish the later remote-session behavior, recipients or retention of
the Cloud service. Do not infer either that all credentials are uploaded or
that enabling Cloud guarantees they stay local. No private bridge file was read.

## Logs and inherited limitation

The module's scheduled log summary deliberately includes SoC/range, optional odometer and times.
The isolated connection-test worker disables logging; its PHP parent discards
stderr and returns fixed error codes instead of exception details. The endpoint
uses `Cache-Control: no-store`; its POST body does not appear in the URL. Server
or proxy configurations that record request bodies are outside module control.

At the pinned Core version, `helpermodules/logger.py` rotates `soc.log` at
2 MiB with one backup and `mqtt.log` at 3 MiB with one backup. SoC in-memory
snapshots also produce current/previous/latest and warning files. These limits
are size/event based, not a guaranteed deletion deadline. Restoring a quieter
log level stops eligible future records; it does not remove existing records,
downloads, shared logs or backups. Treat log-export and sharing features as
separate disclosures; never submit full private logs to issues or a cloud agent.

**BP-SEC-03: inherited MQTT log redaction is incomplete (open).**
`helpermodules/subdata.py:on_message` logs received payloads at DEBUG;
`setdata.py:on_message` also logs settings payloads. The central filter masks
common secret field names using regular expressions, but does not mask
`user_id` or `vin` by default. A synthetic execution of only the pinned pure
`redact_sensitive_info` function confirmed that a JSON password containing an
escaped quotation mark can leave its suffix visible. Reproduction input:

```python
json.dumps({"password": 'invented-prefix"invented-suffix'})
```

The literal `invented-suffix` remains after filtering. A simple synthetic
password without an embedded quote is removed. This is a source-level
confidentiality finding for readers/exports of the affected logs, not evidence
that a real password has been exposed. Severity is provisionally medium and
depends on logging level and log access. The separately prepared UI already
removes values from the three identified browser debug statements; that does
not change backend logging.

Fixing shared log redaction requires separate Core scope and maintainer review.
This module must not install a global log filter or modify shared MQTT behavior
to hide the issue. Keep logs private and use Details only for a bounded test.
Do not weaken a password to accommodate a log parser. This remains an unresolved
inherited finding for maintainer review. The
user notice now explains the exposure; that disclosure is not a Core fix.

## Retention, backups and removal

The manual connection test does not save credentials, vehicle responses or
charging values. Its temporary file stores only the cooldown state above.
Account entries cease to apply after five minutes and are pruned in memory
when state is loaded. Disk pruning occurs on the next successful state write;
an early return can leave expired entries in the file. No timer guarantees
physical deletion after five minutes. The random key and the file can remain
until approved cleanup or the host's temporary-file lifecycle. Provider pauses
are capped at 24 hours. There are at most 1024 live account entries and the
state format is bounded to 128 KiB.

The prepared private-state hardening validates Linux ownership, 0700/0600
modes, file type/link count and descriptor/path identity. It refuses unsafe
existing state without deleting it or repairing permissions. **BP-SEC-01 is
corrected and locally verified**: all 12 previously skipped Linux cases pass
in WSL2/Debian 13 as an ordinary user, including the synthetic HTTP contract.
These are Linux x86_64 test results; installation-specific ARM/Apache evidence
remains separate. Root and other code running as the same UID remain outside
the isolation boundary.

The pinned `runs/backup.sh` copies both MQTT databases and broker configuration
into the normal backup, together with histories and other configuration. It
encrypts only when the configured backup key file exists. Compression and a
checksum alone do not provide confidentiality. No backup or key on a user's
device was inspected, so encryption of any actual backup is unknown.

Replacing the active Nissan configuration with the prior manual configuration
removes the active module settings through the existing recovery procedure;
removing Python/PHP files alone does not. Neither path erases old SD images,
broker snapshots, exported configuration, logs, browser/password-manager copies
or previously shared data. A restored old backup can restore old credentials.
Keep the verified recovery backups until they are no longer needed; do not
delete them as part of an unapproved privacy cleanup. Logical removal is not
secure erasure of flash media or independent copies. Change the MyNISSAN
password at overall project completion and update the new value only privately.

## Reviewed boundaries and remaining evidence

- `src/api.py`, `soc.py`, `config.py`, `connection_test.py`, `tools/probe.py`: module data
  handling, token reuse/renewal, fixed errors and logging; synthetic tests cover
  success, failures, deferred calls and redaction of module diagnostics.
- Settings repository `public/modules/vehicles/nissanconnect/{test_connection,connection_test_lib}.php`
  (deployed under Core `web/settings/modules/vehicles/nissanconnect/`):
  origin/input checks, subprocess flow, cooldown persistence and filesystem
  source review. Windows PHP 7.4.33 passes the portable checks. Linux PHP 8.4.26
  passes 57 endpoint/state cases with one expected non-Linux skip, including
  actual ownership/mode checks and the hardened HTTP contract on native tmpfs.
- UI `vehicle.vue`, its integration tests and pinned preparation script:
  in-memory input/results, account switching, fixed errors, ignored late results
  and removal of the three known payload-bearing console statements.
- Pinned Core: `helpermodules/{logger,subdata,setdata,pub}.py`, broker templates,
  `runs/{backup.sh,save_mqtt.php}`. These were inspected, not modified.

**BP-SEC-02 (corrected locally):** malformed login destinations and an
unrepresentable token lifetime now enter bounded module errors/backoff. An
unrepresentable optional range is ignored while preserving valid SoC/time.
Four failing synthetic cases reproduce the prior defects; all pass after the
correction. Two additional token tests verify rotation and no password-login
fallback on a refresh service outage. These are offline results, not live API
acceptance or a hard deadline for an already active scheduled socket read.

Remaining work includes target ARM/Apache acceptance, dependency advisories,
current authoritative privacy/service terms, Cloud/service recipient and
retention information, and separately approved device acceptance. Technical
source review alone cannot establish GDPR/BDSG compliance or actual deletion.

## Odometer extension (2026-10-02)

The existing car-adapter recipient now also receives a passive cockpit GET
for the same selected VIN. Only totalMileage is extracted. This adds total
kilometres to client memory, CarState, the standard odometer MQTT topic, normal
status/charge-log/CSV consumers, DEBUG diagnostics and private test results.
Existing MQTT/Cloud access and backup boundaries apply to this added activity
data too; the module does not create another recipient, file or retention policy.
The cockpit's other attributes are not retained in module results or logs.
The odometer measurement time is unknown and is not borrowed from the battery.
Unavailable odometer data is not replaced with a previous response. Review this
additional field in final privacy information and any device acceptance.
