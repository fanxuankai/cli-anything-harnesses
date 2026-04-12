"""认证文件管理模块。"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from .client import ManagementClient

CODEX_QUOTA_URL = "https://chatgpt.com/backend-api/wham/usage"
CODEX_QUOTA_USER_AGENT = "codex_cli_rs/0.76.0 (Debian 13.0.0; x86_64) WindowsTerminal"


class AuthManager:
    """管理 CLIProxyAPI 的认证文件。"""

    def __init__(self, client: ManagementClient):
        self.client = client

    def list_auth_files(self, disabled: Optional[bool] = None) -> dict:
        resp = self.client.get("/auth-files", params=None)
        resp.raise_for_status()
        data = resp.json()
        files = data.get("files", [])
        if disabled is None:
            return data
        filtered = [item for item in files if bool(item.get("disabled", False)) is disabled]
        return {**data, "files": filtered}

    def get_codex_quotas(self) -> dict:
        payload = self.list_auth_files(disabled=False)
        files = payload.get("files", [])
        codex_files = [item for item in files if str(item.get("provider") or item.get("type") or "").strip().lower() == "codex"]
        quotas = []
        success = 0
        failed = 0

        for item in codex_files:
            auth_index = str(item.get("auth_index") or "").strip()
            name = str(item.get("name") or item.get("id") or auth_index or "codex")
            email = str(item.get("email") or "").strip()
            id_token = item.get("id_token") if isinstance(item.get("id_token"), dict) else {}
            account_id = str(id_token.get("chatgpt_account_id") or "").strip()
            plan_type = str(id_token.get("plan_type") or "").strip()
            quota = {
                "auth_index": auth_index,
                "name": name,
                "email": email,
                "plan_type": plan_type,
            }

            if not auth_index:
                quota["error"] = "missing auth_index"
                quotas.append(quota)
                failed += 1
                continue
            if not account_id:
                quota["error"] = "missing chatgpt_account_id"
                quotas.append(quota)
                failed += 1
                continue

            request_body = {
                "auth_index": auth_index,
                "method": "GET",
                "url": CODEX_QUOTA_URL,
                "header": {
                    "Authorization": "Bearer $TOKEN$",
                    "Content-Type": "application/json",
                    "User-Agent": CODEX_QUOTA_USER_AGENT,
                    "Chatgpt-Account-Id": account_id,
                },
            }

            try:
                resp = self.client.post("/api-call", json_data=request_body)
                resp.raise_for_status()
                api_result = resp.json()
                body = api_result.get("body") or "{}"
                payload_json = json.loads(body)
                rate_limit = payload_json.get("rate_limit") or {}
                primary = self._build_window(rate_limit.get("primary_window") or {})
                secondary = self._build_window(rate_limit.get("secondary_window") or {})
                quota.update({
                    "status_code": api_result.get("status_code"),
                    "email": str(payload_json.get("email") or email).strip(),
                    "plan_type": str(payload_json.get("plan_type") or plan_type).strip(),
                    "primary_window": primary,
                    "secondary_window": secondary,
                })
                quotas.append(quota)
                success += 1
            except Exception as exc:
                quota["error"] = str(exc)
                quotas.append(quota)
                failed += 1

        return {
            "total": len(quotas),
            "success": success,
            "failed": failed,
            "quotas": quotas,
        }

    @staticmethod
    def _build_window(window: dict) -> dict:
        used_percent = int(window.get("used_percent") or 0)
        reset_at = int(window.get("reset_at") or 0)
        return {
            "used_percent": used_percent,
            "remaining_percent": max(0, 100 - used_percent),
            "limit_window_seconds": int(window.get("limit_window_seconds") or 0),
            "reset_after_seconds": int(window.get("reset_after_seconds") or 0),
            "reset_at": reset_at,
            "reset_at_local": datetime.fromtimestamp(reset_at).strftime("%m/%d %H:%M") if reset_at else "",
        }

    def get_auth_file_models(self) -> dict:
        resp = self.client.get("/auth-files/models")
        resp.raise_for_status()
        return resp.json()

    def upload_auth_file(self, filename: str, content: str) -> dict:
        import requests

        url = f"{self.client.conn.base_url}/v0/management/auth-files"
        files = {"file": (filename, content, "application/json")}
        headers = {"Authorization": f"Bearer {self.client.conn.management_key}"}
        resp = requests.post(url, files=files, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def download_auth_file(self, filename: str) -> str:
        resp = self.client.get("/auth-files/download", params={"filename": filename})
        resp.raise_for_status()
        return resp.text

    def delete_auth_file(self, filename: str) -> dict:
        resp = self.client.delete("/auth-files", json_data={"filename": filename})
        resp.raise_for_status()
        return resp.json()

    def patch_auth_file_status(self, filename: str, disabled: bool) -> dict:
        resp = self.client.patch("/auth-files/status", json_data={
            "filename": filename,
            "disabled": disabled,
        })
        resp.raise_for_status()
        return resp.json()

    def patch_auth_file_fields(self, filename: str, fields: dict) -> dict:
        resp = self.client.patch("/auth-files/fields", json_data={
            "filename": filename,
            **fields,
        })
        resp.raise_for_status()
        return resp.json()

    def get_model_definitions(self, channel: str) -> dict:
        resp = self.client.get(f"/model-definitions/{channel}")
        resp.raise_for_status()
        return resp.json()

    def get_auth_status(self, session_id: str) -> dict:
        resp = self.client.get("/get-auth-status", params={"session_id": session_id})
        resp.raise_for_status()
        return resp.json()

    def import_vertex(self, key_json: str, prefix: str = "") -> dict:
        data: dict[str, Any] = {"key": key_json}
        if prefix:
            data["prefix"] = prefix
        resp = self.client.post("/vertex/import", json_data=data)
        resp.raise_for_status()
        return resp.json()
