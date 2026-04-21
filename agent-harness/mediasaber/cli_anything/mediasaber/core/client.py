from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

import requests

from .config import ConfigManager


class APIError(RuntimeError):
    pass


def normalize_base_url(url: str | None) -> str | None:
    if not url:
        return None
    return url.rstrip("/")


@dataclass
class ConnectionConfig:
    url: str | None = None
    token: str | None = None
    api_key: str | None = None
    source_path: str | None = None

    @classmethod
    def from_sources(
        cls,
        *,
        url: str | None = None,
        token: str | None = None,
        api_key: str | None = None,
        source_path: str | None = None,
        profile: str | None = None,
        config_mgr: ConfigManager | None = None,
    ) -> "ConnectionConfig":
        config_mgr = config_mgr or ConfigManager()
        config = config_mgr.load()
        profile_data = config.profiles.get(profile, {}) if profile else {}
        return cls(
            url=normalize_base_url(
                url
                or os.getenv("MSB_URL")
                or profile_data.get("url")
                or config.url
            ),
            token=token or os.getenv("MSB_TOKEN") or profile_data.get("token") or config.token,
            api_key=api_key or os.getenv("MSB_API_KEY") or profile_data.get("api_key") or config.api_key,
            source_path=source_path
            or os.getenv("MSB_SOURCE")
            or profile_data.get("source_path")
            or config.source_path,
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.url)

    @property
    def auth_mode(self) -> str:
        if self.token:
            return "token"
        if self.api_key:
            return "api_key"
        return "none"

    def as_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "token": self.token,
            "api_key": self.api_key,
            "source_path": self.source_path,
            "auth_mode": self.auth_mode,
        }


class MediaSaberClient:
    def __init__(self, conn: ConnectionConfig):
        self.conn = conn
        self.session = requests.Session()

    def _require_url(self) -> str:
        if not self.conn.url:
            raise APIError("server url is not configured, use --url or session set --url")
        return self.conn.url

    def _url(self, path: str) -> str:
        path = path if path.startswith("/") else f"/{path}"
        return urljoin(f"{self._require_url()}/", path.lstrip("/"))

    def _headers(self, public: bool = False, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if not public:
            if self.conn.token:
                headers["Authorization"] = self.conn.token
            elif self.conn.api_key:
                headers["apiKey"] = self.conn.api_key
        if extra:
            headers.update(extra)
        return headers

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: Any | None = None,
        data: Any | None = None,
        headers: dict[str, str] | None = None,
        public: bool = False,
        timeout: int = 30,
    ) -> requests.Response:
        response = self.session.request(
            method=method.upper(),
            url=self._url(path),
            params=params,
            json=json_data,
            data=data,
            headers=self._headers(public=public, extra=headers),
            timeout=timeout,
        )
        response.raise_for_status()
        return response

    def request_envelope(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: Any | None = None,
        data: Any | None = None,
        public: bool = False,
        timeout: int = 30,
    ) -> dict[str, Any]:
        response = self.request(
            method,
            path,
            params=params,
            json_data=json_data,
            data=data,
            public=public,
            timeout=timeout,
        )
        try:
            payload = response.json()
        except ValueError as exc:
            raise APIError(f"non-json response from {path}") from exc
        if not isinstance(payload, dict):
            raise APIError(f"unexpected response shape from {path}")
        code = payload.get("code")
        if code is not None and code != 20000:
            raise APIError(payload.get("message") or f"request failed with code {code}")
        return payload

    def request_data(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: Any | None = None,
        data: Any | None = None,
        public: bool = False,
        timeout: int = 30,
    ) -> Any:
        payload = self.request_envelope(
            method,
            path,
            params=params,
            json_data=json_data,
            data=data,
            public=public,
            timeout=timeout,
        )
        return payload.get("data")

    def ping(self) -> Any:
        return self.request_data("GET", "/api/v1/user/initAdminStatus", public=True)
