# CLIProxyAPI CLI Harness - SOP

## 软件概述

CLIProxyAPI 是一个 Go 语言编写的代理服务器，为 CLI 工具提供 OpenAI/Gemini/Claude/Codex 兼容的 API 接口。
支持 OAuth 登录、多账户轮询负载均衡、流式/非流式响应、函数调用/工具支持。

## 架构分析

### 后端引擎
- Go 1.26+, Gin HTTP 框架
- 模块化路由系统（RouteModuleV2）
- 多存储后端：文件系统、PostgreSQL、Git、对象存储

### 核心数据模型
- **Config**: 服务器配置（端口、TLS、API密钥、代理、路由策略等）
- **Auth**: 认证凭证（OAuth token、API key、Cookie）
- **Models**: 模型注册表（远程更新 + 本地目录）
- **Usage**: 请求统计和配额跟踪

### API 端点映射

#### 代理 API（需 API Key 认证）
| 端点 | 方法 | 说明 |
|------|------|------|
| `/v1/chat/completions` | POST | OpenAI 聊天补全 |
| `/v1/completions` | POST | OpenAI 文本补全 |
| `/v1/messages` | POST | Claude 消息 |
| `/v1/messages/count_tokens` | POST | Claude token 计数 |
| `/v1/models` | GET | 模型列表 |
| `/v1/responses` | POST/GET | OpenAI Responses API |
| `/v1beta/models` | GET | Gemini 模型列表 |
| `/v1beta/models/*action` | POST/GET | Gemini 生成端点 |

#### 管理 API（需管理密钥认证）
| 端点 | 方法 | 说明 |
|------|------|------|
| `/v0/management/config` | GET | 获取配置 |
| `/v0/management/config.yaml` | GET/PUT | 获取/更新 YAML 配置 |
| `/v0/management/auth-files` | GET/POST/DELETE | 认证文件 CRUD |
| `/v0/management/auth-files/models` | GET | 认证文件关联模型 |
| `/v0/management/auth-files/download` | GET | 下载认证文件 |
| `/v0/management/auth-files/status` | PATCH | 更新认证状态 |
| `/v0/management/auth-files/fields` | PATCH | 更新认证字段 |
| `/v0/management/api-keys` | GET/PUT/PATCH/DELETE | API 密钥管理 |
| `/v0/management/gemini-api-key` | GET/PUT/PATCH/DELETE | Gemini API 密钥 |
| `/v0/management/claude-api-key` | GET/PUT/PATCH/DELETE | Claude API 密钥 |
| `/v0/management/codex-api-key` | GET/PUT/PATCH/DELETE | Codex API 密钥 |
| `/v0/management/openai-compatibility` | GET/PUT/PATCH/DELETE | OpenAI 兼容提供商 |
| `/v0/management/vertex-api-key` | GET/PUT/PATCH/DELETE | Vertex API 密钥 |
| `/v0/management/oauth-model-alias` | GET/PUT/PATCH/DELETE | OAuth 模型别名 |
| `/v0/management/oauth-excluded-models` | GET/PUT/PATCH/DELETE | OAuth 排除模型 |
| `/v0/management/usage` | GET | 使用统计 |
| `/v0/management/usage/export` | GET | 导出统计数据 |
| `/v0/management/usage/import` | POST | 导入统计数据 |
| `/v0/management/logs` | GET/DELETE | 日志管理 |
| `/v0/management/request-log` | GET/PUT | 请求日志 |
| `/v0/management/request-error-logs` | GET | 错误日志 |
| `/v0/management/debug` | GET/PUT/PATCH | 调试模式 |
| `/v0/management/proxy-url` | GET/PUT/PATCH/DELETE | 代理 URL |
| `/v0/management/routing/strategy` | GET/PUT/PATCH | 路由策略 |
| `/v0/management/request-retry` | GET/PUT/PATCH | 重试配置 |
| `/v0/management/anthropic-auth-url` | GET | Claude OAuth |
| `/v0/management/codex-auth-url` | GET | Codex OAuth |
| `/v0/management/gemini-cli-auth-url` | GET | Gemini OAuth |
| `/v0/management/antigravity-auth-url` | GET | Antigravity OAuth |
| `/v0/management/qwen-auth-url` | GET | Qwen OAuth |
| `/v0/management/kimi-auth-url` | GET | Kimi OAuth |
| `/v0/management/iflow-auth-url` | GET/POST | iFlow OAuth |
| `/v0/management/oauth-callback` | POST | OAuth 回调 |
| `/v0/management/get-auth-status` | GET | 认证状态 |
| `/v0/management/api-call` | POST | 通用 API 调用 |
| `/v0/management/latest-version` | GET | 最新版本 |
| `/v0/management/ampcode/*` | GET/PUT/PATCH/DELETE | Amp 集成配置 |

### 支持的 OAuth 提供商
- Google/Gemini CLI
- OpenAI Codex（OAuth + 设备码流程）
- Claude Code
- Qwen Code
- iFlow
- Antigravity
- Kimi

### 配置系统
- YAML 配置文件（config.yaml）
- 热重载（fsnotify 监听）
- 多存储后端（文件/PostgreSQL/Git/对象存储）
- 环境变量覆盖

## CLI 命令组设计

### server - 服务器管理
- `server status` - 健康检查
- `server version` - 获取版本信息

### config - 配置管理
- `config get` - 获取当前配置
- `config get-yaml` - 获取 YAML 配置
- `config set-yaml` - 更新 YAML 配置
- `config debug` - 获取/设置调试模式
- `config proxy-url` - 管理代理 URL
- `config routing` - 路由策略管理
- `config retry` - 重试配置管理
- `config force-model-prefix` - 模型前缀配置

### auth - 认证文件管理
- `auth list` - 列出认证文件
- `auth upload` - 上传认证文件
- `auth download` - 下载认证文件
- `auth delete` - 删除认证文件
- `auth status` - 更新认证状态
- `auth fields` - 更新认证字段
- `auth models` - 查看认证关联模型
- `auth vertex-import` - 导入 Vertex 凭证

### oauth - OAuth 登录
- `oauth anthropic` - Claude OAuth 登录
- `oauth codex` - Codex OAuth 登录
- `oauth gemini` - Gemini OAuth 登录
- `oauth antigravity` - Antigravity OAuth 登录
- `oauth qwen` - Qwen OAuth 登录
- `oauth kimi` - Kimi OAuth 登录
- `oauth iflow` - iFlow OAuth 登录
- `oauth callback` - 处理 OAuth 回调
- `oauth status` - 查看认证状态

### keys - API 密钥管理
- `keys list` - 列出 API 密钥
- `keys set` - 设置 API 密钥
- `keys add` - 添加 API 密钥
- `keys delete` - 删除 API 密钥
- `keys gemini` - Gemini API 密钥管理
- `keys claude` - Claude API 密钥管理
- `keys codex` - Codex API 密钥管理
- `keys openai-compat` - OpenAI 兼容提供商管理
- `keys vertex` - Vertex API 密钥管理

### models - 模型管理
- `models list` - 列出可用模型
- `models aliases` - OAuth 模型别名管理
- `models excluded` - OAuth 排除模型管理
- `models definitions` - 模型定义查询

### usage - 使用统计
- `usage stats` - 获取使用统计
- `usage export` - 导出统计数据
- `usage import` - 导入统计数据

### logs - 日志管理
- `logs list` - 查看日志
- `logs clear` - 清除日志
- `logs request` - 请求日志管理
- `logs errors` - 错误日志查看

### amp - Amp 集成
- `amp config` - 查看 Amp 配置
- `amp upstream-url` - 上游 URL 管理
- `amp upstream-api-key` - 上游 API 密钥管理
- `amp model-mappings` - 模型映射管理

### api-call - 通用 API 调用
- `api-call` - 通过代理发起 HTTP 请求

## 状态模型

CLI 工具为无状态设计，每次调用通过 HTTP 连接到 CLIProxyAPI 管理端点。
所有状态由 CLIProxyAPI 服务器维护（配置文件、认证文件、使用统计等）。

连接参数通过以下方式提供（优先级从高到低）：
1. 命令行参数 `--url` 和 `--key`
2. 环境变量 `CPA_URL` 和 `CPA_KEY`
3. 配置文件 `~/.cliproxyapi-cli.yaml`

## 输出格式
- 默认：人类可读的表格/文本
- `--json`：JSON 格式输出（适合 agent 消费）
- `--raw`：原始 API 响应
