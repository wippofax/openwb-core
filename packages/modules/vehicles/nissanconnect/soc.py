"""Adapt Nissan measurements to the existing openWB vehicle wrapper and scheduler."""
import json
import logging

from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.nissanconnect.api import NissanClient
from modules.vehicles.nissanconnect.config import NissanConnect


log = logging.getLogger(__name__)


def create_vehicle(vehicle_config: NissanConnect, vehicle: int):
    """Keep one client per configuration; delegate scheduling/error policy to Core."""
    client = None
    configuration_key = None

    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        nonlocal client, configuration_key
        config = vehicle_config.configuration
        current = (config.user_id, config.password, config.vin)
        # Keep tokens between updates; discard them when the account/vehicle changes.
        if client is None or current != configuration_key:
            client = NissanClient(*current)
            configuration_key = current
        try:
            battery = client.fetch_battery()
        finally:
            # No account identifiers or secrets; battery values/times are still private.
            if isinstance(client.last_query, dict):
                log.debug("Nissan vehicle %s query: %s", vehicle, json.dumps(client.last_query, sort_keys=True))
        return CarState(soc=battery.soc, range=battery.range_km, soc_timestamp=battery.timestamp)

    return ConfigurableVehicle(vehicle_config=vehicle_config, component_updater=updater,
                               vehicle=vehicle, calc_while_charging=False)


device_descriptor = DeviceDescriptor(configuration_factory=NissanConnect)
