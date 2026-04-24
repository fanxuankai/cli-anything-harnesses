---
name: ms-sub
description: 使用 cli-anything-ms 搜索影视、订阅影视、查看订阅列表，例如：搜索流浪地球电影、订阅白日提灯电视剧、查看电视剧订阅列表。
---

# MS Sub

## 概述

通过本地 `cli-anything-ms` CLI 处理电影和电视剧搜索、订阅列表查看与新增订阅请求。
支持以下功能：

- 搜索 TMDB 候选
- 分页查看现有订阅
- 在用户明确要求时新增订阅

## 安装

```bash
pip install cli-anything-ms
```

## 功能

### 搜索影视

- 适用于：
    - `搜索电影流浪地球`
    - `搜一下电视剧西游记`
    - `先搜一下`
    - `先看下结果`
- 每个意图都必须先识别明确的媒体类型：
    - `电影` -> `movie`
    - `电视剧` -> `tv`
- 如果媒体类型不明确，不要猜，要求用户补充。
- 去掉外壳词和可选的季数描述，只保留真正用于 TMDB 搜索的标题部分。
- 只搜索 TMDB：

  ```bash
  cli-anything-ms --json media search --source tmdb --keyword "<title>" --page-size 5
  ```

- 先把结果按目标媒体类型过滤成 `movie` 或 `tv`。
- 候选选择规则：
    - 优先匹配 `title` 或 `subtitle` 的精确或近似精确结果
    - 如果最后只剩一个高置信候选，直接作为主结果
    - 如果还有多个合理候选，展示最多 3 个候选并要求用户确认
    - 如果没有合理候选，明确告诉用户没有找到匹配标题
- 只搜索时，在展示候选后停止，不要自动进入订阅流程。
- 搜索结果至少包含：
    - 标题
    - 年份
    - 类型
    - 评分
    - 是否已订阅
    - 海报

### 订阅影视

- 适用于：
    - `订阅电影流浪地球`
    - `订阅电视剧西游记`
    - `检查 XXX 有没有订阅，没有就订阅`
- 订阅流程必须建立在 TMDB 搜索结果之上，不要跳过搜索直接订阅。
- 直接使用 `media search` 返回结果里的 `rssId` 判断是否已订阅：
    - `rssId > 0` 视为已经订阅
    - `rssId = 0` 或缺失才继续新增订阅
- 如果已经订阅，回复简短确认，例如 `ℹ️ 已订阅`。
- 如果尚未订阅，执行：
    - 电影

      ```bash
      cli-anything-ms --json subscribe add --type movie --name "<title>" --year <year>
      ```

    - 电视剧

      ```bash
      cli-anything-ms --json subscribe add --type tv --name "<title>" --year <year> --season <season>
      ```

- 如果用户没有明确指定电视剧季数，默认使用第 `1` 季。
- 调用 `subscribe add` 时，优先使用 TMDB 结果里的规范 `title` 和 `year`。
- 成功新增后，统一回复 `✅ 订阅成功`。

### 查看订阅

- 适用于：
    - `看看电影订阅`
    - `查看电视剧订阅`
    - `电影订阅列表`
    - `电视剧订阅前 20 个`
- 直接执行：

  ```bash
  cli-anything-ms --json subscribe page --type <movie|tv> --page <n> --page-size <n>
  ```

- 分页规则：
    - 默认 `page=1`
    - 默认 `page-size=20`
    - 如果用户说“前 N 个”，把 `page-size` 设为 `N`
    - 如果用户说“第 N 页”，把 `page` 设为 `N`
- 输出至少包含：
    - 名称
    - 年份
    - 类型
    - 季数
    - 状态（100: 订阅就绪, 200: 订阅运行中, 300: 订阅已完成）
    - TMDB
- 如果用户明确要求原始结果，再补充原始 JSON。
- 查看订阅时，不要先做 TMDB 搜索。

## 注意事项

- TMDB 是唯一搜索源，不要搜索豆瓣。
- 用户是查看订阅列表时，优先走 `subscribe page`，不要先做 TMDB 搜索。
- 用户只是想搜索时，不要自动进入订阅流程。
- 不要暴露或提及 `subscribe config`；`subscribe add` 内部已经会处理默认配置。
- 如果一句话里有多个搜索、查看订阅或订阅意图，要逐个处理，并逐条返回结果。
- 调用 `subscribe add` 时，优先使用 TMDB 结果里的规范 `title` 和 `year`。
- 如果新增失败，例如后端识别失败或业务校验失败，要清楚转述失败原因，不要误报成功。
