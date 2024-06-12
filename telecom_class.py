#!/usr/bin/env python3
# _*_ coding:utf-8 _*_

import base64
import requests
from datetime import datetime
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5


class Telecom:
    def __init__(self):
        self.login_info = {}
        self.phonenum = None
        self.password = None
        self.token = None
        self.client_type = "#9.6.1#channel50#iPhone 14 Pro#"
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json; charset=UTF-8",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "user-agent": "iPhone 14 Pro/9.6.1",
        }

    def set_login_info(self, login_info):
        self.login_info = login_info
        self.phonenum = login_info.get("phoneNbr", None)
        self.password = login_info.get("password", None)
        self.token = login_info.get("token", None)

    def trans_phone(self, phonenum):
        result = ""
        caesar_size = 2 if phonenum.startswith("1") else -2
        for char in phonenum:
            result += chr(ord(char) + caesar_size & 65535)
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
        enc_str = f"iPhone 14 13.2.3{phonenum}{phonenum}{ts}{password}0$$$0."
        body = {
            "content": {
                "fieldData": {
                    "accountType": "",
                    "authentication": password,
                    "deviceUid": f"3{phonenum}",
                    "isChinatelecom": "0",
                    "loginAuthCipherAsymmertric": self.encrypt(enc_str),
                    "loginType": "4",
                    "phoneNum": self.trans_phone(phonenum),
                    "systemVersion": "13.2.3",
                },
                "attach": "iPhone",
            },
            "headerInfos": {
                "code": "userLoginNormal",
                "clientType": self.client_type,
                "timestamp": ts,
                "shopId": "20002",
                "source": "110003",
                "sourcePassword": "Sid98s",
                "userLoginName": phonenum,
            },
        }
        response = requests.post(
            "https://appgologin.189.cn:9031/login/client/userLoginNormal",
            headers=self.headers,
            json=body,
        )
        return response.json()

    def qry_important_data(self, **kwargs):
        ts = datetime.now().strftime("%Y%m%d%H%M00")
        body = {
            "content": {
                "fieldData": {
                    "provinceCode": self.login_info["provinceCode"] or "600101",
                    "cityCode": self.login_info["cityCode"] or "8441900",
                    "shopId": "20002",
                    "isChinatelecom": "0",
                    "account": self.trans_phone(self.phonenum),
                },
                "attach": "test",
            },
            "headerInfos": {
                "code": "userFluxPackage",
                "clientType": self.client_type,
                "timestamp": ts,
                "shopId": "20002",
                "source": "110003",
                "sourcePassword": "Sid98s",
                "userLoginName": self.phonenum,
                "token": kwargs.get("token") or self.token,
            },
        }
        response = requests.post(
            "https://appfuwu.189.cn:9021/query/qryImportantData",
            headers=self.headers,
            json=body,
        )
        # print(response.text)
        return response.json()

    def user_flux_package(self, **kwargs):
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
                "code": "userFluxPackage",
                "clientType": self.client_type,
                "timestamp": ts,
                "shopId": "20002",
                "source": "110003",
                "sourcePassword": "Sid98s",
                "userLoginName": self.phonenum,
                "token": kwargs.get("token") or self.token,
            },
        }
        response = requests.post(
            "https://appfuwu.189.cn:9021/query/userFluxPackage",
            headers=self.headers,
            json=body,
        )
        # print(response.text)
        return response.json()

    def qry_share_usage(self, **kwargs):
        billing_cycle = kwargs.get("billing_cycle") or datetime.now().strftime("%Y%m")
        ts = datetime.now().strftime("%Y%m%d%H%M00")
        body = {
            "content": {
                "attach": "test",
                "fieldData": {
                    "billingCycle": billing_cycle,
                    "account": self.trans_phone(self.phonenum),
                },
            },
            "headerInfos": {
                "code": "qryShareUsage",
                "clientType": self.client_type,
                "timestamp": ts,
                "shopId": "20002",
                "source": "110003",
                "sourcePassword": "Sid98s",
                "userLoginName": self.phonenum,
                "token": kwargs.get("token") or self.token,
            },
        }
        response = requests.post(
            "https://appfuwu.189.cn:9021/query/qryShareUsage",
            headers=self.headers,
            json=body,
        )
        data = response.json()
        # 返回的号码字段加密，需做解密转换
        if data.get("responseData").get("data").get("sharePhoneBeans"):
            for item in data["responseData"]["data"]["sharePhoneBeans"]:
                item["sharePhoneNum"] = self.trans_phone(item["sharePhoneNum"])
            for share_type in data["responseData"]["data"]["shareTypeBeans"]:
                for share_info in share_type["shareUsageInfos"]:
                    for share_amount in share_info["shareUsageAmounts"]:
                        share_amount["phoneNum"] = self.trans_phone(
                            share_amount["phoneNum"]
                        )
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
        common_use = int(data["flowInfo"]["commonFlow"]["used"])
        common_balance = int(data["flowInfo"]["commonFlow"]["balance"])
        common_total = common_use + common_balance
        # 专用流量
        special_use = int(data["flowInfo"]["specialAmount"]["used"]) if data["flowInfo"].get("specialAmount") else 0
        special_balance = int(data["flowInfo"]["specialAmount"]["balance"])  if data["flowInfo"].get("specialAmount") else 0
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
            "commonUse": common_use,
            "commonTotal": common_total,
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
