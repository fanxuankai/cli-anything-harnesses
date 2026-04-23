"""Media-specific business helpers."""

from __future__ import annotations

from typing import Any

from .client import MSClient


MEDIA_SOURCE_MAP = {
    "douban": 100,
    "tmdb": 200,
}

MEDIA_RANK_SOURCE_MAP = {
    "douban": 100,
    "tmdb": 200,
    "iqiyi": 400,
    "dengta": 700,
    "bilibili": 800,
    "letterboxd": 1300,
}

MEDIA_RECOMMEND_SOURCE_MAP = {
    "douban": 100,
    "tmdb": 200,
    "mgtv": 300,
    "iqiyi": 400,
    "youku": 500,
    "tencent": 600,
    "dengta": 700,
    "bilibili": 800,
    "bangumi": 900,
    "cctv": 1000,
    "miguvideo": 1100,
    "letterboxd": 1300,
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

    def rank_sources(self) -> list[dict[str, Any]]:
        response = self.client.request("GET", "/api/v1/mediaSubject/mediaSources")
        if not response.ok:
            message = response.message or f"Media rank sources failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, list):
            raise ValueError("Media rank sources returned an unexpected response payload")
        return response.data

    def rank_categories(self, media_source: int) -> list[dict[str, Any]]:
        response = self.client.request("GET", f"/api/v1/mediaSubject/categories/{media_source}")
        if not response.ok:
            message = response.message or f"Media rank categories failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, list):
            raise ValueError("Media rank categories returned an unexpected response payload")
        return response.data

    def rank_subjects(self, category_code: str) -> list[dict[str, Any]]:
        response = self.client.request(
            "GET",
            "/api/v1/mediaSubject/list",
            params={"categoryCode": category_code},
        )
        if not response.ok:
            message = response.message or f"Media rank subjects failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, list):
            raise ValueError("Media rank subjects returned an unexpected response payload")
        return response.data

    def rank_items(self, category_code: str, code: str, page: int, page_size: int) -> dict[str, Any]:
        response = self.client.request(
            "GET",
            "/api/v1/mediaSubject/items",
            params={
                "categoryCode": category_code,
                "code": code,
                "pageNum": str(page),
                "pageSize": str(page_size),
            },
        )
        if not response.ok:
            message = response.message or f"Media rank items failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, dict):
            raise ValueError("Media rank items returned an unexpected response payload")
        return response.data

    def recommend_sources(self) -> list[dict[str, Any]]:
        response = self.client.request("GET", "/api/v1/mediaRecommend/mediaSources")
        if not response.ok:
            message = response.message or f"Media recommend sources failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, list):
            raise ValueError("Media recommend sources returned an unexpected response payload")
        return response.data

    def recommend_channels(self, media_source: int) -> list[dict[str, Any]]:
        response = self.client.request("GET", f"/api/v1/mediaRecommend/channels/{media_source}")
        if not response.ok:
            message = response.message or f"Media recommend channels failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, list):
            raise ValueError("Media recommend channels returned an unexpected response payload")
        return response.data

    def recommend_options(self, media_source: int, channel: str) -> list[dict[str, Any]]:
        response = self.client.request(
            "GET",
            "/api/v1/mediaRecommend/options",
            params={
                "mediaSource": str(media_source),
                "channel": channel,
            },
        )
        if not response.ok:
            message = response.message or f"Media recommend options failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, list):
            raise ValueError("Media recommend options returned an unexpected response payload")
        return response.data

    def recommend_items(
        self,
        media_source: int,
        channel: str,
        options: dict[str, str],
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        response = self.client.request(
            "POST",
            "/api/v1/mediaRecommend/page",
            json_body={
                "mediaSource": media_source,
                "channel": channel,
                "options": options,
                "pageNum": page,
                "pageSize": page_size,
            },
        )
        if not response.ok:
            message = response.message or f"Media recommend items failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, dict):
            raise ValueError("Media recommend items returned an unexpected response payload")
        return response.data
