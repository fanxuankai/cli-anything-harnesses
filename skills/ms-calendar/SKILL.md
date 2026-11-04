---
name: ms-calendar
description: 查看追剧日历、订阅日历、全平台播出日历，或把追剧日历加到手机日历 App 时使用，例如“今天有什么更新”“本周追剧日历”“最近有什么在播”“把追剧日历加到手机日历”。
---

# ms Calendar

## 概述

通过本地 `cli-anything-ms` CLI 查看订阅日历，回答“今天/本周有什么更新、XX 什么时候更新”，并把日历订阅地址给到外部日历 App。
这个技能只读，不订阅、不刷新、不修改任何配置。

## 安装

```bash
pip install cli-anything-ms
```

## 触发场景

- `今天有什么更新`
- `本周追剧日历`
- `XX 什么时候更新`
- `最近有什么在播`
- `把追剧日历加到手机日历`
- `给我日历订阅地址`

## 查看日历

默认查看未来 7 天：

```bash
cli-anything-ms --json calendar list
```

按用户说法调整范围：

- “未来三天”“这周” -> `--days 3` / `--days 7`
- “从下周一开始” -> `--from 2026-11-09`（配 `--days`）
- 只看某部剧的更新时间 -> `--subscribe-id <id>`（不确定编号时先让用户跑订阅列表确认）

输出已经按天分组。展示规则：

- 先说一句“这是从 X 开始 N 天内的更新”，再按天列出：剧名（年份）、第几季第几集、具体时间。
- 今天之前的条目默认不展示；如果整个范围都没有条目，直接说“这几天没有更新的剧集”。
- 不要把内部字段名或原始 JSON 写给用户看，除非用户明确要求原始返回。

## iCal 订阅地址

用户想把追剧日历加到手机或电脑的日历 App 时执行：

```bash
cli-anything-ms --json calendar ical-urls
```

- 有地址时，完整给出订阅地址，并用一句话说明怎么用：把地址添加到日历 App 的“订阅日历/添加账户”里即可自动同步更新。
- 返回为空时，按 CLI 给出的原因转述：
    - 缺外部访问域名 → 提示先在系统设置里填好外部访问域名
    - 缺 API Key → 提示先在安全中心创建 API Key
- iCal 地址包含访问凭据，提醒用户不要公开分享。

## 全平台播出日历

用户问的不是自己订阅的剧，而是「最近有什么在播」「这周有什么新剧」时，走全平台播出日历，按三步查：

1. 先看可用的媒体类型：

   ```bash
   cli-anything-ms --json calendar airing-types
   ```

2. 再看该类型下的平台：

   ```bash
   cli-anything-ms --json calendar airing-platforms --media-type <media_type>
   ```

   用户没指定平台时选「全部」（返回里 value 为 all 的项）。

3. 看一段时间的播出安排：

   ```bash
   cli-anything-ms --json calendar airing-days --media-type <media_type> --platform <platform> --days 14
   ```

   按天说明每天有多少部播出；用户对某天感兴趣时再看当天明细：

   ```bash
   cli-anything-ms --json calendar airing-shows --media-type <media_type> --platform <platform> --date <YYYY-MM-DD>
   ```

展示时用自然中文介绍剧名、年份、评分；不要把内部字段名写给用户看。

## 注意事项

- 这个技能只查日历，不新增订阅、不刷新订阅。
- 用户想订阅某部剧时，交给 `ms-sub` 处理。
- 不直接调用后端接口，统一通过 `cli-anything-ms`。
- 不把完整原始 JSON 直接贴给用户，除非用户明确要求。
