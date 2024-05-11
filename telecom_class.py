#!/usr/bin/env python3
# _*_ coding:utf-8 _*_

import base64
import requests
from datetime import datetime
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5


class Telecom:
    def __init__(self):
        self.login_info = None
        self.phonenum = None
        self.password = None

    def set_login_info(self, login_info):
        self.login_info = login_info
        self.phonenum = login_info.get("phoneNbr", None)
        self.password = login_info.get("password", None)

    def trans_phone(self, phone_num):
        result = ""
        for char in phone_num:
            result += chr(ord(char) + 2 & 65535)
        return result

    def encrypt(self, str):
        public_key_pem = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDBkLT15ThVgz6/NOl6s8GNPofd
WzWbCkWnkaAm7O2LjkM1H7dMvzkiqdxU02jamGRHLX/ZNMCXHnPcW/sDhiFCBN18
qFvy8g6VYb9QtroI09e176s+ZCtiv7hbin2cCTj99iUpnEloZm19lwHyo69u5UMi
PMpq0/XKBO8lYhN/gwIDAQAB
-----END PUBLIC KEY-----"""
        public_key = RSA.import_key(public_key_pem.encode())
        cipher = PKCS1_v1_5.new(public_key)
        ciphertext = cipher.encrypt(str.encode())
        encoded_ciphertext = base64.b64encode(ciphertext).decode()
        return encoded_ciphertext

    def get_fee_flow_limit(self, fee_remain_flow):
        today = datetime.today()
        days_in_month = (
            datetime(today.year, today.month + 1, 1)
            - datetime(today.year, today.month, 1)
        ).days
        return int((fee_remain_flow / days_in_month))

    def do_login(self, phonenum, password):
        phonenum = phonenum or self.phonenum
        password = password or self.password
        ts = datetime.now().strftime("%Y%m%d%H%M00")
        enc = f"iPhone 14 13.2.3{phonenum}{phonenum}{ts}{password}0$$$0."
        body = {
            "content": {
                "fieldData": {
                    "accountType": "",
                    "authentication": password,
                    "deviceUid": f"3{phonenum}",
                    "isChinatelecom": "0",
                    "loginAuthCipherAsymmertric": self.encrypt(enc),
                    "loginType": "4",
                    "phoneNum": self.trans_phone(phonenum),
                    "systemVersion": "13.2.3",
                },
                "attach": "iPhone",
            },
            "headerInfos": {
                "clientType": "#9.6.1#channel50#iPhone 14 Pro#",
                "code": "userLoginNormal",
                "shopId": "20002",
                "source": "110003",
                "sourcePassword": "Sid98s",
                "timestamp": ts,
                "userLoginName": phonenum,
            },
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json; charset=UTF-8",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
        }
        response = requests.post(
            "https://appgologin.189.cn:9031/login/client/userLoginNormal",
            headers=headers,
            json=body,
        )
        # print(response.text)
        data = response.json()
        return data

    def qry_important_data(self, token=""):
        token = token or self.login_info["token"]
        provinceCode = self.login_info["provinceCode"] or "600101"
        cityCode = self.login_info["cityCode"] or "8441900"
        ts = datetime.now().strftime("%Y%m%d%H%M00")
        body = {
            "content": {
                "fieldData": {
                    "provinceCode": provinceCode,
                    "cityCode": cityCode,
                    "shopId": "20002",
                    "isChinatelecom": "0",
                    "account": self.trans_phone(self.phonenum),
                },
                "attach": "test",
            },
            "headerInfos": {
                "clientType": "#9.6.1#channel50#iPhone X Plus#",
                "timestamp": ts,
                "code": "userFluxPackage",
                "shopId": "20002",
                "source": "110003",
                "sourcePassword": "Sid98s",
                "token": token,
                "userLoginName": self.phonenum,
            },
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json; charset=UTF-8",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
        }
        response = requests.post(
            "https://appfuwu.189.cn:9021/query/qryImportantData",
            headers=headers,
            json=body,
        )
        # print(response.text)
        data = response.json()
        return data

    def user_flux_package(self, token=""):
        token = token or self.login_info["token"]
        ts = datetime.now().strftime("%Y%m%d%H%M00")
        body = {
            "content": {
                "fieldData": {
                    "queryFlag": "0",
                    "accessAuth": "1",
                    "account": self.trans_phone(self.phonenum),
                },
                "attach": "test",
            },
            "headerInfos": {
                "clientType": "#9.6.1#channel50#iPhone X Plus#",
                "timestamp": ts,
                "code": "userFluxPackage",
                "shopId": "20002",
                "source": "110003",
                "sourcePassword": "Sid98s",
                "token": token,
                "userLoginName": self.phonenum,
            },
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json; charset=UTF-8",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
        }
        response = requests.post(
            "https://appfuwu.189.cn:9021/query/userFluxPackage",
            headers=headers,
            json=body,
        )
        # print(response.text)
        data = response.json()
        return data

    def to_summary(self, data, phonenum=""):
        if not data:
            return {}
        phonenum = phonenum or self.phonenum
        # 总流量
        flow_use = int(data["flowInfo"]["totalAmount"]["used"])
        flow_balance = int(data["flowInfo"]["totalAmount"]["balance"])
        flow_total = flow_use + flow_balance
        # 通用流量
        general_use = int(data["flowInfo"]["commonFlow"]["used"])
        general_balance = int(data["flowInfo"]["commonFlow"]["balance"])
        general_total = general_use + general_balance
        # 专用流量
        special_use = int(data["flowInfo"]["specialAmount"]["used"])
        special_balance = int(data["flowInfo"]["specialAmount"]["balance"])
        special_total = special_use + special_balance
        # 语音通话
        voice_usage = int(data["voiceInfo"]["voiceDataInfo"]["used"])
        voice_balance = int(data["voiceInfo"]["voiceDataInfo"]["balance"])
        voice_total = int(data["voiceInfo"]["voiceDataInfo"]["total"])
        # 余额
        balance = int(
            float(data["balanceInfo"]["indexBalanceDataInfo"]["balance"]) * 100
        )
        # 流量包列表
        flowItems = []
        flow_lists = data.get("flowInfo", {}).get("flowList", [])
        for item in flow_lists:
            if "流量" not in item["title"]:
                continue
            item_use = (
                self.convert_flow(item["leftTitleHh"], "KB")
                if "已用" in item["leftTitle"]
                else 0
            )
            item_balance = (
                self.convert_flow(item["rightTitleHh"], "KB")
                if "剩余" in item["rightTitle"]
                else 0
            )
            flowItems.append(
                {
                    "name": item["title"],
                    "use": item_use,
                    "balance": item_balance,
                    "total": item_use + item_balance,
                }
            )
        summary = {
            "phonenum": phonenum,
            "balance": balance,
            "voiceUsage": voice_usage,
            "voiceTotal": voice_total,
            "flowUse": flow_use,
            "flowTotal": flow_total,
            "generalUse": general_use,
            "generalTotal": general_total,
            "specialUse": special_use,
            "specialTotal": special_total,
            "createTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "flowItems": flowItems,
        }
        return summary

    def convert_flow(self, size_str, target_unit="KB", decimal=0):
        unit_dict = {"KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
        if isinstance(size_str, str):
            size, unit = float(size_str[:-2]), size_str[-2:]
        elif isinstance(size_str, (int, float)):
            size, unit = size_str, "KB"
        if unit in unit_dict or target_unit in unit_dict:
            return (
                int(size * unit_dict[unit] / unit_dict[target_unit])
                if decimal == 0
                else round(size * unit_dict[unit] / unit_dict[target_unit], decimal)
            )
        else:
            raise ValueError("Invalid unit")
