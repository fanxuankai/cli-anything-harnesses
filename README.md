# CLI Anything Harnesses

一个面向 `cli-anything` 生态的 harness 仓库。

可以独立安装和分发的项目级 CLI harness。每个 harness 都把一个具体软件或后端系统整理成稳定的命令面，既适合人工运维，也适合
agent / workflow 直接调用。

## What’s In This Repo

当前仓库包含这些已实现的 harness：

| Harness       | Package                    | Version | Directory                   | Status    |
|---------------|----------------------------|---------|-----------------------------|-----------|
| `cliproxyapi` | `cli-anything-cliproxyapi` | `1.0.0` | `agent-harness/cliproxyapi` | 已发布到 PyPI |
| `mediasaber`  | `cli-anything-mediasaber`  | `1.0.2` | `agent-harness/mediasaber`  | 已发布到 PyPI |

## Quick Start

安装你需要的 harness：

```bash
pip install cli-anything-cliproxyapi
pip install cli-anything-mediasaber
```

如果你是通过 `skills` 工作流安装这两个 skill：

```bash
npx skills add fanxuankai/cli-anything-harnesses --skill cli-anything-cliproxyapi -g -y
npx skills add fanxuankai/cli-anything-harnesses --skill cli-anything-mediasaber -g -y
```

如果是本地开发：

```bash
cd agent-harness/mediasaber
pip install -e .

cd ../cliproxyapi
pip install -e .
```

## Available Harnesses

### `cliproxyapi`

CLIProxyAPI 的管理 CLI harness，用于通过 Management API 管理代理服务、配置、OAuth、认证文件、模型和日志。

- Package: `cli-anything-cliproxyapi`
- Current version: `1.0.0`
- Docs: [README](./agent-harness/cliproxyapi/cli_anything/cliproxyapi/README.md)
- Design notes: [CLIPROXYAPI.md](./agent-harness/cliproxyapi/CLIPROXYAPI.md)

### `mediasaber`

Media Saber 的管理与运维 CLI harness，覆盖系统管理、用户与密钥、站点、下载器、目录、云存储、种子搜索、订阅、消息、媒体服务器、AI
与通用 API 调用。

- Package: `cli-anything-mediasaber`
- Current version: `1.0.1`
- Docs: [README](./agent-harness/mediasaber/cli_anything/mediasaber/README.md)
- Design notes: [MEDIASABER.md](./agent-harness/mediasaber/MEDIASABER.md)

## Repo Layout

```text
agent-harness/
  <name>/
    setup.py
    <NAME>.md
    cli_anything/
      <name>/
        README.md
        skills/
        tests/
INDEX.md
README.md
```

含义：

- `agent-harness/<name>/`：单个 harness 的可发布内容
- `cli_anything/<name>/`：安装后实际暴露给用户和 agent 的 Python 包
- `skills/`：可被 agent 发现的 skill 定义
- `tests/`：单元测试和端到端 smoke tests
- `INDEX.md`：简化索引页

## How To Use This Repo

如果你只是要使用某个 harness：

- 直接安装对应 PyPI 包
- 阅读对应 harness 的 `README.md`
- 用 `--help` 或子命令 `--help` 浏览完整命令树

如果你要继续维护或扩展：

- 进入对应 `agent-harness/<name>/`
- 更新实现、文档、skills 和 tests
- 运行本地验证
- 再构建并发布对应包

## Entry Points

两个当前可用的入口命令：

```bash
cli-anything-cliproxyapi --help
cli-anything-mediasaber --help
```

## Index

如果你只想看一个更简洁的列表页，见 [INDEX.md](./INDEX.md)。
