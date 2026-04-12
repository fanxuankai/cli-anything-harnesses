---
name: cli-anything-cliproxyapi
version: 1.0.0
description: CLI harness for CLIProxyAPI proxy server management
entry_point: cli-anything-cliproxyapi
install: pip install cli-anything-cliproxyapi
python: ">=3.9"
dependencies:
  - click>=8.0
  - requests>=2.28
  - rich>=13.0
  - PyYAML>=6.0
---

# cli-anything-cliproxyapi

CLI 管理工具，用于通过 Management API 管理 CLIProxyAPI 代理服务器。

## 连接配置

优先级：`--url/--key` > 环境变量 `CPA_URL/CPA_KEY` > `~/.cliproxyapi-cli.yaml`

```bash
# 环境变量方式
export CPA_URL=http://127.0.0.1:8317
export CPA_KEY=your-management-key

# 或保存到配置文件
cli-anything-cliproxyapi config save-connection --url http://127.0.0.1:8317 --key your-key
```

## 命令组

### server - 服务器管理

| 命令 | 说明 |
|------|------|
| `server status` | 健康检查 |
| `server version` | 获取最新版本 |

### config - 配置管理

| 命令 | 说明 |
|------|------|
| `config get` | 获取当前配置 |
| `config get-yaml` | 获取 YAML 配置 |
| `config set-yaml [YAML]` | 更新 YAML 配置 |
| `config debug [true/false]` | 获取/设置调试模式 |
| `config proxy-url [URL]` | 获取/设置/删除代理 URL |
| `config routing [strategy]` | 获取/设置路由策略 |
| `config retry [N]` | 获取/设置重试次数 |
| `config ws-auth [true/false]` | WebSocket 认证 |
| `config save-connection` | 保存连接参数 |

### auth - 认证文件管理

| 命令 | 说明 |
|------|------|
| `auth list` | 列出认证文件 |
| `auth codex-quota` | 获取已启用 Codex 凭证额度 |
| `auth upload FILENAME` | 上传认证文件 |
| `auth download FILENAME` | 下载认证文件 |
| `auth delete FILENAME` | 删除认证文件 |
| `auth status FILENAME BOOL` | 启用/禁用 |
| `auth fields FILENAME --set K V` | 更新字段 |
| `auth models` | 关联模型 |
| `auth definitions CHANNEL` | 模型定义 |
| `auth vertex-import KEY_JSON` | 导入 Vertex |

### oauth - OAuth 登录

| 命令 | 说明 |
|------|------|
| `oauth login PROVIDER` | 发起 OAuth (anthropic/codex/gemini/antigravity/qwen/kimi/iflow) |
| `oauth iflow-cookie COOKIE` | iFlow Cookie 登录 |
| `oauth callback` | 处理回调 |
| `oauth status SESSION_ID` | 查看状态 |

### keys - API 密钥管理

| 命令 | 说明 |
|------|------|
| `keys list` | 列出 API 密钥 |
| `keys add KEY` | 添加密钥 |
| `keys delete KEY` | 删除密钥 |
| `keys gemini list/add/delete` | Gemini 密钥 |
| `keys claude list/add/delete` | Claude 密钥 |
| `keys codex list/add/delete` | Codex 密钥 |
| `keys openai-compat list/add/delete` | OpenAI 兼容 |
| `keys vertex list/add/delete` | Vertex 密钥 |

### models - 模型管理

| 命令 | 说明 |
|------|------|
| `models list --api-key KEY` | 列出可用模型 |
| `models aliases` | OAuth 模型别名 |
| `models excluded` | OAuth 排除模型 |

### usage - 使用统计

| 命令 | 说明 |
|------|------|
| `usage stats` | 获取统计 |
| `usage export` | 导出统计 |
| `usage import DATA` | 导入统计 |

### logs - 日志管理

| 命令 | 说明 |
|------|------|
| `logs list --lines N` | 查看日志 |
| `logs clear` | 清除日志 |
| `logs request [bool]` | 请求日志开关 |
| `logs errors [--download NAME]` | 错误日志 |
| `logs by-id ID` | 按 ID 查看 |

### amp - Amp 集成

| 命令 | 说明 |
|------|------|
| `amp config` | 查看 Amp 配置 |
| `amp upstream-url [URL]` | 上游 URL |
| `amp upstream-api-key [KEY]` | 上游 API 密钥 |
| `amp model-mappings` | 模型映射 |
| `amp force-model-mappings [bool]` | 强制映射 |

### api-call - 通用请求

| 命令 | 说明 |
|------|------|
| `api-call -X METHOD --url URL` | 通过代理发起请求 |

## 全局选项

| 选项 | 说明 |
|------|------|
| `--url, -u` | 服务器地址 |
| `--key, -k` | 管理密钥 |
| `--json` | JSON 格式输出 |
| `--repl` | 交互式 REPL |
| `--version` | 版本信息 |
| `--help` | 帮助信息 |

## Agent 使用示例

```bash
# 检查服务器状态
cli-anything-cliproxyapi server status

# 获取配置
cli-anything-cliproxyapi config get

# 列出所有认证文件
cli-anything-cliproxyapi auth list

# 获取已启用 Codex 凭证额度
cli-anything-cliproxyapi auth codex-quota

# 发起 Claude OAuth 登录
cli-anything-cliproxyapi oauth login anthropic

# 列出模型
cli-anything-cliproxyapi --url http://localhost:8317 --key mgmt-key models aliases

# 管理 API 密钥
cli-anything-cliproxyapi keys add "new-api-key-123"
cli-anything-cliproxyapi keys claude add --api-key "sk-ant-..."
```
