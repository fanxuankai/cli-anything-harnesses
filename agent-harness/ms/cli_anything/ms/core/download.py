"""Download-specific business helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from .client import MSClient


MEDIA_TYPE_CHOICES = ("movie", "tv")


class DownloadManager:
    """Business-level helpers for download-related commands."""

    def __init__(self, client: MSClient):
        self.client = client

    def downloaders(self) -> dict[str, Any]:
        response = self.client.request("GET", "/api/v1/downloader/list")
        if not response.ok:
            message = response.message or f"Downloader list failed with HTTP {response.status_code}"
            raise ValueError(message)
        if response.data is None:
            return {"total": 0, "items": []}
        if not isinstance(response.data, list):
            raise ValueError("Downloader list returned an unexpected response payload")
        items = [self._normalize_downloader(item) for item in response.data]
        return {"total": len(items), "items": items}

    def downloading(self, *, download_ids: Optional[list[str]] = None) -> dict[str, Any]:
        clean_ids = [item.strip() for item in download_ids or [] if item.strip()]
        body: dict[str, Any] = {}
        if clean_ids:
            body["downloadIds"] = clean_ids

        response = self.client.request("POST", "/api/v1/download/downloading", json_body=body)
        if not response.ok:
            message = response.message or f"Downloading list failed with HTTP {response.status_code}"
            raise ValueError(message)
        if response.data is None:
            return {"total": 0, "items": []}
        if not isinstance(response.data, list):
            raise ValueError("Downloading list returned an unexpected response payload")
        items = [self._normalize_downloading(item) for item in response.data]
        return {"total": len(items), "items": items}

    def history(
        self,
        *,
        title: Optional[str] = None,
        media_type: Optional[str] = None,
        site_id: Optional[int] = None,
        site_name: Optional[str] = None,
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
        if site_id is not None:
            params["siteId"] = str(site_id)
        site_name = (site_name or "").strip()
        if site_name:
            params["siteName"] = site_name

        response = self.client.request("GET", "/api/v1/download/history", params=params)
        if not response.ok:
            message = response.message or f"Download history failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, dict):
            raise ValueError("Download history returned an unexpected response payload")
        return self._normalize_history_page(response.data)

    def pause(self, download_id: str) -> dict[str, Any]:
        return self._operate("GET", "pause", download_id)

    def resume(self, download_id: str) -> dict[str, Any]:
        return self._operate("GET", "resume", download_id)

    def delete(self, download_id: str, *, delete_file: bool = False) -> dict[str, Any]:
        params = {"deleteFile": "true"} if delete_file else None
        return self._operate("DELETE", "delete", download_id, params=params)

    def _operate(self, method: str, action: str, download_id: str, *, params: Optional[dict[str, str]] = None) -> dict[str, Any]:
        download_id = (download_id or "").strip()
        if not download_id:
            raise ValueError("download id is required")
        response = self.client.request(method, f"/api/v1/download/{action}/{download_id}", params=params)
        if not response.ok:
            message = response.message or f"Download {action} failed with HTTP {response.status_code}"
            raise ValueError(message)
        return {
            "status": "submitted",
            "action": action,
            "download_id": download_id,
            "response": response.data,
            "message": response.message,
        }

    def _normalize_downloader(self, item: Any) -> dict[str, Any]:
        if not isinstance(item, dict):
            item = {}
        config = item.get("config") if isinstance(item.get("config"), dict) else {}
        return {
            "id": _to_int(item.get("id")),
            "type": _to_int(item.get("type")),
            "name": str(item.get("name", "") or ""),
            "enabled": bool(item.get("enabled")),
            "default": bool(item.get("default")),
            "remark": str(item.get("remark", "") or ""),
            "url": str(config.get("url", "") or ""),
            "monitor": str(config.get("monitor", "") or ""),
            "move_mode": str(config.get("moveMode", "") or ""),
            "created_at": _to_int(item.get("createdAt")),
            "created_at_text": _format_timestamp(item.get("createdAt")),
        }

    def _normalize_downloading(self, item: Any) -> dict[str, Any]:
        if not isinstance(item, dict):
            item = {}
        speed = _to_int(item.get("speed")) or 0
        progress = _to_float(item.get("progress")) or 0.0
        return {
            "id": str(item.get("id", "") or ""),
            "title": str(item.get("title", "") or ""),
            "media_type": str(item.get("mediaType", "") or ""),
            "year": _to_int(item.get("year")),
            "season_episode": str(item.get("seasonEpisode", "") or ""),
            "speed": speed,
            "speed_text": f"{_format_bytes(speed)}/s",
            "progress": progress,
            "progress_percent": round(progress * 100, 1),
            "state": str(item.get("state", "") or ""),
            "paused": bool(item.get("paused")),
            "torrent_title": str(item.get("torrentTitle", "") or ""),
            "save_path": str(item.get("savePath", "") or ""),
            "site_id": _to_int(item.get("siteId")),
            "site_name": str(item.get("siteName", "") or ""),
            "page_url": str(item.get("pageUrl", "") or ""),
            "description": str(item.get("description", "") or ""),
        }

    def _normalize_history_page(self, data: dict[str, Any]) -> dict[str, Any]:
        items = data.get("list") or []
        if not isinstance(items, list):
            items = []
        return {
            "total": _to_int(data.get("total")) or 0,
            "pageNum": _to_int(data.get("pageNum")) or 1,
            "pageSize": _to_int(data.get("pageSize")) or len(items),
            "list": [self._normalize_history_item(item) for item in items],
        }

    def _normalize_history_item(self, item: Any) -> dict[str, Any]:
        if not isinstance(item, dict):
            item = {}
        return {
            "id": _to_int(item.get("id")),
            "title": str(item.get("title", "") or ""),
            "media_type": str(item.get("mediaType", "") or ""),
            "year": _to_int(item.get("year")),
            "tmdb_id": _to_int(item.get("tmdbId")),
            "site_id": _to_int(item.get("siteId")),
            "site_name": str(item.get("siteName", "") or ""),
            "torrent_id": str(item.get("torrentId", "") or ""),
            "torrent_title": str(item.get("torrentTitle", "") or ""),
            "description": str(item.get("description", "") or ""),
            "season_episode": str(item.get("seasonEpisode", "") or ""),
            "downloader_id": _to_int(item.get("downloaderId")),
            "download_params_id": _to_int(item.get("downloadParamId")),
            "save_path": str(item.get("savePath", "") or ""),
            "data_dir": str(item.get("dataDir", "") or ""),
            "download_id": str(item.get("downloadId", "") or ""),
            "page_url": str(item.get("pageUrl", "") or ""),
            "created_at": _to_int(item.get("createdAt")),
            "created_at_text": _format_timestamp(item.get("createdAt")),
        }


def _to_int(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_timestamp(value: Any) -> str:
    timestamp = _to_int(value)
    if not timestamp:
        return ""
    if timestamp > 10_000_000_000:
        timestamp = timestamp // 1000
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


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
