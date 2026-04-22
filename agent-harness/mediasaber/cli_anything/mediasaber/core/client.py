from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

import requests

from .config import ConfigManager
from ..utils.request_helpers import write_output_file


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
            url=normalize_base_url(url or os.getenv("MSB_URL") or profile_data.get("url") or config.url),
            token=token or os.getenv("MSB_TOKEN") or profile_data.get("token") or config.token,
            api_key=api_key or os.getenv("MSB_API_KEY") or profile_data.get("api_key") or config.api_key,
            source_path=source_path or os.getenv("MSB_SOURCE") or profile_data.get("source_path") or config.source_path,
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
        files: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        public: bool = False,
        timeout: int = 30,
        allow_redirects: bool = True,
        stream: bool = False,
    ) -> requests.Response:
        response = self.session.request(
            method=method.upper(),
            url=self._url(path),
            params=params,
            json=json_data,
            data=data,
            files=files,
            headers=self._headers(public=public, extra=headers),
            timeout=timeout,
            allow_redirects=allow_redirects,
            stream=stream,
        )
        response.raise_for_status()
        return response

    def request_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: Any | None = None,
        data: Any | None = None,
        files: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        public: bool = False,
        timeout: int = 30,
        allow_redirects: bool = True,
        unwrap_envelope: bool = True,
    ) -> Any:
        response = self.request(
            method,
            path,
            params=params,
            json_data=json_data,
            data=data,
            files=files,
            headers=headers,
            public=public,
            timeout=timeout,
            allow_redirects=allow_redirects,
        )
        try:
            payload = response.json()
        except ValueError as exc:
            raise APIError(f"non-json response from {path}") from exc
        if unwrap_envelope and isinstance(payload, dict) and {"code", "message"}.issubset(payload.keys()):
            code = payload.get("code")
            if code is not None and code != 20000:
                raise APIError(payload.get("message") or f"request failed with code {code}")
            return payload.get("data")
        return payload

    def request_text(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: Any | None = None,
        data: Any | None = None,
        files: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        public: bool = False,
        timeout: int = 30,
        allow_redirects: bool = True,
        output_path: str | None = None,
    ) -> Any:
        response = self.request(
            method,
            path,
            params=params,
            json_data=json_data,
            data=data,
            files=files,
            headers=headers,
            public=public,
            timeout=timeout,
            allow_redirects=allow_redirects,
        )
        if output_path:
            meta = write_output_file(output_path, response.content)
            meta["content_type"] = response.headers.get("Content-Type")
            return meta
        return response.text

    def request_content(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: Any | None = None,
        data: Any | None = None,
        files: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        public: bool = False,
        timeout: int = 30,
        allow_redirects: bool = True,
        output_path: str | None = None,
    ) -> Any:
        response = self.request(
            method,
            path,
            params=params,
            json_data=json_data,
            data=data,
            files=files,
            headers=headers,
            public=public,
            timeout=timeout,
            allow_redirects=allow_redirects,
            stream=bool(output_path),
        )
        content = response.content
        if output_path:
            meta = write_output_file(output_path, content)
            meta["content_type"] = response.headers.get("Content-Type")
            return meta
        return {
            "status_code": response.status_code,
            "content_type": response.headers.get("Content-Type"),
            "bytes": len(content),
            "body": response.text if response.text else "",
        }

    def request_redirect(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        public: bool = False,
        timeout: int = 30,
    ) -> dict[str, Any]:
        response = self.request(
            method,
            path,
            params=params,
            headers=headers,
            public=public,
            timeout=timeout,
            allow_redirects=False,
        )
        return {
            "status_code": response.status_code,
            "location": response.headers.get("Location"),
        }

    def request_result(
        self,
        method: str,
        path: str,
        *,
        response_mode: str = "auto",
        unwrap_envelope: bool = True,
        params: dict[str, Any] | None = None,
        json_data: Any | None = None,
        data: Any | None = None,
        files: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        public: bool = False,
        timeout: int = 30,
        output_path: str | None = None,
        allow_redirects: bool = True,
    ) -> Any:
        if response_mode == "json":
            return self.request_json(
                method,
                path,
                params=params,
                json_data=json_data,
                data=data,
                files=files,
                headers=headers,
                public=public,
                timeout=timeout,
                allow_redirects=allow_redirects,
                unwrap_envelope=unwrap_envelope,
            )
        if response_mode == "text":
            return self.request_text(
                method,
                path,
                params=params,
                json_data=json_data,
                data=data,
                files=files,
                headers=headers,
                public=public,
                timeout=timeout,
                allow_redirects=allow_redirects,
                output_path=output_path,
            )
        if response_mode == "content":
            return self.request_content(
                method,
                path,
                params=params,
                json_data=json_data,
                data=data,
                files=files,
                headers=headers,
                public=public,
                timeout=timeout,
                allow_redirects=allow_redirects,
                output_path=output_path,
            )
        if response_mode == "redirect":
            return self.request_redirect(
                method,
                path,
                params=params,
                headers=headers,
                public=public,
                timeout=timeout,
            )
        response = self.request(
            method,
            path,
            params=params,
            json_data=json_data,
            data=data,
            files=files,
            headers=headers,
            public=public,
            timeout=timeout,
            allow_redirects=allow_redirects,
        )
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type or "text/json" in content_type:
            try:
                payload = response.json()
            except ValueError as exc:
                raise APIError(f"non-json response from {path}") from exc
            if unwrap_envelope and isinstance(payload, dict) and {"code", "message"}.issubset(payload.keys()):
                code = payload.get("code")
                if code is not None and code != 20000:
                    raise APIError(payload.get("message") or f"request failed with code {code}")
                return payload.get("data")
            return payload
        if output_path:
            meta = write_output_file(output_path, response.content)
            meta["content_type"] = content_type
            return meta
        return response.text

    def request_data(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: Any | None = None,
        data: Any | None = None,
        files: dict[str, Any] | None = None,
        public: bool = False,
        timeout: int = 30,
    ) -> Any:
        return self.request_json(
            method,
            path,
            params=params,
            json_data=json_data,
            data=data,
            files=files,
            public=public,
            timeout=timeout,
            unwrap_envelope=True,
        )

    def ping(self) -> Any:
        return self.request_data("GET", "/api/v1/user/initAdminStatus", public=True)
