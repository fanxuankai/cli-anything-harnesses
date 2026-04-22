# cli-anything-mediasaber

Media Saber 的 `cli-anything` harness，覆盖服务运维、登录鉴权、系统管理、站点/订阅/消息/种子/云存储工作流，以及通用 REST 调用。

## 安装

```bash
pip install cli-anything-mediasaber
```

本地开发安装：

```bash
cd agent-harness/mediasaber
pip install -e .
```

## 连接方式

优先级从高到低：

1. 命令行参数 `--url --token --api-key --source`
2. 环境变量 `MSB_URL MSB_TOKEN MSB_API_KEY MSB_SOURCE`
3. `~/.mediasaber-cli.yaml`
4. `session` 命令保存的 profile

用户 token 走原始 `Authorization` 头；apiKey 走 `apiKey` 头，适配 Media Saber 当前中间件逻辑。

## REPL

在交互式终端里直接执行命令会进入 REPL：

```bash
cli-anything-mediasaber --url http://127.0.0.1:8899
```

也可以显式指定：

```bash
cli-anything-mediasaber --repl
```

## 常用命令

```bash
cli-anything-mediasaber --url http://127.0.0.1:8899 server ping
cli-anything-mediasaber --url http://127.0.0.1:8899 auth init-admin
cli-anything-mediasaber --url http://127.0.0.1:8899 auth login admin secret
cli-anything-mediasaber --json system status
cli-anything-mediasaber --json downloader list
cli-anything-mediasaber --json cloud-storage list
cli-anything-mediasaber --json torrent download-url 1
cli-anything-mediasaber --json subscribe page
cli-anything-mediasaber --json message send --body '{"title":"测试","content":"hello"}'
cli-anything-mediasaber --json directory match --tmdb-id 1399 --media-type tv
cli-anything-mediasaber --json media search "The Last of Us" --media-source 1
cli-anything-mediasaber --json ai models
cli-anything-mediasaber --json api GET /api/v1/site/options
```

## 命令覆盖

当前已提供的一层命令组包括：

- `system`、`user`、`network-ping`、`user-api-key`、`dict`、`system-message`、`dynamic-form`、`logs`、`plugins`、`plugins-instance`、`system-tools`
- `site`、`site-data`、`site-notice`、`site-message`、`site-resource`、`site-sign-in`、`site-request-history`
- `downloader`、`download-params`、`download`、`directory`、`directory-category`、`directory-subcategory`
- `cloud-storage`、`cloud-storage-driver`、`cloud-storage-fs`、`cloud-storage-task`、`cloud-storage-transfer`、`generate-strm`、`open115`、`u115`、`open123`、`proxy115`
- `media`、`media-recommend`、`media-person`、`media-subject`、`word-group`、`word-unit`、`filter-rule`、`filter-rule-detail`、`path-sync`、`path-sync-history`、`media-server`、`media-server-sync`、`search-tmdb`、`rename-preview`、`scrape`、`calendar`、`transfer-fail`、`transfer-history`、`douban-subject`、`douban`
- `torrent`、`torrent-search`、`torrent-search-task`、`torrent-search-history`、`torrent-match`、`torrent-sort`
- `subscribe`、`subscribe-default-config`、`subscribe-calendar`
- `message`、`message-channel`、`message-wechat`
- `service-ocr`、`pansou`、`hdhive`、`ai`

被动回调类接口，如 webhook、SSE 和图片代理，没有单独封装成一层命令组；这些场景通过通用 `api` 命令访问。

如果只想快速查看当前版本的完整命令树：

```bash
cli-anything-mediasaber --help
cli-anything-mediasaber cloud-storage --help
cli-anything-mediasaber torrent-search --help
```

## 请求约定

- 大多数写操作统一支持 `--body` 或 `--body-file` 传 JSON。
- 大多数读操作支持显式常用参数，并保留 `--query key=value` 作为补充。
- 许多动态注册的资源命令还支持 `--timeout` 覆盖默认超时。
- 原始内容响应支持 `-o/--output` 保存到文件，例如 `cloud-storage strm302`。
- 通用 `api` 命令支持 `--header`、`--form`、`--file`、`--response-mode` 和 `--output`。

## 会话状态

`session` 命令会把连接信息持久化到本地：

```bash
cli-anything-mediasaber session set --url http://127.0.0.1:8899 --source /path/to/media-saber-back-end
cli-anything-mediasaber session save-profile local-dev
cli-anything-mediasaber session use-profile local-dev
cli-anything-mediasaber session undo
cli-anything-mediasaber session redo
```

注意：

- undo/redo 只作用于本地会话配置，不会回滚服务端数据
- 登录成功后默认会把 token 写入本地配置

## 后端进程包装

如果机器上已经具备 Go、数据库、Redis 和 Media Saber 所需配置，可以直接通过 harness 拉起真实后端：

```bash
cli-anything-mediasaber session set --source /Users/fanxuankai/GolandProjects/media-saber-back-end
cli-anything-mediasaber server start
cli-anything-mediasaber server backend-status
cli-anything-mediasaber server logs
cli-anything-mediasaber server stop
```

## 测试

```bash
cd agent-harness/mediasaber
pytest cli_anything/mediasaber/tests/test_core.py -v
pytest cli_anything/mediasaber/tests/test_full_e2e.py -v
```
