from __future__ import annotations

from typing import Any

from .client import MediaSaberClient


class DownloaderManager:
    def __init__(self, client: MediaSaberClient):
        self.client = client

    def list_downloaders(self) -> Any:
        return self.client.request_data("GET", "/api/v1/downloader/list")

    def detail(self, downloader_id: int) -> Any:
        return self.client.request_data("GET", f"/api/v1/downloader/detail/{downloader_id}")

    def types(self) -> Any:
        return self.client.request_data("GET", "/api/v1/downloader/types")

    def delete_qb_tags(self) -> Any:
        return self.client.request_data("DELETE", "/api/v1/downloader/deleteQbTags")

    def directory_list(self, name: str | None = None, tag: str | None = None) -> Any:
        params = {}
        if name:
            params["name"] = name
        if tag:
            params["tag"] = tag
        return self.client.request_data("GET", "/api/v1/directory/list", params=params or None)

    def directory_match(self, tmdb_id: int, media_type: str, dir_tag: str | None = None) -> Any:
        params = {"tmdbId": tmdb_id, "mediaType": media_type}
        if dir_tag:
            params["dirTag"] = dir_tag
        return self.client.request_data("GET", "/api/v1/directory/match", params=params)

    def directory_tags(self) -> Any:
        return self.client.request_data("GET", "/api/v1/directory/tags")

    def directory_mkdir(self, directory_id: int) -> Any:
        return self.client.request_data("GET", f"/api/v1/directory/mkdir/{directory_id}")

    def directory_categories(self) -> Any:
        return self.client.request_data("GET", "/api/v1/directoryCategory/list")

    def directory_subcategory_options(self) -> Any:
        return self.client.request_data("GET", "/api/v1/directorySubCategory/options")

    def directory_subcategory_list(self, category_id: int | None = None) -> Any:
        params = {"categoryId": category_id} if category_id is not None else None
        return self.client.request_data("GET", "/api/v1/directorySubCategory/list", params=params)
