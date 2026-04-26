---
name: ms-site-state
description: 查看 ms 站点状态、站点列表、站点统计、上传下载量、魔力值、做种数据、登录状态和签到状态时使用，例如“站点状态”“站点统计”“各站上传下载”“哪些站没登录”“今天站点数据”。
---

# ms Site State

## 概述

通过本地 `cli-anything-ms` CLI 查看 ms 站点状态和站点统计数据。
这个技能只读，不签到、不同步站点数据、不修改站点配置。

## 安装

```bash
pip install cli-anything-ms
```

## 默认查询

用户只说“站点状态”“站点统计”“站点情况”时，先执行：

```bash
cli-anything-ms --json site data total
cli-anything-ms --json site data latest
```

回复时先给总体上传量、下载量、做种数量、做种体积和魔力值，再列出重点站点状态。

## 站点列表

用户问“有哪些站点”“哪些站开启了签到/统计/搜索”时执行：

```bash
cli-anything-ms --json site list
```

按需要追加：

```bash
--enabled true
--type statistic
--type sign-in
--type search
--name "<site name>"
```

## 单站查询

用户指定站点名称时，优先执行：

```bash
cli-anything-ms --json site data latest --site-name "<site name>"
```

如果返回多个候选，按名称展示候选并让用户确认。

## 展示规则

- 最多展示前 10 个站点，除非用户要求更多。
- 重点说明站点名、是否登录、是否已签到、分享率、上传量、下载量、魔力值、做种数量、做种体积、统计日期。
- 如果有未登录站点，要明确点名。
- 如果用户只问上传、下载、做种或魔力值，就只突出对应字段。

## 注意事项

- 不调用 `siteData/sync`。
- 不调用 `siteSignIn/go`。
- 不修改站点开关、Cookie、配置或排序。
- 不直接调用后端接口，统一通过 `cli-anything-ms`。
- 不把完整原始 JSON 直接贴给用户，除非用户明确要求。
