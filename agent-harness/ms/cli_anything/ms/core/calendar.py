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
