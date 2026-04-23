# cli-anything-ms - 测试计划

## 测试目标

验证 `ms` harness 的首版骨架可安装、可解析连接配置，并保持稳定的 JSON 输出。

## 单元测试

文件：`test_core.py`

覆盖点：

- `ConnectionConfig` 的 CLI > env > config 优先级
- 配置文件保存和读取
- API key 脱敏展示
- `MSClient` URL 拼接与 Bearer 鉴权头
- `MediaManager.search` 的来源映射和 query 拼装
- `SubscribeManager.get_default_config` 的 detail 路径访问
- `SubscribeManager.add` 的默认配置合并与 save 请求
- `ApiResponse` 对标准 `code/message/data` 的解包
- 非标准响应的保留
- `media search` 的 JSON 输出、人类可读表格输出、空结果和参数校验
- `subscribe add` 的最小参数、TV 默认 season、movie 不允许 season、空白 name 校验

运行方式：

```bash
pytest cli_anything/ms/tests/test_core.py -v
```

## E2E / subprocess 测试

文件：`test_full_e2e.py`

覆盖点：

- `cli-anything-ms --help`
- `cli-anything-ms media search --help`
- `cli-anything-ms subscribe add --help`
- `cli-anything-ms config save-connection`
- 已安装命令与 `python -m cli_anything.ms` 入口兼容

可选联调：

当环境变量已设置或本地 `~/.ms-cli.yaml` 已配置时，额外验证：

```bash
cli-anything-ms --json media search --source tmdb --keyword Interstellar
```

运行方式：

```bash
pytest cli_anything/ms/tests/test_full_e2e.py -v
```
