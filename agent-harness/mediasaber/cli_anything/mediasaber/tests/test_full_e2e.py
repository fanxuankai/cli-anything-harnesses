from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HARNESS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def _resolve_cli() -> list[str]:
    if os.getenv("CLI_ANYTHING_FORCE_INSTALLED"):
        return ["cli-anything-mediasaber"]
    return [sys.executable, "-m", "cli_anything.mediasaber"]


class MockHandler(BaseHTTPRequestHandler):
    token = "token-xyz"

    def log_message(self, format, *args):  # noqa: A003
        return

    def _json(self, payload, status=200):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _require_auth(self) -> bool:
        return self.headers.get("Authorization") == self.token or self.headers.get("apiKey") == "apikey-1"

    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/v1/user/initAdminStatus":
            self._json({"code": 20000, "message": "ok", "data": True})
            return
        if not self._require_auth():
            self._json({"code": 40000, "message": "login required", "data": None})
            return
        if parsed.path == "/api/v1/user/info":
            self._json({"code": 20000, "message": "ok", "data": {"userName": "admin", "nickName": "Media Saber"}})
            return
        if parsed.path == "/api/v1/system/status":
            self._json({"code": 20000, "message": "ok", "data": {"cpuUsedPercent": 1.23, "goroutine": 99}})
            return
        if parsed.path == "/api/v1/downloader/list":
            self._json({"code": 20000, "message": "ok", "data": [{"id": 1, "name": "qb"}]})
            return
        if parsed.path == "/api/v1/site/options":
            self._json({"code": 20000, "message": "ok", "data": [{"value": 1, "text": "MTeam"}]})
            return
        if parsed.path == "/api/v1/media/search":
            params = parse_qs(parsed.query)
            keyword = params.get("keyword", [""])[0]
            self._json(
                {
                    "code": 20000,
                    "message": "ok",
                    "data": {"pageNum": 1, "pageSize": 20, "total": 1, "list": [{"title": keyword}]},
                }
            )
            return
        self._json({"code": 40400, "message": f"unknown path {parsed.path}", "data": None}, status=404)

    def do_POST(self):  # noqa: N802
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8") if length else ""
        payload = json.loads(body or "{}")
        if parsed.path == "/api/v1/user/login":
            if payload.get("userName") == "admin" and payload.get("password") == "secret":
                self._json({"code": 20000, "message": "ok", "data": self.token})
            else:
                self._json({"code": 40000, "message": "bad credentials", "data": None})
            return
        if not self._require_auth():
            self._json({"code": 40000, "message": "login required", "data": None})
            return
        if parsed.path == "/api/v1/path/ls":
            self._json({"code": 20000, "message": "ok", "data": [{"path": payload.get("path"), "isDir": True}]})
            return
        self._json({"code": 40400, "message": f"unknown path {parsed.path}", "data": None}, status=404)


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _start_server():
    port = _free_port()
    server = ThreadingHTTPServer(("127.0.0.1", port), MockHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{port}"


def _cli(home: str, *args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["HOME"] = home
    env["PYTHONPATH"] = HARNESS_ROOT + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        _resolve_cli() + list(args),
        capture_output=True,
        text=True,
        cwd=HARNESS_ROOT,
        env=env,
        timeout=30,
    )


def test_subprocess_workflow():
    server, base_url = _start_server()
    try:
        with tempfile.TemporaryDirectory() as tmp_home:
            result = _cli(tmp_home, "--json", "--url", base_url, "server", "ping")
            assert result.returncode == 0, result.stderr
            assert json.loads(result.stdout)["reachable"] is True

            result = _cli(tmp_home, "--json", "--url", base_url, "auth", "login", "admin", "secret")
            assert result.returncode == 0, result.stderr
            assert json.loads(result.stdout)["token"] == "token-xyz"

            result = _cli(tmp_home, "--json", "--url", base_url, "auth", "whoami")
            assert result.returncode == 0, result.stderr
            assert json.loads(result.stdout)["userName"] == "admin"

            result = _cli(tmp_home, "--json", "--url", base_url, "system", "status")
            assert result.returncode == 0, result.stderr
            assert json.loads(result.stdout)["goroutine"] == 99

            result = _cli(tmp_home, "--json", "--url", base_url, "downloader", "list")
            assert result.returncode == 0, result.stderr
            assert json.loads(result.stdout)[0]["name"] == "qb"

            result = _cli(tmp_home, "--json", "--url", base_url, "api", "GET", "/api/v1/site/options")
            assert result.returncode == 0, result.stderr
            assert json.loads(result.stdout)[0]["text"] == "MTeam"

            result = _cli(tmp_home, "--json", "session", "set", "--source", "/tmp/media-saber")
            assert result.returncode == 0, result.stderr
            assert json.loads(result.stdout)["current"]["source_path"] == "/tmp/media-saber"

            result = _cli(tmp_home, "--json", "session", "undo")
            assert result.returncode == 0, result.stderr
            assert json.loads(result.stdout)["current"]["source_path"] is None

            result = _cli(tmp_home, "--json", "session", "redo")
            assert result.returncode == 0, result.stderr
            assert json.loads(result.stdout)["current"]["source_path"] == "/tmp/media-saber"

            result = _cli(tmp_home, "--json", "--url", base_url, "media", "search", "andor")
            assert result.returncode == 0, result.stderr
            assert json.loads(result.stdout)["list"][0]["title"] == "andor"
    finally:
        server.shutdown()
