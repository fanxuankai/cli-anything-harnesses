"""配置管理模块。"""

from typing import Any, Optional

from .client import ManagementClient


class ConfigManager:
    """管理 CLIProxyAPI 的配置项。"""

    def __init__(self, client: ManagementClient):
        self.client = client

    def get_config(self) -> dict:
        resp = self.client.get("/config")
        resp.raise_for_status()
        return resp.json()

    def get_config_yaml(self) -> str:
        resp = self.client.get("/config.yaml")
        resp.raise_for_status()
        return resp.text

    def put_config_yaml(self, yaml_content: str) -> dict:
        resp = self.client.put(
            "/config.yaml",
            json_data=yaml_content,
        )
        resp.raise_for_status()
        return resp.json()

    # ---- 调试模式 ----

    def get_debug(self) -> bool:
        resp = self.client.get("/debug")
        resp.raise_for_status()
        return resp.json().get("value", False)

    def set_debug(self, enabled: bool) -> dict:
        resp = self.client.put("/debug", json_data={"value": enabled})
        resp.raise_for_status()
        return resp.json()

    # ---- 日志写文件 ----

    def get_logging_to_file(self) -> bool:
        resp = self.client.get("/logging-to-file")
        resp.raise_for_status()
        return resp.json().get("value", False)

    def set_logging_to_file(self, enabled: bool) -> dict:
        resp = self.client.put("/logging-to-file", json_data={"value": enabled})
        resp.raise_for_status()
        return resp.json()

    # ---- 日志大小限制 ----

    def get_logs_max_total_size_mb(self) -> int:
        resp = self.client.get("/logs-max-total-size-mb")
        resp.raise_for_status()
        return resp.json().get("value", 0)

    def set_logs_max_total_size_mb(self, value: int) -> dict:
        resp = self.client.put("/logs-max-total-size-mb", json_data={"value": value})
        resp.raise_for_status()
        return resp.json()

    # ---- 错误日志文件数限制 ----

    def get_error_logs_max_files(self) -> int:
        resp = self.client.get("/error-logs-max-files")
        resp.raise_for_status()
        return resp.json().get("value", 10)

    def set_error_logs_max_files(self, value: int) -> dict:
        resp = self.client.put("/error-logs-max-files", json_data={"value": value})
        resp.raise_for_status()
        return resp.json()

    # ---- 使用统计 ----

    def get_usage_statistics_enabled(self) -> bool:
        resp = self.client.get("/usage-statistics-enabled")
        resp.raise_for_status()
        return resp.json().get("value", False)

    def set_usage_statistics_enabled(self, enabled: bool) -> dict:
        resp = self.client.put("/usage-statistics-enabled", json_data={"value": enabled})
        resp.raise_for_status()
        return resp.json()

    # ---- 代理 URL ----

    def get_proxy_url(self) -> Optional[str]:
        resp = self.client.get("/proxy-url")
        resp.raise_for_status()
        return resp.json().get("value")

    def set_proxy_url(self, url: str) -> dict:
        resp = self.client.put("/proxy-url", json_data={"value": url})
        resp.raise_for_status()
        return resp.json()

    def delete_proxy_url(self) -> dict:
        resp = self.client.delete("/proxy-url")
        resp.raise_for_status()
        return resp.json()

    # ---- 请求重试 ----

    def get_request_retry(self) -> int:
        resp = self.client.get("/request-retry")
        resp.raise_for_status()
        return resp.json().get("value", 3)

    def set_request_retry(self, value: int) -> dict:
        resp = self.client.put("/request-retry", json_data={"value": value})
        resp.raise_for_status()
        return resp.json()

    def get_max_retry_interval(self) -> int:
        resp = self.client.get("/max-retry-interval")
        resp.raise_for_status()
        return resp.json().get("value", 30)

    def set_max_retry_interval(self, value: int) -> dict:
        resp = self.client.put("/max-retry-interval", json_data={"value": value})
        resp.raise_for_status()
        return resp.json()

    # ---- 模型前缀 ----

    def get_force_model_prefix(self) -> bool:
        resp = self.client.get("/force-model-prefix")
        resp.raise_for_status()
        return resp.json().get("value", False)

    def set_force_model_prefix(self, enabled: bool) -> dict:
        resp = self.client.put("/force-model-prefix", json_data={"value": enabled})
        resp.raise_for_status()
        return resp.json()

    # ---- 路由策略 ----

    def get_routing_strategy(self) -> str:
        resp = self.client.get("/routing/strategy")
        resp.raise_for_status()
        return resp.json().get("value", "round-robin")

    def set_routing_strategy(self, strategy: str) -> dict:
        resp = self.client.put("/routing/strategy", json_data={"value": strategy})
        resp.raise_for_status()
        return resp.json()

    # ---- 配额超限行为 ----

    def get_switch_project(self) -> bool:
        resp = self.client.get("/quota-exceeded/switch-project")
        resp.raise_for_status()
        return resp.json().get("value", True)

    def set_switch_project(self, enabled: bool) -> dict:
        resp = self.client.put("/quota-exceeded/switch-project", json_data={"value": enabled})
        resp.raise_for_status()
        return resp.json()

    def get_switch_preview_model(self) -> bool:
        resp = self.client.get("/quota-exceeded/switch-preview-model")
        resp.raise_for_status()
        return resp.json().get("value", True)

    def set_switch_preview_model(self, enabled: bool) -> dict:
        resp = self.client.put("/quota-exceeded/switch-preview-model", json_data={"value": enabled})
        resp.raise_for_status()
        return resp.json()

    # ---- WebSocket 认证 ----

    def get_ws_auth(self) -> bool:
        resp = self.client.get("/ws-auth")
        resp.raise_for_status()
        return resp.json().get("value", False)

    def set_ws_auth(self, enabled: bool) -> dict:
        resp = self.client.put("/ws-auth", json_data={"value": enabled})
        resp.raise_for_status()
        return resp.json()

    # ---- 最新版本 ----

    def get_latest_version(self) -> dict:
        resp = self.client.get("/latest-version")
        resp.raise_for_status()
        return resp.json()
