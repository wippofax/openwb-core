"""Synthetic query diagnostics and isolated settings-worker contracts."""
import json
from unittest.mock import Mock

import pytest

from modules.vehicles.nissanconnect.api import AuthenticationError, NissanError
from modules.vehicles.nissanconnect.api_test import MEASURED_UNIX_SECONDS, VIN, full_script, make_client, reply
from modules.vehicles.nissanconnect.connection_test import run_test


def test_diagnostics_distinguish_contact_measurement_failure_and_deferred_update():
    client, transport, ticks_monotonic_seconds = make_client(full_script() + [reply('synthetic-private-body', 503)])
    client._unix_seconds = lambda: MEASURED_UNIX_SECONDS + 86400 + ticks_monotonic_seconds[0]
    client.fetch_battery()
    success = client.last_query.copy()
    assert success['outcome'] == 'success'
    assert success['http_requests'] == 7
    assert success['measurement_at'] == '2022-01-01T00:00:00+00:00'
    assert success['request_started_at'] == '2022-01-02T00:00:00+00:00'
    assert success['data_age_seconds'] == 86400
    assert (success['soc'], success['range_km']) == (47, 123.4)
    ticks_monotonic_seconds[0] = 10
    with pytest.raises(NissanError):
        client.fetch_battery()
    failure = client.last_query.copy()
    assert failure['outcome'] == 'failed'
    assert failure['last_http_status'] == 503
    assert failure['soc'] is None and failure['measurement_at'] is None
    assert failure['last_success_at'] == success['completed_at']
    assert failure['last_measurement_at'] == success['measurement_at']
    ticks_monotonic_seconds[0] = 20
    requests = len(transport.calls)
    with pytest.raises(NissanError):
        client.fetch_battery()
    deferred = client.last_query
    assert deferred['outcome'] == 'deferred'
    assert deferred['http_requests'] == 0 and deferred['request_started_at'] is None
    assert deferred['last_contact_at'] == failure['last_contact_at']
    assert deferred['last_success_at'] == success['completed_at']
    assert len(transport.calls) == requests
    for value in ('synthetic-private-body', 'synthetic-password', VIN, 'synthetic-access', 'example.invalid'):
        assert value not in json.dumps([success, failure, deferred])


def test_worker_returns_only_query_result_and_does_not_log(caplog):
    client, transport, _ = make_client(full_script() + [reply({"data": {"attributes": {"totalMileage": 12345.6}}})])
    result = run_test({'user_id': 'synthetic@example.invalid', 'password': 'synthetic-password'},
                      client_factory=lambda *args: client)
    assert result['success'] is True
    assert result['query']['soc'] == 47
    assert result['query']['data_age_seconds'] == 86400
    assert len(transport.calls) == 8
    assert result["query"]["odometer_km"] == 12345.6
    assert not caplog.records
    for value in ('synthetic-password', 'example.invalid', VIN, 'synthetic-access'):
        assert value not in json.dumps(result)


@pytest.mark.parametrize('payload', [
    None, [], {}, {'user_id': 'a', 'password': 'p', 'url': 'https://invalid/'},
    {'user_id': 'a', 'password': 'p', 'vin': []},
    {'user_id': 'a', 'password': 'p', 'vin': 'wrong'},
    {'user_id': 'a', 'password': 'p' * 4097}])
def test_worker_rejects_invalid_input_without_creating_client(payload):
    factory = Mock()
    assert run_test(payload, factory) == {'success': False, 'code': 'invalid_input'}
    factory.assert_not_called()


@pytest.mark.parametrize('error,code', [
    (AuthenticationError('synthetic-private'), 'authentication_failed'),
    (NissanError('synthetic-private'), 'query_failed'),
    (RuntimeError('synthetic-private'), 'internal_error')])
def test_worker_never_echoes_error_details(error, code):
    client = Mock(last_query=None)
    client.fetch_battery.side_effect = error
    result = run_test({'user_id': 'a', 'password': 'p'}, lambda *args: client)
    assert result['success'] is False and result['code'] == code
    assert 'synthetic-private' not in json.dumps(result)


@pytest.mark.parametrize('status,headers,expected', [
    (401, {}, 0), (503, {}, 0), (503, {'Retry-After': 'bad'}, 0),
    (503, {'Retry-After': '60'}, 60), (429, {}, 300), (429, {'Retry-After': '900'}, 900)])
def test_provider_advice_is_separate_from_scheduled_error_backoff(status, headers, expected):
    client, _, _ = make_client([reply({}, status, headers)])
    with pytest.raises(NissanError):
        client.fetch_battery()
    assert client.last_query['provider_retry_after_seconds'] == expected
    assert client.last_query['retry_after_seconds'] == max(300, expected)


def test_login_success_followed_by_battery_failure_is_not_a_successful_test():
    client, _, _ = make_client(full_script()[:-1] + [reply({}, 503)])
    result = run_test({'user_id': 'synthetic@example.invalid', 'password': 'synthetic-password'},
                      client_factory=lambda *args: client)
    assert result['success'] is False
    assert result['query']['phase'] == 'battery'
    assert result['query']['provider_retry_after_seconds'] == 0
