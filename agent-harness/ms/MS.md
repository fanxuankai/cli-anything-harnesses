# Media Saber CLI Harness - SOP

## 软件概述

`ms` 是 Media Saber 后端的最小可用 CLI harness。

首版只做三件事：

- 管理连接配置
- 提供稳定的通用 HTTP 客户端
- 通过 `request` 命令调用任意已知 API 路径

当前阶段不自动生成命令，不包装业务模块，只把 `/Users/fanxuankai/GolandProjects/media-saber-back-end/api` 中的接口定义整理成后续可扩展的结构认知。

## API 结构观察

Media Saber 的 `.api` 文件采用 go-zero `@server` 结构，主要由 `group`、`prefix`、`middleware` 和 handler 路由组成。

已确认的主模块包括：

- `system`：系统状态、用户、配置、日志、消息、插件、工具、Webhook
- `media`：媒体检索、主题、人物、推荐、重命名、刮削、历史
- `site`：站点、公告、消息、请求历史、资源
- `download`：下载器、下载参数、目录、历史
- `torrent`：搜索、匹配、分析、排序
- `message`：消息通道、推送、事件
- `cloudStorage`：驱动、文件系统、任务、开放接口

示例路由形态：

- `GET /api/v1/system/status`
- `GET /api/v1/userApiKey/list`
- `POST /api/v1/media/detail`

## 鉴权观察

后端中 `TokenAuthNoRole` 和 `TokenAuthAdminRole` 中间件都支持 API Key 鉴权。

当前已确认兼容的传递方式：

- `Authorization: Bearer <apikey>`
- `apiKey` header
- `apiKey` query 参数

首版客户端固定使用 `Authorization: Bearer <apikey>`，这是最稳定也最通用的形式。

## 响应结构观察

普通业务接口大多返回统一结构：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

也存在少量非统一响应，例如纯字符串、布尔值或原始内容。客户端需要同时保留：

- 标准响应的 `code/message/data`
- 原始响应体

## 首版 CLI 设计

### 全局参数

- `--url/-u`
- `--apikey/-k`
- `--json`
- `--repl`

### 命令

- `config save-connection`
- `config show-connection`
- `media search`
- `subscribe add`
- `request METHOD PATH`

### media search

统一媒体搜索命令固定调用 `/api/v1/media/search`。

CLI 侧当前只开放两个来源映射：

- `douban` -> `100`
- `tmdb` -> `200`

之所以不直接对接 `/api/v1/doubanSubject/search` 或 `/api/v1/searchTmdb/...`，是因为那两类接口返回的是更专门的数据结构，不适合作为一个统一的“媒体搜索”命令入口。

### subscribe

默认订阅配置接口：

- `GET /api/v1/subscribeDefaultConfig/detail/:type`

订阅新增接口：

- `POST /api/v1/subscribe/save`

其中 `:type` 的真实取值就是：

- `movie`
- `tv`

后端公开 API 并没有一个“按默认配置新增订阅”的 HTTP 端点；真正会自动套用默认配置的 `SaveDefault(...)` 只在服务层内部使用。

因此 CLI 的 `subscribe add` 需要采用两步法：

1. 先读取 `movie` / `tv` 默认订阅配置
2. 在客户端侧合并必要默认字段，再提交到 `/api/v1/subscribe/save`

默认配置读取仅作为 `subscribe add` 的内部实现细节，不单独暴露成 CLI 子命令。

当前 `subscribe add` 只做最小新增：

- movie: `name` + `year`
- tv: `name` + `year` + `season`

### REPL

无子命令且当前终端可交互时，默认进入 REPL。

REPL 只做基础命令调度，不在首版引入自动补全、历史文件或业务态会话。

## 后续扩展方向

当通用客户端稳定后，可以按 `.api` 分组逐步增加显式命令面，例如：

- `system status`
- `media search`
- `site list`
- `download list`

扩展时优先遵循：

- 保留 `request` 作为兜底入口
- 继续兼容 `--json`
- 复用同一连接配置和响应解包逻辑
