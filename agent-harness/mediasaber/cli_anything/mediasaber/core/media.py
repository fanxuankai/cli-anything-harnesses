from __future__ import annotations

from typing import Any

from .client import MediaSaberClient


class MediaManager:
    def __init__(self, client: MediaSaberClient):
        self.client = client

    def sources(self) -> Any:
        return self.client.request_data("GET", "/api/v1/media/mediaSources")

    def search(
        self,
        keyword: str,
        *,
        media_source: int = 1,
        page_num: int = 1,
        page_size: int = 20,
    ) -> Any:
        return self.client.request_data(
            "GET",
            "/api/v1/media/search",
            params={
                "keyword": keyword,
                "mediaSource": media_source,
                "pageNum": page_num,
                "pageSize": page_size,
            },
        )

    def search_all(self, keyword: str, *, page_num: int = 1, page_size: int = 20) -> Any:
        return self.client.request_data(
            "GET",
            "/api/v1/media/searchAll",
            params={"keyword": keyword, "pageNum": page_num, "pageSize": page_size},
        )

    def autosuggest(self, query: str) -> Any:
        return self.client.request_data("GET", "/api/v1/media/autosuggest", params={"query": query})
