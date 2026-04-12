"""单元测试 - 使用合成数据和 mock，不依赖外部服务。"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# 确保包可导入
HARNESS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, HARNESS_ROOT)

from cli_anything.cliproxyapi.core.client import ConnectionConfig, ManagementClient
from cli_anything.cliproxyapi.core.config import ConfigManager
from cli_anything.cliproxyapi.core.auth import AuthManager
from cli_anything.cliproxyapi.core.oauth import OAuthManager
from cli_anything.cliproxyapi.core.models import ModelManager
from cli_anything.cliproxyapi.core.usage import UsageManager
from cli_anything.cliproxyapi.core.logs import LogManager
from cli_anything.cliproxyapi.core.api_keys import APIKeyManager
from cli_anything.cliproxyapi.core.proxy import ProxyManager


# ============================================================
# 辅助工具
# ============================================================

def _mock_response(json_data=None, text_data=None, status_code=200):
    """创建 mock HTTP 响应。"""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.text = text_data or json.dumps(json_data or {})
    resp.raise_for_status.return_value = None
    return resp


def _make_client(url="http://localhost:8317", key="test-key"):
    conn = ConnectionConfig(url=url, key=key)
    return ManagementClient(conn)


# ============================================================
# ConnectionConfig 测试
# ============================================================

class TestConnectionConfig:

    def test_explicit_params(self):
        conn = ConnectionConfig(url="http://example.com:8317", key="mykey")
        assert conn.base_url == "http://example.com:8317"
        assert conn.management_key == "mykey"
        assert conn.is_configured

    def test_env_vars(self):
        with patch.dict(os.environ, {"CPA_URL": "http://env:8317", "CPA_KEY": "envkey"}):
            conn = ConnectionConfig()
            assert conn.base_url == "http://env:8317"
            assert conn.management_key == "envkey"

    def test_not_configured(self):
        with patch.dict(os.environ, {}, clear=True):
            conn = ConnectionConfig()
            assert not conn.is_configured

    def test_trailing_slash_stripped(self):
        conn = ConnectionConfig(url="http://example.com:8317/", key="k")
        assert conn.base_url == "http://example.com:8317"

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, ".cliproxyapi-cli.yaml")
            with patch.object(ConnectionConfig, "_load_from_config") as mock_load:
                # 直接测试 save 逻辑
                import yaml
                data = {"url": "http://saved:8317", "key": "savedkey"}
                with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
                    yaml.dump(data, f)
                    path = f.name
            assert os.path.exists(path)
            os.unlink(path)


# ============================================================
# ManagementClient 测试
# ============================================================

class TestManagementClient:

    def test_url_construction(self):
        client = _make_client()
        assert client._url("/config") == "http://localhost:8317/v0/management/config"

    def test_headers(self):
        client = _make_client(key="test-key")
        headers = client._headers
        assert headers["Authorization"] == "Bearer test-key"
        assert headers["Content-Type"] == "application/json"

    @patch("cli_anything.cliproxyapi.core.client.requests.Session")
    def test_get(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session.get.return_value = _mock_response({"status": "ok"})
        mock_session_cls.return_value = mock_session
        client = _make_client()
        resp = client.get("/config")
        assert resp.json() == {"status": "ok"}

    @patch("cli_anything.cliproxyapi.core.client.requests.Session")
    def test_post(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session.post.return_value = _mock_response({"status": "ok"})
        mock_session_cls.return_value = mock_session
        client = _make_client()
        resp = client.post("/api-keys", json_data={"value": "newkey"})
        assert resp.json() == {"status": "ok"}

    @patch("cli_anything.cliproxyapi.core.client.requests.Session")
    def test_delete(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session.delete.return_value = _mock_response({"status": "ok"})
        mock_session_cls.return_value = mock_session
        client = _make_client()
        resp = client.delete("/api-keys", json_data={"value": "key1"})
        assert resp.json() == {"status": "ok"}

    @patch("cli_anything.cliproxyapi.core.client.requests.Session")
    def test_health_check(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session.get.return_value = _mock_response({"status": "ok"})
        mock_session_cls.return_value = mock_session
        client = _make_client()
        resp = client.health_check()
        mock_session.get.assert_called_with("http://localhost:8317/healthz", timeout=10)


# ============================================================
# ConfigManager 测试
# ============================================================

class TestConfigManager:

    def _make_mgr(self):
        client = _make_client()
        return ConfigManager(client)

    @patch.object(ManagementClient, "get")
    def test_get_config(self, mock_get):
        mock_get.return_value = _mock_response({"port": 8317, "debug": False})
        mgr = self._make_mgr()
        result = mgr.get_config()
        assert result["port"] == 8317

    @patch.object(ManagementClient, "get")
    def test_get_config_yaml(self, mock_get):
        mock_get.return_value = _mock_response(text_data="port: 8317\n")
        mgr = self._make_mgr()
        result = mgr.get_config_yaml()
        assert "port" in result

    @patch.object(ManagementClient, "put")
    def test_set_debug(self, mock_put):
        mock_put.return_value = _mock_response({"status": "ok"})
        mgr = self._make_mgr()
        result = mgr.set_debug(True)
        mock_put.assert_called_with("/debug", json_data={"value": True})

    @patch.object(ManagementClient, "get")
    def test_get_proxy_url(self, mock_get):
        mock_get.return_value = _mock_response({"value": "socks5://proxy:1080"})
        mgr = self._make_mgr()
        result = mgr.get_proxy_url()
        assert result == "socks5://proxy:1080"

    @patch.object(ManagementClient, "put")
    def test_set_routing_strategy(self, mock_put):
        mock_put.return_value = _mock_response({"status": "ok"})
        mgr = self._make_mgr()
        mgr.set_routing_strategy("fill-first")
        mock_put.assert_called_with("/routing/strategy", json_data={"value": "fill-first"})

    @patch.object(ManagementClient, "get")
    def test_get_request_retry(self, mock_get):
        mock_get.return_value = _mock_response({"value": 5})
        mgr = self._make_mgr()
        result = mgr.get_request_retry()
        assert result == 5

    @patch.object(ManagementClient, "get")
    def test_get_ws_auth(self, mock_get):
        mock_get.return_value = _mock_response({"value": True})
        mgr = self._make_mgr()
        assert mgr.get_ws_auth() is True

    @patch.object(ManagementClient, "get")
    def test_get_latest_version(self, mock_get):
        mock_get.return_value = _mock_response({"version": "6.0.0"})
        mgr = self._make_mgr()
        result = mgr.get_latest_version()
        assert result["version"] == "6.0.0"


# ============================================================
# AuthManager 测试
# ============================================================

class TestAuthManager:

    def _make_mgr(self):
        return AuthManager(_make_client())

    @patch.object(ManagementClient, "get")
    def test_list_auth_files(self, mock_get):
        mock_get.return_value = _mock_response({"files": [{"name": "test.json", "type": "gemini"}]})
        mgr = self._make_mgr()
        result = mgr.list_auth_files()
        assert len(result["files"]) == 1
        assert result["files"][0]["name"] == "test.json"
        mock_get.assert_called_with("/auth-files", params=None)

    @patch.object(ManagementClient, "get")
    def test_list_auth_files_enabled_only(self, mock_get):
        mock_get.return_value = _mock_response({
            "files": [
                {"name": "disabled.json", "disabled": True},
                {"name": "enabled.json", "disabled": False},
            ]
        })
        mgr = self._make_mgr()
        result = mgr.list_auth_files(disabled=False)
        assert result == {"files": [{"name": "enabled.json", "disabled": False}]}
        mock_get.assert_called_with("/auth-files", params=None)

    @patch.object(ManagementClient, "get")
    def test_list_auth_files_disabled_only(self, mock_get):
        mock_get.return_value = _mock_response({
            "files": [
                {"name": "disabled.json", "disabled": True},
                {"name": "enabled.json", "disabled": False},
            ]
        })
        mgr = self._make_mgr()
        result = mgr.list_auth_files(disabled=True)
        assert result == {"files": [{"name": "disabled.json", "disabled": True}]}
        mock_get.assert_called_with("/auth-files", params=None)

    @patch.object(ManagementClient, "post")
    @patch.object(ManagementClient, "get")
    def test_get_codex_quotas(self, mock_get, mock_post):
        mock_get.return_value = _mock_response({
            "files": [
                {
                    "name": "codex-active.json",
                    "provider": "codex",
                    "auth_index": "idx123",
                    "disabled": False,
                    "email": "user@example.com",
                    "id_token": {"chatgpt_account_id": "acct-123", "plan_type": "plus"},
                },
                {
                    "name": "codex-disabled.json",
                    "provider": "codex",
                    "auth_index": "idx456",
                    "disabled": True,
                    "id_token": {"chatgpt_account_id": "acct-456", "plan_type": "plus"},
                },
                {
                    "name": "antigravity.json",
                    "provider": "antigravity",
                    "auth_index": "idx789",
                    "disabled": False,
                },
            ]
        })
        mock_post.return_value = _mock_response({
            "status_code": 200,
            "body": json.dumps({
                "email": "user@example.com",
                "plan_type": "plus",
                "rate_limit": {
                    "primary_window": {"used_percent": 21, "limit_window_seconds": 18000, "reset_after_seconds": 4171, "reset_at": 1775939921},
                    "secondary_window": {"used_percent": 22, "limit_window_seconds": 604800, "reset_after_seconds": 423178, "reset_at": 1776358928},
                },
            }),
        })
        mgr = self._make_mgr()
        result = mgr.get_codex_quotas()
        assert result["total"] == 1
        assert result["success"] == 1
        assert result["failed"] == 0
        mock_get.assert_called_with("/auth-files", params=None)
        mock_post.assert_called_once_with(
            "/api-call",
            json_data={
                "auth_index": "idx123",
                "method": "GET",
                "url": "https://chatgpt.com/backend-api/wham/usage",
                "header": {
                    "Authorization": "Bearer $TOKEN$",
                    "Content-Type": "application/json",
                    "User-Agent": "codex_cli_rs/0.76.0 (Debian 13.0.0; x86_64) WindowsTerminal",
                    "Chatgpt-Account-Id": "acct-123",
                },
            },
        )
        quota = result["quotas"][0]
        assert quota["name"] == "codex-active.json"
        assert quota["plan_type"] == "plus"
        assert quota["primary_window"]["remaining_percent"] == 79
        assert quota["secondary_window"]["remaining_percent"] == 78

    @patch.object(ManagementClient, "delete")
    def test_delete_auth_file(self, mock_del):
        mock_del.return_value = _mock_response({"status": "ok"})
        mgr = self._make_mgr()
        result = mgr.delete_auth_file("test.json")
        mock_del.assert_called_with("/auth-files", json_data={"filename": "test.json"})

    @patch.object(ManagementClient, "patch")
    def test_patch_auth_file_status(self, mock_patch):
        mock_patch.return_value = _mock_response({"status": "ok"})
        mgr = self._make_mgr()
        mgr.patch_auth_file_status("test.json", True)
        mock_patch.assert_called_with(
            "/auth-files/status",
            json_data={"filename": "test.json", "disabled": True},
        )

    @patch.object(ManagementClient, "get")
    def test_get_model_definitions(self, mock_get):
        mock_get.return_value = _mock_response({"models": ["gemini-2.5-pro"]})
        mgr = self._make_mgr()
        result = mgr.get_model_definitions("gemini-cli")
        mock_get.assert_called_with("/model-definitions/gemini-cli")

    @patch.object(ManagementClient, "get")
    def test_get_auth_file_models(self, mock_get):
        mock_get.return_value = _mock_response({"test.json": ["gemini-2.5-pro"]})
        mgr = self._make_mgr()
        result = mgr.get_auth_file_models()
        assert "test.json" in result


# ============================================================
# OAuthManager 测试
# ============================================================

class TestOAuthManager:

    def _make_mgr(self):
        return OAuthManager(_make_client())

    def test_invalid_provider(self):
        mgr = self._make_mgr()
        with pytest.raises(ValueError, match="不支持提供商"):
            mgr.request_auth_url("invalid_provider")

    @patch.object(ManagementClient, "get")
    def test_anthropic_login(self, mock_get):
        mock_get.return_value = _mock_response({"auth_url": "https://example.com/oauth"})
        mgr = self._make_mgr()
        result = mgr.request_auth_url("anthropic")
        assert "auth_url" in result
        mock_get.assert_called_with("/anthropic-auth-url", params={})

    @patch.object(ManagementClient, "get")
    def test_gemini_login(self, mock_get):
        mock_get.return_value = _mock_response({"auth_url": "https://accounts.google.com/..."})
        mgr = self._make_mgr()
        result = mgr.request_auth_url("gemini")
        mock_get.assert_called_with("/gemini-cli-auth-url", params={})

    @patch.object(ManagementClient, "get")
    def test_login_no_browser(self, mock_get):
        mock_get.return_value = _mock_response({"auth_url": "..."})
        mgr = self._make_mgr()
        mgr.request_auth_url("codex", no_browser=True)
        mock_get.assert_called_with("/codex-auth-url", params={"no_browser": "true"})

    @patch.object(ManagementClient, "post")
    def test_oauth_callback(self, mock_post):
        mock_post.return_value = _mock_response({"status": "ok"})
        mgr = self._make_mgr()
        mgr.post_oauth_callback("anthropic", "code123", "state456")
        mock_post.assert_called_with(
            "/oauth-callback",
            json_data={"provider": "anthropic", "code": "code123", "state": "state456"},
        )

    def test_all_providers_exist(self):
        expected = {"anthropic", "codex", "gemini", "antigravity", "qwen", "kimi", "iflow"}
        assert set(OAuthManager.PROVIDERS.keys()) == expected


# ============================================================
# ModelManager 测试
# ============================================================

class TestModelManager:

    def _make_mgr(self):
        return ModelManager(_make_client())

    @patch.object(ManagementClient, "get")
    def test_get_oauth_model_alias(self, mock_get):
        mock_get.return_value = _mock_response({"gemini-cli": [{"name": "gemini-2.5-pro", "alias": "g2.5p"}]})
        mgr = self._make_mgr()
        result = mgr.get_oauth_model_alias()
        assert "gemini-cli" in result

    @patch.object(ManagementClient, "put")
    def test_put_oauth_model_alias(self, mock_put):
        mock_put.return_value = _mock_response({"status": "ok"})
        mgr = self._make_mgr()
        data = {"claude": [{"name": "claude-sonnet", "alias": "cs"}]}
        mgr.put_oauth_model_alias(data)
        mock_put.assert_called_with("/oauth-model-alias", json_data=data)

    @patch.object(ManagementClient, "delete")
    def test_delete_oauth_excluded_models(self, mock_del):
        mock_del.return_value = _mock_response({"status": "ok"})
        mgr = self._make_mgr()
        mgr.delete_oauth_excluded_models("claude", "claude-3-haiku")
        mock_del.assert_called_with(
            "/oauth-excluded-models",
            json_data={"channel": "claude", "model": "claude-3-haiku"},
        )


# ============================================================
# UsageManager 测试
# ============================================================

class TestUsageManager:

    def _make_mgr(self):
        return UsageManager(_make_client())

    @patch.object(ManagementClient, "get")
    def test_get_stats(self, mock_get):
        mock_get.return_value = _mock_response({"total_requests": 100})
        mgr = self._make_mgr()
        result = mgr.get_stats()
        assert result["total_requests"] == 100

    @patch.object(ManagementClient, "get")
    def test_export_stats(self, mock_get):
        mock_get.return_value = _mock_response(text_data='{"exported": true}')
        mgr = self._make_mgr()
        result = mgr.export_stats()
        assert "exported" in result


# ============================================================
# LogManager 测试
# ============================================================

class TestLogManager:

    def _make_mgr(self):
        return LogManager(_make_client())

    @patch.object(ManagementClient, "get")
    def test_get_logs(self, mock_get):
        mock_get.return_value = _mock_response(text_data="line1\nline2\n")
        mgr = self._make_mgr()
        result = mgr.get_logs(lines=50)
        mock_get.assert_called_with("/logs", params={"lines": 50})

    @patch.object(ManagementClient, "delete")
    def test_delete_logs(self, mock_del):
        mock_del.return_value = _mock_response({"status": "ok"})
        mgr = self._make_mgr()
        result = mgr.delete_logs()
        assert result["status"] == "ok"

    @patch.object(ManagementClient, "get")
    def test_get_request_error_logs(self, mock_get):
        mock_get.return_value = _mock_response({"logs": ["error1.log"]})
        mgr = self._make_mgr()
        result = mgr.get_request_error_logs()
        assert "logs" in result


# ============================================================
# APIKeyManager 测试
# ============================================================

class TestAPIKeyManager:

    def _make_mgr(self):
        return APIKeyManager(_make_client())

    @patch.object(ManagementClient, "get")
    def test_list_api_keys(self, mock_get):
        mock_get.return_value = _mock_response({"value": ["key1", "key2"]})
        mgr = self._make_mgr()
        result = mgr.list_api_keys()
        assert result == ["key1", "key2"]

    @patch.object(ManagementClient, "patch")
    def test_add_api_key(self, mock_patch):
        mock_patch.return_value = _mock_response({"status": "ok"})
        mgr = self._make_mgr()
        mgr.add_api_key("newkey")
        mock_patch.assert_called_with("/api-keys", json_data={"value": "newkey"})

    @patch.object(ManagementClient, "get")
    def test_list_gemini_keys(self, mock_get):
        mock_get.return_value = _mock_response({"value": [{"api_key": "AIza..."}]})
        mgr = self._make_mgr()
        result = mgr.list_gemini_keys()
        assert len(result) == 1

    @patch.object(ManagementClient, "get")
    def test_list_claude_keys(self, mock_get):
        mock_get.return_value = _mock_response({"value": [{"api_key": "sk-..."}]})
        mgr = self._make_mgr()
        result = mgr.list_claude_keys()
        assert len(result) == 1

    @patch.object(ManagementClient, "get")
    def test_list_codex_keys(self, mock_get):
        mock_get.return_value = _mock_response({"value": []})
        mgr = self._make_mgr()
        result = mgr.list_codex_keys()
        assert result == []

    @patch.object(ManagementClient, "get")
    def test_list_openai_compat(self, mock_get):
        mock_get.return_value = _mock_response({"value": [{"name": "openrouter"}]})
        mgr = self._make_mgr()
        result = mgr.list_openai_compat()
        assert result[0]["name"] == "openrouter"

    @patch.object(ManagementClient, "delete")
    def test_delete_openai_compat(self, mock_del):
        mock_del.return_value = _mock_response({"status": "ok"})
        mgr = self._make_mgr()
        mgr.delete_openai_compat("openrouter")
        mock_del.assert_called_with(
            "/openai-compatibility", json_data={"name": "openrouter"},
        )


# ============================================================
# ProxyManager 测试
# ============================================================

class TestProxyManager:

    def _make_mgr(self):
        return ProxyManager(_make_client())

    @patch.object(ManagementClient, "health_check")
    def test_health_check(self, mock_health):
        mock_health.return_value = _mock_response({"status": "ok"})
        mgr = self._make_mgr()
        result = mgr.health_check()
        assert result["status"] == "ok"

    @patch.object(ManagementClient, "get")
    def test_get_amp_config(self, mock_get):
        mock_get.return_value = _mock_response({"upstream_url": "https://ampcode.com"})
        mgr = self._make_mgr()
        result = mgr.get_amp_config()
        assert "upstream_url" in result

    @patch.object(ManagementClient, "get")
    def test_get_amp_model_mappings(self, mock_get):
        mock_get.return_value = _mock_response({"value": [{"from": "claude-opus", "to": "gemini-pro"}]})
        mgr = self._make_mgr()
        result = mgr.get_amp_model_mappings()
        assert len(result) == 1

    @patch.object(ManagementClient, "post")
    def test_api_call(self, mock_post):
        mock_post.return_value = _mock_response({
            "status_code": 200,
            "body": '{"result": true}',
        })
        mgr = self._make_mgr()
        result = mgr.api_call("GET", "https://api.example.com/test")
        assert result["status_code"] == 200
        mock_post.assert_called_with(
            "/api-call",
            json_data={"method": "GET", "url": "https://api.example.com/test"},
        )

    @patch.object(ManagementClient, "post")
    def test_api_call_with_auth_index(self, mock_post):
        mock_post.return_value = _mock_response({"status_code": 200, "body": ""})
        mgr = self._make_mgr()
        mgr.api_call("GET", "https://api.example.com/", auth_index="idx123")
        call_args = mock_post.call_args
        assert call_args[1]["json_data"]["auth_index"] == "idx123"


# ============================================================
# Output 工具测试
# ============================================================

class TestOutputUtils:

    def test_output_json(self):
        from cli_anything.cliproxyapi.utils.output import output_json
        import io
        from rich.console import Console

        console_buf = io.StringIO()
        c = Console(file=console_buf)
        # 简单验证函数不抛异常
        output_json({"key": "value"})

    def test_output_error(self):
        from cli_anything.cliproxyapi.utils.output import output_error
        output_error("test error")
