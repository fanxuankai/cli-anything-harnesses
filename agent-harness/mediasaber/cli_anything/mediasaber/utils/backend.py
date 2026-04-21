from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Any


class BackendManager:
    STATE_DIR = Path.home() / ".mediasaber-cli"
    PID_FILE = STATE_DIR / "backend.json"
    LOG_FILE = STATE_DIR / "backend.log"

    def __init__(self):
        self.STATE_DIR.mkdir(parents=True, exist_ok=True)

    def _is_running(self, pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def start(self, source_path: str, config_file: str | None = None) -> dict[str, Any]:
        if not source_path:
            raise ValueError("source path is required, use --source or session set --source")
        current = self.status()
        if current["running"]:
            return current
        cmd = ["go", "run", "mediasaber.go"]
        if config_file:
            cmd.extend(["--configFile", config_file])
        log_handle = open(self.LOG_FILE, "a", encoding="utf-8")
        process = subprocess.Popen(
            cmd,
            cwd=source_path,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        time.sleep(1)
        payload = {
            "pid": process.pid,
            "source_path": source_path,
            "config_file": config_file,
            "command": cmd,
            "log_file": str(self.LOG_FILE),
            "running": self._is_running(process.pid),
        }
        self.PID_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload

    def status(self) -> dict[str, Any]:
        if not self.PID_FILE.exists():
            return {"running": False, "pid": None, "log_file": str(self.LOG_FILE)}
        payload = json.loads(self.PID_FILE.read_text(encoding="utf-8"))
        pid = payload.get("pid")
        payload["running"] = bool(pid and self._is_running(pid))
        return payload

    def stop(self) -> dict[str, Any]:
        status = self.status()
        pid = status.get("pid")
        if not pid or not status.get("running"):
            return {"stopped": False, "message": "backend is not running"}
        os.killpg(pid, signal.SIGTERM)
        time.sleep(1)
        stopped = not self._is_running(pid)
        status["running"] = not stopped
        status["stopped"] = stopped
        if stopped and self.PID_FILE.exists():
            self.PID_FILE.unlink()
        return status

    def logs(self, lines: int = 40) -> dict[str, Any]:
        if not self.LOG_FILE.exists():
            return {"log_file": str(self.LOG_FILE), "lines": []}
        content = self.LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
        return {"log_file": str(self.LOG_FILE), "lines": content[-lines:]}
