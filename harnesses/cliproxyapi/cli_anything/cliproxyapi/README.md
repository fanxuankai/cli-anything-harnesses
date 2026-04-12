# cli-anything-cliproxyapi

CLIProxyAPI 命令行管理工具。

通过 Management API 管理 CLIProxyAPI 代理服务器的配置、认证、模型、日志等。

## 安装

```bash
pip install cli-anything-cliproxyapi
```

或从源码安装：

```bash
cd agent-harness
pip install -e .
```

## 快速开始

```bash
# 保存连接配置（只需一次）
cli-anything-cliproxyapi config save-connection --url http://127.0.0.1:8317 --key your-management-key

# 检查服务器状态
cli-anything-cliproxyapi server status

# 查看配置
cli-anything-cliproxyapi config get

# 列出认证文件
cli-anything-cliproxyapi auth list

# 仅查看启用或禁用的认证文件
cli-anything-cliproxyapi auth list --enabled
cli-anything-cliproxyapi auth list --disabled

# 获取 Codex 额度
cli-anything-cliproxyapi auth codex-quota

# JSON 输出模式（适合脚本和 agent）
cli-anything-cliproxyapi --json auth list

# 交互式 REPL
cli-anything-cliproxyapi --repl
```

## 连接配置

支持三种方式（优先级从高到低）：

1. 命令行参数：`--url` 和 `--key`
2. 环境变量：`CPA_URL` 和 `CPA_KEY`
3. 配置文件：`~/.cliproxyapi-cli.yaml`

## 命令概览

| 命令组 | 说明 |
|--------|------|
| `server` | 服务器健康检查和版本 |
| `config` | 配置管理（调试、代理、路由策略等） |
| `auth` | 认证文件管理（上传/下载/启用/禁用/筛选/批量刷新） |
| `oauth` | OAuth 登录（Claude/Codex/Gemini/Qwen/Kimi/iFlow） |
| `keys` | API 密钥管理（Gemini/Claude/Codex/OpenAI/Vertex） |
| `models` | 模型列表、别名和排除规则 |
| `usage` | 使用统计（查看/导出/导入） |
| `logs` | 日志管理（查看/清除/请求日志/错误日志） |
| `amp` | Amp CLI 集成配置 |
| `api-call` | 通过代理发起通用 HTTP 请求 |

## 认证管理示例

```bash
# 仅列出启用的认证文件
cli-anything-cliproxyapi --json auth list --enabled

# 仅列出禁用的认证文件
cli-anything-cliproxyapi --json auth list --disabled

# 获取 Codex 额度
cli-anything-cliproxyapi --json auth codex-quota
```

`auth list --enabled|--disabled` 会先读取 `/auth-files` 的全量结果，再按每个条目的 `disabled` 字段在 CLI 侧过滤。

`auth codex-quota` 会固定先筛出已启用的 Codex 凭证，再基于 `auth list` 返回的 `auth_index` 和 `id_token.chatgpt_account_id` 组装 `api-call` 请求，提取 5 小时额度和周额度信息。

## 运行测试

```bash
# 单元测试
pytest cli_anything/cliproxyapi/tests/test_core.py -v

# E2E 测试（需要运行中的 CLIProxyAPI 服务器）
CPA_URL=http://127.0.0.1:8317 CPA_KEY=your-key pytest cli_anything/cliproxyapi/tests/test_full_e2e.py -v
```

## 依赖

- Python >= 3.9
- click >= 8.0
- requests >= 2.28
- rich >= 13.0
- PyYAML >= 6.0
