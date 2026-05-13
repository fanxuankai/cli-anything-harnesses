"""Subprocess tests for the ms CLI harness."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

import pytest


HARNESS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
MS_URL = os.getenv("MS_URL", "")
MS_API_KEY = os.getenv("MS_API_KEY", "")


def _resolve_cli() -> list[str]:
    if os.getenv("CLI_ANYTHING_FORCE_INSTALLED"):
        return ["cli-anything-ms"]
    return [sys.executable, "-m", "cli_anything.ms"]


def _cli(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    merged_env = os.environ.copy()
    merged_env["PYTHONPATH"] = HARNESS_ROOT + os.pathsep + merged_env.get("PYTHONPATH", "")
    if env:
        merged_env.update(env)
    return subprocess.run(
        _resolve_cli() + list(args),
        capture_output=True,
        text=True,
        timeout=30,
        env=merged_env,
    )


def _server_available() -> bool:
    args = ["--json"]
    if MS_URL:
        args.extend(["--url", MS_URL])
    if MS_API_KEY:
        args.extend(["--apikey", MS_API_KEY])
    args.extend(["media", "search", "--source", "tmdb", "--keyword", "Interstellar"])
    result = _cli(*args)
    return result.returncode == 0


skip_no_server = pytest.mark.skipif(
    not _server_available(),
    reason="ms server is unavailable or MS_URL/MS_API_KEY are not set",
)


class TestCLIHelp:

    def test_help_flag(self):
        result = _cli("--help")

        assert result.returncode == 0
        assert "Usage:" in result.stdout
        assert "request" not in result.stdout

    def test_media_search_help(self):
        result = _cli("media", "search", "--help")

        assert result.returncode == 0
        assert "--source" in result.stdout
        assert "--keyword" in result.stdout

    def test_media_rank_sources_help(self):
        result = _cli("media", "rank", "sources", "--help")

        assert result.returncode == 0
        assert "sources" in result.stdout

    def test_media_rank_categories_help(self):
        result = _cli("media", "rank", "categories", "--help")

        assert result.returncode == 0
        assert "--source" in result.stdout

    def test_media_rank_subjects_help(self):
        result = _cli("media", "rank", "subjects", "--help")

        assert result.returncode == 0
        assert "--category-code" in result.stdout

    def test_media_rank_items_help(self):
        result = _cli("media", "rank", "items", "--help")

        assert result.returncode == 0
        assert "--page-size" in result.stdout

    def test_media_recommend_sources_help(self):
        result = _cli("media", "recommend", "sources", "--help")

        assert result.returncode == 0
        assert "sources" in result.stdout

    def test_media_recommend_channels_help(self):
        result = _cli("media", "recommend", "channels", "--help")

        assert result.returncode == 0
        assert "--source" in result.stdout

    def test_media_recommend_options_help(self):
        result = _cli("media", "recommend", "options", "--help")

        assert result.returncode == 0
        assert "--channel" in result.stdout

    def test_media_recommend_items_help(self):
        result = _cli("media", "recommend", "items", "--help")

        assert result.returncode == 0
        assert "--options" in result.stdout

    def test_media_server_miss_episodes_check_help(self):
        result = _cli("media-server", "miss-episodes-check", "--help")

        assert result.returncode == 0
        assert "miss-episodes-check" in result.stdout

    def test_system_nas_info_help(self):
        result = _cli("system", "nas-info", "--help")

        assert result.returncode == 0
        assert "nas-info" in result.stdout

    def test_media_server_list_help(self):
        result = _cli("media-server", "list", "--help")

        assert result.returncode == 0
        assert "list" in result.stdout

    def test_media_server_sync_items_help(self):
        result = _cli("media-server", "sync-items", "--help")

        assert result.returncode == 0
        assert "--miss-eps" in result.stdout
        assert "--page-size" in result.stdout

    def test_media_server_sync_run_help(self):
        result = _cli("media-server", "sync-run", "--help")

        assert result.returncode == 0
        assert "--id" in result.stdout

    def test_site_list_help(self):
        result = _cli("site", "list", "--help")

        assert result.returncode == 0
        assert "--enabled" in result.stdout
        assert "--type" in result.stdout

    def test_site_data_latest_help(self):
        result = _cli("site", "data", "latest", "--help")

        assert result.returncode == 0
        assert "--site-name" in result.stdout

    def test_site_sign_in_history_help(self):
        result = _cli("site", "sign-in", "history", "--help")

        assert result.returncode == 0
        assert "--page-size" in result.stdout

    def test_site_sign_in_go_help(self):
        result = _cli("site", "sign-in", "go", "--help")

        assert result.returncode == 0
        assert "--id" in result.stdout

    def test_download_downloaders_help(self):
        result = _cli("download", "downloaders", "--help")

        assert result.returncode == 0
        assert "downloaders" in result.stdout

    def test_download_downloading_help(self):
        result = _cli("download", "downloading", "--help")

        assert result.returncode == 0
        assert "--id" in result.stdout

    def test_download_history_help(self):
        result = _cli("download", "history", "--help")

        assert result.returncode == 0
        assert "--page-size" in result.stdout
        assert "--type" in result.stdout

    def test_download_pause_resume_delete_help(self):
        for command in ("pause", "resume", "delete"):
            result = _cli("download", command, "--help")

            assert result.returncode == 0
            assert "--id" in result.stdout

    def test_cloud_resource_search_help(self):
        result = _cli("cloud-resource", "search", "--help")

        assert result.returncode == 0
        assert "--keyword" in result.stdout
        assert "--tmdb-id" in result.stdout

    def test_cloud_resource_download_help(self):
        result = _cli("cloud-resource", "download", "--help")

        assert result.returncode == 0
        assert "--request" in result.stdout

    def test_cloud_resource_rank_help(self):
        result = _cli("cloud-resource", "rank", "--help")

        assert result.returncode == 0
        assert "--range" in result.stdout
        assert "--stat" in result.stdout

    def test_plugin_call_help(self):
        result = _cli("plugin", "call", "--help")

        assert result.returncode == 0
        assert "--code" in result.stdout
        assert "--body" in result.stdout

    def test_subscribe_add_help(self):
        result = _cli("subscribe", "add", "--help")

        assert result.returncode == 0
        assert "--name" in result.stdout
        assert "--year" in result.stdout

    def test_subscribe_page_help(self):
        result = _cli("subscribe", "page", "--help")

        assert result.returncode == 0
        assert "--type" in result.stdout
        assert "--page-size" in result.stdout


class TestConfigPersistence:

    def test_save_connection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _cli(
                "config",
                "save-connection",
                "--url",
                "http://localhost:8899",
                "--apikey",
                "secret-key",
                env={"HOME": tmpdir},
            )

            assert result.returncode == 0
            assert os.path.exists(os.path.join(tmpdir, ".ms-cli.yaml"))


class TestLiveServer:

    @skip_no_server
    def test_media_search_tmdb(self):
        args = ["--json"]
        if MS_URL:
            args.extend(["--url", MS_URL])
        if MS_API_KEY:
            args.extend(["--apikey", MS_API_KEY])
        args.extend(["media", "search", "--source", "tmdb", "--keyword", "Interstellar"])
        result = _cli(*args)

        assert result.returncode == 0
        payload = json.loads(result.stdout)
        assert {"total", "pageNum", "pageSize", "list"}.issubset(payload.keys())
        if payload["list"]:
            item = payload["list"][0]
            assert {"media_id", "media_type", "poster_url", "subscription", "library"}.issubset(item.keys())
            assert "rssId" not in item
            assert "archived" not in item

    @skip_no_server
    def test_cloud_resource_search_keyword(self):
        args = ["--json"]
        if MS_URL:
            args.extend(["--url", MS_URL])
        if MS_API_KEY:
            args.extend(["--apikey", MS_API_KEY])
        args.extend(["cloud-resource", "search", "--keyword", "庆余年", "--page", "1", "--page-size", "3"])
        result = _cli(*args)

        assert result.returncode in {0, 1}
        payload = json.loads(result.stdout)
        if result.returncode == 0:
            assert {"total", "pageNum", "pageSize", "list"}.issubset(payload.keys())
            if payload["list"]:
                item = payload["list"][0]
                assert {"title", "size", "driver", "creator", "link", "downloadable", "download_request"}.issubset(item.keys())
        else:
            assert "error" in payload

    @skip_no_server
    def test_cloud_resource_rank_today_count(self):
        args = ["--json"]
        if MS_URL:
            args.extend(["--url", MS_URL])
        if MS_API_KEY:
            args.extend(["--apikey", MS_API_KEY])
        args.extend(["cloud-resource", "rank", "--range", "today", "--stat", "count"])
        result = _cli(*args)

        assert result.returncode in {0, 1}
        payload = json.loads(result.stdout)
        if result.returncode == 0:
            assert {"range_type", "stat_type", "items", "mine"}.issubset(payload.keys())
            assert isinstance(payload["items"], list)
        else:
            assert "error" in payload

    @skip_no_server
    def test_media_rank_sources(self):
        args = ["--json"]
        if MS_URL:
            args.extend(["--url", MS_URL])
        if MS_API_KEY:
            args.extend(["--apikey", MS_API_KEY])
        args.extend(["media", "rank", "sources"])
        result = _cli(*args)

        assert result.returncode in {0, 1}
        payload = json.loads(result.stdout)
        if result.returncode == 0:
            assert isinstance(payload, list)
        else:
            assert "error" in payload

    @skip_no_server
    def test_media_rank_categories(self):
        args = ["--json"]
        if MS_URL:
            args.extend(["--url", MS_URL])
        if MS_API_KEY:
            args.extend(["--apikey", MS_API_KEY])
        args.extend(["media", "rank", "categories", "--source", "douban"])
        result = _cli(*args)

        assert result.returncode in {0, 1}
        payload = json.loads(result.stdout)
        if result.returncode == 0:
            assert isinstance(payload, list)
        else:
            assert "error" in payload

    @skip_no_server
    def test_media_rank_subjects(self):
        args = ["--json"]
        if MS_URL:
            args.extend(["--url", MS_URL])
        if MS_API_KEY:
            args.extend(["--apikey", MS_API_KEY])
        args.extend(["media", "rank", "subjects", "--category-code", "douban_tv"])
        result = _cli(*args)

        assert result.returncode in {0, 1}
        payload = json.loads(result.stdout)
        if result.returncode == 0:
            assert isinstance(payload, list)
        else:
            assert "error" in payload

    @skip_no_server
    def test_media_rank_items(self):
        args = ["--json"]
        if MS_URL:
            args.extend(["--url", MS_URL])
        if MS_API_KEY:
            args.extend(["--apikey", MS_API_KEY])
        args.extend(
            [
                "media",
                "rank",
                "items",
                "--category-code",
                "douban_tv",
                "--code",
                "tv_domestic",
                "--page",
                "1",
                "--page-size",
                "25",
            ]
        )
        result = _cli(*args)

        assert result.returncode in {0, 1}
        payload = json.loads(result.stdout)
        if result.returncode == 0:
            assert isinstance(payload, dict)
            assert {"total", "pageNum", "pageSize", "list"}.issubset(payload.keys())
            if payload["list"]:
                item = payload["list"][0]
                assert {"media_id", "media_type", "poster_url", "subscription", "library"}.issubset(item.keys())
                assert "rssId" not in item
                assert "archived" not in item
        else:
            assert "error" in payload

    @skip_no_server
    def test_media_recommend_sources(self):
        args = ["--json"]
        if MS_URL:
            args.extend(["--url", MS_URL])
        if MS_API_KEY:
            args.extend(["--apikey", MS_API_KEY])
        args.extend(["media", "recommend", "sources"])
        result = _cli(*args)

        assert result.returncode in {0, 1}
        payload = json.loads(result.stdout)
        if result.returncode == 0:
            assert isinstance(payload, list)
        else:
            assert "error" in payload

    @skip_no_server
    def test_media_recommend_channels(self):
        args = ["--json"]
        if MS_URL:
            args.extend(["--url", MS_URL])
        if MS_API_KEY:
            args.extend(["--apikey", MS_API_KEY])
        args.extend(["media", "recommend", "channels", "--source", "douban"])
        result = _cli(*args)

        assert result.returncode in {0, 1}
        payload = json.loads(result.stdout)
        if result.returncode == 0:
            assert isinstance(payload, list)
        else:
            assert "error" in payload

    @skip_no_server
    def test_media_recommend_options(self):
        args = ["--json"]
        if MS_URL:
            args.extend(["--url", MS_URL])
        if MS_API_KEY:
            args.extend(["--apikey", MS_API_KEY])
        args.extend(["media", "recommend", "options", "--source", "douban", "--channel", "movie"])
        result = _cli(*args)

        assert result.returncode in {0, 1}
        payload = json.loads(result.stdout)
        if result.returncode == 0:
            assert isinstance(payload, list)
        else:
            assert "error" in payload

    @skip_no_server
    def test_media_recommend_items(self):
        args = ["--json"]
        if MS_URL:
            args.extend(["--url", MS_URL])
        if MS_API_KEY:
            args.extend(["--apikey", MS_API_KEY])
        args.extend(
            [
                "media",
                "recommend",
                "items",
                "--source",
                "douban",
                "--channel",
                "movie",
                "--options",
                '{"sort":"","year":"","tag":"","country":""}',
                "--page",
                "1",
                "--page-size",
                "25",
            ]
        )
        result = _cli(*args)

        assert result.returncode in {0, 1}
        payload = json.loads(result.stdout)
        if result.returncode == 0:
            assert isinstance(payload, dict)
            assert {"total", "pageNum", "pageSize", "list"}.issubset(payload.keys())
            if payload["list"]:
                item = payload["list"][0]
                assert {"media_id", "media_type", "poster_url", "subscription", "library"}.issubset(item.keys())
                assert "rssId" not in item
                assert "archived" not in item
        else:
            assert "error" in payload

    @skip_no_server
    def test_plugin_call_by_code(self):
        args = ["--json"]
        if MS_URL:
            args.extend(["--url", MS_URL])
        if MS_API_KEY:
            args.extend(["--apikey", MS_API_KEY])
        args.extend(
            [
                "plugin",
                "call",
                "--code",
                "zspace_service_assistant",
                "--body",
                '{"action":"get_recent_state","body":{}}',
            ]
        )
        result = _cli(*args)

        assert result.returncode in {0, 1}
        payload = json.loads(result.stdout)
        if result.returncode == 0:
            assert "data" in payload or payload is None
        else:
            assert "error" in payload

    @skip_no_server
    def test_system_nas_info(self):
        args = ["--json"]
        if MS_URL:
            args.extend(["--url", MS_URL])
        if MS_API_KEY:
            args.extend(["--apikey", MS_API_KEY])
        args.extend(["system", "nas-info"])
        result = _cli(*args)

        assert result.returncode in {0, 1}
        payload = json.loads(result.stdout)
        if result.returncode == 0:
            assert isinstance(payload, list)
        else:
            assert "error" in payload

    @skip_no_server
    def test_media_server_miss_episodes_check(self):
        args = ["--json"]
        if MS_URL:
            args.extend(["--url", MS_URL])
        if MS_API_KEY:
            args.extend(["--apikey", MS_API_KEY])
        args.extend(["media-server", "miss-episodes-check"])
        result = _cli(*args)

        assert result.returncode in {0, 1}
        payload = json.loads(result.stdout)
        if result.returncode == 0:
            assert isinstance(payload, dict)
            assert "total" in payload
            assert "items" in payload
        else:
            assert "error" in payload

    @skip_no_server
    def test_media_server_list(self):
        args = ["--json"]
        if MS_URL:
            args.extend(["--url", MS_URL])
        if MS_API_KEY:
            args.extend(["--apikey", MS_API_KEY])
        args.extend(["media-server", "list"])
        result = _cli(*args)

        assert result.returncode in {0, 1}
        payload = json.loads(result.stdout)
        if result.returncode == 0:
            assert isinstance(payload, dict)
            assert "total" in payload
            assert "items" in payload
        else:
            assert "error" in payload

    @skip_no_server
    def test_site_list(self):
        args = ["--json"]
        if MS_URL:
            args.extend(["--url", MS_URL])
        if MS_API_KEY:
            args.extend(["--apikey", MS_API_KEY])
        args.extend(["site", "list"])
        result = _cli(*args)

        assert result.returncode in {0, 1}
        payload = json.loads(result.stdout)
        if result.returncode == 0:
            assert isinstance(payload, dict)
            assert "total" in payload
            assert "items" in payload
        else:
            assert "error" in payload

    @skip_no_server
    def test_site_data_total(self):
        args = ["--json"]
        if MS_URL:
            args.extend(["--url", MS_URL])
        if MS_API_KEY:
            args.extend(["--apikey", MS_API_KEY])
        args.extend(["site", "data", "total"])
        result = _cli(*args)

        assert result.returncode in {0, 1}
        payload = json.loads(result.stdout)
        if result.returncode == 0:
            assert isinstance(payload, dict)
            assert "uploaded" in payload
            assert "downloaded" in payload
        else:
            assert "error" in payload

    @skip_no_server
    def test_download_downloaders(self):
        args = ["--json"]
        if MS_URL:
            args.extend(["--url", MS_URL])
        if MS_API_KEY:
            args.extend(["--apikey", MS_API_KEY])
        args.extend(["download", "downloaders"])
        result = _cli(*args)

        assert result.returncode in {0, 1}
        payload = json.loads(result.stdout)
        if result.returncode == 0:
            assert isinstance(payload, dict)
            assert "total" in payload
            assert "items" in payload
        else:
            assert "error" in payload

    @skip_no_server
    def test_download_downloading(self):
        args = ["--json"]
        if MS_URL:
            args.extend(["--url", MS_URL])
        if MS_API_KEY:
            args.extend(["--apikey", MS_API_KEY])
        args.extend(["download", "downloading"])
        result = _cli(*args)

        assert result.returncode in {0, 1}
        payload = json.loads(result.stdout)
        if result.returncode == 0:
            assert isinstance(payload, dict)
            assert "total" in payload
            assert "items" in payload
        else:
            assert "error" in payload

    @skip_no_server
    def test_download_history(self):
        args = ["--json"]
        if MS_URL:
            args.extend(["--url", MS_URL])
        if MS_API_KEY:
            args.extend(["--apikey", MS_API_KEY])
        args.extend(["download", "history", "--page", "1", "--page-size", "5"])
        result = _cli(*args)

        assert result.returncode in {0, 1}
        payload = json.loads(result.stdout)
        if result.returncode == 0:
            assert isinstance(payload, dict)
            assert {"total", "pageNum", "pageSize", "list"}.issubset(payload.keys())
        else:
            assert "error" in payload

    @skip_no_server
    def test_subscribe_page_movie(self):
        args = ["--json"]
        if MS_URL:
            args.extend(["--url", MS_URL])
        if MS_API_KEY:
            args.extend(["--apikey", MS_API_KEY])
        args.extend(["subscribe", "page", "--type", "movie", "--page", "1", "--page-size", "99"])
        result = _cli(*args)

        assert result.returncode in {0, 1}
        payload = json.loads(result.stdout)
        if result.returncode == 0:
            assert isinstance(payload, dict)
            assert {"total", "pageNum", "pageSize", "list"}.issubset(payload.keys())
        else:
            assert "error" in payload

    @skip_no_server
    def test_subscribe_page_tv(self):
        args = ["--json"]
        if MS_URL:
            args.extend(["--url", MS_URL])
        if MS_API_KEY:
            args.extend(["--apikey", MS_API_KEY])
        args.extend(["subscribe", "page", "--type", "tv", "--page", "1", "--page-size", "99"])
        result = _cli(*args)

        assert result.returncode in {0, 1}
        payload = json.loads(result.stdout)
        if result.returncode == 0:
            assert isinstance(payload, dict)
            assert {"total", "pageNum", "pageSize", "list"}.issubset(payload.keys())
        else:
            assert "error" in payload
