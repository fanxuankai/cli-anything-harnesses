# Contributing

感谢参与维护 `cli-anything-harnesses`。

本仓库基于 CLI-Anything 方法论维护多个可独立安装的 CLI harness，并配套提供 Codex / Agent skills。

## 开发原则

- 优先封装真实后端、真实 API、已有 CLI 或软件原生能力。
- 保持 CLI 的 `--json` 输出稳定，避免破坏 Agent 调用流程。
- 修改 harness 逻辑时，同步检查对应 `skills/*/SKILL.md`。
- 修改 skill 时，确认它描述的流程和实际 CLI 行为一致。
- 不提交账号、token、cookie、私有服务地址等敏感信息。

## 本地安装

```bash
pip install -e agent-harness/ms
pip install -e agent-harness/cliproxyapi
```

## 测试

```bash
python -m pytest agent-harness/ms/cli_anything/ms/tests
python -m pytest agent-harness/cliproxyapi/cli_anything/cliproxyapi/tests
```

## Pull Request 要求

- 说明改动影响的 harness 或 skill。
- 说明是否改变 CLI 命令、参数或 JSON 输出。
- 附上已运行的验证命令。
- 如果没有运行测试，说明原因。
