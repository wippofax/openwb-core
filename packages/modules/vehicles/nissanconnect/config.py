from typing import Optional


class NissanConnectConfiguration:
    def __init__(self, user_id: Optional[str] = None, password: Optional[str] = None,
                 vin: Optional[str] = None):
        self.user_id = user_id
        self.password = password
        self.vin = vin


class NissanConnect:
    def __init__(self, name: str = "Nissan Leaf ZE1 – MyNISSAN EU (experimental)",
                 type: str = "nissanconnect", configuration: NissanConnectConfiguration = None):
        self.name = name
        self.type = type
        self.configuration = configuration or NissanConnectConfiguration()
