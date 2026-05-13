# cli-anything-ms

ms 后端的最小可用 CLI harness。

当前提供稳定连接层，以及显式业务命令 `media search`、`media rank`、`media recommend`、`cloud-resource search/download/rank`、`media-server`、`site`、`download`、`plugin call` 和 `subscribe add`。

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

查看媒体服务器列表和同步统计：

```bash
cli-anything-ms media-server list
```

查看某台媒体服务器的媒体库：

```bash
cli-anything-ms media-server libraries --id 1
```

查看同步明细：

```bash
cli-anything-ms media-server sync-items --id 1 --page 1 --page-size 20
```

按标题、类型或漏集过滤同步明细：

```bash
cli-anything-ms media-server sync-items --id 1 --title "猎罪" --type tv --miss-eps true
```

查看正在播放、最近添加和继续观看：

```bash
cli-anything-ms media-server playing --id 1
cli-anything-ms media-server latest --id 1 --num 12
cli-anything-ms media-server resume --id 1 --num 12
```

发起媒体库同步任务：

```bash
cli-anything-ms media-server sync-run --id 1
```

`sync-run` 只提交同步任务，不等待同步完成。

检查媒体服务中的电视剧漏集：

```bash
cli-anything-ms media-server miss-episodes-check
```

JSON 输出：

```bash
cli-anything-ms --json media-server list
cli-anything-ms --json media-server sync-items --id 1 --page 1 --page-size 20
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

## 站点状态和签到

查看站点列表：

```bash
cli-anything-ms site list
```

查看站点总体统计：

```bash
cli-anything-ms site data total
```

查看各站最新统计：

```bash
cli-anything-ms site data latest
```

按站点名称查询：

```bash
cli-anything-ms site data latest --site-name "馒头"
```

查看签到记录：

```bash
cli-anything-ms site sign-in history --page 1 --page-size 20
```

提交指定站点签到：

```bash
cli-anything-ms site sign-in go --id 1
```

不传 `--id` 时由后端对所有开启签到的站点执行签到。签到命令只提交任务，不承诺所有站点已经签到成功。

JSON 输出：

```bash
cli-anything-ms --json site data latest
cli-anything-ms --json site sign-in history --page 1 --page-size 20
```

## 下载管理

查看下载器列表：

```bash
cli-anything-ms download downloaders
```

查看下载中任务：

```bash
cli-anything-ms download downloading
```

按下载 ID 查看指定任务：

```bash
cli-anything-ms download downloading --id <download_id>
```

查看下载历史：

```bash
cli-anything-ms download history --page 1 --page-size 20
```

按标题、类型或站点过滤下载历史：

```bash
cli-anything-ms download history --title "庆余年" --type tv --site-name "馒头"
```

暂停、恢复或删除下载任务：

```bash
cli-anything-ms download pause --id <download_id>
cli-anything-ms download resume --id <download_id>
cli-anything-ms download delete --id <download_id>
```

只有需要同时删除已下载文件时才给删除命令追加 `--delete-file`。这些操作只提交任务，不等待下载器实际完成。

JSON 输出：

```bash
cli-anything-ms --json download downloaders
cli-anything-ms --json download downloading
cli-anything-ms --json download history --page 1 --page-size 20
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

## 系统信息

查看 NAS 当前信息：

```bash
cli-anything-ms system nas-info
```

JSON 输出：

```bash
cli-anything-ms --json system nas-info
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
- `system nas-info`
- `media search`
- `media rank`
- `media recommend`
- `cloud-resource search`
- `cloud-resource download`
- `cloud-resource rank`
- `media-server list`
- `media-server detail`
- `media-server libraries`
- `media-server statistics`
- `media-server sync-items`
- `media-server playing`
- `media-server latest`
- `media-server resume`
- `media-server sync-run`
- `media-server miss-episodes-check`
- `site list`
- `site data total`
- `site data latest`
- `site sign-in history`
- `site sign-in go`
- `download downloaders`
- `download downloading`
- `download history`
- `download pause`
- `download resume`
- `download delete`
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
