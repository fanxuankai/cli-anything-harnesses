# cli-anything-ms

Media Saber 后端的最小可用 CLI harness。

当前提供稳定连接层，以及显式业务命令 `media search` 和 `subscribe add`。

## 安装

```bash
pip install cli-anything-ms
```

或从源码安装：

```bash
cd agent-harness/ms
pip install -e .
```

## 连接方式

优先级从高到低：

1. 命令行参数 `--url` 和 `--apikey`
2. 环境变量 `MS_URL` 和 `MS_API_KEY`
3. 配置文件 `~/.ms-cli.yaml`

保存连接：

```bash
cli-anything-ms config save-connection --url http://127.0.0.1:8899 --apikey sk-xxx
```

查看当前生效连接：

```bash
cli-anything-ms --json config show-connection
```

## 媒体搜索

统一走 `/api/v1/media/search`，当前只暴露两个来源：

- `douban`
- `tmdb`

示例：

```bash
cli-anything-ms media search --source tmdb --keyword Interstellar
```

```bash
cli-anything-ms media search --source douban --keyword 霸王别姬 --page 1 --page-size 10
```

JSON 输出：

```bash
cli-anything-ms --json media search --source tmdb --keyword Interstellar
```

## 订阅新增

`subscribe add` 会在内部自动读取对应的默认订阅配置，然后再提交新增请求。

最小新增订阅：

```bash
cli-anything-ms subscribe add --type movie --name "Interstellar" --year 2014
```

```bash
cli-anything-ms subscribe add --type tv --name "Breaking Bad" --year 2008 --season 1
```

JSON 输出：

```bash
cli-anything-ms --json subscribe add --type movie --name "Interstellar" --year 2014
```

## REPL

在交互终端中直接运行 `cli-anything-ms` 会进入 REPL：

```bash
cli-anything-ms
```

也可以显式指定：

```bash
cli-anything-ms --repl
```

REPL 中可直接输入：

```text
config show-connection
media search --source tmdb --keyword Interstellar
```

## 当前范围

首版仅包含：

- `config save-connection`
- `config show-connection`
- `media search`
- `subscribe add`

暂不支持：

- multipart 上传
- SSE 或流式响应
- `.api` 自动生成命令
- `media search-all`
- `autosuggest`
- `doubanSubject`
- `searchTmdb`
- 高级订阅字段覆盖
- 其他 `system/media/site/...` 显式业务命令组

## 内部命令

`request` 命令仍然保留为内部兜底能力，供技能和内部流程使用，但不会作为公开命令在帮助和文档中展示。

## 依赖

- Python >= 3.9
- click >= 8.0
- requests >= 2.28
- rich >= 13.0
- PyYAML >= 6.0
