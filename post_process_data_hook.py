import datetime
import glob
import json
import os
from threading import Thread
from time import sleep
from typing import List
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

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


class MathPlotLibHook(BaseHook):
    def __init__(self):
        with open('config.json', mode='r') as file:
            config = json.load(file)

        self.item_id_to_log = config['device_id']
        self.param_to_log = config['param_name']

        self.times = []
        self.values = []

        self.thread = Thread(target=self.update_plot_in_thread)
        self.thread.start()

    def apply(self, devices_data: List[DeviceData]):
        device_data = self.get_device_by_id(devices_data, self.item_id_to_log)

        self.times.append(device_data.time)

        status_dict = self.status_list_to_status_dict(device_data.status)
        self.values.append(status_dict[self.param_to_log])

    def update_plot_in_thread(self, ):
        y_lim = [50, 600]
        plt.ylim(y_lim)
        plt.yticks(range(*y_lim, 10), alpha=0.5)
        plt.show(block=False)
        plt.grid(True)
        my_fmt = mdates.DateFormatter('%H:%M')
        plt.gca().xaxis.set_major_formatter(my_fmt)
        while (True):
            min_time = min(self.times or [datetime.datetime.now()])
            max_time = max(self.times or [min_time])
            times = np.arange(min_time, max_time, datetime.timedelta(seconds=30*60)).astype(datetime.datetime)

            plt.xticks(times, rotation=90)
            plt.plot(self.times, self.values, color='black', )
            # sleep(0.5)
            plt.pause(1)
