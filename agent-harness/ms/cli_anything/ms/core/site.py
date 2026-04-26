"""Site-specific business helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from .client import MSClient


SITE_SWITCH_TYPE_CHOICES = {
    "enabled": 100,
    "search": 200,
    "rss": 300,
    "brush": 400,
    "statistic": 500,
    "sign-in": 600,
    "notice": 700,
    "message": 800,
    "proxy": 900,
}
SITE_SIGN_IN_CODE_LABELS = {
    100: "签到成功",
    200: "已签到",
    300: "签到失败",
    400: "未登录",
}


class SiteManager:
    """Business-level helpers for site-related commands."""

    def __init__(self, client: MSClient):
        self.client = client

    def list(self, *, name: Optional[str] = None, enabled: Optional[bool] = None, switch_type: Optional[str] = None) -> dict[str, Any]:
        params: dict[str, str] = {}
        name = (name or "").strip()
        if name:
            params["name"] = name
        if enabled is not None:
            params["enabled"] = "true" if enabled else "false"
        if switch_type:
            if switch_type not in SITE_SWITCH_TYPE_CHOICES:
                raise ValueError("--type must be one of: " + ", ".join(SITE_SWITCH_TYPE_CHOICES))
            params["type"] = str(SITE_SWITCH_TYPE_CHOICES[switch_type])

        response = self.client.request("GET", "/api/v1/site/list", params=params or None)
        if not response.ok:
            message = response.message or f"Site list failed with HTTP {response.status_code}"
            raise ValueError(message)
        if response.data is None:
            return {"total": 0, "items": []}
        if not isinstance(response.data, list):
            raise ValueError("Site list returned an unexpected response payload")

        items = [self._normalize_site(item) for item in response.data]
        return {"total": len(items), "items": items}

    def data_total(self) -> dict[str, Any]:
        response = self.client.request("GET", "/api/v1/siteData/total")
        if not response.ok:
            message = response.message or f"Site data total failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, dict):
            raise ValueError("Site data total returned an unexpected response payload")
        return self._normalize_total(response.data)

    def data_latest(
        self,
        *,
        site_id: Optional[int] = None,
        site_name: Optional[str] = None,
        order_by: Optional[str] = None,
        order_direction: Optional[str] = None,
    ) -> dict[str, Any]:
        params: dict[str, str] = {}
        if site_id is not None:
            params["siteId"] = str(site_id)
        site_name = (site_name or "").strip()
        if site_name:
            params["siteName"] = site_name
        order_by = (order_by or "").strip()
        if order_by:
            params["orderBy"] = order_by
        order_direction = (order_direction or "").strip()
        if order_direction:
            params["orderDirection"] = order_direction

        response = self.client.request("GET", "/api/v1/siteData/latest", params=params or None)
        if not response.ok:
            message = response.message or f"Site data latest failed with HTTP {response.status_code}"
            raise ValueError(message)
        if response.data is None:
            return {"total": 0, "items": []}
        if not isinstance(response.data, list):
            raise ValueError("Site data latest returned an unexpected response payload")

        items = [self._normalize_site_data(item) for item in response.data]
        return {"total": len(items), "items": items}

    def sign_in_history(self, *, site_name: Optional[str] = None, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        params = {
            "pageNum": str(page),
            "pageSize": str(page_size),
        }
        site_name = (site_name or "").strip()
        if site_name:
            params["siteName"] = site_name

        response = self.client.request("GET", "/api/v1/siteSignIn/page", params=params)
        if not response.ok:
            message = response.message or f"Site sign-in history failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, dict):
            raise ValueError("Site sign-in history returned an unexpected response payload")
        return self._normalize_sign_in_page(response.data)

    def sign_in(self, *, site_ids: Optional[list[int]] = None) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if site_ids:
            body["ids"] = site_ids

        response = self.client.request("POST", "/api/v1/siteSignIn/go", json_body=body)
        if not response.ok:
            message = response.message or f"Site sign-in failed with HTTP {response.status_code}"
            raise ValueError(message)
        return {
            "status": "submitted",
            "site_ids": site_ids or [],
            "all_enabled": not bool(site_ids),
            "response": response.data,
            "message": response.message,
        }

    def _normalize_site(self, item: Any) -> dict[str, Any]:
        if not isinstance(item, dict):
            item = {}
        return {
            "id": _to_int(item.get("id")),
            "code": str(item.get("code", "") or ""),
            "name": str(item.get("name", "") or ""),
            "enabled": bool(item.get("enabled")),
            "priority": _to_int(item.get("priority")) or 0,
            "user_id": str(item.get("userId", "") or ""),
            "domain": str(item.get("domainDisplay") or item.get("domain") or ""),
            "api": str(item.get("apiDisplay") or item.get("api") or ""),
            "switches": {
                "rss": bool(item.get("rss")),
                "brush": bool(item.get("brush")),
                "statistic": bool(item.get("statistic")),
                "search": bool(item.get("search")),
                "sign_in": bool(item.get("signIn")),
                "notice": bool(item.get("notice")),
                "message": bool(item.get("message")),
                "proxy": bool(item.get("proxy")),
            },
            "created_at": _to_int(item.get("createdAt")),
            "created_at_text": _format_timestamp(item.get("createdAt")),
            "updated_at": _to_int(item.get("updatedAt")),
            "updated_at_text": _format_timestamp(item.get("updatedAt")),
        }

    def _normalize_total(self, item: dict[str, Any]) -> dict[str, Any]:
        uploaded = _to_int(item.get("uploaded")) or 0
        downloaded = _to_int(item.get("downloaded")) or 0
        seeding_size = _to_int(item.get("seedingSize")) or 0
        return {
            "uploaded": uploaded,
            "uploaded_text": _format_bytes(uploaded),
            "downloaded": downloaded,
            "downloaded_text": _format_bytes(downloaded),
            "bonus": _to_float(item.get("bonus")) or 0.0,
            "seeding_count": _to_int(item.get("seedingCount")) or 0,
            "seeding_size": seeding_size,
            "seeding_size_text": _format_bytes(seeding_size),
        }

    def _normalize_site_data(self, item: Any) -> dict[str, Any]:
        if not isinstance(item, dict):
            item = {}
        uploaded = _to_int(item.get("uploaded")) or 0
        downloaded = _to_int(item.get("downloaded")) or 0
        seeding_size = _to_int(item.get("seedingSize")) or 0
        today_uploaded = _to_int(item.get("todayUploaded")) or 0
        today_downloaded = _to_int(item.get("todayDownloaded")) or 0
        return {
            "id": _to_int(item.get("id")),
            "site_id": _to_int(item.get("siteId")),
            "site_code": str(item.get("siteCode", "") or ""),
            "site_name": str(item.get("siteName", "") or ""),
            "domain": str(item.get("siteDomainDisplay", "") or ""),
            "api": str(item.get("siteApiDisplay", "") or ""),
            "is_login": bool(item.get("isLogin")),
            "signed_in": bool(item.get("signedIn")),
            "user_id": str(item.get("userId", "") or ""),
            "user_name": str(item.get("userName", "") or ""),
            "ratio": _to_float(item.get("ratio")) or 0.0,
            "uploaded": uploaded,
            "uploaded_text": _format_bytes(uploaded),
            "downloaded": downloaded,
            "downloaded_text": _format_bytes(downloaded),
            "bonus": _to_float(item.get("bonus")) or 0.0,
            "level": str(item.get("level", "") or ""),
            "seeding_count": _to_int(item.get("seedingCount")) or 0,
            "seeding_size": seeding_size,
            "seeding_size_text": _format_bytes(seeding_size),
            "today_uploaded": today_uploaded,
            "today_uploaded_text": _format_bytes(today_uploaded),
            "today_downloaded": today_downloaded,
            "today_downloaded_text": _format_bytes(today_downloaded),
            "statistic_date": str(item.get("statisticDate", "") or ""),
            "download_count": _to_int(item.get("downloadCount")) or 0,
            "created_at": _to_int(item.get("createdAt")),
            "created_at_text": _format_timestamp(item.get("createdAt")),
            "updated_at": _to_int(item.get("updatedAt")),
            "updated_at_text": _format_timestamp(item.get("updatedAt")),
        }

    def _normalize_sign_in_page(self, data: dict[str, Any]) -> dict[str, Any]:
        items = data.get("list") or []
        if not isinstance(items, list):
            items = []
        return {
            "total": _to_int(data.get("total")) or 0,
            "pageNum": _to_int(data.get("pageNum")) or 1,
            "pageSize": _to_int(data.get("pageSize")) or len(items),
            "list": [self._normalize_sign_in_item(item) for item in items],
        }

    def _normalize_sign_in_item(self, item: Any) -> dict[str, Any]:
        if not isinstance(item, dict):
            item = {}
        code = _to_int(item.get("code"))
        return {
            "id": _to_int(item.get("id")),
            "site_id": _to_int(item.get("siteId")),
            "site_code": str(item.get("siteCode", "") or ""),
            "site_name": str(item.get("siteName", "") or ""),
            "code": code,
            "code_text": SITE_SIGN_IN_CODE_LABELS.get(code, "" if code is None else str(code)),
            "message": str(item.get("content") or item.get("message") or ""),
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
