# TinyTuya Setup Wizard
# -*- coding: utf-8 -*-
"""
TinyTuya Setup Wizard Tuya based WiFi smart devices

Author: Jason A. Cox
For more information see https://github.com/jasonacox/tinytuya

Description
    Setup Wizard will prompt the user for Tuya IoT Developer credentials and will gather all
    registered Device IDs and their Local KEYs.  It will save the credentials and the device
    data in the tinytuya.json and devices.json configuration files respectively. The Wizard
    will then optionally scan the local devices for status.

    HOW to set up your Tuya IoT Developer account: iot.tuya.com:
    https://github.com/jasonacox/tinytuya#get-the-tuya-device-local-key

Credits
* Tuya API Documentation
    https://developer.tuya.com/en/docs/iot/open-api/api-list/api?id=K989ru6gtvspg
* TuyaAPI https://github.com/codetheweb/tuyapi by codetheweb and blackrozes
    The TuyAPI/CLI wizard inspired and informed this python version.
"""
# Modules
import requests
import time
import hmac
import hashlib
import json

# Backward compatability for python2

class TuyaRequestor:
    token: str = None

    def __init__(self, api_key, api_secret):
        self.apiKey = api_key
        self.apiSecret = api_secret

    def _tuya_request(self, uri, token=None, new_sign_algorithm=True, body=None, headers=None):
        api_key = self.apiKey
        api_secret = self.apiSecret

        urlhost = "openapi.tuyaeu.com"  # Central Europe Data Center

        # Build URL
        url = "https://%s/%s" % (urlhost, uri)

        # Build Header
        now = int(time.time() * 1000)
        headers = dict(list(headers.items()) + [('Signature-Headers', ":".join(headers.keys()))]) if headers else {}
        if (token == None):
            payload = api_key + str(now)
            headers['secret'] = api_secret
        else:
            payload = api_key + token + str(now)

        # If running the post 6-30-2021 signing algorithm update the payload to include it's data
        if new_sign_algorithm: payload += ('GET\n' +  # HTTPMethod
                                           hashlib.sha256(
                                               bytes((body or "").encode('utf-8'))).hexdigest() + '\n' +  # Content-SHA256
                                           ''.join(['%s:%s\n' % (key, headers[key])  # Headers
                                                    for key in headers.get("Signature-Headers", "").split(":")
                                                    if key in headers]) + '\n' +
                                           '/' + url.split('//', 1)[-1].split('/', 1)[-1])
        # Sign Payload
        signature = hmac.new(
            api_secret.encode('utf-8'),
            msg=payload.encode('utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest().upper()

        # Create Header Data
        headers['client_id'] = api_key
        headers['sign'] = signature
        headers['t'] = str(now)
        headers['sign_method'] = 'HMAC-SHA256'

        if (token != None):
            headers['access_token'] = token

        # Get Token
        response = requests.get(url, headers=headers)
        try:
            response_dict = json.loads(response.content.decode())
        except:
            try:
                response_dict = json.loads(response.content)
            except:
                print("Failed to get valid JSON response")
                raise
        response_dict['_status_code'] = response.status_code
        return response_dict

    def _tuya_request_with_reauth(self, uri, body=None, headers=None):
        if self.token is not None:
            response = self._tuya_request(uri, token=self.token, body=body, headers=headers)
            if response['success']:
                return response
        self.token = self._get_token()
        return self._tuya_request(uri, token=self.token, body=body, headers=headers)

    def _get_token(self):
        resp = self._tuya_request('v1.0/token?grant_type=1')
        if resp['success']:
            return resp['result']['access_token']
        raise Exception(resp)

    def tuya_request(self, uri, body=None, headers=None):
        return self._tuya_request_with_reauth(uri, body, headers)
