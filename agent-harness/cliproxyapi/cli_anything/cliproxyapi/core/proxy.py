"""代理/服务器管理模块。"""

from __future__ import annotations

from typing import Any, Optional

from .client import ManagementClient


class ProxyManager:
    """管理 CLIProxyAPI 的代理设置和 Amp 集成。"""

    def __init__(self, client: ManagementClient):
        self.client = client

    # ---- 服务器状态 ----

    def health_check(self) -> dict:
        resp = self.client.health_check()
        resp.raise_for_status()
        return resp.json()

    # ---- Amp 集成 ----

    def get_amp_config(self) -> dict:
        resp = self.client.get("/ampcode")
        resp.raise_for_status()
        return resp.json()

    def get_amp_upstream_url(self) -> Optional[str]:
        resp = self.client.get("/ampcode/upstream-url")
        resp.raise_for_status()
        return resp.json().get("value")

    def set_amp_upstream_url(self, url: str) -> dict:
        resp = self.client.put("/ampcode/upstream-url", json_data={"value": url})
        resp.raise_for_status()
        return resp.json()

    def delete_amp_upstream_url(self) -> dict:
        resp = self.client.delete("/ampcode/upstream-url")
        resp.raise_for_status()
        return resp.json()

    def get_amp_upstream_api_key(self) -> Optional[str]:
        resp = self.client.get("/ampcode/upstream-api-key")
        resp.raise_for_status()
        return resp.json().get("value")

    def set_amp_upstream_api_key(self, key: str) -> dict:
        resp = self.client.put("/ampcode/upstream-api-key", json_data={"value": key})
        resp.raise_for_status()
        return resp.json()

    def delete_amp_upstream_api_key(self) -> dict:
        resp = self.client.delete("/ampcode/upstream-api-key")
        resp.raise_for_status()
        return resp.json()

    def get_amp_model_mappings(self) -> list:
        resp = self.client.get("/ampcode/model-mappings")
        resp.raise_for_status()
        return resp.json().get("value", [])

    def set_amp_model_mappings(self, mappings: list) -> dict:
        resp = self.client.put("/ampcode/model-mappings", json_data={"value": mappings})
        resp.raise_for_status()
        return resp.json()

    def patch_amp_model_mappings(self, mapping: dict) -> dict:
        resp = self.client.patch("/ampcode/model-mappings", json_data=mapping)
        resp.raise_for_status()
        return resp.json()

    def delete_amp_model_mappings(self, from_model: str = "") -> dict:
        data: dict[str, Any] = {}
        if from_model:
            data["from"] = from_model
        resp = self.client.delete("/ampcode/model-mappings", json_data=data)
        resp.raise_for_status()
        return resp.json()

    def get_amp_force_model_mappings(self) -> bool:
        resp = self.client.get("/ampcode/force-model-mappings")
        resp.raise_for_status()
        return resp.json().get("value", False)

    def set_amp_force_model_mappings(self, enabled: bool) -> dict:
        resp = self.client.put("/ampcode/force-model-mappings", json_data={"value": enabled})
        resp.raise_for_status()
        return resp.json()

    def get_amp_restrict_management_to_localhost(self) -> bool:
        resp = self.client.get("/ampcode/restrict-management-to-localhost")
        resp.raise_for_status()
        return resp.json().get("value", False)

    def set_amp_restrict_management_to_localhost(self, enabled: bool) -> dict:
        resp = self.client.put("/ampcode/restrict-management-to-localhost", json_data={"value": enabled})
        resp.raise_for_status()
        return resp.json()

    def get_amp_upstream_api_keys(self) -> list:
        resp = self.client.get("/ampcode/upstream-api-keys")
        resp.raise_for_status()
        return resp.json().get("value", [])

    def set_amp_upstream_api_keys(self, keys: list) -> dict:
        resp = self.client.put("/ampcode/upstream-api-keys", json_data={"value": keys})
        resp.raise_for_status()
        return resp.json()

    def patch_amp_upstream_api_keys(self, entry: dict) -> dict:
        resp = self.client.patch("/ampcode/upstream-api-keys", json_data=entry)
        resp.raise_for_status()
        return resp.json()

    def delete_amp_upstream_api_keys(self, upstream_api_key: str = "") -> dict:
        data: dict[str, Any] = {}
        if upstream_api_key:
            data["upstream_api_key"] = upstream_api_key
        resp = self.client.delete("/ampcode/upstream-api-keys", json_data=data)
        resp.raise_for_status()
        return resp.json()

    # ---- 通用 API 调用 ----

    def api_call(
        self,
        method: str,
        url: str,
        headers: Optional[dict] = None,
        data: Optional[str] = None,
        auth_index: Optional[str] = None,
    ) -> dict:
        body: dict[str, Any] = {"method": method, "url": url}
        if headers:
            body["header"] = headers
        if data:
            body["data"] = data
        if auth_index:
            body["auth_index"] = auth_index
        resp = self.client.post("/api-call", json_data=body)
        resp.raise_for_status()
        return resp.json()
