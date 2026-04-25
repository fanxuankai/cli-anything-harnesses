---
name: ms-cloud-resource-rank
description: 查看 ms 云端资源 HASH 上报贡献榜时使用，例如“云端资源贡献榜”“洪荒封神榜”“荣耀数量榜”“今日榜”“7天榜”“总榜”“我的贡献排名”。
---

# ms Cloud Resource Rank

## 概述

通过本地 `cli-anything-ms` CLI 查看 ms 云端资源 HASH 上报贡献榜。
这个技能只查看贡献榜和当前登录用户排名，不搜索具体资源、不下载、不转存。

## 安装

```bash
pip install cli-anything-ms
```

## 查询榜单

- 默认查今日荣耀数量榜：

  ```bash
  cli-anything-ms --json cloud-resource rank --range today --stat count
  ```

- 榜单类型映射：
    - `洪荒封神榜`、`体积榜`、`按体积` -> `--stat size`
    - `荣耀数量榜`、`数量榜`、`按数量` -> `--stat count`
- 时间范围映射：
    - `今日榜`、`今天` -> `--range today`
    - `7天榜`、`最近7天`、`本周` -> `--range week`
    - `总榜`、`全部` -> `--range all`
- 用户说“刷新”时追加 `--refresh`；默认不刷新缓存。

## 展示结果

- 最多展示前 5 名，除非用户明确要求更多。
- 说明每条的排名、贡献者、数量、体积、当前维度值。
- 补充当前登录用户排名、贡献值、超越百分比。
- 如果用户要查看某个贡献者的云端资源，使用 `ms-cloud-resource` 按 `creator_id` 搜索。

## 注意事项

- 不直接调用后端接口，统一通过 `cli-anything-ms`。
- 不把完整原始 JSON 直接贴给用户，除非用户明确要求。
- 不提交下载或转存任务。
