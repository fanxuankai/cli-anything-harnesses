---
name: cli-anything-mediasaber
version: 1.0.0
description: CLI harness for Media Saber backend management and operations
entry_point: cli-anything-mediasaber
install: pip install cli-anything-mediasaber
python: ">=3.9"
dependencies:
  - click>=8.0
  - requests>=2.28
  - PyYAML>=6.0
---

# cli-anything-mediasaber

Media Saber 后端的 CLI harness，用于连接真实 Media Saber REST API，完成登录、系统状态查询、下载器与目录管理、站点查询、媒体搜索，以及通用 API 调用。

## 连接配置

优先级：`--url/--token/--api-key/--source` > 环境变量 `MSB_URL/MSB_TOKEN/MSB_API_KEY/MSB_SOURCE` > `~/.mediasaber-cli.yaml` > 已保存 profile

```bash
export MSB_URL=http://127.0.0.1:8899
export MSB_TOKEN=your-user-token

cli-anything-mediasaber session set \
  --url http://127.0.0.1:8899 \
  --source /Users/fanxuankai/GolandProjects/media-saber-back-end
```

## 命令组

### session

| 命令 | 说明 |
|------|------|
| `session show` | 查看当前连接状态、profile、撤销栈 |
| `session set` | 更新本地连接参数 |
| `session clear-token` | 清除本地 token |
| `session save-profile NAME` | 保存当前会话为 profile |
| `session use-profile NAME` | 应用 profile |
| `session undo` | 撤销最近一次本地会话变更 |
| `session redo` | 重做最近一次本地会话变更 |

### server

| 命令 | 说明 |
|------|------|
| `server ping` | 检查服务是否可达 |
| `server start` | 用 `go run mediasaber.go` 启动真实后端 |
| `server stop` | 停止由 harness 启动的后端 |
| `server backend-status` | 查看本地进程状态 |
| `server logs` | 查看本地包装日志 |

### auth

| 命令 | 说明 |
|------|------|
| `auth init-admin` | 查询是否已初始化管理员 |
| `auth login USER PASSWORD` | 登录并保存 token |
| `auth whoami` | 获取当前用户信息 |
| `auth logout` | 退出登录并清除本地 token |
| `auth tokens` | 获取当前用户 token 列表 |

### system

| 命令 | 说明 |
|------|------|
| `system status` | 查看 CPU / 内存 / goroutine 状态 |
| `system space` | 查询空间信息 |
| `system basic-config` | 获取完整基础配置 |
| `system basic-config-part KEY...` | 获取部分基础配置 |
| `system task-schedule` | 查看定时任务列表 |
| `system upgrade-version` | 查询升级信息 |
| `system path-ls PATH` | 浏览服务端路径 |

### downloader / directory

| 命令 | 说明 |
|------|------|
| `downloader list` | 列出下载器 |
| `downloader detail ID` | 查看下载器详情 |
| `downloader types` | 获取下载器类型 |
| `downloader delete-qb-tags` | 删除 qb 标签 |
| `directory list` | 查询目录列表 |
| `directory match` | 根据 `tmdbId/mediaType` 匹配目录 |
| `directory tags` | 列出目录标签 |
| `directory mkdir ID` | 为指定目录记录创建目录 |
| `directory categories` | 查询目录分类 |
| `directory subcategory-options` | 查询子分类选项 |
| `directory subcategory-list` | 查询子分类列表 |

### site / media

| 命令 | 说明 |
|------|------|
| `site list` | 列出站点 |
| `site options` | 获取站点选项 |
| `site rss ID` | 获取站点 RSS |
| `site rss-torrents ID` | 获取 RSS 种子 |
| `media sources` | 获取媒体来源 |
| `media search KEYWORD` | 媒体搜索 |
| `media search-all KEYWORD` | 聚合媒体搜索 |
| `media autosuggest QUERY` | 自动补全 |

### api

| 命令 | 说明 |
|------|------|
| `api METHOD PATH` | 通用 REST 调用，可带 query/body |

## 全局选项

| 选项 | 说明 |
|------|------|
| `--url` | 服务地址 |
| `--token` | 用户 token |
| `--api-key` | 用户 apiKey |
| `--source` | Media Saber 源码目录 |
| `--profile` | 加载本地 profile |
| `--json` | JSON 输出 |
| `--raw` | `api` 命令输出完整 envelope |
| `--repl` | 进入交互式 REPL |

## Agent 使用示例

```bash
# 初始化本地会话
cli-anything-mediasaber session set \
  --url http://127.0.0.1:8899 \
  --source /Users/fanxuankai/GolandProjects/media-saber-back-end

# 登录并保存 token
cli-anything-mediasaber auth login admin secret

# 查看系统状态
cli-anything-mediasaber --json system status

# 查询下载器
cli-anything-mediasaber --json downloader list

# 目录匹配
cli-anything-mediasaber --json directory match --tmdb-id 1399 --media-type tv

# 媒体搜索
cli-anything-mediasaber --json media search "The Last of Us"

# 通用 API 调用
cli-anything-mediasaber --json api GET /api/v1/site/options
```
