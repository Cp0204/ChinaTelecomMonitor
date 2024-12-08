# ChinaTelecomMonitor

中国电信 话费、通话、流量 套餐用量监控。

本项目是部署在服务器（或x86软路由等设备）使用接口模拟登录，定时获取电信手机话费、通话、流量使用情况，推送到各种通知渠道提醒。

## 特性

- [x] 支持青龙
- [x] 支持通过 json push_config 字段独立配置通知渠道
- [x] 本地保存登录 token ，有效期内不重复登录
- [x] Docker 独立部署 API 查询服务

## 使用案例

- [提供一个ios的自制UI面板](https://github.com/Cp0204/ChinaTelecomMonitor/issues/18) --- By: LRZ9712

## 部署

### 青龙监控

拉库命令：

```
ql repo https://github.com/Cp0204/ChinaTelecomMonitor.git "telecom_monitor" "" "telecom_class|notify"
```

| 环境变量       | 示例                  | 备注                           |
| -------------- | --------------------- | ------------------------------ |
| `TELECOM_USER` | `18912345678password` | 手机号密码直接拼接，会自动截取 |

### Docker API 服务

注意：Docker 部署的是 API 服务，没有监控提醒功能，主要是用于第三方（如 HomeAssistant 等）获取信息，数据原样返回。

```shell
docker run -d \
  --name china-telecom-monitor \
  -p 10000:10000 \
  -v ./china-telecom-monitor/config:/app/config \
  -v /etc/localtime:/etc/localtime \
  -e WHITELIST_NUM= \
  --network bridge \
  --restart unless-stopped \
  cp0204/chinatelecommonitor:main
```

| 环境变量        | 示例                      | 备注         |
| --------------- | ------------------------- | ------------ |
| `WHITELIST_NUM` | `18912345678,13312345678` | 手机号白名单 |

#### 接口URL

- `http://127.0.0.1:10000/login`

  登录，返回用户信息，token长期有效，用以下次请求数据

- `http://127.0.0.1:10000/qryImportantData`

  返回主要信息，总用量 话费、通话、流量 等

- `http://127.0.0.1:10000/userFluxPackage`

  返回流量包明细

- `http://127.0.0.1:10000/qryShareUsage`

  返回共享套餐各号码用量

- `http://127.0.0.1:10000/summary`

  `/qryImportantData` 的数据简化接口，非原样返回，简化后返回格式：

```json
{
  "phonenum": "18912345678", // 手机号码
  "balance": 0,              // 账户余额（分）
  "voiceUsage": 39,          // 语音通话已使用时长（分钟）
  "voiceTotal": 2250,        // 语音通话总时长（分钟）
  "flowUse": 7366923,        // 总流量已使用量（KB）
  "flowTotal": 7366923,      // 总流量总量（KB）
  "flowOver": 222222,        // 总流量超量（KB）
  "commonUse": 7273962,      // 通用流量已使用量（KB）
  "commonTotal": 25550446,   // 通用流量总量（KB）
  "commonOver": 222222,      // 通用流量超量（KB）
  "specialUse": 92961,       // 专用流量已使用量（KB）
  "specialTotal": 215265280, // 专用流量总量（KB）
  "createTime": "2024-05-12 14:13:28", // 数据创建时间
  "flowItems": [             // 流量类型列表
    {
      "name": "国内通用流量(达量降速)", // 流量类型名称
      "use": 10241024,           // 流量包已使用量（KB）
      "balance": 0,              // 流量包剩余量（KB），当为负值时则是超流量
      "total": 10241024          // 流量包总量（KB）
    },
    {
      "name": "国内通用流量(非畅享)",
      "use": 1,
      "balance": 10241023,
      "total": 10241024
    },
    {
      "name": "专用流量",
      "use": 1,
      "balance": 10241023,
      "total": 10241024
    }
  ]
}
```

接口均支持 POST 和 GET 方法，如 GET ：

```
http://127.0.0.1:10000/summary?phonenum=18912345678&password=123456
```

POST 时 Body 须为 json 数据，如：

```bash
curl --request POST \
  --url http://127.0.0.1:10000/summary \
  --header 'Content-Type: application/json' \
  --data '{"phonenum": "18912345678","password": "123456"}'
```

> [!NOTE]
> 登录成功后，会在 config/login_info.json 文件**记录账号敏感信息**。程序请求数据将先尝试用记录的 token 获取，避免重复登录。

## 感谢

本项目大量参考其他项目的代码，在此表示感谢！

- [ChinaTelecomMonitor](https://github.com/LambdaExpression/ChinaTelecomMonitor) : go 语言的实现
- [boxjs](https://github.com/gsons/boxjs) : 感谢开源提供的电信接口
