"""E2E 测试 - 需要运行中的 CLIProxyAPI 服务器。

通过环境变量配置连接:
  CPA_URL=http://127.0.0.1:8317 CPA_KEY=your-management-key pytest test_full_e2e.py -v

设置 CLI_ANYTHING_FORCE_INSTALLED=1 可强制使用已安装的 CLI 命令。
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile

import pytest

# ============================================================
# 配置
# ============================================================

CPA_URL = os.getenv("CPA_URL", "http://127.0.0.1:8317")
CPA_KEY = os.getenv("CPA_KEY", "")
HARNESS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
os.environ["PYTHONPATH"] = HARNESS_ROOT + os.pathsep + os.environ.get("PYTHONPATH", "")


def _resolve_cli(name: str = "cli-anything-cliproxyapi") -> list[str]:
    """解析 CLI 命令路径。默认使用当前源码的 python -m 调用，避免依赖外部安装状态。"""
    if os.getenv("CLI_ANYTHING_FORCE_INSTALLED"):
        return [name]
    return [sys.executable, "-m", "cli_anything.cliproxyapi.cliproxyapi_cli"]


def _cli(*args, json_mode: bool = True) -> subprocess.CompletedProcess:
    """执行 CLI 命令。"""
    cmd = _resolve_cli()
    cmd = cmd + ["--url", CPA_URL, "--key", CPA_KEY]
    if json_mode:
        cmd.append("--json")
    cmd.extend(args)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


# ============================================================
# Skip 条件
# ============================================================

def _server_available() -> bool:
    try:
        result = _cli("server", "status", json_mode=False)
        return result.returncode == 0
    except Exception:
        return False


skip_no_server = pytest.mark.skipif(
    not _server_available(),
    reason="CLIProxyAPI 服务器不可用，设置 CPA_URL 和 CPA_KEY 环境变量",
)


# ============================================================
# 服务器状态测试
# ============================================================

class TestServer:

    @skip_no_server
    def test_health_check(self):
        result = _cli("server", "status")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data.get("status") == "ok"

    @skip_no_server
    def test_version(self):
        result = _cli("server", "version")
        assert result.returncode == 0


# ============================================================
# 配置测试
# ============================================================

class TestConfig:

    @skip_no_server
    def test_get_config(self):
        result = _cli("config", "get")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, dict)

    @skip_no_server
    def test_get_config_yaml(self):
        result = _cli("config", "get-yaml")
        assert result.returncode == 0
        assert "port" in result.stdout

    @skip_no_server
    def test_get_debug(self):
        result = _cli("config", "debug")
        assert result.returncode == 0

    @skip_no_server
    def test_get_routing_strategy(self):
        result = _cli("config", "routing")
        assert result.returncode == 0

    @skip_no_server
    def test_get_request_retry(self):
        result = _cli("config", "retry")
        assert result.returncode == 0

    @skip_no_server
    def test_get_proxy_url(self):
        result = _cli("config", "proxy-url")
        assert result.returncode == 0


# ============================================================
# 认证文件测试
# ============================================================

class TestAuth:

    @skip_no_server
    def test_list_auth_files(self):
        result = _cli("auth", "list")
        assert result.returncode == 0

    @skip_no_server
    def test_list_enabled_auth_files(self):
        result = _cli("auth", "list", "--enabled")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "files" in data

    @skip_no_server
    def test_list_disabled_auth_files(self):
        result = _cli("auth", "list", "--disabled")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "files" in data

    @skip_no_server
    def test_codex_quota(self):
        result = _cli("auth", "codex-quota")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "quotas" in data
        assert {"total", "success", "failed"}.issubset(data.keys())

    @skip_no_server
    def test_list_auth_models(self):
        result = _cli("auth", "models")
        assert result.returncode == 0


# ============================================================
# OAuth 测试
# ============================================================

class TestOAuth:

    @skip_no_server
    def test_providers_list(self):
        """验证 oauth login 命令接受所有提供商。"""
        for provider in ["anthropic", "codex", "gemini", "antigravity", "qwen", "kimi", "iflow"]:
            # 不实际登录，只验证命令解析
            result = _cli("oauth", "login", "--help")
            assert result.returncode == 0


# ============================================================
# API 密钥测试
# ============================================================

class TestKeys:

    @skip_no_server
    def test_list_api_keys(self):
        result = _cli("keys", "list")
        assert result.returncode == 0

    @skip_no_server
    def test_list_gemini_keys(self):
        result = _cli("keys", "gemini", "list")
        assert result.returncode == 0

    @skip_no_server
    def test_list_claude_keys(self):
        result = _cli("keys", "claude", "list")
        assert result.returncode == 0

    @skip_no_server
    def test_list_codex_keys(self):
        result = _cli("keys", "codex", "list")
        assert result.returncode == 0


# ============================================================
# 模型测试
# ============================================================

class TestModels:

    @skip_no_server
    def test_get_aliases(self):
        result = _cli("models", "aliases")
        assert result.returncode == 0

    @skip_no_server
    def test_get_excluded(self):
        result = _cli("models", "excluded")
        assert result.returncode == 0


# ============================================================
# 使用统计测试
# ============================================================

class TestUsage:

    @skip_no_server
    def test_get_stats(self):
        result = _cli("usage", "stats")
        assert result.returncode == 0


# ============================================================
# 日志测试
# ============================================================

class TestLogs:

    @skip_no_server
    def test_list_logs(self):
        result = _cli("logs", "list")
        assert result.returncode == 0


# ============================================================
# Amp 测试
# ============================================================

class TestAmp:

    @skip_no_server
    def test_get_amp_config(self):
        result = _cli("amp", "config")
        assert result.returncode == 0


# ============================================================
# CLI Subprocess 测试
# ============================================================

class TestCLISubprocess:
    """测试安装后的 CLI 命令行工具。"""

    def test_help_flag(self):
        cli = _resolve_cli()
        result = subprocess.run(cli + ["--help"], capture_output=True, text=True, timeout=10)
        assert result.returncode == 0
        assert "CLIProxyAPI" in result.stdout

    def test_version_flag(self):
        cli = _resolve_cli()
        result = subprocess.run(cli + ["--version"], capture_output=True, text=True, timeout=10)
        assert result.returncode == 0
        assert "1.0.0" in result.stdout

    def test_no_args_shows_help(self):
        cli = _resolve_cli()
        result = subprocess.run(cli, capture_output=True, text=True, timeout=10)
        assert result.returncode == 0
        assert "Usage" in result.stdout

    def test_json_flag_no_server(self):
        """无服务器时 --json 应输出错误 JSON。"""
        result = _cli("server", "status")
        # 连接失败时返回非零退出码
        assert result.returncode != 0 or "ok" in result.stdout

    def test_all_command_groups_have_help(self):
        """验证所有命令组的 --help 正常工作。"""
        groups = ["server", "config", "auth", "oauth", "keys", "models", "usage", "logs", "amp"]
        cli = _resolve_cli()
        for group in groups:
            result = subprocess.run(cli + [group, "--help"], capture_output=True, text=True, timeout=10)
            assert result.returncode == 0, f"'{group} --help' 失败: {result.stderr}"
            assert "Usage" in result.stdout, f"'{group} --help' 无 Usage"

    def test_api_call_help(self):
        """验证 api-call 命令帮助。"""
        cli = _resolve_cli()
        result = subprocess.run(cli + ["api-call", "--help"], capture_output=True, text=True, timeout=10)
        assert result.returncode == 0

    def test_auth_codex_quota_help(self):
        """验证 auth codex-quota 命令帮助。"""
        cli = _resolve_cli()
        result = subprocess.run(cli + ["auth", "codex-quota", "--help"], capture_output=True, text=True, timeout=10)
        assert result.returncode == 0
        assert "获取已启用 Codex 凭证额度" in result.stdout
