---
name: ms-site-signin
description: 查看或执行 ms 站点签到时使用，例如“站点签到记录”“哪些站点签到失败”“给馒头签到”“执行站点签到”“全部站点签到”。
---

# ms Site Sign-In

## 概述

通过本地 `cli-anything-ms` CLI 查看站点签到记录，并在用户明确要求时提交站点签到任务。
签到可能触发站点访问；不要在用户只是查询状态时执行签到。

## 安装

```bash
pip install cli-anything-ms
```

## 查看签到记录

用户问“签到记录”“哪些站签到失败”“今天签到情况”时执行：

```bash
cli-anything-ms --json site sign-in history --page 1 --page-size 20
```

用户指定站点名称时追加：

```bash
--site-name "<site name>"
```

回复时说明站点、签到结果、签到信息和签到时间。优先点名失败、未登录或异常站点。

## 执行签到

只有用户明确说“签到”“执行签到”“给某站签到”“全部站点签到”时才执行。

指定站点签到前，先用站点列表确认目标 ID：

```bash
cli-anything-ms --json site list --type sign-in --enabled true
```

确认目标后执行：

```bash
cli-anything-ms --json site sign-in go --id <site_id>
```

多个站点重复传 `--id`。用户明确要求全部已开启签到的站点签到时，执行：

```bash
cli-anything-ms --json site sign-in go
```

执行后只说明签到任务已提交，再建议查看签到记录确认结果；不要承诺已经全部成功。

## 注意事项

- 用户只是问“站点状态”“是否已签到”时，使用 `ms-site-state` 或签到历史，不执行签到。
- 如果站点名称匹配到多个候选，不要猜，先让用户确认。
- 不修改站点配置、Cookie 或开关。
- 不直接调用后端接口，统一通过 `cli-anything-ms`。
- 不把完整原始 JSON 直接贴给用户，除非用户明确要求。
