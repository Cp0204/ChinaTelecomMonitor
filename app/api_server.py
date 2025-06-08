#!/usr/bin/env python3
# _*_ coding:utf-8 _*_

import os
import sys
import json
from datetime import datetime
from flask import Flask, request, jsonify

# 导入父目录的依赖
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from telecom_class import Telecom

telecom = Telecom()

app = Flask(__name__)
app.json.ensure_ascii = False
app.json.sort_keys = False

# 登录信息存储文件
LOGIN_INFO_FILE = os.environ.get("CONFIG_PATH", "./config/login_info.json")


def load_login_info():
    """加载本地登录信息"""
    try:
        with open(LOGIN_INFO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_login_info(login_info):
    """保存登录信息到本地"""
    if not os.path.exists(os.path.dirname(LOGIN_INFO_FILE)):
        os.makedirs(os.path.dirname(LOGIN_INFO_FILE))
    with open(LOGIN_INFO_FILE, "w", encoding="utf-8") as f:
        json.dump(login_info, f, ensure_ascii=False, indent=2)


@app.route("/login", methods=["POST", "GET"])
def login():
    """登录接口"""
    if request.method == "POST":
        data = request.get_json() or {}
    else:
        data = request.args
    phonenum = data.get("phonenum")
    password = data.get("password")
    if not phonenum or not password:
        return jsonify({"message": "手机号和密码不能为空"}), 400
    elif whitelist_num := os.environ.get("WHITELIST_NUM"):
        if not phonenum in whitelist_num:
            return jsonify({"message": "手机号不在白名单"}), 400

    login_info = load_login_info()
    data = telecom.do_login(phonenum, password)
    if data.get("responseData").get("resultCode") == "0000":
        login_info[phonenum] = data["responseData"]["data"]["loginSuccessResult"]
        login_info[phonenum]["phonenum"] = phonenum
        login_info[phonenum]["password"] = password
        login_info[phonenum]["createTime"] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        save_login_info(login_info)
        return jsonify(data), 200
    else:
        return jsonify(data), 400


def query_data(query_func, **kwargs):
    """
    查询数据，如果本地没有登录信息或密码不匹配，则尝试登录后再查询
    """
    if request.method == "POST":
        data = request.get_json() or {}
    else:
        data = request.args
    phonenum = data.get("phonenum")
    password = data.get("password")
    # 检查登录信息，避免重复登录
    login_info = load_login_info()
    if phonenum in login_info and login_info[phonenum]["password"] == password:
        telecom.set_login_info(login_info[phonenum])
        data = query_func(**kwargs)
        if data.get("responseData"):
            return jsonify(data), 200
    # 重新登录
    login_data, status_code = login()
    login_data = json.loads(login_data.data)
    if status_code == 200:
        telecom.set_login_info(login_data["responseData"]["data"]["loginSuccessResult"])
        data = query_func(**kwargs)
        if data.get("responseData"):
            return jsonify(data), 200
        else:
            return jsonify(data), 400
    else:
        return jsonify(login_data), 400


@app.route("/qryImportantData", methods=["POST", "GET"])
def qry_important_data():
    """查询重要数据接口"""
    return query_data(telecom.qry_important_data)


@app.route("/userFluxPackage", methods=["POST", "GET"])
def user_flux_package():
    """查询流量包接口"""
    return query_data(telecom.user_flux_package)


@app.route("/qryShareUsage", methods=["POST", "GET"])
def qry_share_usage():
    """查询共享用量接口"""
    if request.method == "POST":
        data = request.get_json() or {}
    else:
        data = request.args
    return query_data(telecom.qry_share_usage, billing_cycle=data.get("billing_cycle"))


@app.route("/summary", methods=["POST", "GET"])
def summary():
    """查询重要数据简化接口"""
    important_data, status_code = query_data(telecom.qry_important_data)
    print(important_data.data)
    if status_code == 200:
        data = telecom.to_summary(
            json.loads(important_data.data)["responseData"]["data"]
        )
        return jsonify(data), 200


if __name__ == "__main__":
    app.run(debug=os.environ.get("DEBUG", True), host="0.0.0.0", port=10000)
