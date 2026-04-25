"""Cloud resource helpers for ms."""

from __future__ import annotations

from typing import Any, Optional

from .client import MSClient


MEDIA_TYPE_CHOICES = ("movie", "tv")
CLOUD_RESOURCE_RANK_RANGE_CHOICES = ("today", "week", "all")
CLOUD_RESOURCE_RANK_STAT_CHOICES = ("count", "size")
LINK_TYPE_LABELS = {
    100: "PT",
    110: "磁力",
    200: "云分享",
    300: "云下载",
}
DOWNLOADABLE_LINK_TYPES = {200, 300}


class CloudResourceManager:
    """Business-level helpers for cloud resource search and download submission."""

    def __init__(self, client: MSClient):
        self.client = client

    def search(
        self,
        *,
        keyword: Optional[str] = None,
        tmdb_id: Optional[int] = None,
        media_type: Optional[str] = None,
        season: Optional[int] = None,
        episode: Optional[int] = None,
        begin_episode: Optional[int] = None,
        end_episode: Optional[int] = None,
        creator_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> dict[str, Any]:
        keyword = (keyword or "").strip()
        media_type = (media_type or "").strip()
        self._validate_search(keyword=keyword, tmdb_id=tmdb_id, media_type=media_type, creator_id=creator_id)

        body: dict[str, Any] = {"searchCloudStorage": True}
        if keyword:
            body["keyword"] = keyword
        if tmdb_id is not None:
            body["tmdbId"] = tmdb_id
        if media_type:
            body["mediaType"] = media_type
        if season is not None:
            body["season"] = season
        if episode is not None:
            body["episode"] = episode
        if begin_episode is not None:
            body["beginEpisode"] = begin_episode
        if end_episode is not None:
            body["endEpisode"] = end_episode
        if creator_id is not None:
            body["creatorId"] = creator_id

        response = self.client.request(
            "POST",
            "/api/v1/siteResource/page",
            params={
                "pageNum": str(page),
                "pageSize": str(page_size),
            },
            json_body=body,
        )
        if not response.ok:
            message = response.message or f"Cloud resource search failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, dict):
            raise ValueError("Cloud resource search returned an unexpected response payload")
        return self._normalize_page(response.data)

    def submit_download(self, request: dict[str, Any], *, dir_path: Optional[str] = None) -> dict[str, Any]:
        payload = self._build_download_payload(request, dir_path=dir_path)
        response = self.client.request("POST", "/api/v1/cloudStorageFs/upload", json_body=payload)
        if not response.ok:
            message = response.message or f"Cloud resource download failed with HTTP {response.status_code}"
            raise ValueError(message)

        return {
            "status": "submitted",
            "type": payload["type"],
            "dir": payload.get("dir", ""),
            "count": len(payload["contents"]),
            "response": response.data,
            "message": response.message,
        }

    def rank(self, *, range_type: str = "today", stat_type: str = "count", refresh: bool = False) -> dict[str, Any]:
        range_type = (range_type or "").strip().lower()
        stat_type = (stat_type or "").strip().lower()
        self._validate_rank(range_type=range_type, stat_type=stat_type)

        params = {
            "rangeType": range_type,
            "statType": stat_type,
            "refresh": "true" if refresh else "false",
        }
        list_response = self.client.request("GET", "/api/v1/system/hashReportStatistic", params=params)
        if not list_response.ok:
            message = list_response.message or f"Cloud resource rank failed with HTTP {list_response.status_code}"
            raise ValueError(message)
        if not isinstance(list_response.data, list):
            raise ValueError("Cloud resource rank returned an unexpected response payload")

        mine_response = self.client.request("GET", "/api/v1/system/hashReportStatisticMine", params=params)
        if not mine_response.ok:
            message = mine_response.message or f"Cloud resource rank mine failed with HTTP {mine_response.status_code}"
            raise ValueError(message)
        if mine_response.data is not None and not isinstance(mine_response.data, dict):
            raise ValueError("Cloud resource rank mine returned an unexpected response payload")

        items = [self._normalize_rank_item(item, rank=index + 1, stat_type=stat_type) for index, item in enumerate(list_response.data)]
        return {
            "range_type": range_type,
            "stat_type": stat_type,
            "items": items,
            "mine": self._normalize_rank_mine(mine_response.data or {}, stat_type=stat_type),
        }

    def _validate_search(
        self,
        *,
        keyword: str,
        tmdb_id: Optional[int],
        media_type: str,
        creator_id: Optional[int],
    ) -> None:
        if tmdb_id is not None and not media_type:
            raise ValueError("TMDB cloud resource search requires --type")
        if media_type and media_type not in MEDIA_TYPE_CHOICES:
            raise ValueError("--type must be movie or tv")
        if not keyword and creator_id is None and not (tmdb_id is not None and media_type):
            raise ValueError("Cloud resource search requires --keyword, --creator-id, or --tmdb-id with --type")

    def _validate_rank(self, *, range_type: str, stat_type: str) -> None:
        if range_type not in CLOUD_RESOURCE_RANK_RANGE_CHOICES:
            raise ValueError("--range must be today, week, or all")
        if stat_type not in CLOUD_RESOURCE_RANK_STAT_CHOICES:
            raise ValueError("--stat must be count or size")

    def _normalize_page(self, data: dict[str, Any]) -> dict[str, Any]:
        items = data.get("list") or []
        if not isinstance(items, list):
            items = []
        return {
            "total": data.get("total", 0),
            "pageNum": data.get("pageNum", 1),
            "pageSize": data.get("pageSize", len(items)),
            "list": [self._normalize_item(item) for item in items],
        }

    def _normalize_item(self, item: Any) -> dict[str, Any]:
        if not isinstance(item, dict):
            item = {}

        link_type = self._to_int(item.get("linkType"))
        cs_hash_id = self._to_int(item.get("csHashId"))
        enclosure = str(item.get("enclosure", "") or "")
        creator_name = str(item.get("userName", "") or "")
        creator_id = self._to_int(item.get("userId"))
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        tmdb_media = item.get("tmdbMedia") if isinstance(item.get("tmdbMedia"), dict) else {}

        normalized = {
            "id": self._to_int(item.get("id")),
            "title": str(item.get("title", "") or ""),
            "description": str(item.get("description", "") or ""),
            "size": self._to_int(item.get("size")) or 0,
            "pub_date": self._to_int(item.get("pubDate")),
            "media_type": str(item.get("mediaType", "") or ""),
            "tmdb_id": self._to_int(item.get("tmdbId")),
            "tmdb": {
                "id": self._to_int(tmdb_media.get("id")),
                "title": str(tmdb_media.get("title", "") or ""),
                "year": self._to_int(tmdb_media.get("year")),
            },
            "driver": {
                "name": str(item.get("driverName", "") or ""),
                "link_driver_name": str(item.get("linkDriverName", "") or ""),
            },
            "link": {
                "type": link_type,
                "type_name": LINK_TYPE_LABELS.get(link_type, "" if link_type is None else str(link_type)),
                "url": enclosure,
            },
            "creator": {
                "id": creator_id,
                "name": creator_name,
            },
            "metadata": {
                "resource_pix": str(metadata.get("resourcePix", "") or ""),
                "video_encode": str(metadata.get("videoEncode", "") or ""),
                "season_episode": str(metadata.get("seasonEpisode", "") or ""),
            },
            "cs_hash_id": cs_hash_id,
            "archived": bool(item.get("archived")),
            "downloadable": bool(enclosure and link_type in DOWNLOADABLE_LINK_TYPES),
            "download_request": None,
        }
        normalized["download_request"] = self._build_download_request(normalized)
        return normalized

    def _build_download_request(self, item: dict[str, Any]) -> Optional[dict[str, Any]]:
        link = item.get("link") if isinstance(item.get("link"), dict) else {}
        link_type = link.get("type")
        url = str(link.get("url", "") or "")
        if not url or link_type not in DOWNLOADABLE_LINK_TYPES:
            return None

        request: dict[str, Any] = {
            "type": link_type,
            "contents": [url],
        }
        cs_hash_id = item.get("cs_hash_id")
        if cs_hash_id is not None:
            request["csHashId"] = cs_hash_id
        creator = item.get("creator") if isinstance(item.get("creator"), dict) else {}
        creator_name = str(creator.get("name", "") or "")
        if creator_name:
            request["csCreator"] = creator_name
        return request

    def _build_download_payload(self, request: dict[str, Any], *, dir_path: Optional[str]) -> dict[str, Any]:
        if not isinstance(request, dict):
            raise ValueError("--request must be a JSON object")

        upload_type = self._to_int(request.get("type"))
        if upload_type not in DOWNLOADABLE_LINK_TYPES:
            raise ValueError("--request.type must be 200 or 300")

        contents = request.get("contents")
        if not isinstance(contents, list) or not contents:
            raise ValueError("--request.contents must be a non-empty array")

        clean_contents = [str(item).strip() for item in contents if str(item).strip()]
        if not clean_contents:
            raise ValueError("--request.contents must contain at least one non-empty item")

        payload: dict[str, Any] = {
            "type": upload_type,
            "contents": clean_contents,
        }
        if dir_path:
            payload["dir"] = dir_path

        cs_hash_id = self._to_int(request.get("csHashId"))
        if cs_hash_id is not None:
            payload["csHashId"] = cs_hash_id
        cs_creator = str(request.get("csCreator", "") or "").strip()
        if cs_creator:
            payload["csCreator"] = cs_creator
        return payload

    def _normalize_rank_item(self, item: Any, *, rank: int, stat_type: str) -> dict[str, Any]:
        if not isinstance(item, dict):
            item = {}
        creator_id = self._to_int(item.get("creator_id", item.get("creatorId"))) or 0
        count = self._to_int(item.get("count")) or 0
        size = self._to_int(item.get("size")) or 0
        value = size if stat_type == "size" else count
        value_text = _format_bytes(size) if stat_type == "size" else f"{count} 次"
        return {
            "rank": rank,
            "creator_id": creator_id,
            "creator": str(item.get("creator", "") or "未知用户"),
            "count": count,
            "size": size,
            "size_text": _format_bytes(size),
            "value": value,
            "value_text": value_text,
        }

    def _normalize_rank_mine(self, item: dict[str, Any], *, stat_type: str) -> dict[str, Any]:
        creator_id = self._to_int(item.get("creator_id", item.get("creatorId"))) or 0
        count = self._to_int(item.get("count")) or 0
        size = self._to_int(item.get("size")) or 0
        rank = self._to_int(item.get("rank")) or 0
        surpass_percent = self._to_float(item.get("surpass_percent", item.get("surpassPercent"))) or 0.0
        surpass_percent = min(100.0, max(0.0, surpass_percent))
        value = size if stat_type == "size" else count
        value_text = _format_bytes(size) if stat_type == "size" else f"{count} 次"
        return {
            "creator_id": creator_id,
            "creator": str(item.get("creator", "") or "我"),
            "count": count,
            "size": size,
            "size_text": _format_bytes(size),
            "rank": rank,
            "surpass_percent": surpass_percent,
            "value": value,
            "value_text": value_text,
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
