import datetime
import glob
import json
import os
from collections import defaultdict
from dataclasses import dataclass
from threading import Thread
from time import sleep
from typing import List, Optional
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

from config import ConfigReader
from devices_data import DeviceData


class BaseHook:
    def apply(self, devices_data: List[DeviceData]):
        raise NotImplementedError

    def get_device_by_id(self, devices_data: List[DeviceData], device_id: str):
        for device_data in devices_data:
            if device_data.id == device_id:
                return device_data

    def status_list_to_status_dict(self, device_status: dict):
        status_dict = {}
        for status_item in device_status:
            status_dict[status_item['code']] = status_item['value']
        return status_dict


class ExportCsvHook(BaseHook):
    def apply(self, devices_data: List[DeviceData]):
        for device_data in devices_data:
            with open(self._get_log_path(device_data), mode='a') as file:
                if file.tell() == 0:
                    file.write(self._get_csv_headers(device_data) + '\n')
                to_dump = self._pack_device_status_for_log(device_data)
                file.write(to_dump + '\n')

    def _get_or_create_dir_path(self, device_data):
        base_path = glob.glob(os.path.join('history', f'{device_data.id}*'))
        if not base_path:
            path = os.path.join('history', f'{device_data.id} - {device_data.name[:50]}')
            os.makedirs(path)
            return path
        return base_path[0]

    def _get_csv_headers(self, device_data: DeviceData):
        # TODO remove copypaste
        result = ['time']

        status_dict = self.status_list_to_status_dict(device_data.status)

        for key, value in sorted(status_dict.items()):
            result.append(str(key))

        return ', '.join(result)

    def _pack_device_status_for_log(self, device_data: DeviceData):
        # TODO remove copypaste
        result = [str(device_data.time)]

        status_dict = self.status_list_to_status_dict(device_data.status)

        for key, value in sorted(status_dict.items()):
            result.append(str(value))

        return ', '.join(result)

    def _get_log_path(self, device_data: DeviceData):
        return os.path.join(self._get_or_create_dir_path(device_data), f'{device_data.time.date()}.csv')


@dataclass
class TimeAndValue:
    time: datetime
    value: float

class MathPlotLibHook(BaseHook):
    def __init__(self):
        self._config = ConfigReader()

        self.times_and_values_by_device_ids: dict[str, list[TimeAndValue]] = defaultdict(lambda: [])
        self.names = {}
        colors_iterator = self.colors_iter()
        self.colors = defaultdict(lambda: next(colors_iterator))

        self.thread = Thread(target=self.update_plot_in_thread)
        self.thread.start()

    def colors_iter(self):
        colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
        while True:
            yield from colors

    def apply(self, devices_data: List[DeviceData]):
        for device in self._config.devices:
            device_id = device["device_id"]
            device_data = self.get_device_by_id(devices_data, device_id)

            status_dict = self.status_list_to_status_dict(device_data.status)
            
            result = TimeAndValue(
                device_data.time,
                status_dict[device['param_name']],
            )

            self.times_and_values_by_device_ids[device_id].append(result)

            self.names[device_id] = device_data.name

    def update_plot_in_thread(self, ):
        while (True):
            plt.clf()
            y_lim = [50, 600]
            plt.ylim(y_lim)
            plt.yticks(range(*y_lim, 10), alpha=0.5)
            plt.show(block=False)
            plt.grid(True)
            my_fmt = mdates.DateFormatter('%H:%M')
            plt.gca().xaxis.set_major_formatter(my_fmt)


            min_time = self._get_min()
            max_time = self._get_max()
            times_scale = np.arange(min_time, max_time, datetime.timedelta(seconds=30*60)).astype(datetime.datetime)

            plt.xticks(times_scale, rotation=90)

            for device_id, times_and_values in self.times_and_values_by_device_ids.items():
                # чтобы не было гонки
                times_and_values = [*times_and_values]
                
                values = [obj.value for obj in times_and_values]
                times = [obj.time for obj in times_and_values]
                label = self.names.get(device_id, device_id)
                plt.plot(times, values, label=label, color=self.colors[device_id])

            plt.legend(loc='best')
            plt.pause(1)

    def _get_min(self) -> Optional[datetime.datetime]:
        values = [time_arr[0].time for time_arr in self.times_and_values_by_device_ids.values() if time_arr]
        if not values:
            return datetime.datetime.now()
        return min(values)

    def _get_max(self) -> Optional[datetime.datetime]:
        values = [time_arr[-1].time for time_arr in self.times_and_values_by_device_ids.values() if time_arr]
        if not values:
            return datetime.datetime.now()
        return min(values)