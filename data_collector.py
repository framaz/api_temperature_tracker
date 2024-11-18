import json
from time import sleep
from typing import List
import os
import datetime
import glob

from devices_data import DeviceData
from post_process_data_hook import ExportCsvHook, MathPlotLibHook
from tuya_request import TuyaRequestor


class DataCollector:
    hooks = [ExportCsvHook(), MathPlotLibHook()]

    def __init__(self):
        with open('config.json', mode='r') as file:
            config = json.load(file)
        self.requestor = TuyaRequestor(config['apiKey'], config['secretKey'])
        self.period = config['period_ms'] / 1000
        self.device_id = config['device_id']

    def log_error(self, error_str):
        with open('error.log', mode='a') as file:
            file.write(error_str + '\n')

    def get_uid(self):
        response = self.requestor.tuya_request(f'v1.0/devices/{self.device_id}')
        if not response['success']:
            raise Exception(response)
        return response['result']['uid']

    def run(self, ):
        user_id = self.get_uid()

        while True:
            try:
                devices_datas = self.get_devices_data_list(user_id)
                print(f'{devices_datas[0].time} Данные получены')
            except Exception as e:
                self.log_error(str(e))
                sleep(self.period)
                continue

            for hook in self.hooks:
                hook.apply(devices_datas)

            sleep(self.period)

    def get_devices_data_list(self, uid: str):
        response = self.requestor.tuya_request(f'v1.0/users/{uid}/devices')
        if not response['success']:
            raise Exception(str(response))

        result_items = []
        time = datetime.datetime.now()
        for item in response['result']:
            data_item = DeviceData(item['name'], item['id'], item['status'], time)
            result_items.append(data_item)

        return result_items



