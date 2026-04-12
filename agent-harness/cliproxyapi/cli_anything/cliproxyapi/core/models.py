"""模型管理模块。"""

from __future__ import annotations

from typing import Any, Optional

from .client import ManagementClient


class ModelManager:
    """管理 CLIProxyAPI 的模型列表、别名和排除规则。"""

    def __init__(self, client: ManagementClient):
        self.client = client

    def list_models(self, api_key: str) -> dict:
        resp = self.client.proxy_get("/v1/models", api_key)
        resp.raise_for_status()
        return resp.json()

    def get_oauth_model_alias(self) -> dict:
        resp = self.client.get("/oauth-model-alias")
        resp.raise_for_status()
        return resp.json()

    def put_oauth_model_alias(self, aliases: dict) -> dict:
        resp = self.client.put("/oauth-model-alias", json_data=aliases)
        resp.raise_for_status()
        return resp.json()

    def patch_oauth_model_alias(self, channel: str, entry: dict) -> dict:
        resp = self.client.patch("/oauth-model-alias", json_data={"channel": channel, **entry})
        resp.raise_for_status()
        return resp.json()

    def delete_oauth_model_alias(self, channel: str, name: str = "") -> dict:
        data: dict[str, Any] = {"channel": channel}
        if name:
            data["name"] = name
        resp = self.client.delete("/oauth-model-alias", json_data=data)
        resp.raise_for_status()
        return resp.json()

    def get_oauth_excluded_models(self) -> dict:
        resp = self.client.get("/oauth-excluded-models")
        resp.raise_for_status()
        return resp.json()

    def put_oauth_excluded_models(self, exclusions: dict) -> dict:
        resp = self.client.put("/oauth-excluded-models", json_data=exclusions)
        resp.raise_for_status()
        return resp.json()

    def patch_oauth_excluded_models(self, channel: str, models: list) -> dict:
        resp = self.client.patch("/oauth-excluded-models", json_data={"channel": channel, "models": models})
        resp.raise_for_status()
        return resp.json()

    def delete_oauth_excluded_models(self, channel: str, model: str = "") -> dict:
        data: dict[str, Any] = {"channel": channel}
        if model:
            data["model"] = model
        resp = self.client.delete("/oauth-excluded-models", json_data=data)
        resp.raise_for_status()
        return resp.json()
