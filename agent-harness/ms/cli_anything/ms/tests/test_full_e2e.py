"""Subprocess tests for the Media Saber CLI harness."""

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
    args.extend(["request", "GET", "/api/v1/system/status"])
    result = _cli(*args)
    return result.returncode == 0


skip_no_server = pytest.mark.skipif(
    not _server_available(),
    reason="Media Saber server is unavailable or MS_URL/MS_API_KEY are not set",
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

    def test_subscribe_add_help(self):
        result = _cli("subscribe", "add", "--help")

        assert result.returncode == 0
        assert "--name" in result.stdout
        assert "--year" in result.stdout


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
    def test_system_status(self):
        args = ["--json"]
        if MS_URL:
            args.extend(["--url", MS_URL])
        if MS_API_KEY:
            args.extend(["--apikey", MS_API_KEY])
        args.extend(["request", "GET", "/api/v1/system/status"])
        result = _cli(*args)

        assert result.returncode == 0
        payload = json.loads(result.stdout)
        assert payload["status_code"] == 200

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
