"""Media-health business helpers for ms."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from .client import MSClient


MEDIA_HEALTH_ISSUE_TYPE_CHOICES = ("missing", "unmatched", "upgrade", "subtitle_missing")
MEDIA_HEALTH_STATUS_CHOICES = ("active", "open", "processing", "ignored", "resolved")
MEDIA_HEALTH_PREVIEW_ACTION_LABELS = {
    "create": "新建订阅",
    "merge": "并入现有订阅",
    "research": "现有订阅重新搜索",
    "noop": "无需处理",
}


class MediaHealthManager:
    """Business-level helpers for media-health-related commands."""

    def __init__(self, client: MSClient):
        self.client = client

    def page(
        self,
        *,
        issue_type: Optional[str] = None,
        status: Optional[str] = None,
        title: Optional[str] = None,
        media_server_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        issue_type = (issue_type or "").strip().lower()
        if issue_type and issue_type not in MEDIA_HEALTH_ISSUE_TYPE_CHOICES:
            raise ValueError("--type must be one of: " + ", ".join(MEDIA_HEALTH_ISSUE_TYPE_CHOICES))
        status = (status or "").strip().lower()
        if status and status not in MEDIA_HEALTH_STATUS_CHOICES:
            raise ValueError("--status must be one of: " + ", ".join(MEDIA_HEALTH_STATUS_CHOICES))

        params: dict[str, str] = {
            "pageNum": str(page),
            "pageSize": str(page_size),
        }
        if issue_type:
            params["issueType"] = issue_type
        if status:
            params["status"] = status
        title = (title or "").strip()
        if title:
            params["title"] = title
        if media_server_id is not None:
            params["mediaServerId"] = str(media_server_id)

        response = self.client.request("GET", "/api/v1/mediaHealth/page", params=params)
        if not response.ok:
            message = response.message or f"Media health page failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, dict):
            raise ValueError("Media health page returned an unexpected response payload")
        return self._normalize_page(response.data)

    def detail(self, issue_key: str) -> dict[str, Any]:
        response = self.client.request(
            "GET",
            "/api/v1/mediaHealth/detail",
            params={"issueKey": self._require_issue_key(issue_key)},
        )
        if not response.ok:
            message = response.message or f"Media health detail failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, dict):
            raise ValueError("Media health detail returned an unexpected response payload")
        return self._normalize_issue(response.data)

    def subscribe_missing_preview(self, issue_key: str) -> dict[str, Any]:
        return self._missing_action("subscribeMissingPreview", issue_key)

    def subscribe_missing(self, issue_key: str) -> dict[str, Any]:
        return self._missing_action("subscribeMissing", issue_key)

    def ignore(self, issue_key: str, *, note: Optional[str] = None) -> dict[str, Any]:
        body: dict[str, Any] = {"issueKey": self._require_issue_key(issue_key)}
        note = (note or "").strip()
        if note:
            body["note"] = note
        response = self.client.request("POST", "/api/v1/mediaHealth/ignore", json_body=body)
        if not response.ok:
            message = response.message or f"Media health ignore failed with HTTP {response.status_code}"
            raise ValueError(message)
        return {"status": "submitted", "action": "ignore", "issue_key": body["issueKey"], "message": response.message}

    def restore(self, issue_key: str) -> dict[str, Any]:
        body = {"issueKey": self._require_issue_key(issue_key)}
        response = self.client.request("POST", "/api/v1/mediaHealth/restore", json_body=body)
        if not response.ok:
            message = response.message or f"Media health restore failed with HTTP {response.status_code}"
            raise ValueError(message)
        return {"status": "submitted", "action": "restore", "issue_key": body["issueKey"], "message": response.message}

    def _missing_action(self, action: str, issue_key: str) -> dict[str, Any]:
        body = {"issueKey": self._require_issue_key(issue_key)}
        response = self.client.request("POST", f"/api/v1/mediaHealth/{action}", json_body=body)
        if not response.ok:
            message = response.message or f"Media health {action} failed with HTTP {response.status_code}"
            raise ValueError(message)
        if action == "subscribeMissing":
            return {"status": "submitted", "action": action, "issue_key": body["issueKey"], "message": response.message}
        if not isinstance(response.data, dict):
            raise ValueError("Media health preview returned an unexpected response payload")
        return self._normalize_preview(response.data)

    def _require_issue_key(self, issue_key: str) -> str:
        issue_key = (issue_key or "").strip()
        if not issue_key:
            raise ValueError("--issue-key is required")
        return issue_key

    def _normalize_page(self, data: dict[str, Any]) -> dict[str, Any]:
        items = data.get("list") or []
        if not isinstance(items, list):
            items = []
        summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
        return {
            "summary": self._normalize_summary(summary),
            "total": self._to_int(data.get("total")) or 0,
            "pageNum": self._to_int(data.get("pageNum")) or 1,
            "pageSize": self._to_int(data.get("pageSize")) or len(items),
            "list": [self._normalize_issue(item) for item in items],
        }

    def _normalize_summary(self, summary: dict[str, Any]) -> dict[str, Any]:
        return {
            "missing": self._to_int(summary.get("missing")) or 0,
            "processing": self._to_int(summary.get("processing")) or 0,
            "unmatched": self._to_int(summary.get("unmatched")) or 0,
            "upgrade": self._to_int(summary.get("upgrade")) or 0,
            "ignored": self._to_int(summary.get("ignored")) or 0,
            "subtitle_missing": self._to_int(summary.get("subtitleMissing")) or 0,
        }

    def _normalize_issue(self, item: Any) -> dict[str, Any]:
        if not isinstance(item, dict):
            item = {}
        seasons_raw = item.get("seasons") if isinstance(item.get("seasons"), list) else []
        return {
            "issue_key": str(item.get("issueKey", "") or ""),
            "issue_type": str(item.get("issueType", "") or ""),
            "status": str(item.get("status", "") or ""),
            "title": str(item.get("title", "") or ""),
            "year": self._to_int(item.get("year")),
            "media_type": str(item.get("mediaType", "") or ""),
            "tmdb_id": self._to_int(item.get("tmdbId")),
            "media_server_id": self._to_int(item.get("mediaServerId")),
            "library_name": str(item.get("libraryName", "") or ""),
            "path": str(item.get("path", "") or ""),
            "seasons": [self._normalize_season(season) for season in seasons_raw],
            "subscribe_id": self._to_int(item.get("subscribeId")),
            "current_quality": str(item.get("currentQuality", "") or ""),
            "target_quality": str(item.get("targetQuality", "") or ""),
            "risk_tips": [str(tip) for tip in item.get("riskTips") or [] if str(tip).strip()],
            "actions": [str(action) for action in item.get("actions") or [] if str(action).strip()],
            "note": str(item.get("note", "") or ""),
            "updated_at": self._to_int(item.get("updatedAt")),
            "updated_at_text": _format_timestamp(item.get("updatedAt")),
        }

    def _normalize_season(self, season: Any) -> dict[str, Any]:
        if not isinstance(season, dict):
            season = {}
        missing = [self._to_int(ep) for ep in season.get("missingEpisodes") or [] if self._to_int(ep) is not None]
        return {
            "season": self._to_int(season.get("season")) or 0,
            "total_episodes": self._to_int(season.get("totalEpisodes")) or 0,
            "missing_episodes": missing,
            "existing_episodes": [
                self._to_int(ep) for ep in season.get("existingEpisodes") or [] if self._to_int(ep) is not None
            ],
            "missing_text": _format_episode_ranges(missing),
        }

    def _normalize_preview(self, data: dict[str, Any]) -> dict[str, Any]:
        action = str(data.get("action", "") or "")
        episodes = [self._to_int(ep) for ep in data.get("episodes") or [] if self._to_int(ep) is not None]
        return {
            "action": action,
            "action_text": MEDIA_HEALTH_PREVIEW_ACTION_LABELS.get(action, action),
            "season": self._to_int(data.get("season")) or 0,
            "episodes": episodes,
            "episodes_text": _format_episode_ranges(episodes),
            "subscribe_id": self._to_int(data.get("subscribeId")),
            "already_in_library": [
                self._to_int(ep) for ep in data.get("alreadyInLibrary") or [] if self._to_int(ep) is not None
            ],
            "already_downloaded": [
                self._to_int(ep) for ep in data.get("alreadyDownloaded") or [] if self._to_int(ep) is not None
            ],
        }

    def _to_int(self, value: Any) -> Optional[int]:
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None


def _format_timestamp(value: Any) -> str:
    timestamp = 0
    try:
        timestamp = int(value or 0)
    except (TypeError, ValueError):
        return ""
    if timestamp <= 0:
        return ""
    if timestamp > 10_000_000_000:
        timestamp = timestamp // 1000
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def _format_episode_ranges(episodes: list[int]) -> str:
    normalized = sorted(set(episodes))
    if not normalized:
        return ""
    ranges: list[str] = []
    start = normalized[0]
    end = normalized[0]
    for current in normalized[1:]:
        if current == end + 1:
            end = current
            continue
        ranges.append(f"E{start}" if start == end else f"E{start}-{end}")
        start = current
        end = current
    ranges.append(f"E{start}" if start == end else f"E{start}-{end}")
    return ", ".join(ranges)
