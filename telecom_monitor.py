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
    os.system("pip3 install pycryptodome requests &> /dev/null")
    from telecom_class import Telecom


CONFIG_DATA = {}
NOTIFYS = []
CONFIG_PATH = sys.argv[1] if len(sys.argv) > 1 else "telecom_config.json"


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
    # 读取配置
    if os.path.exists(CONFIG_PATH):
        print(f"⚙️ 正从 {CONFIG_PATH} 文件中读取配置")
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            CONFIG_DATA = json.load(file)
    if not CONFIG_DATA.get("user"):
        CONFIG_DATA["user"] = {}

    telecom = Telecom()

    def auto_login():
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
        if not phonenum.isdigit():
            exit("自动登录：手机号设置错误，退出")
        else:
            print(f"自动登录：{phonenum}")
        login_failure_count = CONFIG_DATA.get("user", {}).get("loginFailureCount", 0)
        if login_failure_count < 5:
            data = telecom.do_login(phonenum, password)
            if data.get("responseData").get("resultCode") == "0000":
                print(f"自动登录：成功")
                login_info = data["responseData"]["data"]["loginSuccessResult"]
                login_info["createTime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                CONFIG_DATA["login_info"] = login_info
                telecom.set_login_info(login_info)
            else:
                login_failure_count += 1
                CONFIG_DATA["user"]["loginFailureCount"] = login_failure_count
                update_config()
                add_notify(f"自动登录：记录失败{login_failure_count}次，程序退出")
                exit(data)
        else:
            print(f"自动登录：记录失败{login_failure_count}次，跳过执行")
            exit()

    # 读取缓存Token
    login_info = CONFIG_DATA.get("login_info", {})
    if login_info:
        print(f"尝试使用缓存登录：{login_info['phoneNbr']}")
        telecom.set_login_info(login_info)
    else:
        auto_login()

    # 获取主要信息
    important_data = telecom.qry_important_data()
    if important_data.get("responseData"):
        print(f"获取主要信息：成功")
    elif important_data["headerInfos"]["code"] == "X201":
        print(f"获取主要信息：失败 {important_data['headerInfos']['reason']}")
        auto_login()
        important_data = telecom.qry_important_data()

    # 简化主要信息
    summary = telecom.to_summary(important_data["responseData"]["data"])
    if summary:
        print(f"简化主要信息：{summary}")
        CONFIG_DATA["summary"] = summary

    # 获取流量包明细
    flux_package_str = ""
    user_flux_package = telecom.user_flux_package()
    if user_flux_package:
        print("获取流量包明细：成功")
        packages = user_flux_package["responseData"]["data"]["productOFFRatable"][
            "ratableResourcePackages"
        ]
        for package in packages:
            package_icon = (
                "🇨🇳"
                if "国内" in package["title"]
                else "📺" if "专用" in package["title"] else "🌎"
            )
            flux_package_str += f"\n{package_icon}{package['title']}\n"
            for product in package["productInfos"]:
                flux_package_str += f"""🔹[{product['title']}]{product['leftTitle']}{product['leftHighlight']}{product['rightCommon']}\n"""
    # 流量字符串
    common_str = (
        f"{telecom.convert_flow(summary['commonUse'],'GB',2)} / {telecom.convert_flow(summary['commonTotal'],'GB',2)} GB 🟢"
        if summary["flowOver"] == 0
        else f"-{telecom.convert_flow(summary['flowOver'],'GB',2)} / {telecom.convert_flow(summary['commonTotal'],'GB',2)} GB 🔴"
    )
    special_str = (
        f"{telecom.convert_flow(summary['specialUse'], 'GB', 2)} / {telecom.convert_flow(summary['specialTotal'], 'GB', 2)} GB"
        if summary["specialTotal"] > 0
        else ""
    )
    # 添加通知
    add_notify(
        f"""
📱 手机：{summary['phonenum']}
💰 余额：{round(summary['balance']/100,2)}
📞 通话：{summary['voiceUsage']}{f" / {summary['voiceTotal']}" if summary['voiceTotal']>0 else ""} min
🌐 总流量
  - 通用：{common_str}{f"{chr(10)}  - 专用：{special_str}" if special_str else ""}

【流量包明细】

{flux_package_str.strip()}

查询时间：{summary['createTime']}
""".strip()
    )

    # 通知
    if NOTIFYS:
        notify_body = "\n".join(NOTIFYS)
        print(f"===============推送通知===============")
        send_notify("【电信套餐用量监控】", notify_body)
        print()

    update_config()


def update_config():
    # 更新配置
    with open(CONFIG_PATH, "w", encoding="utf-8") as file:
        json.dump(CONFIG_DATA, file, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
