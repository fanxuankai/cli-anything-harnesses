"""使用统计模块。"""

from .client import ManagementClient


class UsageManager:
    """管理 CLIProxyAPI 的使用统计。"""

    def __init__(self, client: ManagementClient):
        self.client = client

    def get_stats(self) -> dict:
        resp = self.client.get("/usage")
        resp.raise_for_status()
        return resp.json()

    def export_stats(self) -> str:
        resp = self.client.get("/usage/export")
        resp.raise_for_status()
        return resp.text

    def import_stats(self, data: str) -> dict:
        resp = self.client.post("/usage/import", json_data={"data": data})
        resp.raise_for_status()
        return resp.json()
