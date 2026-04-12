"""日志管理模块。"""

from typing import Optional

from .client import ManagementClient


class LogManager:
    """管理 CLIProxyAPI 的日志。"""

    def __init__(self, client: ManagementClient):
        self.client = client

    def get_logs(self, lines: int = 100) -> str:
        resp = self.client.get("/logs", params={"lines": lines})
        resp.raise_for_status()
        return resp.text

    def delete_logs(self) -> dict:
        resp = self.client.delete("/logs")
        resp.raise_for_status()
        return resp.json()

    def get_request_log(self) -> dict:
        resp = self.client.get("/request-log")
        resp.raise_for_status()
        return resp.json()

    def set_request_log(self, enabled: bool) -> dict:
        resp = self.client.put("/request-log", json_data={"value": enabled})
        resp.raise_for_status()
        return resp.json()

    def get_request_error_logs(self) -> dict:
        resp = self.client.get("/request-error-logs")
        resp.raise_for_status()
        return resp.json()

    def download_request_error_log(self, name: str) -> str:
        resp = self.client.get(f"/request-error-logs/{name}")
        resp.raise_for_status()
        return resp.text

    def get_request_log_by_id(self, log_id: str) -> dict:
        resp = self.client.get(f"/request-log-by-id/{log_id}")
        resp.raise_for_status()
        return resp.json()
