"""Unit tests for the Media Saber CLI harness."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner
import pytest


HARNESS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, HARNESS_ROOT)

from cli_anything.ms.core.client import ApiResponse, ConnectionConfig, MSClient
from cli_anything.ms.core.media import MEDIA_SOURCE_MAP, MediaManager
from cli_anything.ms.core.media_server import MediaServerManager
from cli_anything.ms.core.subscribe import SubscribeManager
from cli_anything.ms.ms_cli import main


def _mock_response(*, status_code=200, json_data=None, text_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.ok = 200 <= status_code < 400
    resp.text = text_data if text_data is not None else json.dumps(json_data or {})
    if json_data is None:
        resp.json.side_effect = ValueError("not json")
    else:
        resp.json.return_value = json_data
    return resp


class TestConnectionConfig:

    def test_cli_has_highest_priority(self, monkeypatch, tmp_path):
        config_path = tmp_path / ".ms-cli.yaml"
        monkeypatch.setattr(ConnectionConfig, "DEFAULT_CONFIG_PATH", config_path)
        config_path.write_text("url: http://config\napi_key: config-key\n", encoding="utf-8")
        monkeypatch.setenv("MS_URL", "http://env")
        monkeypatch.setenv("MS_API_KEY", "env-key")

        conn = ConnectionConfig.resolve(url="http://cli", api_key="cli-key")

        assert conn.base_url == "http://cli"
        assert conn.api_key == "cli-key"
        assert conn.url_source == "cli"
        assert conn.api_key_source == "cli"

    def test_env_priority_over_config(self, monkeypatch, tmp_path):
        config_path = tmp_path / ".ms-cli.yaml"
        monkeypatch.setattr(ConnectionConfig, "DEFAULT_CONFIG_PATH", config_path)
        config_path.write_text("url: http://config\napi_key: config-key\n", encoding="utf-8")
        monkeypatch.setenv("MS_URL", "http://env")
        monkeypatch.setenv("MS_API_KEY", "env-key")

        conn = ConnectionConfig.resolve()

        assert conn.base_url == "http://env"
        assert conn.api_key == "env-key"
        assert conn.url_source == "env"
        assert conn.api_key_source == "env"

    def test_config_is_used_when_no_cli_or_env(self, monkeypatch, tmp_path):
        config_path = tmp_path / ".ms-cli.yaml"
        monkeypatch.setattr(ConnectionConfig, "DEFAULT_CONFIG_PATH", config_path)
        monkeypatch.delenv("MS_URL", raising=False)
        monkeypatch.delenv("MS_API_KEY", raising=False)
        config_path.write_text("url: http://config/\napi_key: saved-key\n", encoding="utf-8")

        conn = ConnectionConfig.resolve()

        assert conn.base_url == "http://config"
        assert conn.api_key == "saved-key"
        assert conn.url_source == "config"
        assert conn.api_key_source == "config"

    def test_save_and_mask(self, monkeypatch, tmp_path):
        config_path = tmp_path / ".ms-cli.yaml"
        monkeypatch.setattr(ConnectionConfig, "DEFAULT_CONFIG_PATH", config_path)

        saved_to = ConnectionConfig.save("http://localhost:8899/", "sk-1234567890")
        conn = ConnectionConfig.resolve()

        assert saved_to == config_path
        assert conn.base_url == "http://localhost:8899"
        assert conn.masked_api_key == "sk-1...7890"
        assert conn.is_configured is True

    def test_require_configured(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ConnectionConfig, "DEFAULT_CONFIG_PATH", tmp_path / ".ms-cli.yaml")
        conn = ConnectionConfig.resolve()

        with pytest.raises(ValueError, match="URL is not configured"):
            conn.require_configured()


class TestApiResponse:

    def test_standard_response_is_unwrapped(self):
        response = _mock_response(
            json_data={"code": 0, "message": "ok", "data": {"status": "healthy"}},
        )

        normalized = ApiResponse.from_http_response(response)

        assert normalized.ok is True
        assert normalized.is_standard_response is True
        assert normalized.code == 0
        assert normalized.message == "ok"
        assert normalized.data == {"status": "healthy"}

    def test_mediasaber_success_code_is_treated_as_ok(self):
        response = _mock_response(
            json_data={"code": 20000, "message": "SUCCESS", "data": {"status": "healthy"}},
        )

        normalized = ApiResponse.from_http_response(response)

        assert normalized.ok is True
        assert normalized.code == 20000
        assert normalized.message == "SUCCESS"

    def test_non_standard_response_is_preserved(self):
        response = _mock_response(text_data="plain text body")

        normalized = ApiResponse.from_http_response(response)

        assert normalized.is_standard_response is False
        assert normalized.data == "plain text body"
        assert normalized.raw_body == "plain text body"


class TestMSClient:

    def test_build_url_requires_full_path(self):
        conn = ConnectionConfig.resolve(url="http://localhost:8899", api_key="key")
        client = MSClient(conn)

        with pytest.raises(ValueError, match="must start with '/'"):
            client.build_url("api/v1/system/status")

    @patch("cli_anything.ms.core.client.requests.Session")
    def test_request_sends_bearer_and_json(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session.request.return_value = _mock_response(
            json_data={"code": 0, "message": "ok", "data": {"value": 1}},
        )
        mock_session_cls.return_value = mock_session

        conn = ConnectionConfig.resolve(url="http://localhost:8899", api_key="secret-token")
        client = MSClient(conn)
        response = client.request(
            "POST",
            "/api/v1/system/status",
            params={"verbose": "1"},
            headers={"X-Test": "true"},
            json_body={"hello": "world"},
        )

        assert response.ok is True
        mock_session.request.assert_called_once_with(
            method="POST",
            url="http://localhost:8899/api/v1/system/status",
            params={"verbose": "1"},
            headers={
                "Authorization": "Bearer secret-token",
                "X-Test": "true",
            },
            json={"hello": "world"},
            timeout=30,
        )


class TestMediaManager:

    def test_search_uses_media_search_endpoint(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=0,
            message="success",
            data={"total": 1, "pageNum": 1, "pageSize": 20, "list": [{"title": "Test"}]},
            raw_body={"code": 0, "message": "success", "data": {"total": 1, "pageNum": 1, "pageSize": 20, "list": [{"title": "Test"}]}},
            is_standard_response=True,
        )

        manager = MediaManager(client)
        result = manager.search(source_code=200, keyword="Interstellar", page=2, page_size=5)

        assert result["total"] == 1
        client.request.assert_called_once_with(
            "GET",
            "/api/v1/media/search",
            params={
                "mediaSource": "200",
                "keyword": "Interstellar",
                "pageNum": "2",
                "pageSize": "5",
            },
        )


class TestMediaServerManager:

    def test_miss_episodes_check_uses_media_server_endpoint(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data=[
                {
                    "tmdbId": 139797,
                    "mediaType": "tv",
                    "title": "猎罪图鉴",
                    "year": 2022,
                    "episodes": [
                        {
                            "season": 1,
                            "totalEpisodes": 20,
                            "missEpisodes": [7],
                        }
                    ],
                }
            ],
            raw_body={},
            is_standard_response=True,
        )

        manager = MediaServerManager(client)
        result = manager.miss_episodes_check()

        assert result["total"] == 1
        assert result["items"][0]["title"] == "猎罪图鉴"
        client.request.assert_called_once_with("GET", "/api/v1/mediaServer/missEpisodesCheck")

    def test_miss_episodes_check_limits_to_first_twenty_items(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=20000,
            message="SUCCESS",
            data=[
                {
                    "tmdbId": idx,
                    "mediaType": "tv",
                    "title": f"title-{idx}",
                    "year": 2020,
                    "episodes": [],
                }
                for idx in range(25)
            ],
            raw_body={},
            is_standard_response=True,
        )

        manager = MediaServerManager(client)
        result = manager.miss_episodes_check()

        assert result["total"] == 25
        assert len(result["items"]) == 20
        assert result["items"][0]["title"] == "title-0"
        assert result["items"][-1]["title"] == "title-19"


class TestSubscribeManager:

    def test_get_default_config_uses_detail_endpoint(self):
        client = MagicMock()
        client.request.return_value = ApiResponse(
            status_code=200,
            ok=True,
            code=0,
            message="success",
            data={"type": "movie", "downloaderId": 1},
            raw_body={"code": 0, "message": "success", "data": {"type": "movie", "downloaderId": 1}},
            is_standard_response=True,
        )

        manager = SubscribeManager(client)
        result = manager.get_default_config("movie")

        assert result == {"type": "movie", "downloaderId": 1}
        client.request.assert_called_once_with("GET", "/api/v1/subscribeDefaultConfig/detail/movie")

    def test_add_fetches_default_config_then_saves(self):
        client = MagicMock()
        client.request.side_effect = [
            ApiResponse(
                status_code=200,
                ok=True,
                code=0,
                message="success",
                data={
                    "type": "tv",
                    "filterRuleId": 10,
                    "torrentSortId": 20,
                    "downloaderId": 1,
                    "downloaderParamsId": 2,
                    "downloaderDirectoryId": 3,
                    "rssSites": [11],
                    "searchSites": [22],
                    "autoUpdateTotalEpisode": True,
                    "include": "HDR",
                    "exclude": "CAM",
                    "subCloudStorage": False,
                    "subCloudStoragePath": "/cloud",
                    "csCreatorIds": "1,2",
                    "mediums": ["BluRay"],
                },
                raw_body={},
                is_standard_response=True,
            ),
            ApiResponse(
                status_code=200,
                ok=True,
                code=0,
                message="success",
                data=None,
                raw_body={"code": 0, "message": "success", "data": None},
                is_standard_response=True,
            ),
        ]

        manager = SubscribeManager(client)
        result = manager.add(name="Breaking Bad", media_type="tv", year=2008, season=1)

        assert result["status"] == "ok"
        assert result["subscribe"]["season"] == 1
        assert result["subscribe"]["filterRuleId"] == 10
        assert "mediums" not in result["subscribe"]
        assert client.request.call_args_list[1].kwargs["json_body"]["searchSites"] == [22]


class TestCLI:

    def test_help_without_tty_shows_help(self):
        runner = CliRunner()
        result = runner.invoke(main, [])

        assert result.exit_code == 0
        assert "Usage:" in result.output

    def test_show_connection_json(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ConnectionConfig, "DEFAULT_CONFIG_PATH", tmp_path / ".ms-cli.yaml")
        ConnectionConfig.save("http://localhost:8899", "secret-key")

        runner = CliRunner()
        result = runner.invoke(main, ["--json", "config", "show-connection"])

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["configured"] is True
        assert payload["base_url"] == "http://localhost:8899"
        assert payload["api_key"] == "secr...-key"

    def test_media_search_command_normalized_json(self, monkeypatch):
        runner = CliRunner()

        def fake_search(self, source_code, keyword, page, page_size):
            assert source_code == MEDIA_SOURCE_MAP["tmdb"]
            assert keyword == "Interstellar"
            assert page == 1
            assert page_size == 20
            return {
                "total": 1,
                "pageNum": 1,
                "pageSize": 20,
                "list": [
                    {
                        "title": "Interstellar",
                        "subtitle": "星际穿越",
                        "year": 2014,
                        "type": "movie",
                        "source": 200,
                        "vote": 8.6,
                    }
                ],
            }

        monkeypatch.setattr(MediaManager, "search", fake_search)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "media",
                "search",
                "--source",
                "tmdb",
                "--keyword",
                "Interstellar",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["total"] == 1
        assert payload["list"][0]["title"] == "Interstellar"

    def test_media_search_command_human_output(self, monkeypatch):
        runner = CliRunner()

        def fake_search(self, source_code, keyword, page, page_size):
            return {
                "total": 1,
                "pageNum": 1,
                "pageSize": 20,
                "list": [
                    {
                        "title": "Interstellar",
                        "subtitle": "星际穿越",
                        "year": 2014,
                        "type": "movie",
                        "source": 200,
                        "vote": 8.6,
                    }
                ],
            }

        monkeypatch.setattr(MediaManager, "search", fake_search)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media",
                "search",
                "--source",
                "tmdb",
                "--keyword",
                "Interstellar",
            ],
        )

        assert result.exit_code == 0
        assert "Media Search" in result.output
        assert "Interstellar" in result.output
        assert "TMDB" in result.output

    def test_media_search_command_empty_result(self, monkeypatch):
        runner = CliRunner()

        monkeypatch.setattr(
            MediaManager,
            "search",
            lambda self, source_code, keyword, page, page_size: {
                "total": 0,
                "pageNum": 1,
                "pageSize": 20,
                "list": [],
            },
        )

        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media",
                "search",
                "--source",
                "douban",
                "--keyword",
                "霸王别姬",
            ],
        )

        assert result.exit_code == 0
        assert "(空)" in result.output

    def test_media_search_requires_valid_source(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media",
                "search",
                "--source",
                "unknown",
                "--keyword",
                "foo",
            ],
        )

        assert result.exit_code != 0
        assert "Invalid value for '--source'" in result.output

    def test_media_search_rejects_empty_keyword(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media",
                "search",
                "--source",
                "tmdb",
                "--keyword",
                "   ",
            ],
        )

        assert result.exit_code != 0
        assert "--keyword cannot be empty" in result.output

    def test_media_server_miss_episodes_check_json(self, monkeypatch):
        runner = CliRunner()

        def fake_miss_episodes_check(self):
            return {
                "total": 1,
                "items": [
                    {
                        "tmdbId": 139797,
                        "mediaType": "tv",
                        "title": "猎罪图鉴",
                        "year": 2022,
                        "episodes": [
                            {
                                "season": 1,
                                "totalEpisodes": 20,
                                "missEpisodes": [7],
                            }
                        ],
                    }
                ],
            }

        monkeypatch.setattr(MediaServerManager, "miss_episodes_check", fake_miss_episodes_check)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "media-server",
                "miss-episodes-check",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["total"] == 1
        assert payload["items"][0]["title"] == "猎罪图鉴"
        assert payload["items"][0]["episodes"][0]["missEpisodes"] == [7]

    def test_media_server_miss_episodes_check_human_output(self, monkeypatch):
        runner = CliRunner()

        def fake_miss_episodes_check(self):
            return {
                "total": 1,
                "items": [
                    {
                        "tmdbId": 68095,
                        "mediaType": "tv",
                        "title": "法医秦明",
                        "year": 2016,
                        "episodes": [
                            {
                                "season": 2,
                                "totalEpisodes": 18,
                                "missEpisodes": [5, 10, 12],
                            }
                        ],
                    }
                ],
            }

        monkeypatch.setattr(MediaServerManager, "miss_episodes_check", fake_miss_episodes_check)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media-server",
                "miss-episodes-check",
            ],
        )

        assert result.exit_code == 0
        assert "Miss Episodes Check" in result.output
        assert "Total: 1" in result.output
        assert "法医秦明 (2016)" in result.output
        assert "Season 2 / Total 18 / Missing: 5, 10, 12" in result.output

    def test_media_server_miss_episodes_check_empty_output(self, monkeypatch):
        runner = CliRunner()

        monkeypatch.setattr(MediaServerManager, "miss_episodes_check", lambda self: {"total": 0, "items": []})
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media-server",
                "miss-episodes-check",
            ],
        )

        assert result.exit_code == 0
        assert "Total: 0" in result.output
        assert "✅ 无漏集" in result.output

    def test_media_server_miss_episodes_check_truncates_long_missing_list(self, monkeypatch):
        runner = CliRunner()

        def fake_miss_episodes_check(self):
            return {
                "total": 25,
                "items": [
                    {
                        "tmdbId": 69714,
                        "mediaType": "tv",
                        "title": "心理罪",
                        "year": 2015,
                        "episodes": [
                            {
                                "season": 1,
                                "totalEpisodes": 2110,
                                "missEpisodes": list(range(12, 40)),
                            }
                        ],
                    }
                ],
            }

        monkeypatch.setattr(MediaServerManager, "miss_episodes_check", fake_miss_episodes_check)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "media-server",
                "miss-episodes-check",
            ],
        )

        assert result.exit_code == 0
        assert "Showing first 1 items" in result.output
        assert "... (28 total)" in result.output

    def test_media_server_miss_episodes_check_surfaces_backend_error(self, monkeypatch):
        runner = CliRunner()

        def fake_miss_episodes_check(self):
            raise ValueError("404 page not found")

        monkeypatch.setattr(MediaServerManager, "miss_episodes_check", fake_miss_episodes_check)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "media-server",
                "miss-episodes-check",
            ],
        )

        assert result.exit_code != 0
        payload = json.loads(result.output)
        assert payload["error"] == "404 page not found"

    def test_plugin_call_json(self, monkeypatch):
        runner = CliRunner()

        def fake_request(self, method, path, *, params=None, headers=None, json_body=None, timeout=30):
            assert method == "POST"
            assert path == "/api/v1/pluginsInstance/callByCode/zspace_service_assistant"
            assert json_body == {"action": "get_recent_state", "body": {}}
            return ApiResponse(
                status_code=200,
                ok=True,
                code=20000,
                message="SUCCESS",
                data={"message": "", "data": [{"basic": {"name": "Z4Pro"}}]},
                raw_body={},
                is_standard_response=True,
            )

        monkeypatch.setattr(MSClient, "request", fake_request)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "plugin",
                "call",
                "--code",
                "zspace_service_assistant",
                "--body",
                '{"action":"get_recent_state","body":{}}',
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["message"] == ""
        assert payload["data"][0]["basic"]["name"] == "Z4Pro"

    def test_plugin_call_human_output_with_message_and_data(self, monkeypatch):
        runner = CliRunner()

        def fake_request(self, method, path, *, params=None, headers=None, json_body=None, timeout=30):
            return ApiResponse(
                status_code=200,
                ok=True,
                code=20000,
                message="SUCCESS",
                data={"message": "密钥生成成功", "data": {"value": 1}},
                raw_body={},
                is_standard_response=True,
            )

        monkeypatch.setattr(MSClient, "request", fake_request)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "plugin",
                "call",
                "--code",
                "cloud_backup",
                "--body",
                '{"action":"genKey","body":{}}',
            ],
        )

        assert result.exit_code == 0
        assert "密钥生成成功" in result.output
        assert '"value": 1' in result.output

    def test_plugin_call_human_output_when_plugin_result_is_null(self, monkeypatch):
        runner = CliRunner()

        def fake_request(self, method, path, *, params=None, headers=None, json_body=None, timeout=30):
            return ApiResponse(
                status_code=200,
                ok=True,
                code=20000,
                message="SUCCESS",
                data=None,
                raw_body={},
                is_standard_response=True,
            )

        monkeypatch.setattr(MSClient, "request", fake_request)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "plugin",
                "call",
                "--code",
                "moment",
                "--body",
                '{"action":"noop","body":{}}',
            ],
        )

        assert result.exit_code == 0
        assert "插件调用成功" in result.output

    def test_plugin_call_rejects_invalid_json(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "plugin",
                "call",
                "--code",
                "moment",
                "--body",
                "{bad json",
            ],
        )

        assert result.exit_code != 0
        assert "--body must be valid JSON" in result.output

    def test_plugin_call_rejects_non_object_body(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "plugin",
                "call",
                "--code",
                "moment",
                "--body",
                '["x"]',
            ],
        )

        assert result.exit_code != 0
        assert "--body must be a JSON object" in result.output

    def test_plugin_call_requires_action(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "plugin",
                "call",
                "--code",
                "moment",
                "--body",
                '{"body":{}}',
            ],
        )

        assert result.exit_code != 0
        assert "--body.action must be a non-empty string" in result.output

    def test_plugin_call_requires_object_body_field(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "plugin",
                "call",
                "--code",
                "moment",
                "--body",
                '{"action":"noop","body":"x"}',
            ],
        )

        assert result.exit_code != 0
        assert "--body.body must be a JSON object" in result.output

    def test_plugin_call_surfaces_backend_error(self, monkeypatch):
        runner = CliRunner()

        def fake_request(self, method, path, *, params=None, headers=None, json_body=None, timeout=30):
            return ApiResponse(
                status_code=200,
                ok=False,
                code=50000,
                message="还没有安装秘籍: 极空间服务助手",
                data=None,
                raw_body={},
                is_standard_response=True,
            )

        monkeypatch.setattr(MSClient, "request", fake_request)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "plugin",
                "call",
                "--code",
                "zspace_service_assistant",
                "--body",
                '{"action":"get_recent_state","body":{}}',
            ],
        )

        assert result.exit_code != 0
        payload = json.loads(result.output)
        assert "还没有安装秘籍" in payload["error"]

    def test_subscribe_add_json(self, monkeypatch):
        runner = CliRunner()

        def fake_add(self, name, media_type, year, season):
            assert media_type == "movie"
            assert name == "Interstellar"
            assert year == 2014
            assert season is None
            return {
                "status": "ok",
                "subscribe": {
                    "name": name,
                    "type": media_type,
                    "year": year,
                },
            }

        monkeypatch.setattr(SubscribeManager, "add", fake_add)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "--json",
                "subscribe",
                "add",
                "--type",
                "movie",
                "--name",
                "Interstellar",
                "--year",
                "2014",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["status"] == "ok"
        assert payload["subscribe"]["name"] == "Interstellar"

    def test_subscribe_add_tv_defaults_season(self, monkeypatch):
        runner = CliRunner()

        def fake_add(self, name, media_type, year, season):
            assert media_type == "tv"
            assert season == 1
            return {
                "status": "ok",
                "subscribe": {
                    "name": name,
                    "type": media_type,
                    "year": year,
                    "season": season,
                },
            }

        monkeypatch.setattr(SubscribeManager, "add", fake_add)
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "subscribe",
                "add",
                "--type",
                "tv",
                "--name",
                "Breaking Bad",
                "--year",
                "2008",
            ],
        )

        assert result.exit_code == 0
        assert "season" in result.output
        assert "1" in result.output

    def test_subscribe_add_rejects_movie_season(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "subscribe",
                "add",
                "--type",
                "movie",
                "--name",
                "Interstellar",
                "--year",
                "2014",
                "--season",
                "1",
            ],
        )

        assert result.exit_code != 0
        assert "--season is only valid for tv subscriptions" in result.output

    def test_subscribe_add_rejects_empty_name(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                "subscribe",
                "add",
                "--type",
                "movie",
                "--name",
                "   ",
                "--year",
                "2014",
            ],
        )

        assert result.exit_code != 0
        assert "--name cannot be empty" in result.output
