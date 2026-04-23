"""Media-server-specific business helpers."""

from __future__ import annotations

from typing import Any

from .client import MSClient


class MediaServerManager:
    """Business-level helpers for media-server-related commands."""

    MISS_EPISODES_PREVIEW_LIMIT = 20

    def __init__(self, client: MSClient):
        self.client = client

    def miss_episodes_check(self) -> dict[str, Any]:
        response = self.client.request("GET", "/api/v1/mediaServer/missEpisodesCheck")
        if not response.ok:
            message = response.message or f"Miss episodes check failed with HTTP {response.status_code}"
            raise ValueError(message)
        if response.data is None:
            return {"total": 0, "items": []}
        if not isinstance(response.data, list):
            raise ValueError("Miss episodes check returned an unexpected response payload")

        items = response.data[: self.MISS_EPISODES_PREVIEW_LIMIT]
        return {
            "total": len(response.data),
            "items": items,
        }
