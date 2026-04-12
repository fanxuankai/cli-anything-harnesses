"""CLIProxyAPI CLI 入口 - 基于 Click 的命令行工具。

支持 REPL 模式和一次性命令，所有命令支持 --json 输出。
"""

import json
import sys
from typing import Optional

import click

from .core.client import ConnectionConfig, ManagementClient
from .core.config import ConfigManager
from .core.auth import AuthManager
from .core.oauth import OAuthManager
from .core.models import ModelManager
from .core.usage import UsageManager
from .core.logs import LogManager
from .core.api_keys import APIKeyManager
from .core.proxy import ProxyManager
from .utils.output import output_result, output_json, output_error, output_table, console


# ---- 全局上下文 ----

class Context:
    """CLI 运行时上下文。"""

    def __init__(self):
        self.json_mode = False
        self._client: Optional[ManagementClient] = None
        self._conn: Optional[ConnectionConfig] = None

    def setup(self, url: Optional[str], key: Optional[str]):
        self._conn = ConnectionConfig(url=url, key=key)
        self._client = ManagementClient(self._conn)

    @property
    def client(self) -> ManagementClient:
        if self._client is None:
            self.setup(None, None)
        return self._client

    @property
    def conn(self) -> ConnectionConfig:
        if self._conn is None:
            self.setup(None, None)
        return self._conn

    @property
    def config_mgr(self) -> ConfigManager:
        return ConfigManager(self.client)

    @property
    def auth_mgr(self) -> AuthManager:
        return AuthManager(self.client)

    @property
    def oauth_mgr(self) -> OAuthManager:
        return OAuthManager(self.client)

    @property
    def model_mgr(self) -> ModelManager:
        return ModelManager(self.client)

    @property
    def usage_mgr(self) -> UsageManager:
        return UsageManager(self.client)

    @property
    def log_mgr(self) -> LogManager:
        return LogManager(self.client)

    @property
    def key_mgr(self) -> APIKeyManager:
        return APIKeyManager(self.client)

    @property
    def proxy_mgr(self) -> ProxyManager:
        return ProxyManager(self.client)


pass_ctx = click.make_pass_decorator(Context, ensure=True)


def handle_error(ctx: Context, exc: Exception):
    if ctx.json_mode:
        output_json({"error": str(exc)})
    else:
        output_error(str(exc))
    sys.exit(1)


# ---- 根命令组 ----

@click.group(invoke_without_command=True)
@click.option("--url", "-u", envvar="CPA_URL", help="CLIProxyAPI 服务器地址")
@click.option("--key", "-k", envvar="CPA_KEY", help="管理 API 密钥")
@click.option("--json", "json_mode", is_flag=True, help="JSON 格式输出")
@click.option("--repl", "repl_mode", is_flag=True, help="进入交互式 REPL")
@click.version_option(version="1.0.0", prog_name="cli-anything-cliproxyapi")
@click.pass_context
def main(click_ctx, url, key, json_mode, repl_mode):
    """CLIProxyAPI 命令行管理工具。

    通过 Management API 管理 CLIProxyAPI 代理服务器的配置、认证、模型等。

    连接参数优先级: --url/--key > 环境变量 CPA_URL/CPA_KEY > ~/.cliproxyapi-cli.yaml
    """
    ctx: Context = click_ctx.ensure_object(Context)
    ctx.json_mode = json_mode
    ctx.setup(url, key)

    if repl_mode:
        _enter_repl(click_ctx, ctx)
    elif click_ctx.invoked_subcommand is None:
        click.echo(click_ctx.get_help())


def _enter_repl(click_ctx, ctx: Context):
    """交互式 REPL 模式。"""
    import prompt_toolkit
    from prompt_toolkit.history import FileHistory

    history = FileHistory(str(ConnectionConfig._load_from_config.__func__.__self__ or ""))
    session = prompt_toolkit.PromptSession(
        history=FileHistory(str(ConnectionConfig.DEFAULT_CONFIG_PATH.parent / ".cliproxyapi_history")),
        message="cliproxyapi> ",
    )

    console.print("[bold]CLIProxyAPI REPL[/bold] - 输入 help 查看命令, exit 退出")
    while True:
        try:
            line = session.prompt()
        except (EOFError, KeyboardInterrupt):
            break
        line = line.strip()
        if not line or line in ("exit", "quit"):
            break
        if line == "help":
            click.echo(click_ctx.get_help())
            continue
        try:
            args = line.split()
            main(args, standalone_mode=False, parent=click_ctx.parent)
        except SystemExit:
            pass
        except Exception as e:
            output_error(str(e))


# ============================================================
# server 命令组
# ============================================================

@main.group()
@pass_ctx
def server(ctx: Context):
    """服务器状态管理。"""


@server.command("status")
@pass_ctx
def server_status(ctx: Context):
    """检查服务器健康状态。"""
    try:
        result = ctx.proxy_mgr.health_check()
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@server.command("version")
@pass_ctx
def server_version(ctx: Context):
    """获取最新版本信息。"""
    try:
        result = ctx.config_mgr.get_latest_version()
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


# ============================================================
# config 命令组
# ============================================================

@main.group()
@pass_ctx
def config(ctx: Context):
    """配置管理。"""


@config.command("get")
@pass_ctx
def config_get(ctx: Context):
    """获取当前配置。"""
    try:
        result = ctx.config_mgr.get_config()
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@config.command("get-yaml")
@pass_ctx
def config_get_yaml(ctx: Context):
    """获取 YAML 配置。"""
    try:
        result = ctx.config_mgr.get_config_yaml()
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@config.command("set-yaml")
@click.argument("yaml_content", required=False)
@click.option("--file", "-f", type=click.Path(exists=True), help="从文件读取 YAML")
@pass_ctx
def config_set_yaml(ctx: Context, yaml_content, file):
    """更新 YAML 配置。"""
    try:
        if file:
            with open(file) as f:
                yaml_content = f.read()
        if not yaml_content:
            click.echo("请提供 YAML 内容或使用 --file 指定文件")
            sys.exit(1)
        result = ctx.config_mgr.put_config_yaml(yaml_content)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@config.command("debug")
@click.argument("value", type=bool, required=False)
@pass_ctx
def config_debug(ctx: Context, value):
    """获取或设置调试模式。"""
    try:
        if value is None:
            result = ctx.config_mgr.get_debug()
        else:
            result = ctx.config_mgr.set_debug(value)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@config.command("proxy-url")
@click.argument("value", required=False)
@click.option("--delete", is_flag=True, help="删除代理 URL")
@pass_ctx
def config_proxy_url(ctx: Context, value, delete):
    """获取、设置或删除代理 URL。"""
    try:
        if delete:
            result = ctx.proxy_mgr.delete_proxy_url()
        elif value:
            result = ctx.config_mgr.set_proxy_url(value)
        else:
            result = ctx.config_mgr.get_proxy_url()
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@config.command("routing")
@click.argument("value", required=False)
@pass_ctx
def config_routing(ctx: Context, value):
    """获取或设置路由策略 (round-robin / fill-first)。"""
    try:
        if value:
            result = ctx.config_mgr.set_routing_strategy(value)
        else:
            result = ctx.config_mgr.get_routing_strategy()
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@config.command("retry")
@click.argument("value", type=int, required=False)
@pass_ctx
def config_retry(ctx: Context, value):
    """获取或设置请求重试次数。"""
    try:
        if value is not None:
            result = ctx.config_mgr.set_request_retry(value)
        else:
            result = ctx.config_mgr.get_request_retry()
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@config.command("max-retry-interval")
@click.argument("value", type=int, required=False)
@pass_ctx
def config_max_retry_interval(ctx: Context, value):
    """获取或设置最大重试等待时间（秒）。"""
    try:
        if value is not None:
            result = ctx.config_mgr.set_max_retry_interval(value)
        else:
            result = ctx.config_mgr.get_max_retry_interval()
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@config.command("force-model-prefix")
@click.argument("value", type=bool, required=False)
@pass_ctx
def config_force_model_prefix(ctx: Context, value):
    """获取或设置强制模型前缀。"""
    try:
        if value is None:
            result = ctx.config_mgr.get_force_model_prefix()
        else:
            result = ctx.config_mgr.set_force_model_prefix(value)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@config.command("ws-auth")
@click.argument("value", type=bool, required=False)
@pass_ctx
def config_ws_auth(ctx: Context, value):
    """获取或设置 WebSocket 认证。"""
    try:
        if value is None:
            result = ctx.config_mgr.get_ws_auth()
        else:
            result = ctx.config_mgr.set_ws_auth(value)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@config.command("quota-switch-project")
@click.argument("value", type=bool, required=False)
@pass_ctx
def config_quota_switch_project(ctx: Context, value):
    """获取或设置配额超限时自动切换项目。"""
    try:
        if value is None:
            result = ctx.config_mgr.get_switch_project()
        else:
            result = ctx.config_mgr.set_switch_project(value)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@config.command("quota-switch-preview")
@click.argument("value", type=bool, required=False)
@pass_ctx
def config_quota_switch_preview(ctx: Context, value):
    """获取或设置配额超限时自动切换预览模型。"""
    try:
        if value is None:
            result = ctx.config_mgr.get_switch_preview_model()
        else:
            result = ctx.config_mgr.set_switch_preview_model(value)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@config.command("save-connection")
@click.option("--url", "-u", required=True, help="服务器地址")
@click.option("--key", "-k", required=True, help="管理密钥")
@pass_ctx
def config_save_connection(ctx: Context, url, key):
    """保存连接参数到配置文件。"""
    try:
        ctx.conn.save(url, key)
        output_result({"status": "ok", "saved_to": str(ConnectionConfig.DEFAULT_CONFIG_PATH)}, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


# ============================================================
# auth 命令组
# ============================================================

@main.group()
@pass_ctx
def auth(ctx: Context):
    """认证文件管理。"""


@auth.command("list")
@click.option("--enabled", is_flag=True, help="仅显示启用的认证文件")
@click.option("--disabled", "disabled_only", is_flag=True, help="仅显示禁用的认证文件")
@pass_ctx
def auth_list(ctx: Context, enabled, disabled_only):
    """列出认证文件。"""
    try:
        if enabled and disabled_only:
            raise click.UsageError("--enabled 和 --disabled 不能同时使用")
        disabled = None
        if enabled:
            disabled = False
        elif disabled_only:
            disabled = True
        result = ctx.auth_mgr.list_auth_files(disabled=disabled)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@auth.command("codex-quota")
@pass_ctx
def auth_codex_quota(ctx: Context):
    """获取已启用 Codex 凭证额度。"""
    try:
        result = ctx.auth_mgr.get_codex_quotas()
        if ctx.json_mode:
            output_result(result, True)
            return
        quotas = result.get("quotas", [])
        rows = []
        for item in quotas:
            if item.get("error"):
                rows.append([
                    item.get("name", ""),
                    item.get("plan_type", "-"),
                    "失败",
                    item.get("error", ""),
                    "失败",
                    "",
                ])
                continue
            primary = item.get("primary_window") or {}
            secondary = item.get("secondary_window") or {}
            rows.append([
                item.get("name", ""),
                item.get("plan_type", "-"),
                f"{primary.get('remaining_percent', 0)}%",
                primary.get("reset_at_local", ""),
                f"{secondary.get('remaining_percent', 0)}%",
                secondary.get("reset_at_local", ""),
            ])
        output_table(["文件", "套餐", "5小时额度", "5小时重置", "周额度", "周重置"], rows, title="Codex 额度")
    except Exception as e:
        handle_error(ctx, e)


@auth.command("models")
@pass_ctx
def auth_models(ctx: Context):
    """查看认证文件关联的模型。"""
    try:
        result = ctx.auth_mgr.get_auth_file_models()
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@auth.command("upload")
@click.argument("filename")
@click.option("--content", "-c", help="认证文件内容")
@click.option("--file", "-f", type=click.Path(exists=True), help="从文件上传")
@pass_ctx
def auth_upload(ctx: Context, filename, content, file):
    """上传认证文件。"""
    try:
        if file:
            with open(file) as f:
                content = f.read()
        if not content:
            click.echo("请提供 --content 或 --file")
            sys.exit(1)
        result = ctx.auth_mgr.upload_auth_file(filename, content)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@auth.command("download")
@click.argument("filename")
@pass_ctx
def auth_download(ctx: Context, filename):
    """下载认证文件。"""
    try:
        result = ctx.auth_mgr.download_auth_file(filename)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@auth.command("delete")
@click.argument("filename")
@pass_ctx
def auth_delete(ctx: Context, filename):
    """删除认证文件。"""
    try:
        result = ctx.auth_mgr.delete_auth_file(filename)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@auth.command("status")
@click.argument("filename")
@click.argument("disabled", type=bool)
@pass_ctx
def auth_status(ctx: Context, filename, disabled):
    """设置认证文件启用/禁用状态。"""
    try:
        result = ctx.auth_mgr.patch_auth_file_status(filename, disabled)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@auth.command("fields")
@click.argument("filename")
@click.option("--set", "field_sets", multiple=True, nargs=2, help="设置字段: --set key value")
@pass_ctx
def auth_fields(ctx: Context, filename, field_sets):
    """更新认证文件字段。"""
    try:
        fields = {k: v for k, v in field_sets}
        result = ctx.auth_mgr.patch_auth_file_fields(filename, fields)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@auth.command("vertex-import")
@click.argument("key_json")
@click.option("--prefix", default="", help="Vertex 模型命名前缀")
@pass_ctx
def auth_vertex_import(ctx: Context, key_json, prefix):
    """导入 Vertex 服务账号密钥。"""
    try:
        result = ctx.auth_mgr.import_vertex(key_json, prefix)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@auth.command("definitions")
@click.argument("channel")
@pass_ctx
def auth_definitions(ctx: Context, channel):
    """查看指定渠道的模型定义。"""
    try:
        result = ctx.auth_mgr.get_model_definitions(channel)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


# ============================================================
# oauth 命令组
# ============================================================

@main.group()
@pass_ctx
def oauth(ctx: Context):
    """OAuth 登录管理。"""


@oauth.command("login")
@click.argument("provider", type=click.Choice(list(OAuthManager.PROVIDERS.keys())))
@click.option("--no-browser", is_flag=True, help="不自动打开浏览器")
@pass_ctx
def oauth_login(ctx: Context, provider, no_browser):
    """发起 OAuth 登录。支持: anthropic, codex, gemini, antigravity, qwen, kimi, iflow"""
    try:
        result = ctx.oauth_mgr.request_auth_url(provider, no_browser=no_browser)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@oauth.command("iflow-cookie")
@click.argument("cookie")
@pass_ctx
def oauth_iflow_cookie(ctx: Context, cookie):
    """使用 Cookie 登录 iFlow。"""
    try:
        result = ctx.oauth_mgr.request_iflow_cookie(cookie)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@oauth.command("callback")
@click.option("--provider", required=True, help="提供商名称")
@click.option("--code", required=True, help="授权码")
@click.option("--state", required=True, help="状态参数")
@pass_ctx
def oauth_callback(ctx: Context, provider, code, state):
    """处理 OAuth 回调。"""
    try:
        result = ctx.oauth_mgr.post_oauth_callback(provider, code, state)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@oauth.command("status")
@click.argument("session_id")
@pass_ctx
def oauth_status(ctx: Context, session_id):
    """查看认证会话状态。"""
    try:
        result = ctx.oauth_mgr.get_auth_status(session_id)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


# ============================================================
# keys 命令组
# ============================================================

@main.group()
@pass_ctx
def keys(ctx: Context):
    """API 密钥管理。"""


# ---- 全局 API 密钥 ----

@keys.command("list")
@pass_ctx
def keys_list(ctx: Context):
    """列出 API 密钥。"""
    try:
        result = ctx.key_mgr.list_api_keys()
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@keys.command("set")
@click.argument("keys_list", nargs=-1, required=True)
@pass_ctx
def keys_set(ctx: Context, keys_list):
    """设置 API 密钥（覆盖）。"""
    try:
        result = ctx.key_mgr.set_api_keys(list(keys_list))
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@keys.command("add")
@click.argument("key")
@pass_ctx
def keys_add(ctx: Context, key):
    """添加一个 API 密钥。"""
    try:
        result = ctx.key_mgr.add_api_key(key)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@keys.command("delete")
@click.argument("key")
@pass_ctx
def keys_delete(ctx: Context, key):
    """删除一个 API 密钥。"""
    try:
        result = ctx.key_mgr.delete_api_key(key)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


# ---- Gemini 密钥子命令 ----

@keys.group("gemini")
@pass_ctx
def keys_gemini(ctx: Context):
    """Gemini API 密钥管理。"""


@keys_gemini.command("list")
@pass_ctx
def keys_gemini_list(ctx: Context):
    try:
        result = ctx.key_mgr.list_gemini_keys()
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@keys_gemini.command("add")
@click.option("--api-key", required=True, help="API 密钥")
@click.option("--prefix", default="", help="前缀")
@click.option("--base-url", default="", help="基础 URL")
@click.option("--proxy-url", default="", help="代理 URL")
@pass_ctx
def keys_gemini_add(ctx: Context, api_key, prefix, base_url, proxy_url):
    try:
        data = {"api_key": api_key}
        if prefix:
            data["prefix"] = prefix
        if base_url:
            data["base_url"] = base_url
        if proxy_url:
            data["proxy_url"] = proxy_url
        result = ctx.key_mgr.add_gemini_key(data)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@keys_gemini.command("delete")
@click.argument("api_key")
@pass_ctx
def keys_gemini_delete(ctx: Context, api_key):
    try:
        result = ctx.key_mgr.delete_gemini_key(api_key)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


# ---- Claude 密钥子命令 ----

@keys.group("claude")
@pass_ctx
def keys_claude(ctx: Context):
    """Claude API 密钥管理。"""


@keys_claude.command("list")
@pass_ctx
def keys_claude_list(ctx: Context):
    try:
        result = ctx.key_mgr.list_claude_keys()
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@keys_claude.command("add")
@click.option("--api-key", required=True, help="API 密钥")
@click.option("--prefix", default="", help="前缀")
@click.option("--base-url", default="", help="基础 URL")
@click.option("--proxy-url", default="", help="代理 URL")
@pass_ctx
def keys_claude_add(ctx: Context, api_key, prefix, base_url, proxy_url):
    try:
        data = {"api_key": api_key}
        if prefix:
            data["prefix"] = prefix
        if base_url:
            data["base_url"] = base_url
        if proxy_url:
            data["proxy_url"] = proxy_url
        result = ctx.key_mgr.add_claude_key(data)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@keys_claude.command("delete")
@click.argument("api_key")
@pass_ctx
def keys_claude_delete(ctx: Context, api_key):
    try:
        result = ctx.key_mgr.delete_claude_key(api_key)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


# ---- Codex 密钥子命令 ----

@keys.group("codex")
@pass_ctx
def keys_codex(ctx: Context):
    """Codex API 密钥管理。"""


@keys_codex.command("list")
@pass_ctx
def keys_codex_list(ctx: Context):
    try:
        result = ctx.key_mgr.list_codex_keys()
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@keys_codex.command("add")
@click.option("--api-key", required=True, help="API 密钥")
@click.option("--prefix", default="", help="前缀")
@click.option("--base-url", default="", help="基础 URL")
@click.option("--proxy-url", default="", help="代理 URL")
@pass_ctx
def keys_codex_add(ctx: Context, api_key, prefix, base_url, proxy_url):
    try:
        data = {"api_key": api_key}
        if prefix:
            data["prefix"] = prefix
        if base_url:
            data["base_url"] = base_url
        if proxy_url:
            data["proxy_url"] = proxy_url
        result = ctx.key_mgr.add_codex_key(data)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@keys_codex.command("delete")
@click.argument("api_key")
@pass_ctx
def keys_codex_delete(ctx: Context, api_key):
    try:
        result = ctx.key_mgr.delete_codex_key(api_key)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


# ---- OpenAI 兼容提供商子命令 ----

@keys.group("openai-compat")
@pass_ctx
def keys_openai_compat(ctx: Context):
    """OpenAI 兼容提供商管理。"""


@keys_openai_compat.command("list")
@pass_ctx
def keys_openai_compat_list(ctx: Context):
    try:
        result = ctx.key_mgr.list_openai_compat()
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@keys_openai_compat.command("add")
@click.option("--name", required=True, help="提供商名称")
@click.option("--base-url", required=True, help="基础 URL")
@click.option("--api-key", required=True, help="API 密钥")
@click.option("--prefix", default="", help="前缀")
@pass_ctx
def keys_openai_compat_add(ctx: Context, name, base_url, api_key, prefix):
    try:
        provider = {"name": name, "base_url": base_url, "api_key_entries": [{"api_key": api_key}]}
        if prefix:
            provider["prefix"] = prefix
        result = ctx.key_mgr.add_openai_compat(provider)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@keys_openai_compat.command("delete")
@click.argument("name")
@pass_ctx
def keys_openai_compat_delete(ctx: Context, name):
    try:
        result = ctx.key_mgr.delete_openai_compat(name)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


# ---- Vertex 密钥子命令 ----

@keys.group("vertex")
@pass_ctx
def keys_vertex(ctx: Context):
    """Vertex API 密钥管理。"""


@keys_vertex.command("list")
@pass_ctx
def keys_vertex_list(ctx: Context):
    try:
        result = ctx.key_mgr.list_vertex_keys()
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@keys_vertex.command("add")
@click.option("--api-key", required=True, help="API 密钥")
@click.option("--base-url", default="", help="基础 URL")
@click.option("--prefix", default="", help="前缀")
@pass_ctx
def keys_vertex_add(ctx: Context, api_key, base_url, prefix):
    try:
        data = {"api_key": api_key}
        if base_url:
            data["base_url"] = base_url
        if prefix:
            data["prefix"] = prefix
        result = ctx.key_mgr.add_vertex_key(data)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@keys_vertex.command("delete")
@click.argument("api_key")
@pass_ctx
def keys_vertex_delete(ctx: Context, api_key):
    try:
        result = ctx.key_mgr.delete_vertex_key(api_key)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


# ============================================================
# models 命令组
# ============================================================

@main.group()
@pass_ctx
def models(ctx: Context):
    """模型管理。"""


@models.command("list")
@click.option("--api-key", envvar="CPA_API_KEY", help="代理 API 密钥（非管理密钥）")
@pass_ctx
def models_list(ctx: Context, api_key):
    """列出可用模型。"""
    try:
        if not api_key:
            click.echo("需要 --api-key 或设置 CPA_API_KEY 环境变量")
            sys.exit(1)
        result = ctx.model_mgr.list_models(api_key)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@models.command("aliases")
@click.option("--set", "alias_data", default=None, help="设置别名的 JSON 数据")
@click.option("--delete", "delete_alias", nargs=2, type=str, help="删除别名: --delete channel name")
@pass_ctx
def models_aliases(ctx: Context, alias_data, delete_alias):
    """管理 OAuth 模型别名。"""
    try:
        if delete_alias:
            channel, name = delete_alias
            result = ctx.model_mgr.delete_oauth_model_alias(channel, name)
        elif alias_data:
            import json as _json
            data = _json.loads(alias_data)
            result = ctx.model_mgr.put_oauth_model_alias(data)
        else:
            result = ctx.model_mgr.get_oauth_model_alias()
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@models.command("excluded")
@click.option("--set", "excl_data", default=None, help="设置排除模型的 JSON 数据")
@click.option("--delete", "delete_excl", nargs=2, type=str, help="删除排除: --delete channel model")
@pass_ctx
def models_excluded(ctx: Context, excl_data, delete_excl):
    """管理 OAuth 排除模型。"""
    try:
        if delete_excl:
            channel, model = delete_excl
            result = ctx.model_mgr.delete_oauth_excluded_models(channel, model)
        elif excl_data:
            import json as _json
            data = _json.loads(excl_data)
            result = ctx.model_mgr.put_oauth_excluded_models(data)
        else:
            result = ctx.model_mgr.get_oauth_excluded_models()
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


# ============================================================
# usage 命令组
# ============================================================

@main.group()
@pass_ctx
def usage(ctx: Context):
    """使用统计。"""


@usage.command("stats")
@pass_ctx
def usage_stats(ctx: Context):
    """获取使用统计。"""
    try:
        result = ctx.usage_mgr.get_stats()
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@usage.command("export")
@pass_ctx
def usage_export(ctx: Context):
    """导出统计数据。"""
    try:
        result = ctx.usage_mgr.export_stats()
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@usage.command("import")
@click.argument("data")
@pass_ctx
def usage_import(ctx: Context, data):
    """导入统计数据。"""
    try:
        result = ctx.usage_mgr.import_stats(data)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


# ============================================================
# logs 命令组
# ============================================================

@main.group()
@pass_ctx
def logs(ctx: Context):
    """日志管理。"""


@logs.command("list")
@click.option("--lines", "-n", default=100, help="显示行数")
@pass_ctx
def logs_list(ctx: Context, lines):
    """查看日志。"""
    try:
        result = ctx.log_mgr.get_logs(lines)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@logs.command("clear")
@pass_ctx
def logs_clear(ctx: Context):
    """清除日志。"""
    try:
        result = ctx.log_mgr.delete_logs()
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@logs.command("request")
@click.argument("value", type=bool, required=False)
@pass_ctx
def logs_request(ctx: Context, value):
    """获取或设置请求日志。"""
    try:
        if value is None:
            result = ctx.log_mgr.get_request_log()
        else:
            result = ctx.log_mgr.set_request_log(value)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@logs.command("errors")
@click.option("--download", "-d", "name", default=None, help="下载指定错误日志文件")
@pass_ctx
def logs_errors(ctx: Context, name):
    """查看或下载错误日志。"""
    try:
        if name:
            result = ctx.log_mgr.download_request_error_log(name)
        else:
            result = ctx.log_mgr.get_request_error_logs()
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@logs.command("by-id")
@click.argument("log_id")
@pass_ctx
def logs_by_id(ctx: Context, log_id):
    """按 ID 查看请求日志。"""
    try:
        result = ctx.log_mgr.get_request_log_by_id(log_id)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


# ============================================================
# amp 命令组
# ============================================================

@main.group()
@pass_ctx
def amp(ctx: Context):
    """Amp CLI 集成管理。"""


@amp.command("config")
@pass_ctx
def amp_config(ctx: Context):
    """查看 Amp 配置。"""
    try:
        result = ctx.proxy_mgr.get_amp_config()
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@amp.command("upstream-url")
@click.argument("value", required=False)
@click.option("--delete", is_flag=True, help="删除上游 URL")
@pass_ctx
def amp_upstream_url(ctx: Context, value, delete):
    """获取、设置或删除 Amp 上游 URL。"""
    try:
        if delete:
            result = ctx.proxy_mgr.delete_amp_upstream_url()
        elif value:
            result = ctx.proxy_mgr.set_amp_upstream_url(value)
        else:
            result = ctx.proxy_mgr.get_amp_upstream_url()
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@amp.command("upstream-api-key")
@click.argument("value", required=False)
@click.option("--delete", is_flag=True, help="删除上游 API 密钥")
@pass_ctx
def amp_upstream_api_key(ctx: Context, value, delete):
    """获取、设置或删除 Amp 上游 API 密钥。"""
    try:
        if delete:
            result = ctx.proxy_mgr.delete_amp_upstream_api_key()
        elif value:
            result = ctx.proxy_mgr.set_amp_upstream_api_key(value)
        else:
            result = ctx.proxy_mgr.get_amp_upstream_api_key()
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@amp.command("model-mappings")
@click.option("--set", "mappings_json", default=None, help="设置映射的 JSON")
@click.option("--add", "add_json", default=None, help="添加一条映射的 JSON")
@click.option("--delete", "delete_from", default=None, help="删除指定 from 模型的映射")
@pass_ctx
def amp_model_mappings(ctx: Context, mappings_json, add_json, delete_from):
    """管理 Amp 模型映射。"""
    try:
        if delete_from:
            result = ctx.proxy_mgr.delete_amp_model_mappings(delete_from)
        elif mappings_json:
            import json as _json
            data = _json.loads(mappings_json)
            result = ctx.proxy_mgr.set_amp_model_mappings(data)
        elif add_json:
            import json as _json
            data = _json.loads(add_json)
            result = ctx.proxy_mgr.patch_amp_model_mappings(data)
        else:
            result = ctx.proxy_mgr.get_amp_model_mappings()
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


@amp.command("force-model-mappings")
@click.argument("value", type=bool, required=False)
@pass_ctx
def amp_force_model_mappings(ctx: Context, value):
    """获取或设置强制模型映射。"""
    try:
        if value is None:
            result = ctx.proxy_mgr.get_amp_force_model_mappings()
        else:
            result = ctx.proxy_mgr.set_amp_force_model_mappings(value)
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


# ============================================================
# api-call 命令
# ============================================================

@main.command("api-call")
@click.option("--method", "-X", default="GET", help="HTTP 方法")
@click.option("--url", required=True, help="请求 URL")
@click.option("--header", "-H", multiple=True, help="请求头 (key:value)")
@click.option("--data", "-d", default=None, help="请求体")
@click.option("--auth-index", default=None, help="认证索引")
@pass_ctx
def api_call(ctx: Context, method, url, header, data, auth_index):
    """通过代理发起 HTTP 请求。"""
    try:
        headers = {}
        for h in header:
            if ":" in h:
                k, v = h.split(":", 1)
                headers[k.strip()] = v.strip()
        result = ctx.proxy_mgr.api_call(
            method=method,
            url=url,
            headers=headers or None,
            data=data,
            auth_index=auth_index,
        )
        output_result(result, ctx.json_mode)
    except Exception as e:
        handle_error(ctx, e)


if __name__ == "__main__":
    main()
