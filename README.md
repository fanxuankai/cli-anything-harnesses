# CLI Anything Harnesses

[![GitHub release](https://img.shields.io/github/v/release/fanxuankai/cli-anything-harnesses?sort=semver&display_name=tag)](https://github.com/fanxuankai/cli-anything-harnesses/releases)
[![Last commit](https://img.shields.io/github/last-commit/fanxuankai/cli-anything-harnesses)](https://github.com/fanxuankai/cli-anything-harnesses/commits/main)
[![Issues](https://img.shields.io/github/issues/fanxuankai/cli-anything-harnesses)](https://github.com/fanxuankai/cli-anything-harnesses/issues)
[![Pull requests](https://img.shields.io/github/issues-pr/fanxuankai/cli-anything-harnesses)](https://github.com/fanxuankai/cli-anything-harnesses/pulls)
[![Skills](https://img.shields.io/badge/skills-12-2f6f9f)](#skills)
[![PyPI - cli-anything-ms](https://img.shields.io/pypi/v/cli-anything-ms?label=cli-anything-ms)](https://pypi.org/project/cli-anything-ms/)
[![PyPI - cli-anything-cliproxyapi](https://img.shields.io/pypi/v/cli-anything-cliproxyapi?label=cli-anything-cliproxyapi)](https://pypi.org/project/cli-anything-cliproxyapi/)

一个基于 [CLI Anything](https://github.com/HKUDS/CLI-Anything) 开发的 harness 仓库。

这里的每个 harness 都把一个具体软件、后端服务或已有系统整理成稳定的命令面，既适合人工运维，也适合 Agent 和自动化流程直接调用。

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
| [`ms-cloud-resource-rank`](skills/ms-cloud-resource-rank/SKILL.md)     | 查看云端资源 HASH 上报贡献榜。 | `npx skills add fanxuankai/cli-anything-harnesses --skill ms-cloud-resource-rank`   |
| [`ms-media-server`](skills/ms-media-server/SKILL.md)                   | 查看媒体服务器、同步统计、媒体库和播放列表。 | `npx skills add fanxuankai/cli-anything-harnesses --skill ms-media-server`          |
| [`ms-site-state`](skills/ms-site-state/SKILL.md)                       | 查看站点状态、站点统计、上传下载量和签到状态。 | `npx skills add fanxuankai/cli-anything-harnesses --skill ms-site-state`            |
| [`ms-site-signin`](skills/ms-site-signin/SKILL.md)                     | 查看或执行站点签到。          | `npx skills add fanxuankai/cli-anything-harnesses --skill ms-site-signin`           |
| [`ms-download`](skills/ms-download/SKILL.md)                           | 查看下载器、下载中任务和下载历史。    | `npx skills add fanxuankai/cli-anything-harnesses --skill ms-download`              |
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
hermes skills tap add fanxuankai/cli-anything-harnesses
hermes skills install fanxuankai/cli-anything-harnesses/skills/ms-sub --force
```

如果使用 Hermes 访问私有仓库，先在 `~/.hermes/.env` 中配置 GitHub Token：

```env
GITHUB_TOKEN=你的 Github PAT
```

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

常用 ms 下载管理命令：

```bash
cli-anything-ms --json download downloaders
cli-anything-ms --json download downloading
cli-anything-ms --json download history --page 1 --page-size 20
cli-anything-ms --json download pause --id <download_id>
cli-anything-ms --json download resume --id <download_id>
cli-anything-ms --json download delete --id <download_id>
```

## Project Layout

```text
agent-harness/
  ms/                 # ms harness
  cliproxyapi/        # CLIProxyAPI harness
skills/               # Codex / Agent skills
.github/              # GitHub metadata and contribution templates
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

## GitHub

- Releases: <https://github.com/fanxuankai/cli-anything-harnesses/releases>
- Tags: <https://github.com/fanxuankai/cli-anything-harnesses/tags>
- Issues: <https://github.com/fanxuankai/cli-anything-harnesses/issues>
- Pull requests: <https://github.com/fanxuankai/cli-anything-harnesses/pulls>

## Contributing

修改 harness 时，同步检查对应 skill 是否需要更新。修改 skill 时，确认它描述的流程和实际 CLI 行为一致。

更多协作规则见 [CONTRIBUTING.md](CONTRIBUTING.md) 和 [AGENTS.md](AGENTS.md)。
