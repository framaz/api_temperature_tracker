import json
from functools import lru_cache
from typing import TypedDict


class DeviceConfig(TypedDict):
    device_id: str
    param_name: str


class Config(TypedDict):
    apiKey: str
    secretKey: str
    devices_config: list[str]
    period_ms: int


class ConfigReader:
    def __init__(self):
        self._config = self._read_config()

    @lru_cache
    def _read_config(self) -> Config:
        with open('config.json', mode='r') as file:
            config = json.load(file)
        return config

    @property
    def api_key(self) -> str:
        return self._config['apiKey']

    @property
    def secret_key(self) -> str:
        return self._config['secretKey']

    @property
    def devices(self) -> list[DeviceConfig]:
        return self._config["devices_config"]

    @property
    def period_ms(self) -> float:
        return self._config['period_ms']
