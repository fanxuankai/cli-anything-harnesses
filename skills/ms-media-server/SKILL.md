---
name: ms-media-server
description: 查看和同步 ms 媒体服务器时使用，例如“媒体服务器状态”“媒体服务同步信息”“媒体库列表”“同步历史”“正在播放”“最近添加”“继续观看”“立即同步媒体库”。
---

# ms Media Server

## 概述

通过本地 `cli-anything-ms` CLI 查看 ms 媒体服务器、同步统计、媒体库和媒体项目。
默认只读；只有用户明确要求“同步”“立即同步”“刷新媒体库”时，才发起媒体库同步任务。

## 安装

```bash
pip install cli-anything-ms
```

## 默认查询

用户只说“媒体服务器”“媒体服务状态”“同步信息”时，执行：

```bash
cli-anything-ms --json media-server list
```

回复时按服务器说明名称、类型、是否开启、是否默认、电影数、电视剧数、同步耗时、同步时间和更新时间。

## 服务器选择

- 用户给了服务器 ID，直接使用该 ID。
- 用户给了服务器名称，先执行 `media-server list`，按名称匹配对应服务器。
- 如果有多个候选，不要猜，先让用户确认具体是哪一个。
- 如果用户没有指定服务器，但查询需要 ID，先列出服务器并让用户选择。

## 常用查询

- 媒体库列表：

  ```bash
  cli-anything-ms --json media-server libraries --id <id>
  ```

- 同步统计：

  ```bash
  cli-anything-ms --json media-server statistics --id <id>
  ```

- 同步明细：

  ```bash
  cli-anything-ms --json media-server sync-items --id <id> --page 1 --page-size 20
  ```

- 查漏集同步明细时追加：

  ```bash
  --miss-eps true
  ```

- 正在播放、最近添加、继续观看：

  ```bash
  cli-anything-ms --json media-server playing --id <id>
  cli-anything-ms --json media-server latest --id <id> --num 12
  cli-anything-ms --json media-server resume --id <id> --num 12
  ```

## 立即同步

只有用户明确说“同步”“立即同步”“刷新媒体库”时才执行：

```bash
cli-anything-ms --json media-server sync-run --id <id>
```

执行前必须先确认目标服务器。执行后只说明同步任务已发起，不承诺已经同步完成。

## 注意事项

- 不删除服务器。
- 不删除同步历史。
- 不编辑服务器配置。
- 不设置默认服务器。
- 不保存同步配置。
- 不直接调用后端接口，统一通过 `cli-anything-ms`。
- 不把完整原始 JSON 直接贴给用户，除非用户明确要求。
