---
name: ms-status
description: 一句话总览 ms 系统状态、工作台概况、系统体检或版本更新时使用，例如“系统状态”“家里服务怎么样”“体检有没有问题”“有没有新版本”。
---

# ms Status

## 概述

通过本地 `cli-anything-ms` CLI 一句话总览 ms 整体运行情况：站点、系统、媒体库、播放四个摘要，或系统体检结果和版本状态。
这个技能只读，不做任何变更操作。

## 安装

```bash
pip install cli-anything-ms
```

## 触发场景

- `系统状态`
- `家里服务怎么样`
- `今天概况`
- `体检有没有问题`
- `有没有新版本`

## 一句话总览

用户问整体情况时执行：

```bash
cli-anything-ms --json system workbench
```

像正常汇报一样总结四个方面的关键数字（站点、系统、媒体库、播放），异常或为零的项要点名，不要写成字段清单。
用户要最新数据时追加 `--force`。

## 系统体检

用户问“体检怎么样”“有没有什么问题”时，先用低成本的即时概览：

```bash
cli-anything-ms --json system health
```

说明资源占用和任务队列情况；数值明显偏高（CPU、内存、磁盘使用率）要显式提示。

用户追问具体问题明细时再看完整报告：

```bash
cli-anything-ms --json system health-report
```

只点名非正常的检查项，转述结论和建议；全部正常就一句话带过。
不要主动执行单项重测或忽略操作。

## 版本状态

用户问“有没有新版本”时执行：

```bash
cli-anything-ms --json system version
```

有更新时告知最新版本号；只提示，不引导升级操作。

## 注意事项

- 硬件细节（磁盘温度、风扇、UPS）问的是 NAS 本身，交给 `ms-nas-state`；这个技能只管 ms 服务侧。
- 不直接调用后端接口，统一通过 `cli-anything-ms`。
- 不把完整原始 JSON 直接贴给用户，除非用户明确要求。
