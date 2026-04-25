# AGENTS.md

## 基本要求

- 始终使用简体中文回复。
- 直接回答问题，不写客套话。
- 代码、命令、文件名使用英文。
- 代码注释和日志优先使用中文。
- 不确定时先查证源码、文档或命令输出，不要猜。

## 项目定位

这是一个基于 `cli-anything` skill 方法论实现的 CLI harness 仓库。

- `agent-harness/ms/`：ms 相关 CLI harness。
- `agent-harness/cliproxyapi/`：CLIProxyAPI 相关 CLI harness。
- `skills/`：面向 Codex/Agent 使用的技能说明。
- `README.md`：仓库安装和使用说明。
- `pyproject.toml`：仓库级 Python 依赖声明。

核心目标是把具体软件、后端服务或已有系统封装成稳定、可脚本化、可被 Agent 调用的命令面。

## CLI-Anything 工作原则

- 新建或维护 harness 时，遵循 `cli-anything` skill 的结构和流程。
- 优先封装真实后端、真实 API、已有 CLI 或软件原生能力，不重新实现业务系统。
- CLI 应提供一次性子命令；目标适合时，保留无子命令时的默认交互入口。
- CLI 必须优先考虑机器可读场景，已有 `--json` 行为不能破坏。
- Python 包使用 `cli_anything.<software>` 命名空间。
- `setup.py` 通过 `console_scripts` 暴露 `cli-anything-<software>` 命令。
- 核心逻辑放在 `core/` 或合适模块中，CLI 文件只做参数解析和输出组织。
- 不删除或重命名已有命令，除非用户明确要求破坏性变更。

## 修改原则

- 优先保持现有目录结构和代码风格。
- 修改 harness 逻辑时，同步检查对应的 skill 是否需要更新。
- 修改 skill 时，确认它描述的流程和实际 CLI 行为一致。
- 修改 CLI 输出时，要考虑 Agent 调用场景，保持 JSON 字段稳定。
- 不要随意改动无关 harness。
- 不要提交本地配置、账号、token、cookie、私有服务地址等敏感信息。

## Skills 编写约定

- `skills/*/SKILL.md` 是工作指引，不写成接口文档。
- 少列内部字段名，除非必须保证解析正确。
- CLI 命令只保留必要示例，不围绕所有参数展开。
- 规则用自然语言描述，例如“先确认用户要看电影还是电视剧”。
- 输出要求写给用户视角，例如“说明是否已订阅、是否已入库”。
- Skill 只做它声明的职责，不要顺手执行订阅、删除、修改配置等额外动作。

## 测试和验证

修改 harness 后，按影响范围选择验证命令：

```bash
python -m pytest agent-harness/ms/cli_anything/ms/tests
python -m pytest agent-harness/cliproxyapi/cli_anything/cliproxyapi/tests
```

手动验证 CLI 时优先使用 JSON 输出，例如：

```bash
cli-anything-ms --json media recommend sources
cli-anything-ms --json subscribe page --type tv --page 1 --page-size 20
```

能验证安装入口时，优先通过 `cli-anything-<software>` 命令运行，而不是只测模块导入。

## Git 和本地状态

- 不回滚用户已有改动。
- 不使用 `git reset --hard` 或 `git checkout --` 清理工作区，除非用户明确要求。
- 不改动 `.venv/`、`.pytest_cache/`、`.idea/`、`.omc/` 等本地状态目录。
- 只提交与当前任务相关的文件。
