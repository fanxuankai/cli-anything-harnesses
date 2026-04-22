---
name: ms-sub
description: 当用户想通过自然语言为 Media Saber 订阅电影或电视剧时使用，例如“订阅电影流浪地球”“订阅电视剧西游记”或“检查 XXX 有没有订阅，没有就订阅”。这个技能会通过 `cli-anything-ms` 固定搜索 TMDB、检查现有订阅，并且只在尚未订阅时新增订阅。
---

# MS Sub

## 概述

通过本地 `cli-anything-ms` CLI 处理电影和电视剧订阅请求。
始终先搜索 TMDB，再检查是否已订阅，只有在未订阅时才调用 `subscribe add`。

## 工作流

### 步骤 1：拆分订阅意图

- 把用户消息拆成一个或多个订阅意图。
- 如果一句话里有多个订阅对象，按顺序逐个处理。

### 步骤 2：识别媒体类型

- 每个意图都必须识别出明确的媒体类型：
    - `电影` -> `movie`
    - `电视剧` -> `tv`
- 如果媒体类型不明确，不要猜，停下来要求用户补充是电影还是电视剧。

### 步骤 3：提取标题关键词

- 去掉外壳词，例如 `订阅电影`、`订阅电视剧`、`帮我订阅`。
- 去掉可选的季数描述，例如 `第X季`。
- 保留真正用于 TMDB 搜索的标题部分。

### 步骤 4：搜索 TMDB

- 只搜索 TMDB：

   ```bash
   cli-anything-ms --json media search --source tmdb --keyword "<title>" --page-size 5
   ```

### 步骤 5：筛选 TMDB 候选

- 先把 TMDB 搜索结果按目标媒体类型过滤成 `movie` 或 `tv`。
- 按下面的规则选择候选：
    - 优先匹配 `title` 或 `subtitle` 的精确或近似精确结果
    - 如果最后只剩一个高置信候选，直接使用它
    - 如果还有多个合理候选，不要自动订阅；展示最多 3 个候选并要求用户确认
    - 如果没有合理候选，明确告诉用户没有找到匹配标题

### 步骤 6：检查是否已订阅

- 在订阅前检查该候选是否已经订阅：

   ```bash
   cli-anything-ms --json request GET /api/v1/subscribe/page \
     --query type=<movie|tv> \
     --query pageNum=<n> \
     --query pageSize=100
   ```

- 按页扫描订阅列表，直到找完所有订阅项或者提前找到匹配项。
- 用下面的规则判断是否已订阅：
    - `movie`：`tmdbId` 相同就视为已订阅
    - `tv`：`tmdbId` 相同并且季数相同才视为已订阅
- 如果已经订阅，回复简短确认，例如 `ℹ️ 已订阅`。

### 步骤 7：新增订阅

- 如果尚未订阅，新增订阅。
- 电影：

      ```bash
      cli-anything-ms --json subscribe add --type movie --name "<title>" --year <year>
      ```

- 电视剧：

      ```bash
      cli-anything-ms --json subscribe add --type tv --name "<title>" --year <year> --season <season>
      ```

- 如果用户没有明确指定电视剧季数，默认使用第 `1` 季。
- 成功新增后，统一回复 `✅ 订阅成功`。

## 注意事项

- TMDB 是唯一搜索源，不要搜索豆瓣。
- 不要暴露或提及 `subscribe config`；`subscribe add` 内部已经会处理默认配置。
- 如果一句话里有多个订阅意图，要逐个处理，并逐条返回结果。
- 调用 `subscribe add` 时，优先使用 TMDB 结果里的规范 `title` 和 `year`。
- 如果新增失败，例如后端识别失败或业务校验失败，要清楚转述失败原因，不要误报成功。
