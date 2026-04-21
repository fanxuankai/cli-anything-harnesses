# CLI Anything Harnesses

我维护并开源的 cli-anything harness 项目仓库，提供可独立分发、可直接安装的项目级命令行封装。

## 项目概览

| 名称 | 目录 | 简介 | 状态 | 文档 |
|------|------|------|------|------|
| cliproxyapi | `agent-harness/cliproxyapi` | CLIProxyAPI 的管理 CLI harness | 已发布到 PyPI | [README](./agent-harness/cliproxyapi/cli_anything/cliproxyapi/README.md) |
| mediasaber | `agent-harness/mediasaber` | Media Saber 的管理与运维 CLI harness | 本地开发中 | [README](./agent-harness/mediasaber/cli_anything/mediasaber/README.md) |

## 快速入口

- 项目索引：[`INDEX.md`](./INDEX.md)
- cliproxyapi 使用文档：[`agent-harness/cliproxyapi/cli_anything/cliproxyapi/README.md`](./agent-harness/cliproxyapi/cli_anything/cliproxyapi/README.md)
- cliproxyapi 设计说明：[`agent-harness/cliproxyapi/CLIPROXYAPI.md`](./agent-harness/cliproxyapi/CLIPROXYAPI.md)
- mediasaber 使用文档：[`agent-harness/mediasaber/cli_anything/mediasaber/README.md`](./agent-harness/mediasaber/cli_anything/mediasaber/README.md)
- mediasaber 设计说明：[`agent-harness/mediasaber/MEDIASABER.md`](./agent-harness/mediasaber/MEDIASABER.md)

## 安装

```bash
pip install cli-anything-cliproxyapi
pip install cli-anything-mediasaber
```

## 仓库结构

- `agent-harness/<name>/`：单个项目的公开 harness 内容
- `INDEX.md`：所有已开源 harness 的索引页

更多能力、命令示例和使用细节请直接查看对应项目的 README。
