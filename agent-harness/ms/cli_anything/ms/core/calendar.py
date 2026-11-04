"""Calendar business helpers for ms."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

from .client import MSClient


class CalendarManager:
    """Business-level helpers for calendar-related commands."""

    def __init__(self, client: MSClient):
        self.client = client

    def list(
        self,
        *,
        subscribe_id: Optional[int] = None,
        days: int = 7,
        from_date: Optional[str] = None,
    ) -> dict[str, Any]:
        if days < 1:
            raise ValueError("--days must be at least 1")

        if from_date:
            try:
                start = datetime.strptime(from_date.strip(), "%Y-%m-%d")
            except ValueError:
                raise ValueError("--from must be YYYY-MM-DD")
        else:
            start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=days)

        params: dict[str, str] = {
            "startTime": str(int(start.timestamp())),
            "endTime": str(int(end.timestamp())),
        }
        if subscribe_id is not None:
            params["subscribeId"] = str(subscribe_id)

        response = self.client.request("GET", "/api/v1/subscribeCalendar/list", params=params)
        if not response.ok:
            message = response.message or f"Calendar list failed with HTTP {response.status_code}"
            raise ValueError(message)
        if response.data is None:
            return {"start": start.strftime("%Y-%m-%d"), "days": days, "days_list": [], "total": 0}
        if not isinstance(response.data, list):
            raise ValueError("Calendar list returned an unexpected response payload")

        items = [self._normalize_item(item) for item in response.data]
        return {
            "start": start.strftime("%Y-%m-%d"),
            "days": days,
            "total": len(items),
            "days_list": self._group_by_day(items),
        }

    def ical_urls(self) -> dict[str, Any]:
        response = self.client.request("GET", "/api/v1/subscribeCalendar/icalUrls")
        if not response.ok:
            message = response.message or f"Calendar ical urls failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, dict):
            raise ValueError("Calendar ical urls returned an unexpected response payload")
        items = response.data.get("items") or []
        if not isinstance(items, list):
            items = []
        return {
            "items": [
                {
                    "title": str(item.get("title", "") or ""),
                    "ical_url": str(item.get("icalUrl", "") or ""),
                }
                for item in items
                if isinstance(item, dict)
            ],
            "empty_reason": str(response.data.get("emptyReason", "") or ""),
        }

    def airing_media_types(self) -> list[dict[str, Any]]:
        """获取全平台播出日历的媒体类型选项。"""
        response = self.client.request("GET", "/api/v1/calendar/mediaTypes")
        if not response.ok:
            message = response.message or f"Calendar media types failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, list):
            raise ValueError("Calendar media types returned an unexpected response payload")
        return response.data

    def airing_platforms(self, media_type: str) -> list[dict[str, Any]]:
        """获取全平台播出日历的平台选项。"""
        media_type = self._require_media_type(media_type)
        response = self.client.request("GET", "/api/v1/calendar/platforms", params={"mediaType": media_type})
        if not response.ok:
            message = response.message or f"Calendar platforms failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, list):
            raise ValueError("Calendar platforms returned an unexpected response payload")
        return response.data

    def airing_days(
        self,
        *,
        media_type: str,
        platform: str,
        from_date: Optional[str] = None,
        days: int = 14,
    ) -> dict[str, Any]:
        """查询全平台播出日历（按天的发布数量）。"""
        media_type = self._require_media_type(media_type)
        platform = self._require_platform(platform)
        if days < 1:
            raise ValueError("--days must be at least 1")

        if from_date:
            try:
                start = datetime.strptime(from_date.strip(), "%Y-%m-%d")
            except ValueError:
                raise ValueError("--from must be YYYY-MM-DD")
        else:
            start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=days)

        response = self.client.request(
            "GET",
            "/api/v1/calendar/calendar",
            params={
                "mediaType": media_type,
                "platform": platform,
                "beginDate": start.strftime("%Y-%m-%d"),
                "endDate": end.strftime("%Y-%m-%d"),
            },
        )
        if not response.ok:
            message = response.message or f"Calendar airing days failed with HTTP {response.status_code}"
            raise ValueError(message)
        if response.data is None:
            return {"start": start.strftime("%Y-%m-%d"), "days": days, "items": []}
        if not isinstance(response.data, list):
            raise ValueError("Calendar airing days returned an unexpected response payload")

        items = []
        for item in response.data:
            if not isinstance(item, dict):
                continue
            items.append(
                {
                    "release_date": str(item.get("releaseDate", "") or ""),
                    "release_count": item.get("releaseCount") or 0,
                    "selected": bool(item.get("selected")),
                }
            )
        return {"start": start.strftime("%Y-%m-%d"), "days": days, "items": items}

    def airing_shows(self, *, media_type: str, platform: str, show_date: str) -> dict[str, Any]:
        """查询指定日期的全平台播出剧目。"""
        media_type = self._require_media_type(media_type)
        platform = self._require_platform(platform)
        try:
            datetime.strptime(show_date.strip(), "%Y-%m-%d")
        except ValueError:
            raise ValueError("--date must be YYYY-MM-DD")

        response = self.client.request(
            "GET",
            "/api/v1/calendar/showPerDayList",
            params={
                "mediaType": media_type,
                "platform": platform,
                "showDate": show_date.strip(),
            },
        )
        if not response.ok:
            message = response.message or f"Calendar airing shows failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, dict):
            raise ValueError("Calendar airing shows returned an unexpected response payload")

        days_raw = response.data.get("showPerDayList") or []
        if not isinstance(days_raw, list):
            days_raw = []
        days = []
        for day in days_raw:
            if not isinstance(day, dict):
                continue
            media_list = day.get("mediaList") if isinstance(day.get("mediaList"), list) else []
            days.append(
                {
                    "release_date": str(day.get("releaseDate", "") or ""),
                    "scheduled": bool(day.get("scheduled")),
                    "items": [self._normalize_show_item(item) for item in media_list if isinstance(item, dict)],
                }
            )
        return {
            "prev_date": str(response.data.get("prevQueryShowDate", "") or ""),
            "next_date": str(response.data.get("nextQueryShowDate", "") or ""),
            "days": days,
        }

    def _normalize_show_item(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item.get("id"),
            "title": str(item.get("title", "") or ""),
            "subtitle": str(item.get("subtitle", "") or ""),
            "media_type": str(item.get("type", "") or ""),
            "year": item.get("year"),
            "vote": item.get("vote"),
            "poster": str(item.get("poster", "") or ""),
            "overview": str(item.get("overview", "") or ""),
        }

    def _require_media_type(self, media_type: str) -> str:
        media_type = (media_type or "").strip().lower()
        if not media_type:
            raise ValueError("--media-type is required")
        return media_type

    def _require_platform(self, platform: str) -> str:
        platform = (platform or "").strip()
        if not platform:
            raise ValueError("--platform is required")
        return platform

    def _normalize_item(self, item: Any) -> dict[str, Any]:
        if not isinstance(item, dict):
            item = {}
        air_time = item.get("airTime")
        air_time_int = 0
        try:
            air_time_int = int(air_time or 0)
        except (TypeError, ValueError):
            air_time_int = 0
        if air_time_int > 10_000_000_000:
            air_time_int = air_time_int // 1000
        air_dt = datetime.fromtimestamp(air_time_int) if air_time_int > 0 else None
        return {
            "subscribe_id": item.get("subscribeId"),
            "tmdb_id": item.get("tmdbId"),
            "name": str(item.get("name", "") or ""),
            "type": str(item.get("type", "") or ""),
            "year": item.get("year"),
            "season": item.get("season") or 0,
            "episode": item.get("episode") or 0,
            "air_time": air_time_int or None,
            "air_time_text": air_dt.strftime("%Y-%m-%d %H:%M") if air_dt else "",
            "air_date": air_dt.strftime("%Y-%m-%d") if air_dt else "",
            "poster": str(item.get("poster", "") or ""),
            "overview": str(item.get("overview", "") or ""),
        }

    def _group_by_day(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for item in items:
            grouped.setdefault(item["air_date"] or "未知日期", []).append(item)
        return [{"date": date, "items": entries} for date, entries in grouped.items()]
