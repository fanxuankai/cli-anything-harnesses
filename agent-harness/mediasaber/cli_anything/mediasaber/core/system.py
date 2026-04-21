from __future__ import annotations

from typing import Any

from .client import MediaSaberClient


class SystemManager:
    def __init__(self, client: MediaSaberClient):
        self.client = client

    def status(self) -> Any:
        return self.client.request_data("GET", "/api/v1/system/status")

    def space(self) -> Any:
        return self.client.request_data("GET", "/api/v1/system/space")

    def basic_config(self) -> Any:
        return self.client.request_data("GET", "/api/v1/basicConfig/detail")

    def basic_config_part(self, keys: list[str]) -> Any:
        return self.client.request_data("POST", "/api/v1/basicConfig/getPart", json_data={"keys": keys})

    def task_schedule(self) -> Any:
        return self.client.request_data("GET", "/api/v1/taskSchedule/list")

    def upgrade_version(self) -> Any:
        return self.client.request_data("GET", "/api/v1/system/upgradeVersion")

    def path_ls(self, path: str) -> Any:
        return self.client.request_data("POST", "/api/v1/path/ls", json_data={"path": path})
