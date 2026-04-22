"""Core HTTP client for Media Saber."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any, Optional

import requests

SUCCESS_CODES = {0, 20000, None}


@dataclass
class ConnectionConfig:
    """Resolved connection parameters for the CLI."""

    DEFAULT_CONFIG_PATH = Path.home() / ".ms-cli.yaml"

    base_url: str
    api_key: str
    url_source: str
    api_key_source: str

    @classmethod
    def resolve(
        cls,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> "ConnectionConfig":
        config_data = cls._load_from_config()

        resolved_url = cls._pick_value(
            explicit=url,
            env_name="MS_URL",
            config_value=config_data.get("url"),
            config_label="config",
        )
        resolved_key = cls._pick_value(
            explicit=api_key,
            env_name="MS_API_KEY",
            config_value=config_data.get("api_key") or config_data.get("apikey"),
            config_label="config",
        )

        return cls(
            base_url=(resolved_url[0] or "").rstrip("/"),
            api_key=(resolved_key[0] or "").strip(),
            url_source=resolved_url[1],
            api_key_source=resolved_key[1],
        )

    @classmethod
    def _pick_value(
        cls,
        explicit: Optional[str],
        env_name: str,
        config_value: Optional[str],
        config_label: str,
    ) -> tuple[Optional[str], str]:
        if explicit:
            return explicit, "cli"
        env_value = os.getenv(env_name)
        if env_value:
            return env_value, "env"
        if config_value:
            return config_value, config_label
        return None, "unset"

    @classmethod
    def _load_from_config(cls) -> dict[str, Any]:
        if not cls.DEFAULT_CONFIG_PATH.exists():
            return {}

        try:
            import yaml

            data = yaml.safe_load(cls.DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}

        return data if isinstance(data, dict) else {}

    @classmethod
    def save(cls, url: str, api_key: str) -> Path:
        import yaml

        cls.DEFAULT_CONFIG_PATH.write_text(
            yaml.safe_dump(
                {
                    "url": url.rstrip("/"),
                    "api_key": api_key,
                },
                allow_unicode=True,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return cls.DEFAULT_CONFIG_PATH

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    @property
    def masked_api_key(self) -> str:
        if not self.api_key:
            return ""
        if len(self.api_key) <= 8:
            return "*" * len(self.api_key)
        return f"{self.api_key[:4]}...{self.api_key[-4:]}"

    def require_configured(self) -> None:
        if not self.base_url:
            raise ValueError("Media Saber URL is not configured")
        if not self.api_key:
            raise ValueError("Media Saber API key is not configured")

    def as_display_dict(self) -> dict[str, Any]:
        return {
            "configured": self.is_configured,
            "base_url": self.base_url,
            "url_source": self.url_source,
            "api_key": self.masked_api_key,
            "api_key_source": self.api_key_source,
            "config_path": str(self.DEFAULT_CONFIG_PATH),
        }


@dataclass
class ApiResponse:
    """Normalized API response returned by MSClient."""

    status_code: int
    ok: bool
    code: Optional[int]
    message: Optional[str]
    data: Any
    raw_body: Any
    is_standard_response: bool

    @classmethod
    def from_http_response(cls, response: requests.Response) -> "ApiResponse":
        try:
            parsed: Any = response.json()
        except ValueError:
            parsed = None

        raw_body: Any = parsed if parsed is not None else response.text
        is_standard = isinstance(parsed, dict) and {"code", "message", "data"}.issubset(parsed.keys())

        if is_standard:
            code = parsed.get("code")
            message = parsed.get("message")
            data = parsed.get("data")
        else:
            code = None
            message = None
            data = raw_body

        ok = response.ok and (code in SUCCESS_CODES)

        return cls(
            status_code=response.status_code,
            ok=ok,
            code=code,
            message=message,
            data=data,
            raw_body=raw_body,
            is_standard_response=is_standard,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status_code": self.status_code,
            "ok": self.ok,
            "is_standard_response": self.is_standard_response,
            "code": self.code,
            "message": self.message,
            "data": self.data,
            "raw_body": self.raw_body,
        }


class MSClient:
    """Generic HTTP client for Media Saber."""

    def __init__(self, conn: ConnectionConfig):
        self.conn = conn
        self._session = requests.Session()

    def build_url(self, path: str) -> str:
        if not path.startswith("/"):
            raise ValueError("PATH must start with '/' and be a full API path")
        if not self.conn.base_url:
            raise ValueError("Media Saber URL is not configured")
        return f"{self.conn.base_url}{path}"

    def _build_headers(self, headers: Optional[dict[str, str]] = None) -> dict[str, str]:
        merged = {"Authorization": f"Bearer {self.conn.api_key}"} if self.conn.api_key else {}
        if headers:
            merged.update(headers)
        return merged

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict[str, str]] = None,
        headers: Optional[dict[str, str]] = None,
        json_body: Any = None,
        timeout: int = 30,
    ) -> ApiResponse:
        response = self._session.request(
            method=method.upper(),
            url=self.build_url(path),
            params=params,
            headers=self._build_headers(headers),
            json=json_body,
            timeout=timeout,
        )
        return ApiResponse.from_http_response(response)
