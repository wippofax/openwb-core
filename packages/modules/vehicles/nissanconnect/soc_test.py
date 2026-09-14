import importlib
import sys
from types import ModuleType
from unittest.mock import Mock

import pytest

from modules.vehicles.nissanconnect.api import BatteryStatus
from modules.vehicles.nissanconnect.config import NissanConnect, NissanConnectConfiguration


@pytest.fixture
def soc_module(monkeypatch):
    # The standalone suite must not bootstrap openWB services on the test PC.
    # In the normal core suite this dependency is already imported by conftest.
    dependency = "modules.common.configurable_vehicle"
    if dependency not in sys.modules:
        stub = ModuleType(dependency)
        stub.ConfigurableVehicle = Mock()
        monkeypatch.setitem(sys.modules, dependency, stub)
    return importlib.import_module("modules.vehicles.nissanconnect.soc")


def test_openwb_adapter_preserves_timestamp_reuses_client_and_handles_config_change(monkeypatch, soc_module):
    soc = soc_module

    # Only replace the scheduling/storage wrapper; use the real CarState and updater.
    wrapper = Mock()
    monkeypatch.setattr(soc, "ConfigurableVehicle", wrapper)
    fake_client = Mock()
    fake_client.fetch_battery.return_value = BatteryStatus(0, 1640995200, 0)
    factory = Mock(return_value=fake_client)
    monkeypatch.setattr(soc, "NissanClient", factory)
    config = NissanConnect(configuration=NissanConnectConfiguration("synthetic@example.invalid", "synthetic-password"))
    soc.create_vehicle(config, 7)
    updater = wrapper.call_args.kwargs["component_updater"]
    state = updater(None)
    assert (state.soc, state.range, state.soc_timestamp) == (0, 0, 1640995200)
    updater(None)
    assert factory.call_count == 1
    config.configuration.password = "synthetic-new-password"
    updater(None)
    assert factory.call_count == 2
    assert wrapper.call_args.kwargs["calc_while_charging"] is False
    assert wrapper.call_args.kwargs["vehicle"] == 7


def test_configuration_descriptor_and_module_name_agree(soc_module):
    config = soc_module.device_descriptor.configuration_factory()
    assert config.type == "nissanconnect"
    assert config.configuration.vin is None


def test_configuration_roundtrip_uses_openwb_serializer():
    from dataclass_utils import asdict, dataclass_from_dict

    config = NissanConnect(configuration=NissanConnectConfiguration(
        "synthetic@example.invalid", "synthetic-password", "SJNFAAZE1U0000001"))
    encoded = asdict(config)
    decoded = dataclass_from_dict(NissanConnect, encoded)
    assert decoded.type == "nissanconnect"
    assert isinstance(decoded.configuration, NissanConnectConfiguration)
    assert decoded.configuration.user_id == config.configuration.user_id
    assert decoded.configuration.password == config.configuration.password
    assert decoded.configuration.vin == config.configuration.vin
