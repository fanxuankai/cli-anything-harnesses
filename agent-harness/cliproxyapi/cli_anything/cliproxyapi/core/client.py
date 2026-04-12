"""HTTP 客户端，封装与 CLIProxyAPI 管理 API 的所有通信。"""

import json
import os
from typing import Any, Optional
from pathlib import Path

import requests


# 默认配置文件路径
DEFAULT_CONFIG_PATH = Path.home() / ".cliproxyapi-cli.yaml"


class ConnectionConfig:
    """从 CLI 参数 / 环境变量 / 配置文件解析连接参数。"""

    def __init__(
        self,
        url: Optional[str] = None,
        key: Optional[str] = None,
    ):
        self.base_url = (url or os.getenv("CPA_URL") or self._load_from_config("url") or "").rstrip("/")
        self.management_key = key or os.getenv("CPA_KEY") or self._load_from_config("key") or ""

    @staticmethod
    def _load_from_config(field: str) -> Optional[str]:
        if not DEFAULT_CONFIG_PATH.exists():
            return None
        try:
            import yaml

            data = yaml.safe_load(DEFAULT_CONFIG_PATH.read_text())
            if isinstance(data, dict):
                return data.get(field)
        except Exception:
            pass
        return None

    def save(self, url: str, key: str) -> None:
        import yaml

        data = {}
        if DEFAULT_CONFIG_PATH.exists():
            try:
                data = yaml.safe_load(DEFAULT_CONFIG_PATH.read_text()) or {}
            except Exception:
                data = {}
        data["url"] = url.rstrip("/")
        data["key"] = key
        DEFAULT_CONFIG_PATH.write_text(yaml.dump(data, default_flow_style=False))

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.management_key)


class ManagementClient:
    """CLIProxyAPI 管理 API 的 HTTP 客户端。"""

    def __init__(self, conn: ConnectionConfig):
        self.conn = conn
        self._session = requests.Session()

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.conn.management_key}",
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        return f"{self.conn.base_url}/v0/management{path}"

    def get(self, path: str, params: Optional[dict] = None) -> requests.Response:
        return self._session.get(self._url(path), headers=self._headers, params=params, timeout=30)

    def post(self, path: str, json_data: Any = None, **kwargs) -> requests.Response:
        return self._session.post(self._url(path), headers=self._headers, json=json_data, timeout=30, **kwargs)

    def put(self, path: str, json_data: Any = None) -> requests.Response:
        return self._session.put(self._url(path), headers=self._headers, json=json_data, timeout=30)

    def patch(self, path: str, json_data: Any = None) -> requests.Response:
        return self._session.patch(self._url(path), headers=self._headers, json=json_data, timeout=30)

    def delete(self, path: str, json_data: Any = None) -> requests.Response:
        return self._session.delete(self._url(path), headers=self._headers, json=json_data, timeout=30)

    # ---- 代理 API（非管理端点） ----

    def health_check(self) -> requests.Response:
        return self._session.get(f"{self.conn.base_url}/healthz", timeout=10)

    def proxy_get(self, path: str, api_key: str, params: Optional[dict] = None) -> requests.Response:
        headers = {"Authorization": f"Bearer {api_key}"}
        return self._session.get(f"{self.conn.base_url}{path}", headers=headers, params=params, timeout=30)

    def proxy_post(self, path: str, api_key: str, json_data: Any = None) -> requests.Response:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        return self._session.post(f"{self.conn.base_url}{path}", headers=headers, json=json_data, timeout=60)
