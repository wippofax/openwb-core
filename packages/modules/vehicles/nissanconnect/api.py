"""MyNISSAN EU/OneID client. Only cached battery data; no vehicle commands.

Protocol adapted from HomeAssistant-NissanConnect; see NOTICE.md for attribution.
Credentials, cookies and tokens stay in memory. Never log transport payloads.
"""
import base64
from dataclasses import dataclass, field
from datetime import datetime
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
                    raise NissanError("Nissan-Antwort ist zu groß.")
                return HttpResponse(response.code, dict(response.headers), body.decode("utf-8"))
        except (URLError, OSError, HTTPException, ValueError):
            raise NissanError("Nissan ist nicht erreichbar oder liefert eine ungültige Antwort.") from None


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
        raise NissanError("Nissan liefert keine gültige JSON-Antwort.") from None
    if not isinstance(body, dict) or body.get("errors") or body.get("error"):
        raise NissanError("Nissan meldet einen Fehler oder ein unbekanntes Antwortformat.")
    return body


def _number(value, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise NissanError("Nissan liefert einen ungültigen Batteriewert.")
    if not math.isfinite(value) or value < 0 or (maximum is not None and value > maximum):
        raise NissanError("Nissan liefert einen ungültigen Batteriewert.")
    return float(value)


@dataclass(frozen=True)
class BatteryStatus:
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
        raise NissanError("Nissan liefert keinen gültigen SoC mit Messzeitpunkt.") from None


class NissanClient:
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
        self._deadline = None

    def _request(self, method, url, auth_request=False, **kwargs):
        if _origin(url) not in {_origin(AUTH), _origin(BFF), _origin(USERS), _origin(CARS)}:
            raise NissanError("Unerwartetes Nissan-Anfrageziel; Anfrage abgebrochen.")
        remaining = self._deadline - self._clock()
        if remaining <= 0:
            raise NissanError("Zeitlimit für die Nissan-Abfrage überschritten.")
        response = self._transport.request(method, url, timeout=min(10, remaining), **kwargs)
        if response.status == 429:
            # Avoid request storms, including on the next openWB update.
            delay = 300
            try:
                raw_delay = next(v for k, v in response.headers.items() if k.lower() == "retry-after")
                delay = max(300, min(int(raw_delay), 86400))
            except (StopIteration, ValueError, TypeError):
                pass
            self._retry_at = self._clock() + delay
            raise RateLimitError("Nissan begrenzt die Abfragen. Bitte später erneut versuchen.")
        if response.status in (401, 403) or (auth_request and response.status == 400):
            raise AuthenticationError("Nissan lehnt die Anmeldung oder Zugriffsberechtigung ab.")
        if response.status >= 400:
            raise NissanError("Nissan-Dienst meldet einen HTTP-Fehler ({}).".format(response.status))
        return response

    def _json(self, method, url, **kwargs):
        response = self._request(method, url, **kwargs)
        if not 200 <= response.status < 300:
            raise NissanError("Unerwartete Weiterleitung der Nissan-API.")
        return _object(response)

    def _redirects(self, response, url, callback=False):
        for _ in range(10):
            if response.status not in (301, 302, 303, 307, 308):
                return response, url
            location = next((v for k, v in response.headers.items() if k.lower() == "location"), None)
            if not isinstance(location, str) or not location:
                break
            target = urljoin(url, location)
            parsed = urlsplit(target)
            expected = urlsplit(CALLBACK)
            if callback and (parsed.scheme, parsed.netloc, parsed.path) == (
                    expected.scheme, expected.netloc, expected.path) and not parsed.fragment:
                return response, target
            if _origin(target) != _origin(AUTH):
                raise NissanError("Unerwartete Weiterleitung beim Nissan-Login.")
            response = self._request("GET", target)
            url = target
        raise NissanError("Zu viele oder ungültige Nissan-Weiterleitungen.")

    def _login(self):
        if (not isinstance(self._user, str) or not self._user.strip()
                or not isinstance(self._password, str) or not self._password):
            raise AuthenticationError("MyNISSAN-Benutzername und Passwort fehlen.")
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
            raise NissanError("Nissan-Anmeldeformular nicht verfügbar; eventuell ist eine App-Anmeldung erforderlich.")
        target = urljoin(url, form["action"])
        if _origin(target) != _origin(AUTH):
            raise NissanError("Unerwartetes Ziel des Nissan-Anmeldeformulars.")
        data = dict(form["inputs"])
        region = data.get("regionCode", "")
        data.update(userName=self._user, username=region + "/" + self._user if region else self._user,
                    password=self._password)
        response = self._request("POST", target, form=data, headers={"Origin": AUTH.rstrip("/"), "Referer": url})
        response, callback = self._redirects(response, target, callback=True)
        parsed = urlsplit(callback)
        if (parsed.scheme, parsed.netloc, parsed.path) != ("com", "wso2.service.nci", ""):
            raise AuthenticationError("Nissan-Login nicht abgeschlossen. Zugang und Hinweise in MyNISSAN prüfen.")
        values = parse_qs(parsed.query)
        if values.get("state") != [state] or len(values.get("code", [])) != 1 or values.get("error"):
            raise AuthenticationError("Nissan liefert keine gültige Anmeldebestätigung.")
        token = self._json("POST", AUTH + "oauth2/token", auth_request=True, form={
            "grant_type": "authorization_code", "redirect_uri": CALLBACK, "client_id": CLIENT_ID,
            "code": values["code"][0], "code_verifier": verifier, "scope": SCOPE})
        identity_token = token.get("id_token")
        if not isinstance(identity_token, str) or not identity_token:
            raise AuthenticationError("Nissan liefert kein Identitätstoken.")
        self._install(self._json("POST", BFF + "v1/oauth2/access_token?platform=Android", auth_request=True,
                                 headers={"Authorization": identity_token, "Content-Type": "application/vnd.api+json"}))

    def _install(self, token):
        access = token.get("access_token")
        refresh = token.get("refresh_token")
        if not isinstance(access, str) or not access or (refresh is not None and not isinstance(refresh, str)):
            raise AuthenticationError("Nissan liefert kein gültiges Zugriffstoken.")
        try:
            expires = float(token.get("expires_in", 3600))
            if not math.isfinite(expires) or expires <= 0:
                raise ValueError
        except (ValueError, TypeError):
            raise AuthenticationError("Nissan liefert eine ungültige Token-Laufzeit.") from None
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
            raise NissanError("Die konfigurierte FIN ist ungültig.")
        if not self._user_id:
            user = self._get(USERS + "v1/users/current").get("userId")
            if not isinstance(user, str) or not user:
                raise NissanError("Nissan liefert keine Benutzerzuordnung.")
            self._user_id = user
        vehicles = self._get(BFF + "v5/users/" + quote(self._user_id, safe="") + "/cars").get("data")
        if not isinstance(vehicles, list):
            raise NissanError("Nissan liefert keine Fahrzeugliste.")
        candidates = [v.get("vin", "").upper() for v in vehicles
                      if isinstance(v, dict) and isinstance(v.get("vin"), str)
                      and re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", v["vin"].upper())]
        if self._configured_vin:
            if self._configured_vin not in candidates:
                raise NissanError("Die konfigurierte FIN wurde im Nissan-Konto nicht gefunden.")
            self._vin = self._configured_vin
        elif len(set(candidates)) == 1:
            self._vin = candidates[0]
        else:
            raise NissanError("Kein eindeutiges Fahrzeug gefunden. Bitte die FIN konfigurieren.")

    def fetch_battery(self):
        if self._clock() < self._retry_at:
            raise RateLimitError(
                "Nissan-Abfragen pausieren nach einer Anfragebegrenzung oder fehlgeschlagenen Anmeldung.")
        self._deadline = self._clock() + 60
        try:
            self._authenticate()
            if not self._vin:
                self._select_vehicle()
            body = self._get(CARS + "v1/cars/" + self._vin + "/battery-status")
            return parse_battery(body, now=self._wall_clock())
        except AuthenticationError:
            # Rejected credentials must not trigger a new login on every scheduler tick.
            self._access_token = self._refresh_token = None
            self._user_id = self._vin = None
            self._retry_at = self._clock() + 300
            raise
        finally:
            self._deadline = None
