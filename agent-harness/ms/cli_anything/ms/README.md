# cli-anything-ms

ms 后端的最小可用 CLI harness。

当前提供稳定连接层，以及显式业务命令 `media search`、`media rank`、`media recommend`、`cloud-resource search/download/rank`、`media-server miss-episodes-check`、`plugin call` 和 `subscribe add`。

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

## 媒体榜单

获取榜单来源：

```bash
cli-anything-ms media rank sources
```

获取某个平台下的榜单分类：

```bash
cli-anything-ms media rank categories --source douban
```

获取某个榜单分类下的主题：

```bash
cli-anything-ms media rank subjects --category-code douban_tv
```

获取某个榜单主题下的条目：

```bash
cli-anything-ms media rank items --category-code douban_tv --code tv_domestic --page 1 --page-size 25
```

JSON 输出：

```bash
cli-anything-ms --json media rank items --category-code douban_tv --code tv_domestic
```

## 媒体推荐

获取推荐来源：

```bash
cli-anything-ms media recommend sources
```

获取某个平台下的频道：

```bash
cli-anything-ms media recommend channels --source douban
```

获取某个平台和频道下的动态选项：

```bash
cli-anything-ms media recommend options --source douban --channel movie
```

获取推荐条目：

```bash
cli-anything-ms media recommend items --source douban --channel movie --options '{"sort":"","year":"","tag":"","country":""}' --page 1 --page-size 25
```

JSON 输出：

```bash
cli-anything-ms --json media recommend items --source douban --channel movie --options '{"sort":"","year":"","tag":"","country":""}'
```

## 媒体服务

检查媒体服务中的电视剧漏集：

```bash
cli-anything-ms media-server miss-episodes-check
```

JSON 输出：

```bash
cli-anything-ms --json media-server miss-episodes-check
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

## 订阅分页

按类型分页查询订阅：

```bash
cli-anything-ms subscribe page --type movie --page 1 --page-size 99
```

```bash
cli-anything-ms subscribe page --type tv --page 1 --page-size 99
```

JSON 输出：

```bash
cli-anything-ms --json subscribe page --type movie --page 1 --page-size 99
```

## 云端资源

搜索云端资源：

```bash
cli-anything-ms cloud-resource search --keyword "庆余年" --page 1 --page-size 5
```

按 TMDB ID 搜索时必须指定类型：

```bash
cli-anything-ms cloud-resource search --tmdb-id 95842 --type tv --season 1 --episode 46
```

可选过滤条件：

```bash
cli-anything-ms cloud-resource search --keyword "庆余年" --creator-id 931 --begin-episode 40 --end-episode 46
```

JSON 输出里每条可下载资源会带 `download_request`，后续下载只使用这个字段：

```bash
cli-anything-ms --json cloud-resource search --keyword "庆余年" --page-size 5
```

提交云下载或转存任务：

```bash
cli-anything-ms cloud-resource download --request '{"type":300,"contents":["ed2k://..."],"csHashId":1246925,"csCreator":"Lucifer"}'
```

指定目标目录：

```bash
cli-anything-ms cloud-resource download --request '{"type":200,"contents":["..."]}' --dir "/downloads"
```

`--dir` 不传时使用后端默认云下载或默认转存目录。下载命令只提交任务，不等待任务完成。

查看云端资源贡献榜：

```bash
cli-anything-ms cloud-resource rank --range today --stat count
```

查看洪荒封神榜（按体积）：

```bash
cli-anything-ms cloud-resource rank --range today --stat size
```

JSON 输出：

```bash
cli-anything-ms --json cloud-resource rank --range week --stat count
```

`--range` 支持 `today`、`week`、`all`，`--stat` 支持 `count`、`size`。需要刷新后端缓存时追加 `--refresh`。

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

## 插件调用

统一走 `/api/v1/pluginsInstance/callByCode/:code`。

示例：

```bash
cli-anything-ms plugin call --code zspace_service_assistant --body '{"action":"get_recent_state","body":{}}'
```

JSON 输出：

```bash
cli-anything-ms --json plugin call --code zspace_service_assistant --body '{"action":"get_recent_state","body":{}}'
```

## 当前范围

首版仅包含：

- `config save-connection`
- `config show-connection`
- `media search`
- `media rank`
- `media recommend`
- `cloud-resource search`
- `cloud-resource download`
- `cloud-resource rank`
- `media-server miss-episodes-check`
- `plugin call`
- `subscribe page`
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

## 依赖

- Python >= 3.9
- click >= 8.0
- requests >= 2.28
- rich >= 13.0
- PyYAML >= 6.0
