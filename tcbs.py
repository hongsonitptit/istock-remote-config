# Suppress the warnings from urllib3
from urllib3.exceptions import InsecureRequestWarning
import requests
import os
import time
import json
from config import TCBS_USER, TCBS_PASSWORD, TCBS_NAME

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

CUR_DIR = os.path.dirname(__file__)

class TCBSAccount():
    def __init__(self, **kwargs) -> None:
        self.name = kwargs['name']
        self.id = kwargs['id']
        self.username = kwargs['user']
        self.password = kwargs['password']
        self.list_ids = kwargs['list_ids']
        self.potential_group_id = kwargs['potential_group_id']
        self.watchlist_group_id = kwargs['watchlist_group_id']
        self.owner_group_id = kwargs['owner_group_id']
        self.tcbsid = kwargs['tcbsid']
        self.code = kwargs['code']
        self.device_info = kwargs['device_info']

tcbs_son = TCBSAccount(**{
    'name': TCBS_NAME,
    'id': 'xxx',
    'user': TCBS_USER,
    'password': TCBS_PASSWORD,
    'list_ids': ['xxx','xxx'], # tk thuong + ky quy
    'potential_group_id': None,
    'owner_group_id': None,
    'watchlist_group_id': None,
    'tcbsid': 'xxx',
    'code': 'xxx',
    "device_info": '{"os.name":"Linux","os.version":0,"browser.name":"Chrome","browser.version":131,"device.platform":"web","device.name":"Chrome Linux x86_64","device.physicalID":"ddbf6018-12fc-43af-abc2-a2479de60b30","navigator.userAgent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36","navigator.appVersion":"5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36","navigator.platform":"Linux x86_64","navigator.vendor":"Google Inc.","webVersion":"5.9.7"}',
})

def get_token(account: TCBSAccount) -> str:
    EXPIRED_TIME = 8 * 60 * 60  # 8 hours
    TOKEN_FILE = f"{CUR_DIR}/.token/tcinvest.{account.id}.token"

    token = ""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as fi:
            timestamp = int(fi.readline())
            token = fi.readline()
            if time.time() - timestamp < EXPIRED_TIME:
                return token

    url = "https://apipub.tcbs.com.vn/authen/v1/login"

    payload = json.dumps({
        "username": account.username,
        "password": account.password,
        "device_info": account.device_info,
    })
    headers = {
        'Content-Type': 'application/json',
    }

    response = requests.request(
        "POST", url, headers=headers, data=payload, verify=False)

    data = json.loads(response.text)
    token = data['token']

    # save token to file
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    with open(TOKEN_FILE, "w") as fo:
        fo.write(f"{int(time.time())}\n")
        fo.write(token)

    return token