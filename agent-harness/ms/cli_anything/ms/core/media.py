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

MEDIA_SOURCE_LABELS = {
    100: "豆瓣",
    200: "TMDB",
    300: "芒果",
    400: "爱奇艺",
    500: "优酷",
    600: "腾讯",
    700: "灯塔",
    800: "B站",
    900: "Bangumi",
    1000: "央视影音",
    1100: "咪咕视频",
    1300: "Letterboxd",
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
        return self._normalize_media_page(response.data)

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
        return self._normalize_media_page(response.data)

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
        return self._normalize_media_page(response.data)

    def _normalize_media_page(self, data: dict[str, Any]) -> dict[str, Any]:
        items = data.get("list") or []
        if not isinstance(items, list):
            items = []
        return {
            "total": data.get("total", 0),
            "pageNum": data.get("pageNum", 1),
            "pageSize": data.get("pageSize", len(items)),
            "list": [self._normalize_media_item(item) for item in items],
        }

    def _normalize_media_item(self, item: Any) -> dict[str, Any]:
        if not isinstance(item, dict):
            item = {}

        source_code = item.get("source")
        subscription_id = self._normalize_subscription_id(item.get("rssId"))
        published_sites = item.get("publishedSites")

        return {
            "media_id": item.get("id"),
            "title": item.get("title", "") or "",
            "subtitle": item.get("subtitle", "") or "",
            "source": {
                "code": source_code,
                "name": MEDIA_SOURCE_LABELS.get(source_code, "" if source_code in (None, "") else str(source_code)),
            },
            "media_type": item.get("type", "") or "",
            "year": item.get("year"),
            "vote": item.get("vote"),
            "overview": item.get("overview", "") or "",
            "poster_url": item.get("poster", "") or "",
            "subscription": {
                "subscribed": subscription_id is not None,
                "id": subscription_id,
            },
            "library": {
                "archived": bool(item.get("archived")),
                "resource_count": item.get("cloudStorageResourceCount", 0) or 0,
            },
            "published_site_count": len(published_sites) if isinstance(published_sites, list) else 0,
        }

    def _normalize_subscription_id(self, rss_id: Any) -> Any | None:
        if rss_id in (None, "", 0):
            return None
        try:
            return rss_id if int(rss_id) > 0 else None
        except (TypeError, ValueError):
            return rss_id
