---
name: ms-rank
description: 查看 ms 影视榜单时使用，例如“影视榜单”“豆瓣电视榜单”“看豆瓣热播国产剧”“榜单前10个”“看电影年榜 2025”。这个技能会通过 `cli-anything-ms` 逐步查询榜单来源、分类、主题和条目，并输出简洁摘要。
---

# ms Rank

## 概述

通过本地 `cli-anything-ms` CLI 处理影视榜单浏览请求。
处理时先确认榜单来源，再确认分类和主题，最后取条目。不要直接调用后端接口，也不要顺手订阅。

## 安装

```bash
pip install cli-anything-ms
```

## 触发场景

- `影视榜单`
- `豆瓣电视榜单`
- `看豆瓣热播国产剧`
- `榜单前10个`
- `看电影年榜 2025`

## 工作流

### 1. 先确认榜单来源

如果用户没有明确说明平台，先执行：

```bash
cli-anything-ms --json media rank sources
```

把可选来源用中文告诉用户，请用户选一个。

如果用户已经说了平台，就按 CLI 支持的来源名调用。例如：

- `豆瓣` -> `douban`
- `TMDB` -> `tmdb`
- 其他平台同理，使用 CLI 返回或文档里支持的名称

### 2. 确认榜单分类

平台确定后执行：

```bash
cli-anything-ms --json media rank categories --source <alias>
```

优先按用户说的中文分类去匹配。遇到多个看起来都可能的分类时，不要猜，先把候选告诉用户让他确认。

### 3. 确认榜单主题

分类确定后执行：

```bash
cli-anything-ms --json media rank subjects --category-code <code>
```

继续按用户说法匹配主题。主题不明确时，先展示候选，不要自动选择。

### 4. 获取榜单条目

主题确定后执行：

```bash
cli-anything-ms --json media rank items --category-code <code> --code <subject-code> --page <n> --page-size <n>
```

分页按用户说法处理：

- 默认 `page=1`
- 用户说“前 N 个”，就取 N 个
- 用户没给数量，默认取 10 个
- 用户要求看第 N 页，就取对应页

### 5. 用自然语言展示结果

不要直接倾倒整段 JSON。先说明正在看的是什么榜单，再用自然中文列出条目。每个条目说明片名、年份、类型、评分、是否已订阅、是否已入库和海报链接即可。不要把内部字段名写给用户看。

如果用户明确要求看原始结果，再补充原始 JSON。

## 注意事项

- 这个技能只做榜单浏览，不继续执行订阅。
- 不直接调用后端 HTTP。
- 不发明新的筛选参数。
- 分类和主题有歧义时，一律要求用户确认。
