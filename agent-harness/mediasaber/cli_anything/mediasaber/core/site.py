from __future__ import annotations

from typing import Any

from .client import MediaSaberClient


class SiteManager:
    def __init__(self, client: MediaSaberClient):
        self.client = client

    def list_sites(
        self,
        *,
        name: str | None = None,
        enabled: bool | None = None,
        site_type: int | None = None,
    ) -> Any:
        params = {}
        if name:
            params["name"] = name
        if enabled is not None:
            params["enabled"] = str(enabled).lower()
        if site_type is not None:
            params["type"] = site_type
        return self.client.request_data("GET", "/api/v1/site/list", params=params or None)

    def options(self) -> Any:
        return self.client.request_data("GET", "/api/v1/site/options")

    def rss(self, site_id: int) -> Any:
        return self.client.request_data("GET", f"/api/v1/site/getRss/{site_id}")

    def rss_torrents(self, site_id: int) -> Any:
        return self.client.request_data("GET", f"/api/v1/site/rssTorrents/{site_id}")
