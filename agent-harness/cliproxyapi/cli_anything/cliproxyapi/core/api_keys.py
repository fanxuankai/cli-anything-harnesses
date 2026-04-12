"""API 密钥管理模块。"""

from typing import Any, Optional

from .client import ManagementClient


class APIKeyManager:
    """管理 CLIProxyAPI 的各类 API 密钥。"""

    def __init__(self, client: ManagementClient):
        self.client = client

    # ---- 全局 API 密钥 ----

    def list_api_keys(self) -> list:
        resp = self.client.get("/api-keys")
        resp.raise_for_status()
        return resp.json().get("value", [])

    def set_api_keys(self, keys: list) -> dict:
        resp = self.client.put("/api-keys", json_data={"value": keys})
        resp.raise_for_status()
        return resp.json()

    def add_api_key(self, key: str) -> dict:
        resp = self.client.patch("/api-keys", json_data={"value": key})
        resp.raise_for_status()
        return resp.json()

    def delete_api_key(self, key: str) -> dict:
        resp = self.client.delete("/api-keys", json_data={"value": key})
        resp.raise_for_status()
        return resp.json()

    # ---- Gemini API 密钥 ----

    def list_gemini_keys(self) -> list:
        resp = self.client.get("/gemini-api-key")
        resp.raise_for_status()
        return resp.json().get("value", [])

    def set_gemini_keys(self, keys: list) -> dict:
        resp = self.client.put("/gemini-api-key", json_data={"value": keys})
        resp.raise_for_status()
        return resp.json()

    def add_gemini_key(self, key_data: dict) -> dict:
        resp = self.client.patch("/gemini-api-key", json_data=key_data)
        resp.raise_for_status()
        return resp.json()

    def delete_gemini_key(self, api_key: str) -> dict:
        resp = self.client.delete("/gemini-api-key", json_data={"api_key": api_key})
        resp.raise_for_status()
        return resp.json()

    # ---- Claude API 密钥 ----

    def list_claude_keys(self) -> list:
        resp = self.client.get("/claude-api-key")
        resp.raise_for_status()
        return resp.json().get("value", [])

    def set_claude_keys(self, keys: list) -> dict:
        resp = self.client.put("/claude-api-key", json_data={"value": keys})
        resp.raise_for_status()
        return resp.json()

    def add_claude_key(self, key_data: dict) -> dict:
        resp = self.client.patch("/claude-api-key", json_data=key_data)
        resp.raise_for_status()
        return resp.json()

    def delete_claude_key(self, api_key: str) -> dict:
        resp = self.client.delete("/claude-api-key", json_data={"api_key": api_key})
        resp.raise_for_status()
        return resp.json()

    # ---- Codex API 密钥 ----

    def list_codex_keys(self) -> list:
        resp = self.client.get("/codex-api-key")
        resp.raise_for_status()
        return resp.json().get("value", [])

    def set_codex_keys(self, keys: list) -> dict:
        resp = self.client.put("/codex-api-key", json_data={"value": keys})
        resp.raise_for_status()
        return resp.json()

    def add_codex_key(self, key_data: dict) -> dict:
        resp = self.client.patch("/codex-api-key", json_data=key_data)
        resp.raise_for_status()
        return resp.json()

    def delete_codex_key(self, api_key: str) -> dict:
        resp = self.client.delete("/codex-api-key", json_data={"api_key": api_key})
        resp.raise_for_status()
        return resp.json()

    # ---- OpenAI 兼容提供商 ----

    def list_openai_compat(self) -> list:
        resp = self.client.get("/openai-compatibility")
        resp.raise_for_status()
        return resp.json().get("value", [])

    def set_openai_compat(self, providers: list) -> dict:
        resp = self.client.put("/openai-compatibility", json_data={"value": providers})
        resp.raise_for_status()
        return resp.json()

    def add_openai_compat(self, provider: dict) -> dict:
        resp = self.client.patch("/openai-compatibility", json_data=provider)
        resp.raise_for_status()
        return resp.json()

    def delete_openai_compat(self, name: str) -> dict:
        resp = self.client.delete("/openai-compatibility", json_data={"name": name})
        resp.raise_for_status()
        return resp.json()

    # ---- Vertex API 密钥 ----

    def list_vertex_keys(self) -> list:
        resp = self.client.get("/vertex-api-key")
        resp.raise_for_status()
        return resp.json().get("value", [])

    def set_vertex_keys(self, keys: list) -> dict:
        resp = self.client.put("/vertex-api-key", json_data={"value": keys})
        resp.raise_for_status()
        return resp.json()

    def add_vertex_key(self, key_data: dict) -> dict:
        resp = self.client.patch("/vertex-api-key", json_data=key_data)
        resp.raise_for_status()
        return resp.json()

    def delete_vertex_key(self, api_key: str) -> dict:
        resp = self.client.delete("/vertex-api-key", json_data={"api_key": api_key})
        resp.raise_for_status()
        return resp.json()
