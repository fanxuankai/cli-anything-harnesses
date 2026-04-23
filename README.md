# CLI Anything Harnesses

一个基于 [CLI Anything](https://github.com/HKUDS/CLI-Anything) 开发的 harness 仓库。

可以独立安装和分发的项目级 CLI harness。每个 harness 都把一个具体软件或后端系统整理成稳定的命令面，既适合人工运维，也适合
agent / workflow 直接调用。

## Quick Start

浏览 skills：

```bash
npx skills add fanxuankai/cli-anything-harnesses --list
```

安装 skills：

```bash
npx skills add fanxuankai/cli-anything-harnesses --skill <skill-name>
```

通过 Hermes 安装 skills：

先在 `~/.hermes/.env` 中配置 GitHub Token：

```env
GITHUB_TOKEN=你的 Github PAT
```

然后执行安装命令：

```bash
hermes skills install fanxuankai/cli-anything-harnesses/skills/<skill-name> --force
```
