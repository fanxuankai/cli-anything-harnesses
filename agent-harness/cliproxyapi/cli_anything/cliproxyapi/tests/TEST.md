# CLIProxyAPI CLI Harness - 测试计划

## 测试策略

### 单元测试 (test_core.py)
使用合成数据，不依赖外部服务。通过 mock HTTP 响应测试所有核心模块。

覆盖范围：
- **client.py**: ConnectionConfig 解析（环境变量、配置文件、命令行参数优先级）
- **config.py**: ConfigManager 所有方法（get/set 配置项）
- **auth.py**: AuthManager CRUD 操作、`auth list` 本地启用/禁用筛选、`codex-quota` 额度查询
- **oauth.py**: OAuthManager 提供商验证和认证 URL 请求
- **models.py**: ModelManager 模型列表、别名、排除规则
- **usage.py**: UsageManager 统计数据操作
- **logs.py**: LogManager 日志操作
- **api_keys.py**: APIKeyManager 各类密钥管理
- **proxy.py**: ProxyManager 代理设置和 Amp 集成
- **output.py**: 输出格式化工具

### E2E 测试 (test_full_e2e.py)
需要运行中的 CLIProxyAPI 服务器。测试真实 API 调用流程。

覆盖范围：
- 健康检查
- 配置读取和更新
- 认证文件上传/列表/删除
- `auth list --enabled|--disabled`
- `auth codex-quota`
- 模型列表获取
- API 密钥管理
- 使用统计
- 日志查看
- `--json` 输出模式验证
- CLI subprocess 测试

### Subprocess 测试
通过 `_resolve_cli()` 函数测试安装后的命令行工具。

## 运行方式

```bash
# 单元测试（无需服务器）
pytest cli_anything/cliproxyapi/tests/test_core.py -v

# E2E 测试（需要运行中的 CLIProxyAPI 服务器）
CPA_URL=http://127.0.0.1:8317 CPA_KEY=your-key pytest cli_anything/cliproxyapi/tests/test_full_e2e.py -v

# 全部测试
pytest cli_anything/cliproxyapi/tests/ -v
```

## 测试结果

### 单元测试 (test_core.py) - 55 passed

```text
uv run pytest cli_anything/cliproxyapi/tests/test_core.py -v

...
test_core.py::TestAuthManager::test_list_auth_files PASSED
test_core.py::TestAuthManager::test_list_auth_files_enabled_only PASSED
test_core.py::TestAuthManager::test_list_auth_files_disabled_only PASSED
test_core.py::TestAuthManager::test_refresh_auth_files PASSED
test_core.py::TestAuthManager::test_delete_auth_file PASSED
test_core.py::TestAuthManager::test_patch_auth_file_status PASSED
test_core.py::TestAuthManager::test_get_model_definitions PASSED
test_core.py::TestAuthManager::test_get_auth_file_models PASSED
...

============================== 55 passed in 0.19s ==============================
```

### E2E / CLI 测试 (test_full_e2e.py) - 7 passed, 23 skipped

```text
uv run pytest cli_anything/cliproxyapi/tests/test_full_e2e.py -v

...
test_full_e2e.py::TestAuth::test_list_auth_files SKIPPED
test_full_e2e.py::TestAuth::test_list_enabled_auth_files SKIPPED
test_full_e2e.py::TestAuth::test_list_disabled_auth_files SKIPPED
test_full_e2e.py::TestAuth::test_codex_quota SKIPPED
test_full_e2e.py::TestAuth::test_list_auth_models SKIPPED
...
test_full_e2e.py::TestCLISubprocess::test_help_flag PASSED
test_full_e2e.py::TestCLISubprocess::test_version_flag PASSED
test_full_e2e.py::TestCLISubprocess::test_no_args_shows_help PASSED
test_full_e2e.py::TestCLISubprocess::test_json_flag_no_server PASSED
test_full_e2e.py::TestCLISubprocess::test_all_command_groups_have_help PASSED
test_full_e2e.py::TestCLISubprocess::test_api_call_help PASSED
test_full_e2e.py::TestCLISubprocess::test_auth_codex_quota_help PASSED

======================== 7 passed, 23 skipped in 1.72s =========================
```

## 测试覆盖率总结

| 模块 | 测试数 | 通过率 |
|------|--------|--------|
| ConnectionConfig | 5 | 100% |
| ManagementClient | 5 | 100% |
| ConfigManager | 7 | 100% |
| AuthManager | 8 | 100% |
| OAuthManager | 6 | 100% |
| ModelManager | 3 | 100% |
| UsageManager | 2 | 100% |
| LogManager | 3 | 100% |
| APIKeyManager | 7 | 100% |
| ProxyManager | 5 | 100% |
| OutputUtils | 2 | 100% |
| CLISubprocess (E2E) | 7 | 100% |
| **总计** | **60+** | **100%** |
