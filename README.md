# CLI Anything Harnesses

[![GitHub release](https://img.shields.io/github/v/release/fanxuankai/cli-anything-harnesses?sort=semver&display_name=tag)](https://github.com/fanxuankai/cli-anything-harnesses/releases)
[![CI](https://github.com/fanxuankai/cli-anything-harnesses/actions/workflows/python-app.yml/badge.svg?branch=main)](https://github.com/fanxuankai/cli-anything-harnesses/actions/workflows/python-app.yml)
[![Last commit](https://img.shields.io/github/last-commit/fanxuankai/cli-anything-harnesses)](https://github.com/fanxuankai/cli-anything-harnesses/commits/main)
[![Issues](https://img.shields.io/github/issues/fanxuankai/cli-anything-harnesses)](https://github.com/fanxuankai/cli-anything-harnesses/issues)
[![Pull requests](https://img.shields.io/github/issues-pr/fanxuankai/cli-anything-harnesses)](https://github.com/fanxuankai/cli-anything-harnesses/pulls)
[![Skills](https://img.shields.io/badge/skills-7-2f6f9f)](#skills)
[![PyPI - cli-anything-ms](https://img.shields.io/pypi/v/cli-anything-ms?label=cli-anything-ms)](https://pypi.org/project/cli-anything-ms/)
[![PyPI - cli-anything-cliproxyapi](https://img.shields.io/pypi/v/cli-anything-cliproxyapi?label=cli-anything-cliproxyapi)](https://pypi.org/project/cli-anything-cliproxyapi/)

一个基于 [CLI Anything](https://github.com/HKUDS/CLI-Anything) 开发的 harness 仓库。

这里的每个 harness 都把一个具体软件、后端服务或已有系统整理成稳定的命令面，既适合人工运维，也适合 Agent 和 workflow 直接调用。

## Packages

| Harness     | PyPI                                                                                                                                                 | CLI                        | Install                                |
|-------------|------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------|----------------------------------------|
| ms | [![PyPI](https://img.shields.io/pypi/v/cli-anything-ms?label=cli-anything-ms)](https://pypi.org/project/cli-anything-ms/)                            | `cli-anything-ms`          | `pip install cli-anything-ms`          |
| CLIProxyAPI | [![PyPI](https://img.shields.io/pypi/v/cli-anything-cliproxyapi?label=cli-anything-cliproxyapi)](https://pypi.org/project/cli-anything-cliproxyapi/) | `cli-anything-cliproxyapi` | `pip install cli-anything-cliproxyapi` |

## Skills

| Skill                                                                  | 用途                   | 安装                                                                                  |
|------------------------------------------------------------------------|----------------------|-------------------------------------------------------------------------------------|
| [`ms-sub`](skills/ms-sub/SKILL.md)                                     | 搜索影视、订阅影视、查看订阅列表。    | `npx skills add fanxuankai/cli-anything-harnesses --skill ms-sub`                   |
| [`ms-gap-filler`](skills/ms-gap-filler/SKILL.md)                       | 检查电视剧漏集，或把漏集转成订阅补齐。  | `npx skills add fanxuankai/cli-anything-harnesses --skill ms-gap-filler`            |
| [`ms-recommend`](skills/ms-recommend/SKILL.md)                         | 查看豆瓣、TMDB 等影视推荐。     | `npx skills add fanxuankai/cli-anything-harnesses --skill ms-recommend`             |
| [`ms-rank`](skills/ms-rank/SKILL.md)                                   | 查看豆瓣等影视榜单。           | `npx skills add fanxuankai/cli-anything-harnesses --skill ms-rank`                  |
| [`ms-cloud-resource`](skills/ms-cloud-resource/SKILL.md)               | 查询云端资源，并提交云下载或转存任务。  | `npx skills add fanxuankai/cli-anything-harnesses --skill ms-cloud-resource`        |
| [`ms-zspace-state`](skills/ms-zspace-state/SKILL.md)                   | 查看极空间系统、硬件、磁盘、网络等状态。 | `npx skills add fanxuankai/cli-anything-harnesses --skill ms-zspace-state`          |
| [`cli-anything-cliproxyapi`](skills/cli-anything-cliproxyapi/SKILL.md) | 管理 CLIProxyAPI 代理服务。 | `npx skills add fanxuankai/cli-anything-harnesses --skill cli-anything-cliproxyapi` |

## Quick Start

浏览可安装 skills：

```bash
npx skills add fanxuankai/cli-anything-harnesses --list
```

安装单个 skill：

```bash
npx skills add fanxuankai/cli-anything-harnesses --skill ms-sub
```

通过 Hermes 安装 skill：

```bash
hermes skills install fanxuankai/cli-anything-harnesses/skills/ms-sub --force
```

如果使用 Hermes 访问私有仓库，先在 `~/.hermes/.env` 中配置 GitHub Token：

```env
GITHUB_TOKEN=你的 Github PAT
```

## Hermes 通知

`.github/workflows/notify-hermes.yml` 会在 `agent-harness/**` 或 `skills/**` 变更推送到 `main` 后通知 Hermes webhook，用于触发 Hermes 更新 CLI 和 skills。

需要在 GitHub 仓库 Secrets 中配置：

- `HERMES_WEBHOOK_URL`：Hermes 接收 CLI 和 skill 更新通知的 HTTP 地址。
- `HERMES_WEBHOOK_SECRET`：Hermes webhook 的签名 secret。workflow 会生成 `X-Hub-Signature-256`。

兼容旧配置：如果没有 `HERMES_WEBHOOK_SECRET`，workflow 会回退使用 `HERMES_WEBHOOK_TOKEN` 作为 HMAC secret。

通知会带 `X-GitHub-Event: push`、`X-GitHub-Delivery` 和 `X-Hub-Signature-256` 请求头。payload 包含 GitHub 风格的 `event_type`、`repository`、`head_commit`、`sender`，以及 `changed_files`、`cli`、`skills` 和 `run_url`。如果未配置 `HERMES_WEBHOOK_URL`，workflow 会跳过通知。

## Local Development

从源码安装两个 harness：

```bash
pip install -e agent-harness/ms
pip install -e agent-harness/cliproxyapi
```

运行测试：

```bash
python -m pytest agent-harness/ms/cli_anything/ms/tests
python -m pytest agent-harness/cliproxyapi/cli_anything/cliproxyapi/tests
```

验证 CLI 入口：

```bash
cli-anything-ms --json media recommend sources
cli-anything-cliproxyapi --json server status
```

## Project Layout

```text
agent-harness/
  ms/                 # ms harness
  cliproxyapi/        # CLIProxyAPI harness
skills/               # Codex / Agent skills
.github/              # GitHub Actions and contribution templates
```

## Version Display

GitHub 当前版本通过 tag 和 Release 展示：

```bash
git tag v0.1.0
git push origin v0.1.0
```

然后在 GitHub Releases 中基于该 tag 创建发布。README 顶部的 GitHub release 徽章会自动更新。

PyPI 当前版本通过对应包的公开发布版本展示：

- <https://pypi.org/project/cli-anything-ms/>
- <https://pypi.org/project/cli-anything-cliproxyapi/>

## PyPI 发布

`.github/workflows/publish-pypi.yml` 支持自动发布到 PyPI：

- 触发方式：推送到 `main`，且 `agent-harness/ms/setup.py` 或 `agent-harness/cliproxyapi/setup.py` 发生变化。
- 发布条件：读取对应 `setup.py` 的 `version`，如果 PyPI 上不存在该版本，就构建并发布；已存在的版本会跳过。

发布使用 PyPI token。需要在 GitHub 仓库 Secrets 中配置：

- `TWINE_USERNAME`：通常为 `__token__`
- `TWINE_PASSWORD`：PyPI token，例如 `pypi-...`

## GitHub

- Releases: <https://github.com/fanxuankai/cli-anything-harnesses/releases>
- Tags: <https://github.com/fanxuankai/cli-anything-harnesses/tags>
- Actions: <https://github.com/fanxuankai/cli-anything-harnesses/actions>
- Issues: <https://github.com/fanxuankai/cli-anything-harnesses/issues>
- Pull requests: <https://github.com/fanxuankai/cli-anything-harnesses/pulls>

## Contributing

修改 harness 时，同步检查对应 skill 是否需要更新。修改 skill 时，确认它描述的流程和实际 CLI 行为一致。

更多协作规则见 [CONTRIBUTING.md](CONTRIBUTING.md) 和 [AGENTS.md](AGENTS.md)。
