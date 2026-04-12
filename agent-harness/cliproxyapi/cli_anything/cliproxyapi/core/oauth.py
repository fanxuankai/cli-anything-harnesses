"""OAuth 登录流程模块。"""

from typing import Optional

from .client import ManagementClient


class OAuthManager:
    """管理 CLIProxyAPI 的 OAuth 登录流程。"""

    PROVIDERS = {
        "anthropic": {"path": "/anthropic-auth-url", "label": "Claude"},
        "codex": {"path": "/codex-auth-url", "label": "Codex"},
        "gemini": {"path": "/gemini-cli-auth-url", "label": "Gemini CLI"},
        "antigravity": {"path": "/antigravity-auth-url", "label": "Antigravity"},
        "qwen": {"path": "/qwen-auth-url", "label": "Qwen Code"},
        "kimi": {"path": "/kimi-auth-url", "label": "Kimi"},
        "iflow": {"path": "/iflow-auth-url", "label": "iFlow"},
    }

    def __init__(self, client: ManagementClient):
        self.client = client

    def request_auth_url(self, provider: str, no_browser: bool = False) -> dict:
        if provider not in self.PROVIDERS:
            raise ValueError(f"不支持提供商: {provider}，可选: {', '.join(self.PROVIDERS)}")

        info = self.PROVIDERS[provider]
        params = {}
        if no_browser:
            params["no_browser"] = "true"

        if provider == "iflow":
            resp = self.client.get(info["path"], params=params)
        else:
            resp = self.client.get(info["path"], params=params)
        resp.raise_for_status()
        return resp.json()

    def request_iflow_cookie(self, cookie: str) -> dict:
        resp = self.client.post("/iflow-auth-url", json_data={"cookie": cookie})
        resp.raise_for_status()
        return resp.json()

    def post_oauth_callback(self, provider: str, code: str, state: str) -> dict:
        resp = self.client.post("/oauth-callback", json_data={
            "provider": provider,
            "code": code,
            "state": state,
        })
        resp.raise_for_status()
        return resp.json()

    def get_auth_status(self, session_id: str) -> dict:
        resp = self.client.get("/get-auth-status", params={"session_id": session_id})
        resp.raise_for_status()
        return resp.json()
