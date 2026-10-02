import os
from pathlib import Path
import subprocess
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
    client.fetch_battery.return_value = BatteryStatus(47, 1640995200, 123, 12345.6)
    factory = Mock(return_value=client)
    monkeypatch.setattr(probe, "NissanClient", factory)
    assert probe.main() == 0
    output = capsys.readouterr().out
    assert "synthetic@example.invalid" not in output
    assert "synthetic-password" not in output
    assert "SoC: 47 %" in output
    assert "Odometer: 12345.6 km (measurement time unavailable)" in output
    client.fetch_battery.assert_called_once_with(include_odometer=True)


def test_probe_aborts_if_hidden_input_is_unavailable(monkeypatch, local_terminal):
    monkeypatch.setattr("builtins.input", lambda prompt: "y")
    monkeypatch.setattr(probe, "getpass", Mock(side_effect=probe.GetPassWarning("synthetic")))
    factory = Mock()
    monkeypatch.setattr(probe, "NissanClient", factory)
    assert probe.main() == 2
    factory.assert_not_called()


def test_direct_probe_start_with_isolated_python_loads_adjacent_api(tmp_path):
    # Reproduce embedded Python's missing script-directory search path without
    # importing a real client or allowing a live request in the child process.
    script = tmp_path / "probe.py"
    script.write_text(Path(probe.__file__).read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "api.py").write_text(
        'class NissanError(Exception): pass\n'
        'class NissanClient:\n'
        '    def __init__(self, *args, **kwargs):\n'
        '        raise AssertionError("No real client in the startup test")\n',
        encoding="utf-8")
    result = subprocess.run(
        [probe.sys.executable, "-I", str(script)], cwd=str(tmp_path),
        env=dict(os.environ, CODEX_CI="1"), capture_output=True, text=True, timeout=10)
    assert result.returncode == 2, result.stderr
    assert "Aborted: Please run in a private terminal outside a Codex or agent session." in result.stdout
    assert result.stderr == ""
