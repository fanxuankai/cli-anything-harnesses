---
name: ms-download
description: 查看和管理 ms 下载器、下载中任务和下载历史时使用，例如“下载任务”“下载器状态”“下载中”“下载历史”“暂停这个下载”“恢复下载”“删除下载任务”。
---

# ms Download

## 概述

通过本地 `cli-anything-ms` CLI 查看 ms 下载器、下载中任务和下载历史。
默认只读；只有用户明确要求“暂停”“恢复”“删除下载任务”时，才执行对应变更操作。

## 安装

```bash
pip install cli-anything-ms
```

## 默认查询

用户只说“下载任务”“下载中”“当前下载”时，执行：

```bash
cli-anything-ms --json download downloading
```

回复时最多展示 10 条，说明标题、进度、速度、状态、是否暂停、站点和保存路径。

## 下载器

用户问“下载器”“下载器状态”“默认下载器”时，执行：

```bash
cli-anything-ms --json download downloaders
```

回复时说明下载器名称、类型、是否开启、是否默认、地址、监控目录和备注。不要展示账号、密码、token 或完整配置。

## 下载历史

用户问“下载历史”“已下载记录”时，执行：

```bash
cli-anything-ms --json download history --page 1 --page-size 20
```

如果用户给出标题、类型或站点，追加对应筛选参数。回复时最多展示 10 条，说明标题、类型、年份、站点、种子标题、下载 ID 和创建时间。

## 任务选择

- 用户给了下载 ID，直接使用该 ID。
- 用户只说“第几个”“这个下载”“卡住的下载”时，先执行 `download downloading`，基于当前结果选择具体任务。
- 不能确定唯一任务时，先让用户确认。

## 变更操作

只有用户明确要求时才执行：

```bash
cli-anything-ms --json download pause --id <download_id>
cli-anything-ms --json download resume --id <download_id>
cli-anything-ms --json download delete --id <download_id>
```

只有用户明确说“同时删除文件”“删除已下载文件”时，删除命令才追加：

```bash
--delete-file
```

执行后只说明任务操作已提交，不承诺任务已经完成。

## 注意事项

- 不新增种子、磁力或订阅下载。
- 不清空下载历史。
- 不编辑下载器配置。
- 不删除下载器。
- 不直接调用后端接口，统一通过 `cli-anything-ms`。
- 不把完整原始 JSON 直接贴给用户，除非用户明确要求。
