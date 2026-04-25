"""Media-server-specific business helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Optional

from .client import MSClient


MEDIA_SERVER_TYPE_LABELS = {
    100: "Emby",
    200: "极影视",
    300: "Jellyfin",
    400: "UGOS Pro",
    500: "Plex",
    600: "FNOS",
}
MEDIA_TYPE_CHOICES = ("movie", "tv")


class MediaServerManager:
    """Business-level helpers for media-server-related commands."""

    MISS_EPISODES_PREVIEW_LIMIT = 20

    def __init__(self, client: MSClient):
        self.client = client

    def list(self) -> dict[str, Any]:
        response = self.client.request("GET", "/api/v1/mediaServer/list")
        if not response.ok:
            message = response.message or f"Media server list failed with HTTP {response.status_code}"
            raise ValueError(message)
        if response.data is None:
            return {"total": 0, "items": []}
        if not isinstance(response.data, list):
            raise ValueError("Media server list returned an unexpected response payload")

        items = [self._normalize_server(item) for item in response.data]
        return {"total": len(items), "items": items}

    def detail(self, server_id: int) -> dict[str, Any]:
        response = self.client.request("GET", f"/api/v1/mediaServer/detail/{server_id}")
        if not response.ok:
            message = response.message or f"Media server detail failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, dict):
            raise ValueError("Media server detail returned an unexpected response payload")
        return self._normalize_server(response.data)

    def libraries(self, server_id: int) -> dict[str, Any]:
        response = self.client.request("GET", f"/api/v1/mediaServer/libraries/{server_id}")
        if not response.ok:
            message = response.message or f"Media server libraries failed with HTTP {response.status_code}"
            raise ValueError(message)
        if response.data is None:
            return {"server_id": server_id, "total": 0, "items": []}
        if not isinstance(response.data, list):
            raise ValueError("Media server libraries returned an unexpected response payload")
        items = [self._normalize_library(item) for item in response.data]
        return {"server_id": server_id, "total": len(items), "items": items}

    def statistics(self, server_id: int) -> dict[str, Any]:
        response = self.client.request("GET", f"/api/v1/mediaServerSync/statistics/{server_id}")
        if not response.ok:
            message = response.message or f"Media server statistics failed with HTTP {response.status_code}"
            raise ValueError(message)
        if response.data is None:
            return self._normalize_statistics({}, server_id=server_id)
        if not isinstance(response.data, dict):
            raise ValueError("Media server statistics returned an unexpected response payload")
        return self._normalize_statistics(response.data, server_id=server_id)

    def sync_items(
        self,
        server_id: int,
        *,
        title: Optional[str] = None,
        media_type: Optional[str] = None,
        miss_eps: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        media_type = (media_type or "").strip().lower()
        if media_type and media_type not in MEDIA_TYPE_CHOICES:
            raise ValueError("--type must be movie or tv")

        params: dict[str, str] = {
            "pageNum": str(page),
            "pageSize": str(page_size),
        }
        title = (title or "").strip()
        if title:
            params["title"] = title
        if media_type:
            params["mediaType"] = media_type
        if miss_eps is not None:
            params["missEps"] = "true" if miss_eps else "false"

        response = self.client.request("GET", f"/api/v1/mediaServerSync/items/{server_id}", params=params)
        if not response.ok:
            message = response.message or f"Media server sync items failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, dict):
            raise ValueError("Media server sync items returned an unexpected response payload")
        return self._normalize_page(response.data)

    def playing(self, server_id: int) -> dict[str, Any]:
        return self._media_items(
            server_id,
            path=f"/api/v1/mediaServer/playing/{server_id}",
            error_label="Media server playing",
            payload_label="Media server playing",
            normalizer=self._normalize_resume_item,
        )

    def latest(self, server_id: int, *, num: int = 12) -> dict[str, Any]:
        return self._media_items(
            server_id,
            path=f"/api/v1/mediaServer/latest/{server_id}",
            params={"num": str(num)},
            error_label="Media server latest",
            payload_label="Media server latest",
            normalizer=self._normalize_latest_item,
        )

    def resume(self, server_id: int, *, num: int = 12) -> dict[str, Any]:
        return self._media_items(
            server_id,
            path=f"/api/v1/mediaServer/resume/{server_id}",
            params={"num": str(num)},
            error_label="Media server resume",
            payload_label="Media server resume",
            normalizer=self._normalize_resume_item,
        )

    def sync_run(self, server_id: int) -> dict[str, Any]:
        response = self.client.request("GET", f"/api/v1/mediaServerSync/run/{server_id}")
        if not response.ok:
            message = response.message or f"Media server sync run failed with HTTP {response.status_code}"
            raise ValueError(message)
        return {
            "status": "submitted",
            "server_id": server_id,
            "response": response.data,
            "message": response.message,
        }

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

    def _media_items(
        self,
        server_id: int,
        *,
        path: str,
        error_label: str,
        payload_label: str,
        normalizer: Callable[[Any], dict[str, Any]],
        params: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        response = self.client.request("GET", path, params=params)
        if not response.ok:
            message = response.message or f"{error_label} failed with HTTP {response.status_code}"
            raise ValueError(message)
        if response.data is None:
            return {"server_id": server_id, "total": 0, "items": []}
        if not isinstance(response.data, list):
            raise ValueError(f"{payload_label} returned an unexpected response payload")
        items = [normalizer(item) for item in response.data]
        return {"server_id": server_id, "total": len(items), "items": items}

    def _normalize_server(self, item: Any) -> dict[str, Any]:
        if not isinstance(item, dict):
            item = {}
        server_type = self._to_int(item.get("type"))
        statistics = item.get("statistics") if isinstance(item.get("statistics"), dict) else {}
        return {
            "id": self._to_int(item.get("id")),
            "name": str(item.get("name", "") or ""),
            "type": server_type,
            "type_text": MEDIA_SERVER_TYPE_LABELS.get(server_type, "" if server_type is None else str(server_type)),
            "enabled": bool(item.get("enabled")),
            "default": bool(item.get("default")),
            "updated_at": self._to_int(item.get("updatedAt")),
            "updated_at_text": _format_timestamp(item.get("updatedAt")),
            "statistics": self._normalize_statistics(statistics, server_id=self._to_int(item.get("id"))),
        }

    def _normalize_statistics(self, item: dict[str, Any], *, server_id: Optional[int] = None) -> dict[str, Any]:
        media_server_id = self._to_int(item.get("mediaServerId")) or server_id
        time_ms = self._to_int(item.get("time")) or 0
        return {
            "id": self._to_int(item.get("id")),
            "media_server_id": media_server_id,
            "movie_count": self._to_int(item.get("movieCount")) or 0,
            "tv_count": self._to_int(item.get("tvCount")) or 0,
            "time_ms": time_ms,
            "time_seconds": round(time_ms / 1000, 3),
            "created_at": self._to_int(item.get("createdAt")),
            "created_at_text": _format_timestamp(item.get("createdAt")),
            "updated_at": self._to_int(item.get("updatedAt")),
            "updated_at_text": _format_timestamp(item.get("updatedAt")),
        }

    def _normalize_library(self, item: Any) -> dict[str, Any]:
        if not isinstance(item, dict):
            item = {}
        return {
            "id": str(item.get("id", "") or ""),
            "name": str(item.get("name", "") or ""),
            "paths": item.get("paths") if isinstance(item.get("paths"), list) else [],
            "media_type": str(item.get("mediaType", "") or ""),
            "image": str(item.get("image", "") or ""),
            "link": str(item.get("link", "") or ""),
        }

    def _normalize_page(self, data: dict[str, Any]) -> dict[str, Any]:
        items = data.get("list") or []
        if not isinstance(items, list):
            items = []
        return {
            "total": self._to_int(data.get("total")) or 0,
            "pageNum": self._to_int(data.get("pageNum")) or 1,
            "pageSize": self._to_int(data.get("pageSize")) or len(items),
            "list": [self._normalize_sync_item(item) for item in items],
        }

    def _normalize_sync_item(self, item: Any) -> dict[str, Any]:
        if not isinstance(item, dict):
            item = {}
        size = self._to_int(item.get("size")) or 0
        return {
            "id": self._to_int(item.get("id")),
            "media_server_id": self._to_int(item.get("mediaServerId")),
            "library": str(item.get("library", "") or ""),
            "library_name": str(item.get("libraryName", "") or ""),
            "item_id": str(item.get("itemId", "") or ""),
            "item_type": str(item.get("itemType", "") or ""),
            "title": str(item.get("title", "") or ""),
            "origin_title": str(item.get("originTitle", "") or ""),
            "year": self._to_int(item.get("year")),
            "tmdb_id": self._to_int(item.get("tmdbId")),
            "imdb_id": str(item.get("imdbId", "") or ""),
            "path": str(item.get("path", "") or ""),
            "size": size,
            "size_text": _format_bytes(size),
            "episodes": item.get("episodes") if isinstance(item.get("episodes"), list) else [],
            "episodes_text": _format_episodes(item.get("episodes")),
            "miss_eps": bool(item.get("missEps")),
            "created_at": self._to_int(item.get("createdAt")),
            "created_at_text": _format_timestamp(item.get("createdAt")),
            "updated_at": self._to_int(item.get("updatedAt")),
            "updated_at_text": _format_timestamp(item.get("updatedAt")),
        }

    def _normalize_resume_item(self, item: Any) -> dict[str, Any]:
        normalized = self._normalize_latest_item(item)
        if not isinstance(item, dict):
            item = {}
        normalized["percent"] = self._to_float(item.get("percent")) or 0.0
        return normalized

    def _normalize_latest_item(self, item: Any) -> dict[str, Any]:
        if not isinstance(item, dict):
            item = {}
        return {
            "id": str(item.get("id", "") or ""),
            "name": str(item.get("name", "") or ""),
            "type": str(item.get("type", "") or ""),
            "image": str(item.get("image", "") or ""),
            "link": str(item.get("link", "") or ""),
        }

    def _to_int(self, value: Any) -> Optional[int]:
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _to_float(self, value: Any) -> Optional[float]:
        if value in (None, ""):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


def _format_bytes(value: Any) -> str:
    try:
        size = float(value or 0)
    except (TypeError, ValueError):
        return ""
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_idx = 0
    while size >= 1024 and unit_idx < len(units) - 1:
        size /= 1024
        unit_idx += 1
    if unit_idx == 0:
        return f"{int(size)} {units[unit_idx]}"
    return f"{size:.2f} {units[unit_idx]}"


def _format_timestamp(value: Any) -> str:
    try:
        timestamp = int(value)
    except (TypeError, ValueError):
        return ""
    if timestamp <= 0:
        return ""
    if timestamp > 10_000_000_000:
        timestamp = timestamp // 1000
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def _format_episodes(value: Any) -> str:
    if not isinstance(value, list) or not value:
        return ""
    parts = []
    for item in value:
        if not isinstance(item, dict):
            continue
        season = item.get("season")
        episodes = item.get("episodes")
        if isinstance(episodes, list) and episodes:
            parts.append(f"S{int(season or 0):02d}:{_format_episode_ranges(episodes)}")
    return " / ".join(parts)


def _format_episode_ranges(episodes: list[Any]) -> str:
    normalized = sorted({int(item) for item in episodes if isinstance(item, int) or str(item).isdigit()})
    if not normalized:
        return ""
    ranges: list[str] = []
    start = normalized[0]
    end = normalized[0]
    for current in normalized[1:]:
        if current == end + 1:
            end = current
            continue
        ranges.append(_format_episode_range(start, end))
        start = current
        end = current
    ranges.append(_format_episode_range(start, end))
    return ", ".join(ranges)


def _format_episode_range(start: int, end: int) -> str:
    return f"E{start}" if start == end else f"E{start}-{end}"
