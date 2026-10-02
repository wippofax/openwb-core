"""MyNISSAN EU/OneID client. Only cached battery data; no vehicle commands.

Protocol adapted from HomeAssistant-NissanConnect; see NOTICE.md for attribution.
Credentials, cookies and tokens stay in memory. Never log transport payloads.
"""
import base64
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
from html.parser import HTMLParser
from http.client import HTTPException
from http.cookiejar import CookieJar
import json
import math
import re
import secrets
import ssl
import time
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlencode, urljoin, urlsplit
from urllib.request import build_opener, HTTPCookieProcessor, HTTPRedirectHandler, HTTPSHandler, Request


AUTH = "https://login.mynissan-account.com/"
BFF = "https://nci-bff-web-prod.apps.eu2.kamereon.io/bff-web/"
USERS = "https://alliance-platform-usersadapter-prod.apps.eu2.kamereon.io/user-adapter/"
CARS = "https://alliance-platform-caradapter-prod.apps.eu2.kamereon.io/car-adapter/"
CALLBACK = "com://wso2.service.nci"
# Public application identifier from the reference implementation; not a secret.
CLIENT_ID = "ZM3WK7ax1OtQKYQ8Qqzcv5VgiA8a"
SCOPE = "openid name profile email offline_access"
MAX_RESPONSE = 1024 * 1024


class NissanError(Exception):
    """A deliberately bounded message safe for openWB's error reporting."""


class AuthenticationError(NissanError):
    pass


class RateLimitError(NissanError):
    pass


@dataclass
class HttpResponse:
    status: int
    headers: dict = field(repr=False)
    body: str = field(repr=False)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class PrivateTransport:
    """TLS-verified transport without response logging, netrc or automatic redirects.

    openWB's standard requests hook logs complete authentication responses. urllib
    avoids that hook and urllib3's debug logging of URLs containing VINs/codes.
    CookieJar is memory-only; no cookie or token cache is written to disk.
    urllib may inherit system/environment proxies; TLS still uses the local
    trust store. This transport is not an independent network sandbox.
    """

    def __init__(self):
        self._cookies = CookieJar()
        self._opener = build_opener(
            HTTPSHandler(context=ssl.create_default_context()),
            HTTPCookieProcessor(self._cookies), _NoRedirect())

    def clear_cookies(self):
        self._cookies.clear()

    def request(self, method, url, headers=None, form=None, json_body=None, timeout=10):
        request_headers = dict(headers or {})
        data = None
        if form is not None:
            data = urlencode(form).encode("utf-8")
            request_headers["Content-Type"] = "application/x-www-form-urlencoded"
        elif json_body is not None:
            data = json.dumps(json_body).encode("utf-8")
            request_headers["Content-Type"] = "application/vnd.api+json"
        try:
            request = Request(url, data=data, headers=request_headers, method=method)
            try:
                response = self._opener.open(request, timeout=timeout)
            except HTTPError as error:
                response = error
            with response:
                body = response.read(MAX_RESPONSE + 1)
                if len(body) > MAX_RESPONSE:
                    raise NissanError("Nissan response is too large.")
                return HttpResponse(response.code, dict(response.headers), body.decode("utf-8"))
        except (URLError, OSError, HTTPException, ValueError):
            raise NissanError("Nissan is unreachable or returned an invalid response.") from None


class _LoginForm(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            self.current = {"action": attrs.get("action"), "inputs": {}}
        elif tag == "input" and self.current is not None and attrs.get("name"):
            self.current["inputs"][attrs["name"]] = attrs.get("value", "")

    def handle_endtag(self, tag):
        if tag == "form" and self.current is not None:
            self.forms.append(self.current)
            self.current = None

    @classmethod
    def parse(cls, body):
        parser = cls()
        parser.feed(body)
        for form in parser.forms:
            if {"sessionDataKey", "password"}.issubset(form["inputs"]):
                return form
        return None


def _origin(url):
    try:
        parsed = urlsplit(url)
        if parsed.username or parsed.password or parsed.fragment or parsed.scheme != "https":
            return None
        return parsed.hostname, parsed.port or 443
    except ValueError:
        return None


def _object(response):
    try:
        body = json.loads(response.body)
    except (ValueError, TypeError):
        raise NissanError("Nissan returned an invalid JSON response.") from None
    if not isinstance(body, dict) or body.get("errors") or body.get("error"):
        raise NissanError("Nissan reported an error or returned an unknown response format.")
    return body


def _number(value, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise NissanError("Nissan returned an invalid battery value.")
    try:
        value = float(value)
    except OverflowError:
        raise NissanError("Nissan returned an invalid battery value.") from None
    if not math.isfinite(value) or value < 0 or (maximum is not None and value > maximum):
        raise NissanError("Nissan returned an invalid battery value.")
    return float(value)


@dataclass(frozen=True)
class BatteryStatus:
    """SoC in percent, original Unix measurement time in seconds and optional km."""

    soc: float
    timestamp: float
    range_km: Optional[float] = None


def parse_battery(body, now=None):
    """Require an actual, timezone-aware measurement time; never substitute now."""
    try:
        attributes = body["data"]["attributes"]
        soc = _number(attributes["batteryLevel"], 100)
        raw_time = attributes["lastUpdateTime"]
        if not isinstance(raw_time, str):
            raise ValueError
        measured = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
        if measured.tzinfo is None or measured.utcoffset() is None:
            raise ValueError
        timestamp = measured.timestamp()
        if not math.isfinite(timestamp) or timestamp <= 0 or timestamp > (time.time() if now is None else now) + 300:
            raise ValueError
        distance = attributes.get("rangeHvacOn")
        if distance is None:
            distance = attributes.get("rangeHvacOff")
        # An unavailable optional range must not discard a valid SoC measurement.
        try:
            distance = None if distance is None else _number(distance)
        except NissanError:
            distance = None
        return BatteryStatus(soc, timestamp, distance)
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError):
        raise NissanError("Nissan did not return a valid SoC with a measurement timestamp.") from None


class NissanClient:
    """Stateful client for one account/vehicle; callers must serialize its use.

    Keeps tokens, vehicle selection and backoff in memory between queries.
    Create a new instance when credentials/VIN change. The injected transport
    and clocks support synthetic tests; production requests use PrivateTransport.
    """

    def __init__(self, user_id, password, vin=None, transport=None, clock=time.monotonic, wall_clock=time.time):
        self._user = user_id
        self._password = password
        self._configured_vin = (vin or "").strip().upper()
        self._transport = transport if transport is not None else PrivateTransport()
        self._clock = clock
        self._wall_clock = wall_clock
        self._access_token = None
        self._refresh_token = None
        self._expires_at = 0
        self._user_id = None
        self._vin = None
        self._retry_at = 0
        self._provider_retry_at = 0
        self._failed_queries = 0
        self._retry_error_type = NissanError
        self._retry_reason = ""
        self._deadline = None
        self.last_query = None
        self._last_contact_at = None
        self._last_success_at = None
        self._last_measurement_at = None
        self._request_started_at = None
        self._request_count = 0
        self._http_status = None
        self._phase = "idle"

    def _request(self, method, url, auth_request=False, **kwargs):
        if _origin(url) not in {_origin(AUTH), _origin(BFF), _origin(USERS), _origin(CARS)}:
            raise NissanError("Unexpected Nissan request destination; request aborted.")
        remaining = self._deadline - self._clock()
        if remaining <= 0:
            raise NissanError("Nissan query time limit exceeded.")
        self._last_contact_at = self._wall_clock()
        if self._request_started_at is None:
            self._request_started_at = self._last_contact_at
        self._request_count += 1
        self._http_status = None
        response = self._transport.request(method, url, timeout=min(10, remaining), **kwargs)
        self._http_status = response.status
        if response.status in (429, 503):
            self._retry_at = self._clock() + self._retry_after(response)
            # Separate provider advice from the scheduled client's own error backoff.
            provider_delay = self._retry_after(response, minimum=0, default=300 if response.status == 429 else 0)
            self._provider_retry_at = self._clock() + provider_delay
        if response.status == 429:
            raise RateLimitError("Nissan is rate limiting requests. Please try again later.")
        if response.status in (401, 403) or (auth_request and response.status == 400):
            raise AuthenticationError("Nissan rejected the login or access authorization.")
        if response.status >= 400:
            raise NissanError("Nissan service returned an HTTP error ({}).".format(response.status))
        return response

    def _retry_after(self, response, minimum=300, default=300):
        """Accept delay seconds or an HTTP date; bound server-directed pauses."""
        value = next((v for k, v in response.headers.items() if k.lower() == "retry-after"), None)
        try:
            delay = int(value)
        except (ValueError, TypeError, OverflowError):
            try:
                deadline = parsedate_to_datetime(value)
                if deadline.tzinfo is None:
                    raise ValueError
                delay = deadline.timestamp() - self._wall_clock()
            except (ValueError, TypeError, AttributeError, OverflowError):
                delay = default
        return max(minimum, min(delay, 86400))

    def _json(self, method, url, **kwargs):
        response = self._request(method, url, **kwargs)
        if not 200 <= response.status < 300:
            raise NissanError("Unexpected redirect from the Nissan API.")
        return _object(response)

    def _redirects(self, response, url, callback=False):
        for _ in range(10):
            if response.status not in (301, 302, 303, 307, 308):
                return response, url
            location = next((v for k, v in response.headers.items() if k.lower() == "location"), None)
            if not isinstance(location, str) or not location:
                break
            try:
                target = urljoin(url, location)
                parsed = urlsplit(target)
            except ValueError:
                raise NissanError("Unexpected redirect during Nissan login.") from None
            expected = urlsplit(CALLBACK)
            if callback and (parsed.scheme, parsed.netloc, parsed.path) == (
                    expected.scheme, expected.netloc, expected.path) and not parsed.fragment:
                return response, target
            if _origin(target) != _origin(AUTH):
                raise NissanError("Unexpected redirect during Nissan login.")
            response = self._request("GET", target)
            url = target
        raise NissanError("Too many or invalid Nissan redirects.")

    def _login(self):
        if (not isinstance(self._user, str) or not self._user.strip()
                or not isinstance(self._password, str) or not self._password):
            raise AuthenticationError("MyNISSAN username and password are required.")
        # A new login must not reuse an expired/partially authenticated web session.
        if hasattr(self._transport, "clear_cookies"):
            self._transport.clear_cookies()
        self._refresh_token = None
        verifier = secrets.token_urlsafe(64)
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
        state = secrets.token_urlsafe(32)
        url = AUTH + "oauth2/authorize?" + urlencode({
            "response_type": "code", "redirect_uri": CALLBACK, "client_id": CLIENT_ID,
            "state": state, "scope": SCOPE, "code_challenge": challenge, "code_challenge_method": "S256",
            "locale": "en_GB", "brand": "Nissan", "client": "mynissanapp"})
        response, url = self._redirects(self._request("GET", url), url)
        form = _LoginForm.parse(response.body)
        if not form or not form["action"]:
            raise NissanError("Nissan login form is unavailable; you may need to sign in through the app.")
        try:
            target = urljoin(url, form["action"])
        except ValueError:
            raise NissanError("Unexpected Nissan login form destination.") from None
        if _origin(target) != _origin(AUTH):
            raise NissanError("Unexpected Nissan login form destination.")
        data = dict(form["inputs"])
        region = data.get("regionCode", "")
        data.update(userName=self._user, username=region + "/" + self._user if region else self._user,
                    password=self._password)
        response = self._request("POST", target, form=data, headers={"Origin": AUTH.rstrip("/"), "Referer": url})
        response, callback = self._redirects(response, target, callback=True)
        parsed = urlsplit(callback)
        if (parsed.scheme, parsed.netloc, parsed.path) != ("com", "wso2.service.nci", ""):
            raise AuthenticationError(
                "Nissan login did not complete. Check your credentials and any notices in MyNISSAN.")
        values = parse_qs(parsed.query)
        if values.get("state") != [state] or len(values.get("code", [])) != 1 or values.get("error"):
            raise AuthenticationError("Nissan returned an invalid login confirmation.")
        token = self._json("POST", AUTH + "oauth2/token", auth_request=True, form={
            "grant_type": "authorization_code", "redirect_uri": CALLBACK, "client_id": CLIENT_ID,
            "code": values["code"][0], "code_verifier": verifier, "scope": SCOPE})
        identity_token = token.get("id_token")
        if not isinstance(identity_token, str) or not identity_token:
            raise AuthenticationError("Nissan did not return an identity token.")
        self._install(self._json("POST", BFF + "v1/oauth2/access_token?platform=Android", auth_request=True,
                                 headers={"Authorization": identity_token, "Content-Type": "application/vnd.api+json"}))

    def _install(self, token):
        access = token.get("access_token")
        refresh = token.get("refresh_token")
        if not isinstance(access, str) or not access or (refresh is not None and not isinstance(refresh, str)):
            raise AuthenticationError("Nissan did not return a valid access token.")
        try:
            expires = float(token.get("expires_in", 3600))
            if not math.isfinite(expires) or expires <= 0:
                raise ValueError
        except (ValueError, TypeError, OverflowError):
            raise AuthenticationError("Nissan returned an invalid token lifetime.") from None
        self._access_token = access
        self._refresh_token = refresh or self._refresh_token
        self._expires_at = self._clock() + max(0, expires - 30)

    def _authenticate(self, force=False):
        if self._access_token and not force and self._clock() < self._expires_at:
            return
        if self._refresh_token:
            try:
                self._install(self._json("POST", BFF + "v1/oauth2/refresh-token?platform=Android", auth_request=True,
                                         headers={"Authorization": self._refresh_token},
                                         json_body={"scope": "openid profile vehicles"}))
                return
            except AuthenticationError:
                self._access_token = self._refresh_token = None
        self._login()

    def _get(self, url):
        for attempt in range(2):
            try:
                return self._json("GET", url, headers={
                    "Authorization": "Bearer " + self._access_token, "Content-Type": "application/vnd.api+json"})
            except AuthenticationError:
                if attempt:
                    raise
                self._authenticate(force=True)

    def _select_vehicle(self):
        if self._configured_vin and not re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", self._configured_vin):
            raise NissanError("The configured VIN is invalid.")
        if not self._user_id:
            user = self._get(USERS + "v1/users/current").get("userId")
            if not isinstance(user, str) or not user:
                raise NissanError("Nissan did not return a user identifier.")
            self._user_id = user
        vehicles = self._get(BFF + "v5/users/" + quote(self._user_id, safe="") + "/cars").get("data")
        if not isinstance(vehicles, list):
            raise NissanError("Nissan did not return a vehicle list.")
        candidates = [v.get("vin", "").upper() for v in vehicles
                      if isinstance(v, dict) and isinstance(v.get("vin"), str)
                      and re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", v["vin"].upper())]
        if self._configured_vin:
            if self._configured_vin not in candidates:
                raise NissanError("The configured VIN was not found in the Nissan account.")
            self._vin = self._configured_vin
        elif len(set(candidates)) == 1:
            self._vin = candidates[0]
        else:
            raise NissanError("Could not select a unique vehicle. Please configure the VIN.")

    def _finish_query(self, outcome, started, result=None):
        """Keep an allowlisted diagnostic summary, never raw transport data."""
        completed = self._wall_clock()
        if result is not None:
            self._last_success_at = completed
            self._last_measurement_at = result.timestamp

        def iso(value):
            return None if value is None else datetime.fromtimestamp(value, timezone.utc).isoformat()

        self.last_query = {
            "outcome": outcome,
            "phase": self._phase,
            "request_started_at": iso(self._request_started_at),
            "completed_at": iso(completed),
            "duration_seconds": round(max(0, self._clock() - started), 3),
            "http_requests": self._request_count,
            "last_http_status": self._http_status,
            "last_contact_at": iso(self._last_contact_at),
            "last_success_at": iso(self._last_success_at),
            "last_measurement_at": iso(self._last_measurement_at),
            "measurement_at": iso(result.timestamp) if result else None,
            "data_age_seconds": round(completed - result.timestamp, 1) if result else None,
            "soc": result.soc if result else None,
            "range_km": result.range_km if result else None,
            "retry_after_seconds": max(0, math.ceil(self._retry_at - self._clock())),
            "provider_retry_after_seconds": max(0, math.ceil(self._provider_retry_at - self._clock())),
            "source": "nissan_cached_api",
        }

    def fetch_battery(self):
        """Return cached battery data or raise NissanError; never issue wake commands.

        Updates last_query with allowlisted diagnostics on success/failure and
        deferred calls. Failure pauses subsequent calls without sleeping. The
        60-second budget limits new request starts, not total socket read time.
        Core, not this client, decides whether to accept a measurement timestamp.
        """
        started = self._clock()
        self._request_started_at = None
        self._request_count = 0
        self._http_status = None
        self._phase = "idle"
        if started < self._retry_at:
            remaining = math.ceil(self._retry_at - started)
            self._finish_query("deferred", started)
            raise self._retry_error_type(
                "Nissan requests are paused for {} more seconds. {}".format(remaining, self._retry_reason))
        self._deadline = started + 60
        result = None
        outcome = "failed"
        try:
            self._phase = "authentication"
            self._authenticate()
            if not self._vin:
                self._phase = "vehicle_selection"
                self._select_vehicle()
            self._phase = "battery"
            body = self._get(CARS + "v1/cars/" + self._vin + "/battery-status")
            result = parse_battery(body, now=self._wall_clock())
            self._failed_queries = 0
            self._retry_at = 0
            self._provider_retry_at = 0
            self._retry_error_type = NissanError
            self._retry_reason = ""
            outcome = "success"
            return result
        except NissanError as error:
            if isinstance(error, AuthenticationError):
                self._access_token = self._refresh_token = None
                self._user_id = self._vin = None
            # Do not sleep in an openWB worker or retain exception tracebacks.
            # A successful query resets this backoff; deferred calls do not extend it.
            self._failed_queries = min(self._failed_queries + 1, 5)
            delay = min(300 * 2 ** (self._failed_queries - 1), 3600)
            self._retry_at = max(self._retry_at, self._clock() + delay)
            self._retry_error_type = type(error)
            self._retry_reason = str(error)
            raise
        finally:
            self._deadline = None
            self._finish_query(outcome, started, result)
