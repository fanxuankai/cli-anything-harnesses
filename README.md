# CLI Anything Harnesses

一个基于 [CLI Anything](https://github.com/HKUDS/CLI-Anything) 开发的 harness 仓库。

可以独立安装和分发的项目级 CLI harness。每个 harness 都把一个具体软件或后端系统整理成稳定的命令面，既适合人工运维，也适合
agent / workflow 直接调用。

## What’s In This Repo

当前仓库包含这些已实现的 harness：

| Harness                    | Version | Docs                                                                     |
|----------------------------|---------|--------------------------------------------------------------------------|
| `cli-anything-cliproxyapi` | `1.0.0` | [README](./agent-harness/cliproxyapi/cli_anything/cliproxyapi/README.md) |
| `cli-anything-ms`          | `0.1.0` | [README](./agent-harness/ms/cli_anything/ms/README.md)                   |

## Quick Start

安装 harness：

```bash
pip install cli-anything-cliproxyapi
pip install cli-anything-ms
```

浏览所有 skills：

```bash
npx skills add fanxuankai/cli-anything-harnesses --list
```

安装 skill：

```bash
npx skills add fanxuankai/cli-anything-harnesses --skill cli-anything-cliproxyapi
npx skills add fanxuankai/cli-anything-harnesses --skill ms-sub
```

## Entry Points

当前可用的入口命令：

```bash
cli-anything-cliproxyapi --help
cli-anything-ms --help
```

## Index

如果你只想看一个更简洁的列表页，见 [INDEX.md](./INDEX.md)。
