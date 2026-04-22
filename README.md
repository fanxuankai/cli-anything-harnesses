# CLI Anything Harnesses

一个基于 [CLI Anything](https://github.com/HKUDS/CLI-Anything) 开发的 harness 仓库。

可以独立安装和分发的项目级 CLI harness。每个 harness 都把一个具体软件或后端系统整理成稳定的命令面，既适合人工运维，也适合
agent / workflow 直接调用。

## What’s In This Repo

当前仓库包含这些已实现的 harness：

| Harness                    | Version | Docs                                                                     | Design notes                                                 |
|----------------------------|---------|--------------------------------------------------------------------------|--------------------------------------------------------------|
| `cli-anything-cliproxyapi` | `1.0.0` | [README](./agent-harness/cliproxyapi/cli_anything/cliproxyapi/README.md) | [CLIPROXYAPI.md](./agent-harness/cliproxyapi/CLIPROXYAPI.md) |
| `cli-anything-mediasaber`  | `1.0.2` | [README](./agent-harness/mediasaber/cli_anything/mediasaber/README.md)   | [MEDIASABER.md](./agent-harness/mediasaber/MEDIASABER.md)    |

## Quick Start

安装 harness：

```bash
pip install cli-anything-mediasaber
```

浏览所有 skills：

```bash
npx skills add fanxuankai/cli-anything-harnesses --list
```

安装 skill：

```bash
npx skills add fanxuankai/cli-anything-harnesses --skill cli-anything-mediasaber
```

## Entry Points

当前可用的入口命令：

```bash
cli-anything-mediasaber --help
```

## Index

如果你只想看一个更简洁的列表页，见 [INDEX.md](./INDEX.md)。
