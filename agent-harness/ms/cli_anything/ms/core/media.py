"""Media-specific business helpers."""

from __future__ import annotations

from typing import Any

from .client import MSClient


MEDIA_SOURCE_MAP = {
    "douban": 100,
    "tmdb": 200,
}


class MediaManager:
    """Business-level helpers for media-related commands."""

    def __init__(self, client: MSClient):
        self.client = client

    def search(self, source_code: int, keyword: str, page: int, page_size: int) -> dict[str, Any]:
        response = self.client.request(
            "GET",
            "/api/v1/media/search",
            params={
                "mediaSource": str(source_code),
                "keyword": keyword,
                "pageNum": str(page),
                "pageSize": str(page_size),
            },
        )
        if not response.ok:
            message = response.message or f"Media search failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, dict):
            raise ValueError("Media search returned an unexpected response payload")
        return response.data
