import datetime
from dataclasses import dataclass


@dataclass
class DeviceData:
    name: str
    id: str
    status: dict
    time: datetime.datetime