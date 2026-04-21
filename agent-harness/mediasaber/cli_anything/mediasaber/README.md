# cli-anything-mediasaber

Media Saber 后端的 `cli-anything` harness，面向服务运维、登录鉴权、常用管理接口和通用 REST 调用。

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
cli-anything-mediasaber --json directory match --tmdb-id 1399 --media-type tv
cli-anything-mediasaber --json media search "The Last of Us" --media-source 1
cli-anything-mediasaber --json api GET /api/v1/site/options
```

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
