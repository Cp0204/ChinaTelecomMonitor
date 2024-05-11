# ChinaTelecomMonitor

中国电信 话费、通话、流量 套餐用量监控。

本脚本是部署在服务器（或x86软路由等设备）使用接口模拟登录获取Token，定时获取电信手机话费、通话、流量使用情况，推送到各种通知渠道提醒。

## 特性

- [x] 兼容青龙
- [x] 本地保存Token，有效期内不重复登录
- [x] 支持通过 json push_config 字段独立配置通知渠道
- [ ] Docker 独立部署，开放查询 API

## 青龙部署

拉库命令：

```
ql repo https://github.com/Cp0204/ChinaTelecomMonitor.git "telecom_monitor" "" "telecom_class"
```

| 环境变量       | 示例                  | 备注                           |
| -------------- | --------------------- | ------------------------------ |
| `TELECOM_USER` | `18912345678password` | 手机号密码直接拼接，会自动截取 |


## 感谢

本项目大量参考前人的代码，在此表示感谢！

- [ChinaTelecomMonitor](https://github.com/LambdaExpression/ChinaTelecomMonitor) : go 语言的实现
- [boxjs](https://github.com/gsons/boxjs) : 感谢开源提供的电信接口