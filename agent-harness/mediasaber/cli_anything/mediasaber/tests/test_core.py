from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

HARNESS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, HARNESS_ROOT)

from cli_anything.mediasaber.core.auth import AuthManager
from cli_anything.mediasaber.core.client import APIError, ConnectionConfig, MediaSaberClient, normalize_base_url
from cli_anything.mediasaber.core.config import ConfigManager
from cli_anything.mediasaber.core.downloader import DownloaderManager
from cli_anything.mediasaber.core.media import MediaManager
from cli_anything.mediasaber.core.system import SystemManager
from cli_anything.mediasaber.mediasaber_cli import main


def _mock_response(payload, status_code=200, content_type="application/json", content=None, text=None):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload
    response.headers = {"Content-Type": content_type}
    response.content = content if content is not None else json.dumps(payload).encode("utf-8")
    response.text = text if text is not None else response.content.decode("utf-8", errors="ignore")
    response.raise_for_status.return_value = None
    return response


def test_normalize_base_url():
    assert normalize_base_url("http://localhost:8899/") == "http://localhost:8899"
    assert normalize_base_url(None) is None


def test_connection_from_env_and_profile(tmp_path: Path):
    config_mgr = ConfigManager(tmp_path / "config.yaml")
    config_mgr.save_profile("dev", {"url": "http://profile:8899", "source_path": "/repo"})
    with patch.dict(os.environ, {"MSB_TOKEN": "env-token"}, clear=True):
        conn = ConnectionConfig.from_sources(profile="dev", config_mgr=config_mgr)
    assert conn.url == "http://profile:8899"
    assert conn.token == "env-token"
    assert conn.source_path == "/repo"


def test_config_manager_undo_redo(tmp_path: Path):
    mgr = ConfigManager(tmp_path / "config.yaml")
    mgr.update_state(url="http://one", source_path="/repo/a")
    mgr.update_state(url="http://two")
    undone = mgr.undo()
    redone = mgr.redo()
    assert undone["url"] == "http://one"
    assert redone["url"] == "http://two"


@patch("cli_anything.mediasaber.core.client.requests.Session.request")
def test_client_unwraps_success_envelope(mock_request):
    mock_request.return_value = _mock_response({"code": 20000, "message": "ok", "data": {"value": 1}})
    client = MediaSaberClient(ConnectionConfig(url="http://localhost:8899", token="abc"))
    data = client.request_data("GET", "/api/v1/system/status")
    assert data == {"value": 1}


@patch("cli_anything.mediasaber.core.client.requests.Session.request")
def test_client_raises_on_failed_envelope(mock_request):
    mock_request.return_value = _mock_response({"code": 40000, "message": "denied", "data": None})
    client = MediaSaberClient(ConnectionConfig(url="http://localhost:8899", token="abc"))
    with pytest.raises(APIError, match="denied"):
        client.request_data("GET", "/api/v1/system/status")


@patch("cli_anything.mediasaber.core.client.requests.Session.request")
def test_client_reads_raw_json(mock_request):
    mock_request.return_value = _mock_response([{"id": "gpt-4.1"}])
    client = MediaSaberClient(ConnectionConfig(url="http://localhost:8899", token="abc"))
    data = client.request_result("GET", "/ai/v1/models", response_mode="json", unwrap_envelope=False)
    assert data == [{"id": "gpt-4.1"}]


@patch("cli_anything.mediasaber.core.client.requests.Session.request")
def test_client_writes_binary_output(mock_request, tmp_path: Path):
    mock_request.return_value = _mock_response(
        payload={},
        content_type="application/octet-stream",
        content=b"video-bytes",
        text="video-bytes",
    )
    client = MediaSaberClient(ConnectionConfig(url="http://localhost:8899", token="abc"))
    output = tmp_path / "media.bin"
    result = client.request_result("GET", "/api/v1/cloudStorage/strm302", response_mode="content", output_path=str(output))
    assert output.read_bytes() == b"video-bytes"
    assert result["bytes"] == 11


def test_auth_manager_login_calls_expected_path():
    client = MagicMock()
    client.request_data.return_value = "token-123"
    token = AuthManager(client).login("admin", "secret", device_type="cli", device_name="box")
    assert token == "token-123"
    client.request_data.assert_called_once_with(
        "POST",
        "/api/v1/user/login",
        json_data={
            "userName": "admin",
            "password": "secret",
            "deviceType": "cli",
            "deviceName": "box",
        },
        public=True,
    )


def test_system_manager_path_ls():
    client = MagicMock()
    manager = SystemManager(client)
    manager.path_ls("/data")
    client.request_data.assert_called_once_with("POST", "/api/v1/path/ls", json_data={"path": "/data"})


def test_downloader_manager_directory_match():
    client = MagicMock()
    manager = DownloaderManager(client)
    manager.directory_match(1399, "tv", dir_tag="tv")
    client.request_data.assert_called_once_with(
        "GET",
        "/api/v1/directory/match",
        params={"tmdbId": 1399, "mediaType": "tv", "dirTag": "tv"},
    )


def test_media_manager_search():
    client = MagicMock()
    manager = MediaManager(client)
    manager.search("The Last of Us", media_source=2, page_num=3, page_size=5)
    client.request_data.assert_called_once_with(
        "GET",
        "/api/v1/media/search",
        params={"keyword": "The Last of Us", "mediaSource": 2, "pageNum": 3, "pageSize": 5},
    )


def test_help_registers_new_groups():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "cloud-storage" in result.output
    assert "torrent-search" in result.output
    assert "service-ocr" in result.output
    assert "ai" in result.output


@patch("cli_anything.mediasaber.core.client.MediaSaberClient.request_result")
def test_dynamic_command_builds_path_and_query(mock_request):
    mock_request.return_value = {"ok": True}
    runner = CliRunner()
    result = runner.invoke(main, ["--json", "pansou", "search", "--keyword", "andor", "--page-num", "2"])
    assert result.exit_code == 0, result.output
    _, path = mock_request.call_args.args[:2]
    assert path == "/api/v1/pansou/search"
    assert mock_request.call_args.kwargs["params"]["keyword"] == "andor"


@patch("cli_anything.mediasaber.core.client.MediaSaberClient.request_result")
def test_dynamic_command_upload_spec(mock_request, tmp_path: Path):
    mock_request.return_value = {"ok": True}
    payload = tmp_path / "avatar.png"
    payload.write_bytes(b"png")
    runner = CliRunner()
    result = runner.invoke(main, ["--json", "user", "upload-avatar", "--file", str(payload)])
    assert result.exit_code == 0, result.output
    _, path = mock_request.call_args.args[:2]
    assert path == "/api/v1/user/uploadAvatar"
    assert "file" in mock_request.call_args.kwargs["files"]
