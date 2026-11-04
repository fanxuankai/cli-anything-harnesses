# Changelog

## Unreleased

- 漏集检查改走媒体健康体系：新增 `media-health` 命令组，补漏集改为先预览决策再执行；删除已失效的 `media-server miss-episodes-check`（破坏性变更，需后端 ≥ 2026-11 版本）。
- 云资源下载改走按需取料接口，修复提交空链路任务；站点种子支持直接提交下载；新增云存储任务进度查询。
- 订阅新增精简为最小信息并支持透传 TMDB 编号；新增订阅暂停、恢复、删除、刷新等生命周期命令。
- 新增追剧日历 `calendar` 命令组和 `ms-calendar` 技能（含 iCal 订阅地址、全平台播出日历）。
- 新增 `system workbench` 总览、系统体检 `system health`/`health-report`/`version` 命令和 `ms-status` 技能。
- 新增媒体服务器库内实时检索、站点数据刷新、季集查询、演员详情、全源聚合搜索。
- 签到记录支持按结果筛选；云资源搜索支持按体积和发布时间排序。
- 新增技能：`ms-calendar`、`ms-status`。

- 整理 README 的 GitHub、PyPI、Packages 和 Skills 展示。
- 增加项目级 `AGENTS.md`。
- 增加 GitHub issue 和 pull request 模板。
- 更新 CI workflow 的名称、手动触发和 Actions 版本。
- 为 `cli-anything-ms` 增加云端资源搜索、下载提交命令和 `ms-cloud-resource` skill。
- 为 `cli-anything-ms` 增加云端资源贡献榜命令和 `ms-cloud-resource-rank` skill。
- 增加 GitHub Actions PyPI 自动发布流程。
- 增加 GitHub Actions Hermes CLI 和 skill 变更通知流程。
