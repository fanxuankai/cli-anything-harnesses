"""Subscribe-specific business helpers."""

from __future__ import annotations

from typing import Any, Optional

from .client import MSClient


MEDIA_TYPE_CHOICES = ("movie", "tv")

_DEFAULT_CONFIG_FIELDS = (
    "filterRuleId",
    "torrentSortId",
    "downloaderId",
    "downloaderParamsId",
    "downloaderDirectoryId",
    "rssSites",
    "searchSites",
    "autoUpdateTotalEpisode",
    "include",
    "exclude",
    "subCloudStorage",
    "subCloudStoragePath",
    "csCreatorIds",
)


class SubscribeManager:
    """Business-level helpers for subscribe-related commands."""

    def __init__(self, client: MSClient):
        self.client = client

    def get_default_config(self, media_type: str) -> Optional[dict[str, Any]]:
        response = self.client.request("GET", f"/api/v1/subscribeDefaultConfig/detail/{media_type}")
        if not response.ok:
            message = response.message or f"Subscribe config request failed with HTTP {response.status_code}"
            raise ValueError(message)
        if response.data is None:
            return None
        if not isinstance(response.data, dict):
            raise ValueError("Subscribe default config returned an unexpected response payload")
        return response.data

    def add(self, name: str, media_type: str, year: int, season: int | None = None) -> dict[str, Any]:
        default_config = self.get_default_config(media_type)
        if default_config is None:
            raise ValueError(f"未配置{media_type}默认订阅设置")

        payload: dict[str, Any] = {
            "name": name,
            "type": media_type,
            "year": year,
        }
        if media_type == "tv":
            payload["season"] = season if season is not None else 1

        for key in _DEFAULT_CONFIG_FIELDS:
            if key in default_config:
                payload[key] = default_config[key]

        response = self.client.request("POST", "/api/v1/subscribe/save", json_body=payload)
        if not response.ok:
            message = response.message or f"Subscribe add failed with HTTP {response.status_code}"
            raise ValueError(message)

        return {
            "status": "ok",
            "subscribe": payload,
        }
