from __future__ import annotations

import socket
from typing import Any

from .client import MediaSaberClient


class AuthManager:
    def __init__(self, client: MediaSaberClient):
        self.client = client

    def init_admin_status(self) -> Any:
        return self.client.request_data("GET", "/api/v1/user/initAdminStatus", public=True)

    def login(
        self,
        user_name: str,
        password: str,
        *,
        device_type: str = "cli",
        device_name: str | None = None,
        backend_domain: str | None = None,
    ) -> str:
        payload = {
            "userName": user_name,
            "password": password,
            "deviceType": device_type,
            "deviceName": device_name or socket.gethostname(),
        }
        if backend_domain:
            payload["backendDomain"] = backend_domain
        return self.client.request_data("POST", "/api/v1/user/login", json_data=payload, public=True)

    def whoami(self) -> Any:
        return self.client.request_data("GET", "/api/v1/user/info")

    def logout(self) -> Any:
        return self.client.request_data("POST", "/api/v1/user/logout")

    def tokens(self) -> Any:
        return self.client.request_data("GET", "/api/v1/user/tokens")
