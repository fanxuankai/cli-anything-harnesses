"""System information helpers for ms."""

from __future__ import annotations

from typing import Any

from .client import MSClient


class SystemManager:
    """系统信息管理器。"""

    def __init__(self, client: MSClient):
        self.client = client

    def nas_info(self) -> list[dict[str, Any]]:
        """获取 NAS 信息列表。"""
        response = self.client.request("GET", "/api/v1/system/nas/info")
        if not response.ok:
            message = response.message or f"NAS info request failed with HTTP {response.status_code}"
            raise ValueError(message)

        if response.data is None:
            return []
        if not isinstance(response.data, list):
            raise ValueError("NAS info response data is not a list")

        return response.data
