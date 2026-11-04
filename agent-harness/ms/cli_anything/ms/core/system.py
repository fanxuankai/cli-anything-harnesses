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

    def workbench(self, *, force: bool = False) -> dict[str, Any]:
        """获取首页工作台聚合概览。"""
        params = {"force": "true"} if force else None
        response = self.client.request("GET", "/api/v1/system/workbenchOverview", params=params)
        if not response.ok:
            message = response.message or f"Workbench overview failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, dict):
            raise ValueError("Workbench overview returned an unexpected response payload")
        return response.data

    def health_overview(self) -> dict[str, Any]:
        """获取系统体检即时概览（低成本，无连通探测）。"""
        response = self.client.request("GET", "/api/v1/system/health/overview")
        if not response.ok:
            message = response.message or f"Health overview failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, dict):
            raise ValueError("Health overview returned an unexpected response payload")
        return response.data

    def health_report(self, *, refresh: bool = False) -> dict[str, Any]:
        """获取系统体检报告（优先返回缓存）。"""
        params = {"refresh": "true"} if refresh else None
        response = self.client.request("GET", "/api/v1/system/health/report", params=params)
        if not response.ok:
            message = response.message or f"Health report failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, dict):
            raise ValueError("Health report returned an unexpected response payload")
        return response.data

    def version(self) -> dict[str, Any]:
        """查询系统版本与更新状态。"""
        response = self.client.request("GET", "/api/v1/system/upgradeVersion")
        if not response.ok:
            message = response.message or f"Version request failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, dict):
            raise ValueError("Version response returned an unexpected response payload")
        return {
            "has_update": bool(response.data.get("hasUpdate")),
            "latest_version": str(response.data.get("latestVersion", "") or ""),
        }
