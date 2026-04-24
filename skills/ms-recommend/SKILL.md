---
name: ms-recommend
description: 查看 Media Saber 影视推荐时使用，例如“影视推荐”“推荐电影”“豆瓣电影推荐”“TMDB 高分电影推荐”“推荐 2025 年动作片”。这个技能会通过 `cli-anything-ms` 逐步查询推荐来源、频道、动态选项和推荐条目，并输出简洁摘要。
---

# MS Recommend

## 概述

通过本地 `cli-anything-ms` CLI 处理影视推荐浏览请求。
始终按“来源 -> 频道 -> 动态选项 -> 推荐条目”的顺序收集信息，不直接调用后端接口，也不继续执行订阅。

## 安装

```bash
pip install cli-anything-ms
```

如果不可用，只提示用户安装，不自动安装。

## 触发场景

- `影视推荐`
- `推荐电影`
- `豆瓣电影推荐`
- `TMDB 高分电影推荐`
- `推荐 2025 年动作片`
- `推荐豆瓣电视剧，近期热度，华语`

## 工作流

### 步骤 1：确定推荐来源

如果用户没有明确说明平台，先执行：

```bash
cli-anything-ms --json media recommend sources
```

展示来源并要求用户选择平台。

如果用户已经说了平台，把中文意图映射成 CLI alias，例如：

- `豆瓣` -> `douban`
- `TMDB` -> `tmdb`

### 步骤 2：确定频道

来源确定后执行：

```bash
cli-anything-ms --json media recommend channels --source <alias>
```

频道通常是 `movie` 或 `tv`。
如果用户没说清楚，就展示频道并要求用户确认，不要猜。

### 步骤 3：读取动态选项

频道确定后执行：

```bash
cli-anything-ms --json media recommend options --source <alias> --channel <channel>
```

必须先读动态选项，不能硬编码不同平台或频道的筛选项。
按每组的：

- `id`
- `text`
- `options[].text`
- `options[].value`

解析用户偏好。

构造 `--options` JSON 的规则：

- 默认包含当前返回的全部 option group `id`
- 用户未指定的项统一填空字符串 `""`
- 用户明确提到的偏好，按 `text` 匹配成真实 `value`

例如用户说“高分优先”“2025”“动作”，就先在当前平台和频道的 options 中找到这些文本，再填入对应的 value。

如果用户提到的筛选项不在当前 options 里，明确告诉用户该平台或频道不支持这个条件，并要求用户调整。

### 步骤 4：获取推荐条目

构造完整的 `--options` JSON 后执行：

```bash
cli-anything-ms --json media recommend items --source <alias> --channel <channel> --options '<json>' --page <n> --page-size <n>
```

分页规则：

- 默认 `page=1`
- 默认 `page-size=10`
- 如果用户说“前 N 个”，把 `page-size` 设为 `N`
- 如果用户要求看第 N 页，传 `--page N`

### 步骤 5：展示结果

先输出简洁摘要，不直接倾倒整段 JSON。
至少包含：

- 标题
- 年份
- 类型
- 评分
- RSS
- 入库状态
- 海报

如果用户明确要求看原始结果，再补充原始 JSON。

## 注意事项

- 这个技能只做推荐浏览，不继续执行订阅。
- 不跳过 `options` 直接猜平台参数。
- 不直接调用后端接口。
- 未指定筛选项时，为当前返回的全部 option group 填空字符串。
- 海报展示属于技能层格式化逻辑，不要要求 CLI 自己渲染图片。

