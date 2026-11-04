"""Subscribe-specific business helpers."""

from __future__ import annotations

from typing import Any, Optional

from .client import MSClient


MEDIA_TYPE_CHOICES = ("movie", "tv")


class SubscribeManager:
    """Business-level helpers for subscribe-related commands."""

    def __init__(self, client: MSClient):
        self.client = client

    def page(self, media_type: str, page: int, page_size: int) -> dict[str, Any]:
        response = self.client.request(
            "GET",
            "/api/v1/subscribe/page",
            params={
                "type": media_type,
                "pageNum": str(page),
                "pageSize": str(page_size),
            },
        )
        if not response.ok:
            message = response.message or f"Subscribe page failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, dict):
            raise ValueError("Subscribe page returned an unexpected response payload")
        return response.data

    def detail(self, subscribe_id: int) -> dict[str, Any]:
        response = self.client.request("GET", f"/api/v1/subscribe/detail/{subscribe_id}")
        if not response.ok:
            message = response.message or f"Subscribe detail failed with HTTP {response.status_code}"
            raise ValueError(message)
        if not isinstance(response.data, dict):
            raise ValueError("Subscribe detail returned an unexpected response payload")
        return response.data

    def pause(self, subscribe_id: int) -> dict[str, Any]:
        return self._operate("pause", subscribe_id)

    def resume(self, subscribe_id: int) -> dict[str, Any]:
        return self._operate("resume", subscribe_id)

    def delete(self, subscribe_id: int) -> dict[str, Any]:
        subscribe_id = self._require_id(subscribe_id)
        response = self.client.request("DELETE", f"/api/v1/subscribe/delete/{subscribe_id}")
        if not response.ok:
            message = response.message or f"Subscribe delete failed with HTTP {response.status_code}"
            raise ValueError(message)
        return {"status": "submitted", "action": "delete", "subscribe_id": subscribe_id, "message": response.message}

    def refresh(self, subscribe_id: int) -> dict[str, Any]:
        return self._operate("refresh", subscribe_id)

    def refresh_all(self, media_type: str) -> dict[str, Any]:
        media_type = (media_type or "").strip().lower()
        if media_type not in MEDIA_TYPE_CHOICES:
            raise ValueError("--type must be movie or tv")
        response = self.client.request("POST", "/api/v1/subscribe/refreshAll", json_body={"mediaType": media_type})
        if not response.ok:
            message = response.message or f"Subscribe refresh all failed with HTTP {response.status_code}"
            raise ValueError(message)
        return {"status": "submitted", "action": "refreshAll", "media_type": media_type, "message": response.message}

    def _operate(self, action: str, subscribe_id: int) -> dict[str, Any]:
        subscribe_id = self._require_id(subscribe_id)
        response = self.client.request("POST", f"/api/v1/subscribe/{action}/{subscribe_id}")
        if not response.ok:
            message = response.message or f"Subscribe {action} failed with HTTP {response.status_code}"
            raise ValueError(message)
        return {"status": "submitted", "action": action, "subscribe_id": subscribe_id, "message": response.message}

    def _require_id(self, subscribe_id: int) -> int:
        try:
            subscribe_id = int(subscribe_id)
        except (TypeError, ValueError):
            raise ValueError("--id is required")
        if subscribe_id <= 0:
            raise ValueError("--id is required")
        return subscribe_id

    def add(
        self,
        name: str,
        media_type: str,
        year: int,
        season: int | None = None,
        *,
        tmdb_id: int | None = None,
    ) -> dict[str, Any]:
        # 最小 payload：未显式给出的衍生字段由后端订阅默认配置运行时兜底（跟随默认体系）
        payload: dict[str, Any] = {
            "name": name,
            "type": media_type,
            "year": year,
        }
        if media_type == "tv":
            payload["season"] = season if season is not None else 1
        if tmdb_id is not None:
            payload["tmdbId"] = tmdb_id

        response = self.client.request("POST", "/api/v1/subscribe/save", json_body=payload)
        if not response.ok:
            message = response.message or f"Subscribe add failed with HTTP {response.status_code}"
            raise ValueError(message)

        return {
            "status": "ok",
            "subscribe": payload,
        }
