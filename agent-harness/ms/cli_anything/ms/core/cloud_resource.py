"""Cloud resource helpers for ms."""

from __future__ import annotations

import uuid
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
# 云资源可下载链路：200 云分享走转存（123_fast_link），300 云下载走离线下载（ed2k）
CLOUD_SHARE_LINK_TYPE = 200
CLOUD_OFFLINE_LINK_TYPE = 300
CLOUD_DOWNLOADABLE_LINK_TYPES = (CLOUD_SHARE_LINK_TYPE, CLOUD_OFFLINE_LINK_TYPE)
MATERIAL_TYPE_BY_LINK_TYPE = {
    CLOUD_SHARE_LINK_TYPE: "123_fast_link",
    CLOUD_OFFLINE_LINK_TYPE: "ed2k",
}
ACTION_BY_LINK_TYPE = {
    CLOUD_SHARE_LINK_TYPE: "share_receive",
    CLOUD_OFFLINE_LINK_TYPE: "offline_download",
}
MATERIAL_TYPE_CHOICES = ("ed2k", "123_fast_link")
ACTION_CHOICES = ("offline_download", "share_receive", "copy_link")
# 站点种子链路：100 PT 走站点下载通道，110 磁力走 BT 直链
SITE_DOWNLOADABLE_LINK_TYPES = (100, 110)
CLOUD_TASK_STATE_CHOICES = ("undone", "done")
CLOUD_TASK_TYPE_CHOICES = ("upload", "download", "shareReceive", "copy")
CLOUD_TASK_STATE_LABELS = {
    0: "等待中",
    1: "处理中",
    2: "已完成",
    3: "失败",
    4: "已取消",
}


CLOUD_RESOURCE_ORDER_BY_CHOICES = ("size", "pubdate")
CLOUD_RESOURCE_ORDER_DIRECTION_CHOICES = ("asc", "desc")


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
        order_by: Optional[str] = None,
        order_direction: Optional[str] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> dict[str, Any]:
        keyword = (keyword or "").strip()
        media_type = (media_type or "").strip()
        self._validate_search(keyword=keyword, tmdb_id=tmdb_id, media_type=media_type, creator_id=creator_id)

        order_by = (order_by or "").strip().lower()
        if order_by and order_by not in CLOUD_RESOURCE_ORDER_BY_CHOICES:
            raise ValueError("--order-by must be size or pubdate")
        order_direction = (order_direction or "").strip().lower()
        if order_direction and order_direction not in CLOUD_RESOURCE_ORDER_DIRECTION_CHOICES:
            raise ValueError("--order-direction must be asc or desc")

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
        if order_by:
            body["orderBy"] = order_by
        if order_direction:
            body["orderDirection"] = order_direction

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
        item = self._build_use_item(request, dir_path=dir_path)
        response = self.client.request("POST", "/api/v1/cloudStorageResource/use", json_body={"items": [item]})
        if not response.ok:
            message = response.message or f"Cloud resource download failed with HTTP {response.status_code}"
            raise ValueError(message)
        if response.data is not None and not isinstance(response.data, list):
            raise ValueError("Cloud resource download returned an unexpected response payload")

        results = response.data if isinstance(response.data, list) else []
        normalized = [self._normalize_use_result(result) for result in results]
        return {
            "status": "submitted",
            "items": normalized,
            "message": response.message,
        }

    def submit_site_download(self, request: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(request, dict):
            raise ValueError("--request must be a JSON object")
        site_id = self._to_int(request.get("siteId"))
        if site_id is None:
            raise ValueError("--request.siteId is required")
        torrent = request.get("torrent")
        if not isinstance(torrent, dict) or not torrent:
            raise ValueError("--request.torrent must be the raw torrent object from search result")

        response = self.client.request(
            "POST",
            "/api/v1/download/siteResource",
            json_body={"siteId": site_id, "torrents": [torrent]},
        )
        if not response.ok:
            message = response.message or f"Site torrent download failed with HTTP {response.status_code}"
            raise ValueError(message)
        return {
            "status": "submitted",
            "site_id": site_id,
            "title": str(torrent.get("title", "") or ""),
            "message": response.message,
        }

    def tasks(
        self,
        *,
        state: str = "undone",
        task_type: str = "download",
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        state = (state or "").strip().lower()
        if state not in CLOUD_TASK_STATE_CHOICES:
            raise ValueError("--state must be undone or done")
        task_type = (task_type or "").strip()
        if task_type not in CLOUD_TASK_TYPE_CHOICES:
            raise ValueError("--task-type must be one of: " + ", ".join(CLOUD_TASK_TYPE_CHOICES))

        params: dict[str, str] = {
            "type": task_type,
            "pageNum": str(page),
            "pageSize": str(page_size),
        }
        keyword = (keyword or "").strip()
        if keyword:
            params["keyword"] = keyword

        response = self.client.request("GET", f"/api/v1/cloudStorageTask/{state}", params=params)
        if not response.ok:
            message = response.message or f"Cloud storage tasks failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, dict):
            raise ValueError("Cloud storage tasks returned an unexpected response payload")
        return self._normalize_task_page(response.data)

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
        creator_name = str(item.get("userName", "") or "")
        creator_id = self._to_int(item.get("userId"))
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        cloud_metadata = metadata.get("cloudResource") if isinstance(metadata.get("cloudResource"), dict) else {}
        capabilities = [str(cap) for cap in cloud_metadata.get("capabilities") or [] if str(cap).strip()]
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
            "downloadable": False,
            "download_request": None,
        }
        if link_type in CLOUD_DOWNLOADABLE_LINK_TYPES:
            normalized["download_request"] = self._build_cloud_download_request(
                link_type=link_type, cs_hash_id=cs_hash_id, capabilities=capabilities
            )
        elif link_type in SITE_DOWNLOADABLE_LINK_TYPES:
            site_id = self._to_int(item.get("siteId"))
            if site_id is not None:
                # 站点种子直下需回传完整原始条目，后端按 LinkType 分流 BT/PT 通道
                normalized["download_request"] = {"siteId": site_id, "torrent": item}
        normalized["downloadable"] = normalized["download_request"] is not None
        return normalized

    def _build_cloud_download_request(
        self, *, link_type: int, cs_hash_id: Optional[int], capabilities: list[str]
    ) -> Optional[dict[str, Any]]:
        if cs_hash_id is None:
            return None
        material_type = MATERIAL_TYPE_BY_LINK_TYPE[link_type]
        # 与前端一致：仅当资源明确声明能力且不含目标方式时拦下，历史数据缺 capabilities 时放行
        if capabilities and material_type not in capabilities:
            return None
        return {
            "csHashId": cs_hash_id,
            "materialType": material_type,
            "action": ACTION_BY_LINK_TYPE[link_type],
        }

    def _build_use_item(self, request: dict[str, Any], *, dir_path: Optional[str]) -> dict[str, Any]:
        if not isinstance(request, dict):
            raise ValueError("--request must be a JSON object")

        cs_hash_id = self._to_int(request.get("csHashId"))
        if cs_hash_id is None:
            raise ValueError("--request.csHashId is required")
        material_type = str(request.get("materialType", "") or "").strip()
        if material_type not in MATERIAL_TYPE_CHOICES:
            raise ValueError("--request.materialType must be ed2k or 123_fast_link")
        action = str(request.get("action", "") or "").strip()
        if action not in ACTION_CHOICES:
            raise ValueError("--request.action must be offline_download, share_receive, or copy_link")

        item: dict[str, Any] = {
            "csHashId": cs_hash_id,
            "operationId": str(uuid.uuid4()),
            "action": action,
            "materialType": material_type,
        }
        if dir_path:
            item["dstDir"] = dir_path
        return item

    def _normalize_use_result(self, result: Any) -> dict[str, Any]:
        if not isinstance(result, dict):
            result = {}
        return {
            "cs_hash_id": self._to_int(result.get("csHashId")),
            "operation_id": str(result.get("operationId", "") or ""),
            "status": str(result.get("status", "") or ""),
            "task_id": str(result.get("taskId", "") or ""),
            "task_type": str(result.get("taskType", "") or ""),
            "message": str(result.get("message", "") or ""),
            "link": str(result.get("link", "") or ""),
        }

    def _normalize_task_page(self, data: dict[str, Any]) -> dict[str, Any]:
        items = data.get("list") or []
        if not isinstance(items, list):
            items = []
        return {
            "total": self._to_int(data.get("total")) or 0,
            "pageNum": self._to_int(data.get("pageNum")) or 1,
            "pageSize": self._to_int(data.get("pageSize")) or len(items),
            "list": [self._normalize_task_item(item) for item in items],
        }

    def _normalize_task_item(self, item: Any) -> dict[str, Any]:
        if not isinstance(item, dict):
            item = {}
        state = self._to_int(item.get("state"))
        task_event = item.get("task_event") if isinstance(item.get("task_event"), dict) else {}
        return {
            "id": str(item.get("id", "") or ""),
            "name": str(item.get("name", "") or ""),
            "state": state,
            "state_text": CLOUD_TASK_STATE_LABELS.get(state, "" if state is None else str(state)),
            "status": str(item.get("status", "") or ""),
            "progress": self._to_float(item.get("progress")) or 0.0,
            "progress_percent": round((self._to_float(item.get("progress")) or 0.0) * 100, 1),
            "speed": self._to_float(item.get("speed")) or 0.0,
            "speed_text": f"{_format_bytes(self._to_float(item.get('speed')) or 0)}/s",
            "total_bytes": self._to_int(item.get("totalBytes")) or 0,
            "total_bytes_text": _format_bytes(item.get("totalBytes")),
            "error": str(item.get("error", "") or ""),
            "file_name": str(task_event.get("source_file", "") or ""),
            "target_path": str(task_event.get("target_file_path", "") or ""),
            "tmdb_title": str((item.get("tmdbMedia") or {}).get("title", "") or "") if isinstance(item.get("tmdbMedia"), dict) else "",
            "start_time": self._to_int(item.get("start_time")),
            "end_time": self._to_int(item.get("end_time")),
        }

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
