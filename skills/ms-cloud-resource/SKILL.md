---
name: ms-cloud-resource
description: 查询和下载 ms 云端资源时使用，例如“查庆余年云端资源”“搜网盘资源”“下载第 1 个云端资源”“转存这个资源”。
---

# ms Cloud Resource

## 概述

通过本地 `cli-anything-ms` CLI 查询 ms 云端资源，并在用户明确要求时提交云下载或转存任务。
这个技能只处理云端资源搜索和下载提交，不管理云端文件、不查看任务进度、不生成 STRM。

## 安装

```bash
pip install cli-anything-ms
```

## 查询云端资源

- 适用于：
    - `查庆余年云端资源`
    - `搜一下流浪地球网盘资源`
    - `找 TMDB 95842 第 1 季第 46 集`
    - `看贡献者 931 的资源`
- 查询时直接执行：

  ```bash
  cli-anything-ms --json cloud-resource search --keyword "<keyword>" --page 1 --page-size 5
  ```

- 如果用户给了 TMDB ID，必须同时知道电影还是电视剧：
    - `电影` -> `movie`
    - `电视剧` -> `tv`
    - 用户没说清楚时，先让用户补充类型，不要猜。
- TMDB 查询示例：

  ```bash
  cli-anything-ms --json cloud-resource search --tmdb-id <tmdb_id> --type <movie|tv> --season <season> --episode <episode> --page-size 5
  ```

- 可按用户描述追加过滤：
    - 贡献者 ID -> `--creator-id`
    - 季 -> `--season`
    - 单集 -> `--episode`
    - 集数范围 -> `--begin-episode` 和 `--end-episode`
    - “前 N 个” -> `--page-size N`

## 展示结果

- 最多展示 5 条，除非用户明确要求更多。
- 用自然中文说明标题、大小、网盘、贡献者、TMDB、链接类型、是否可下载。
- 不要把完整原始 JSON 直接贴给用户，除非用户明确要求。
- 保留本轮搜索结果中的 `download_request`，后续下载必须从选中条目的 `download_request` 取值。

## 下载或转存

- 只有用户明确说“下载”“转存”“添加云下载”“保存到云盘”时，才提交下载。
- 下载前必须基于本轮或刚刚明确的搜索结果，让用户选中具体资源；不要凭标题重新拼下载请求。
- 执行：

  ```bash
  cli-anything-ms --json cloud-resource download --request '<download_request_json>'
  ```

- 如果用户指定保存目录，追加：

  ```bash
  --dir "<cloud_storage_dir>"
  ```

- 下载命令只表示任务已提交，不代表资源已经下载或转存完成。
- 如果下载失败，清楚转述 CLI 返回的失败原因。

## 注意事项

- 不直接调用后端接口，统一通过 `cli-anything-ms`。
- 不手写 `download_request`，只使用搜索结果里已有的字段。
- 不自动批量下载全部结果，除非用户明确要求批量下载哪些条目。
- 不删除、不移动、不重命名云端文件。
- 不承诺任务完成状态；需要任务进度时，说明当前技能不覆盖任务查询。
