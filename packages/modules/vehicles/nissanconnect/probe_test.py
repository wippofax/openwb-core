from unittest.mock import Mock

import pytest

from modules.vehicles.nissanconnect import probe
from modules.vehicles.nissanconnect.api import BatteryStatus


@pytest.fixture
def local_terminal(monkeypatch):
    for name in ("CODEX_THREAD_ID", "CODEX_SANDBOX", "CODEX_CI"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(probe.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(probe.sys.stdout, "isatty", lambda: True)
    # Do not change the test process's global logging state.
    monkeypatch.setattr(probe.logging, "disable", Mock())


def test_probe_refuses_agent_context(monkeypatch, local_terminal):
    monkeypatch.setenv("CODEX_THREAD_ID", "synthetic-agent-session")
    credentials = Mock(side_effect=AssertionError("Credentials must not be requested"))
    monkeypatch.setattr(probe, "getpass", credentials)
    assert probe.main() == 2
    credentials.assert_not_called()


def test_probe_refuses_redirected_output(monkeypatch, local_terminal):
    monkeypatch.setattr(probe.sys.stdout, "isatty", lambda: False)
    assert probe.main() == 2


def test_probe_aborts_before_requesting_credentials(monkeypatch, local_terminal):
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    credentials = Mock()
    monkeypatch.setattr(probe, "getpass", credentials)
    assert probe.main() == 0
    credentials.assert_not_called()


def test_probe_uses_hidden_inputs_without_echo(monkeypatch, local_terminal, capsys):
    monkeypatch.setattr(probe.sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt: "y")
    monkeypatch.setattr(probe, "getpass", Mock(side_effect=["synthetic@example.invalid", "synthetic-password", ""]))
    client = Mock()
    client.fetch_battery.return_value = BatteryStatus(47, 1640995200, 123)
    factory = Mock(return_value=client)
    monkeypatch.setattr(probe, "NissanClient", factory)
    assert probe.main() == 0
    output = capsys.readouterr().out
    assert "synthetic@example.invalid" not in output
    assert "synthetic-password" not in output
    assert "SoC: 47 %" in output
    client.fetch_battery.assert_called_once()


def test_probe_aborts_if_hidden_input_is_unavailable(monkeypatch, local_terminal):
    monkeypatch.setattr("builtins.input", lambda prompt: "y")
    monkeypatch.setattr(probe, "getpass", Mock(side_effect=probe.GetPassWarning("synthetic")))
    factory = Mock()
    monkeypatch.setattr(probe, "NissanClient", factory)
    assert probe.main() == 2
    factory.assert_not_called()
