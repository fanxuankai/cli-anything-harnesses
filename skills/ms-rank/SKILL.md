---
name: ms-rank
description: 查看 Media Saber 影视榜单时使用，例如“影视榜单”“豆瓣电视榜单”“看豆瓣热播国产剧”“榜单前10个”“看电影年榜 2025”。这个技能会通过 `cli-anything-ms` 逐步查询榜单来源、分类、主题和条目，并输出简洁摘要。
---

# MS Rank

## 概述

通过本地 `cli-anything-ms` CLI 处理影视榜单浏览请求。
始终按“来源 -> 分类 -> 主题 -> 条目”的顺序收集信息，不直接调用后端接口，也不继续执行订阅。

## 安装

```bash
pip install cli-anything-ms
```

如果不可用，只提示用户安装，不自动安装。

## 触发场景

- `影视榜单`
- `豆瓣电视榜单`
- `看豆瓣热播国产剧`
- `榜单前10个`
- `看电影年榜 2025`

## 工作流

### 步骤 1：确定榜单来源

如果用户没有明确说明平台，先执行：

```bash
cli-anything-ms --json media rank sources
```

展示来源并要求用户选择平台。

如果用户已经说了平台，例如“豆瓣”“TMDB”，把中文意图映射成 CLI alias：

- `豆瓣` -> `douban`
- `TMDB` -> `tmdb`
- 其他平台同理，统一使用 CLI 支持的 alias

### 步骤 2：确定榜单分类

平台确定后执行：

```bash
cli-anything-ms --json media rank categories --source <alias>
```

按返回结果里的 `name` 优先匹配用户提到的分类，其次按 `code` 匹配。
如果有多个合理候选，不要猜，先展示候选并要求用户确认。

### 步骤 3：确定榜单主题

分类确定后执行：

```bash
cli-anything-ms --json media rank subjects --category-code <code>
```

继续按 `name` 优先、`code` 次之匹配主题。
如果主题不明确，先展示候选，不要自动选择。

### 步骤 4：获取榜单条目

主题确定后执行：

```bash
cli-anything-ms --json media rank items --category-code <code> --code <subject-code> --page <n> --page-size <n>
```

分页规则：

- 默认 `page=1`
- 如果用户说“前 N 个”，把 `page-size` 设为 `N`
- 如果用户没给数量，默认 `page-size=10`
- 如果用户要求看第 N 页，传 `--page N`

### 步骤 5：展示结果

不要直接倾倒整段 JSON。
先输出简洁摘要，至少包含：

- 标题
- 年份
- 类型
- 评分
- 是否已订阅
- 是否已入库

如果用户明确要求看原始结果，再补充原始 JSON。

## 注意事项

- 这个技能只做榜单浏览，不继续执行订阅。
- 不直接调用后端 HTTP。
- 不发明新的筛选参数。
- 分类和主题有歧义时，一律要求用户确认。
