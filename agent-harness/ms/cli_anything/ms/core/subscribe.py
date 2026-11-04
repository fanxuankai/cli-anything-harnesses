"""Subscribe-specific business helpers."""

from __future__ import annotations

from typing import Any, Optional

from .client import MSClient


MEDIA_TYPE_CHOICES = ("movie", "tv")


class SubscribeManager:
    """Business-level helpers for subscribe-related commands."""

    def __init__(self, client: MSClient):
        self.client = client

    def page(self, media_type: str, page: int, page_size: int) -> dict[str, Any]:
        response = self.client.request(
            "GET",
            "/api/v1/subscribe/page",
            params={
                "type": media_type,
                "pageNum": str(page),
                "pageSize": str(page_size),
            },
        )
        if not response.ok:
            message = response.message or f"Subscribe page failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, dict):
            raise ValueError("Subscribe page returned an unexpected response payload")
        return response.data

    def add(
        self,
        name: str,
        media_type: str,
        year: int,
        season: int | None = None,
        *,
        tmdb_id: int | None = None,
    ) -> dict[str, Any]:
        # 最小 payload：未显式给出的衍生字段由后端订阅默认配置运行时兜底（跟随默认体系）
        payload: dict[str, Any] = {
            "name": name,
            "type": media_type,
            "year": year,
        }
        if media_type == "tv":
            payload["season"] = season if season is not None else 1
        if tmdb_id is not None:
            payload["tmdbId"] = tmdb_id

        response = self.client.request("POST", "/api/v1/subscribe/save", json_body=payload)
        if not response.ok:
            message = response.message or f"Subscribe add failed with HTTP {response.status_code}"
            raise ValueError(message)

        return {
            "status": "ok",
            "subscribe": payload,
        }
