"""Synthetic fixtures only. No captured account responses or real identifiers."""
import base64
import hashlib
import io
import json
import logging
import traceback
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

import pytest

from modules.vehicles.nissanconnect.api import (
    AUTH, CARS, AuthenticationError, HttpResponse, MAX_RESPONSE,
    NissanClient, NissanError, PrivateTransport, RateLimitError, parse_battery)


# Deliberately invented test values, unrelated to any account or vehicle.
VIN = "SJNFAAZE1U0000001"
SECOND_VIN = "SJNFAAZE1U0000002"
MEASURED = 1640995200.0
FORM = ('<form action="/commonauth"><input name="sessionDataKey" value="synthetic-session">'
        '<input name="regionCode" value="EU"><input name="password" type="password"></form>')


def reply(body, status=200, headers=None):
    return HttpResponse(status, headers or {}, body if isinstance(body, str) else json.dumps(body))


def battery(soc=47, timestamp="2022-01-01T00:00:00Z", **extra):
    return {"data": {"attributes": dict(batteryLevel=soc, lastUpdateTime=timestamp, **extra)}}


class ScriptedTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.cookies_cleared = 0

    def clear_cookies(self):
        self.cookies_cleared += 1

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        assert self.responses, "Unexpected extra HTTP request"
        response = self.responses.pop(0)
        return response(self.calls) if callable(response) else response


def login_script():
    def authorize(calls):
        state = parse_qs(urlsplit(calls[-2][1]).query)["state"][0]
        return reply("", 302, {"Location": "com://wso2.service.nci?code=synthetic-code&state=" + state})
    return [reply(FORM), authorize, reply({"id_token": "synthetic-id"}),
            reply({"access_token": "synthetic-access", "refresh_token": "synthetic-refresh", "expires_in": 3600})]


def make_client(responses, vin=None):
    transport = ScriptedTransport(responses)
    ticks = [0.0]
    client = NissanClient("synthetic@example.invalid", "synthetic-password", vin, transport,
                          clock=lambda: ticks[0], wall_clock=lambda: MEASURED + 86400)
    return client, transport, ticks


def full_script(vehicles=None):
    return login_script() + [reply({"userId": "synthetic-user"}),
                             reply({"data": [{"vin": VIN}] if vehicles is None else vehicles}),
                             reply(battery(rangeHvacOn=123.4))]


@pytest.mark.parametrize("soc", [0, 47.5, 100])
def test_valid_soc_preserves_old_measurement(soc):
    result = parse_battery(battery(soc, rangeHvacOn=0, rangeHvacOff=150), now=MEASURED + 86400)
    assert (result.soc, result.timestamp, result.range_km) == (soc, MEASURED, 0)


@pytest.mark.parametrize("soc", [None, True, False, -1, 101, "47", float("nan"), float("inf"), [], {}])
def test_invalid_soc_never_becomes_zero(soc):
    with pytest.raises(NissanError):
        parse_battery(battery(soc), now=MEASURED)


@pytest.mark.parametrize("timestamp", [None, 0, "", "bad", "2022-01-01T00:00:00", "2099-01-01T00:00:00Z"])
def test_missing_ambiguous_or_future_time_rejected(timestamp):
    with pytest.raises(NissanError):
        parse_battery(battery(timestamp=timestamp), now=MEASURED)


def test_offset_time_and_optional_range():
    result = parse_battery(battery(timestamp="2022-01-01T01:00:00+01:00", rangeHvacOff=150), now=MEASURED)
    assert result.timestamp == MEASURED
    assert result.range_km == 150
    assert parse_battery(battery(rangeHvacOn=-1), now=MEASURED).range_km is None


@pytest.mark.parametrize("body", [{}, {"data": None}, {"data": {"attributes": {}}}, [], None])
def test_invalid_shape_has_safe_error(body):
    with pytest.raises(NissanError):
        parse_battery(body)


def test_login_pkce_selection_and_cached_battery_only(caplog):
    caplog.set_level(logging.DEBUG)
    client, transport, _ = make_client(full_script())
    status = client.fetch_battery()
    assert status.soc == 47 and status.timestamp == MEASURED and status.range_km == 123.4
    calls = transport.calls
    authorize = parse_qs(urlsplit(calls[0][1]).query)
    verifier = calls[2][2]["form"]["code_verifier"]
    expected = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    assert authorize["code_challenge"] == [expected]
    assert authorize["code_challenge_method"] == ["S256"]
    assert calls[1][2]["form"]["username"] == "EU/synthetic@example.invalid"
    assert calls[3][2]["headers"]["Authorization"] == "synthetic-id"
    assert calls[-1][2]["headers"]["Authorization"] == "Bearer synthetic-access"
    assert calls[-1][:2] == ("GET", CARS + "v1/cars/" + VIN + "/battery-status")
    assert all("/actions/" not in url for _, url, _ in calls)
    assert all(0 < kwargs["timeout"] <= 10 for _, _, kwargs in calls)
    assert not caplog.records
    assert not transport.responses


def test_subsequent_update_reuses_tokens_and_vehicle():
    client, transport, _ = make_client(full_script() + [reply(battery(48))])
    client.fetch_battery()
    count = len(transport.calls)
    assert client.fetch_battery().soc == 48
    assert len(transport.calls) == count + 1


def test_expired_token_is_refreshed_in_memory():
    script = full_script() + [reply({"access_token": "synthetic-renewed"}), reply(battery())]
    client, transport, ticks = make_client(script)
    client.fetch_battery()
    ticks[0] = 3600
    client.fetch_battery()
    assert "refresh-token" in transport.calls[-2][1]
    assert transport.calls[-2][2]["headers"]["Authorization"] == "synthetic-refresh"
    assert transport.calls[-1][2]["headers"]["Authorization"] == "Bearer synthetic-renewed"


def test_rejected_refresh_logs_in_once():
    script = full_script() + [reply({"error": "invalid_grant"}, 400)] + login_script() + [reply(battery())]
    client, transport, ticks = make_client(script)
    client.fetch_battery()
    ticks[0] = 3600
    client.fetch_battery()
    assert sum("oauth2/authorize?" in url for _, url, _ in transport.calls) == 2
    assert transport.cookies_cleared == 2


def test_401_retries_once_then_stops_and_cools_down():
    script = full_script() + [reply("synthetic-private-body", 401), reply({"access_token": "synthetic-new"}),
                              reply("synthetic-private-body", 401)]
    client, transport, _ = make_client(script)
    client.fetch_battery()
    with pytest.raises(AuthenticationError, match="Nissan"):
        client.fetch_battery()
    count = len(transport.calls)
    with pytest.raises(RateLimitError):
        client.fetch_battery()
    assert len(transport.calls) == count


def test_state_mismatch_never_exchanges_tokens():
    client, transport, _ = make_client([reply(FORM), reply("", 302, {
        "Location": "com://wso2.service.nci?code=synthetic-code&state=wrong"})])
    with pytest.raises(AuthenticationError):
        client.fetch_battery()
    assert len(transport.calls) == 2


@pytest.mark.parametrize("target", [
    "https://example.invalid/steal", "http://login.mynissan-account.com/",
    "https://login.mynissan-account.com:444/", "https://user@login.mynissan-account.com/",
])
def test_form_target_validated_before_sending_credentials(target):
    client, transport, _ = make_client([reply(FORM.replace("/commonauth", target))])
    with pytest.raises(NissanError):
        client.fetch_battery()
    assert len(transport.calls) == 1


def test_cross_origin_redirect_is_never_followed():
    client, transport, _ = make_client([reply("", 302, {"Location": "https://example.invalid/steal"})])
    with pytest.raises(NissanError):
        client.fetch_battery()
    assert len(transport.calls) == 1


def test_redirect_loop_is_bounded():
    client, transport, _ = make_client([reply("", 302, {"Location": "/loop"})] * 11)
    with pytest.raises(NissanError):
        client.fetch_battery()
    assert len(transport.calls) == 11


@pytest.mark.parametrize("vehicles,vin", [
    ([], None), ([{"vin": VIN}, {"vin": SECOND_VIN}], None), ([{"vin": VIN}], SECOND_VIN),
])
def test_missing_or_ambiguous_vehicle_never_guessed(vehicles, vin):
    client, transport, _ = make_client(full_script(vehicles), vin)
    with pytest.raises(NissanError):
        client.fetch_battery()
    assert not any("battery-status" in url for _, url, _ in transport.calls)


def test_configured_vehicle_is_selected():
    client, transport, _ = make_client(full_script([{"vin": VIN}, {"vin": SECOND_VIN}]), SECOND_VIN.lower())
    client.fetch_battery()
    assert SECOND_VIN in transport.calls[-1][1]


def test_rate_limit_pauses_later_updates_without_sleeping():
    client, transport, ticks = make_client(full_script() + [reply("private", 429, {"Retry-After": "600"})])
    client.fetch_battery()
    with pytest.raises(RateLimitError):
        client.fetch_battery()
    ticks[0] = 599
    count = len(transport.calls)
    with pytest.raises(RateLimitError):
        client.fetch_battery()
    assert len(transport.calls) == count
    ticks[0] = 600
    transport.responses.append(reply(battery()))
    assert client.fetch_battery().soc == 47


@pytest.mark.parametrize("response", [
    reply("private", 500), reply("private", 503), reply("not-json"),
    reply({"errors": [{"detail": "private"}]}), reply({"id_token": None}),
])
def test_bad_response_not_logged_or_in_error(response, caplog):
    caplog.set_level(logging.DEBUG)
    script = login_script()
    script[2] = response
    client, _, _ = make_client(script)
    with pytest.raises(NissanError) as error:
        client.fetch_battery()
    assert "private" not in str(error.value)
    assert "synthetic-password" not in str(error.value)
    assert not caplog.records


def test_transport_hides_exception_details_and_response_repr(monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)
    transport = PrivateTransport()
    private_value = "synthetic-secret-value"

    def fail(*args, **kwargs):
        raise URLError(private_value)

    monkeypatch.setattr(transport._opener, "open", fail)
    with pytest.raises(NissanError) as error:
        transport.request("GET", AUTH)
    formatted = "".join(traceback.format_exception(type(error.value), error.value, error.value.__traceback__))
    assert private_value not in formatted
    assert private_value not in repr(reply(private_value, headers={"Authorization": private_value}))
    assert not caplog.records


def test_transport_returns_redirect_without_following(monkeypatch):
    transport = PrivateTransport()

    def respond(*args, **kwargs):
        raise HTTPError(AUTH, 302, "redirect", {"Location": "/next"}, io.BytesIO(b""))

    monkeypatch.setattr(transport._opener, "open", respond)
    result = transport.request("GET", AUTH)
    assert result.status == 302 and result.headers["Location"] == "/next"


def test_transport_limits_response_size(monkeypatch):
    transport = PrivateTransport()

    def respond(*args, **kwargs):
        raise HTTPError(AUTH, 500, "error", {}, io.BytesIO(b"x" * (MAX_RESPONSE + 1)))

    monkeypatch.setattr(transport._opener, "open", respond)
    with pytest.raises(NissanError, match="groß"):
        transport.request("GET", AUTH)


def test_total_request_budget_stops_redirect_chain():
    client, transport, ticks = make_client([])

    def slow_response(calls):
        ticks[0] += 61
        return reply("", 302, {"Location": "/next"})

    transport.responses.append(slow_response)
    with pytest.raises(NissanError, match="Zeitlimit"):
        client.fetch_battery()
    assert len(transport.calls) == 1
