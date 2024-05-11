# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# Repo: https://github.com/Cp0204/ChinaTelecomMonitor
# ConfigFile: telecom_config.json
# Modify: 2024-05-11

"""
任务名称
name: 电信套餐用量监控
定时规则
cron: 0 20 * * *
"""

import os
import sys
import json
from datetime import datetime

# 兼容青龙
try:
    from telecom_class import Telecom
except:
    print("正在尝试自动安装依赖...")
    os.system("pip3 install pycryptodome &> /dev/null")
    from telecom_class import Telecom


CONFIG_DATA = {}
NOTIFYS = []


# 发送通知消息
def send_notify(title, body):
    try:
        # 导入通知模块
        import notify

        # 如未配置 push_config 则使用青龙环境通知设置
        if CONFIG_DATA.get("push_config"):
            CONFIG_DATA["push_config"]["CONSOLE"] = True
            notify.push_config = CONFIG_DATA["push_config"]
        notify.send(title, body)
    except Exception as e:
        if e:
            print("发送通知消息失败！")


# 添加消息
def add_notify(text):
    global NOTIFYS
    NOTIFYS.append(text)
    print("📢", text)
    return text


def main():
    global CONFIG_DATA
    start_time = datetime.now()
    print(f"===============程序开始===============")
    print(f"⏰ 执行时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    # 读取启动参数
    config_path = sys.argv[1] if len(sys.argv) > 1 else "telecom_config.json"
    # 读取配置
    if os.path.exists(config_path):
        print(f"⚙️ 正从 {config_path} 文件中读取配置")
        with open(config_path, "r", encoding="utf-8") as file:
            CONFIG_DATA = json.load(file)

    telecom = Telecom()

    def auto_login():
        print(f"开始自动登录")
        if TELECOM_USER := os.environ.get("TELECOM_USER"):
            phonenum, password = (
                TELECOM_USER[:11],
                TELECOM_USER[11:],
            )
        elif TELECOM_USER := CONFIG_DATA.get("user", {}):
            phonenum, password = (
                TELECOM_USER.get("phonenum", ""),
                TELECOM_USER.get("password", ""),
            )
        else:
            exit("自动登录：未设置账号密码，退出")
        if not phonenum.isdigit:
            exit("自动登录：手机号设置错误，退出")
        else:
            print(phonenum, password)
        login_failure_count = CONFIG_DATA.get("user", {}).get("loginFailureCount", 0)
        if login_failure_count < 5:
            login_info = telecom.do_login(phonenum, password)
            if login_info:
                print(f"自动登录：成功")
                CONFIG_DATA["login_info"] = login_info
                telecom.set_login_info(login_info)
            else:
                CONFIG_DATA["user"]["loginFailureCount"] = login_failure_count + 1
        else:
            print(f"自动登录：已失败{login_failure_count}次，跳过执行")

    # 读取缓存Token
    login_info = CONFIG_DATA.get("login_info", {})
    if login_info:
        print(f"尝试使用缓存登录：{login_info['phoneNbr']}")
        telecom.set_login_info(login_info)
    else:
        auto_login()

    # 获取信息
    data = telecom.do_query()
    if data["responseData"]:
        print(f"获取信息：成功")
    elif data["headerInfos"]["code"] == "X201":
        print(f"获取信息：失败 {data['headerInfos']['reason']}")
        auto_login()
        data = telecom.do_query()

    # 提取简化信息
    summary = telecom.to_summary(data["responseData"]["data"])
    if summary:
        print("简化信息：", summary)
        CONFIG_DATA["summary"] = summary

    add_notify(
        f"""
📱 手机：{summary['phonenum']}
💰 余额：{summary['balance']}
📞 通话：{summary['voiceUsage']}/{summary['voiceTotal']}min
🌐 流量
  - 通用：{telecom.convert_flow(summary['generalUse'],"GB")}/{telecom.convert_flow(summary['generalTotal'],"GB")}GB
  - 专用：{telecom.convert_flow(summary['specialUse'],"GB")}/{telecom.convert_flow(summary['specialTotal'],"GB")}GB
""".strip()
    )

    # 通知
    if NOTIFYS:
        notify_body = "\n".join(NOTIFYS)
        print(f"===============推送通知===============")
        send_notify("【电信套餐用量监控】", notify_body)
        print()

    # 更新配置
    with open(config_path, "w", encoding="utf-8") as file:
        json.dump(CONFIG_DATA, file, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
