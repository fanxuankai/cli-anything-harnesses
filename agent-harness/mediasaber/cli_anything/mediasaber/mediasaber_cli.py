from __future__ import annotations

import json
import shlex
import sys
from dataclasses import dataclass, field
from typing import Any, Optional

import click

from .core.auth import AuthManager
from .core.cli_specs import CommandSpec, EXISTING_GROUP_SPECS, GroupSpec, NEW_GROUP_SPECS, ParamSpec
from .core.client import APIError, ConnectionConfig, MediaSaberClient
from .core.config import ConfigManager
from .core.downloader import DownloaderManager
from .core.media import MediaManager
from .core.site import SiteManager
from .core.system import SystemManager
from .utils.backend import BackendManager
from .utils.output import fail, output_result
from .utils.request_helpers import parse_file_pairs, parse_key_value_pairs, read_json_payload


@dataclass
class Context:
    json_mode: bool = False
    raw_mode: bool = False
    profile: str | None = None
    initialized: bool = False
    conn: Optional[ConnectionConfig] = None
    client: Optional[MediaSaberClient] = None
    config_mgr: ConfigManager = field(default_factory=ConfigManager)

    def setup(
        self,
        *,
        url: str | None = None,
        token: str | None = None,
        api_key: str | None = None,
        source_path: str | None = None,
        profile: str | None = None,
        force_reload: bool = False,
    ) -> None:
        should_reload = force_reload or not self.initialized or any(
            value is not None for value in (url, token, api_key, source_path, profile)
        )
        if not should_reload:
            return
        self.profile = profile or self.profile
        self.conn = ConnectionConfig.from_sources(
            url=url,
            token=token,
            api_key=api_key,
            source_path=source_path,
            profile=self.profile,
            config_mgr=self.config_mgr,
        )
        self.client = MediaSaberClient(self.conn)
        self.initialized = True

    def refresh(self) -> None:
        self.setup(profile=self.profile, force_reload=True)

    @property
    def auth_mgr(self) -> AuthManager:
        return AuthManager(self.client)

    @property
    def system_mgr(self) -> SystemManager:
        return SystemManager(self.client)

    @property
    def downloader_mgr(self) -> DownloaderManager:
        return DownloaderManager(self.client)

    @property
    def site_mgr(self) -> SiteManager:
        return SiteManager(self.client)

    @property
    def media_mgr(self) -> MediaManager:
        return MediaManager(self.client)


pass_ctx = click.make_pass_decorator(Context, ensure=True)


def _handle_error(ctx: Context, exc: Exception) -> None:
    fail(str(exc), json_mode=ctx.json_mode)


def _enter_repl(ctx: Context) -> None:
    click.echo("Media Saber REPL - 输入 help 查看帮助, exit 退出")
    try:
        import readline  # noqa: F401
    except ImportError:
        pass

    while True:
        try:
            line = input("mediasaber> ").strip()
        except (EOFError, KeyboardInterrupt):
            click.echo()
            break
        if not line:
            continue
        if line in {"exit", "quit"}:
            break
        args = shlex.split(line)
        if args == ["help"]:
            args = ["--help"]
        try:
            main.main(args=args, prog_name="cli-anything-mediasaber", standalone_mode=False, obj=ctx)
        except SystemExit:
            pass
        except Exception as exc:  # pragma: no cover - repl guard
            _handle_error(ctx, exc)


def _normalize_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return list(value)
    return value


def _is_missing(value: Any) -> bool:
    return value is None or value == () or value == []


def _apply_option(fn, spec: ParamSpec):
    option_kwargs: dict[str, Any] = {
        "required": spec.required,
        "multiple": spec.multiple,
        "help": spec.help,
    }
    if spec.is_flag:
        option_kwargs["is_flag"] = True
    else:
        option_kwargs["type"] = spec.click_type
    if spec.default is not None:
        option_kwargs["default"] = spec.default
    return click.option(*spec.flags, spec.key, **option_kwargs)(fn)


def _build_payload_parts(spec: CommandSpec, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any] | None, Any | None, dict[str, Any] | None]:
    path_values: dict[str, str] = {}
    params: dict[str, Any] = {}
    body_fields: dict[str, Any] = {}
    files: dict[str, Any] = {}
    handles = []
    try:
        for param in spec.args + spec.options:
            value = kwargs.pop(param.key, None)
            if _is_missing(value):
                continue
            value = _normalize_value(value)
            if param.target == "path":
                path_values[param.field_name] = str(value)
            elif param.target == "query":
                params[param.field_name] = value
            elif param.target == "body":
                body_fields[param.field_name] = value
            elif param.target == "file":
                handle = open(value, "rb")
                handles.append(handle)
                files[param.field_name] = handle

        extra_query = kwargs.pop("query_pairs", ())
        if extra_query:
            params.update(parse_key_value_pairs(extra_query))

        body = kwargs.pop("body", None)
        body_file = kwargs.pop("body_file", None)
        json_body = None
        if spec.body_mode == "json":
            raw_json = read_json_payload(body, body_file)
            if raw_json is not None and body_fields:
                if not isinstance(raw_json, dict):
                    raise click.ClickException("explicit body fields require JSON object payload")
                json_body = {**raw_json, **body_fields}
            elif raw_json is not None:
                json_body = raw_json
            elif body_fields:
                json_body = body_fields
        elif body or body_file:
            raise click.ClickException("this command does not accept --body or --body-file")

        path = spec.path.format(**path_values)
        return path, params or None, json_body, files or None
    except Exception:
        for handle in handles:
            handle.close()
        raise


def _close_files(files: dict[str, Any] | None) -> None:
    if not files:
        return
    for handle in files.values():
        try:
            handle.close()
        except Exception:
            pass


def _make_spec_command(spec: CommandSpec):
    @pass_ctx
    def command(ctx: Context, **kwargs):
        files = None
        try:
            timeout = kwargs.pop("timeout", spec.timeout)
            output_path = kwargs.pop("output_path", None)
            path, params, json_body, files = _build_payload_parts(spec, kwargs)
            result = ctx.client.request_result(
                spec.method,
                path,
                response_mode=spec.response_mode,
                unwrap_envelope=spec.unwrap_envelope and not ctx.raw_mode,
                params=params,
                json_data=json_body,
                files=files,
                public=spec.public,
                timeout=timeout,
                output_path=output_path,
                allow_redirects=spec.response_mode != "redirect",
            )
            output_result(result, json_mode=ctx.json_mode)
        except Exception as exc:
            _handle_error(ctx, exc)
        finally:
            _close_files(files)

    decorated = command
    if spec.allow_query_pairs:
        decorated = click.option("--query", "query_pairs", multiple=True, help="额外 query 参数，格式 key=value")(decorated)
    if spec.body_mode == "json":
        decorated = click.option("--body-file", type=click.Path(exists=True), help="从文件读取 JSON body")(decorated)
        decorated = click.option("--body", help="JSON 字符串 body")(decorated)
    if spec.supports_output:
        decorated = click.option("-o", "--output", "output_path", type=click.Path(), help="保存响应到文件")(decorated)
    decorated = click.option("--timeout", default=spec.timeout, show_default=True, type=int, help="请求超时秒数")(decorated)
    for option in reversed(spec.options):
        decorated = _apply_option(decorated, option)
    for argument in reversed(spec.args):
        decorated = click.argument(argument.key, type=argument.click_type)(decorated)
    return click.command(spec.name)(decorated)


def _register_group_specs(root_group, group_obj_map: dict[str, click.Group]):
    for group_spec in EXISTING_GROUP_SPECS:
        target = group_obj_map[group_spec.existing_group]
        for command_spec in group_spec.commands:
            target.add_command(_make_spec_command(command_spec))
    for group_spec in NEW_GROUP_SPECS:
        new_group = click.Group(name=group_spec.name, help=group_spec.help)
        for command_spec in group_spec.commands:
            new_group.add_command(_make_spec_command(command_spec))
        root_group.add_command(new_group)


@click.group(invoke_without_command=True)
@click.option("--url", help="Media Saber 服务地址")
@click.option("--token", help="用户 token")
@click.option("--api-key", "api_key", help="用户 apiKey")
@click.option("--source", "source_path", help="Media Saber 源码目录")
@click.option("--profile", help="加载本地 profile")
@click.option("--json", "json_mode", is_flag=True, help="JSON 输出")
@click.option("--raw", "raw_mode", is_flag=True, help="尽量返回未解包响应")
@click.option("--repl", "repl_mode", is_flag=True, help="进入 REPL")
@click.version_option(version="1.0.0", prog_name="cli-anything-mediasaber")
@click.pass_context
def main(click_ctx, url, token, api_key, source_path, profile, json_mode, raw_mode, repl_mode):
    """Media Saber CLI harness。"""
    ctx = click_ctx.obj if isinstance(click_ctx.obj, Context) else Context()
    click_ctx.obj = ctx
    if json_mode:
        ctx.json_mode = True
    if raw_mode:
        ctx.raw_mode = True
    ctx.setup(
        url=url,
        token=token,
        api_key=api_key,
        source_path=source_path,
        profile=profile,
    )

    if click_ctx.invoked_subcommand is None:
        if repl_mode or sys.stdin.isatty():
            _enter_repl(ctx)
        else:
            click.echo(click_ctx.get_help())


@main.group()
@pass_ctx
def session(ctx: Context):
    """本地会话与 profile 管理。"""


@session.command("show")
@pass_ctx
def session_show(ctx: Context):
    config = ctx.config_mgr.load()
    result = {
        "current": ctx.conn.as_dict(),
        "profiles": sorted(config.profiles.keys()),
        "history_depth": len(config.history),
        "redo_depth": len(config.future),
    }
    output_result(result, json_mode=ctx.json_mode)


@session.command("set")
@click.option("--url")
@click.option("--token")
@click.option("--api-key", "api_key")
@click.option("--source", "source_path")
@pass_ctx
def session_set(ctx: Context, url, token, api_key, source_path):
    updates = {}
    for key, value in {
        "url": url,
        "token": token,
        "api_key": api_key,
        "source_path": source_path,
    }.items():
        if value is not None:
            updates[key] = value
    if not updates:
        fail("nothing to update", json_mode=ctx.json_mode)
    ctx.config_mgr.update_state(**updates)
    ctx.refresh()
    output_result({"updated": updates, "current": ctx.conn.as_dict()}, json_mode=ctx.json_mode)


@session.command("clear-token")
@pass_ctx
def session_clear_token(ctx: Context):
    ctx.config_mgr.clear_state("token")
    ctx.refresh()
    output_result({"cleared": ["token"], "current": ctx.conn.as_dict()}, json_mode=ctx.json_mode)


@session.command("save-profile")
@click.argument("name")
@pass_ctx
def session_save_profile(ctx: Context, name):
    ctx.config_mgr.save_profile(name, ctx.conn.as_dict())
    output_result({"saved_profile": name, "state": ctx.conn.as_dict()}, json_mode=ctx.json_mode)


@session.command("use-profile")
@click.argument("name")
@pass_ctx
def session_use_profile(ctx: Context, name):
    try:
        ctx.config_mgr.use_profile(name)
    except KeyError as exc:
        _handle_error(ctx, exc)
    ctx.profile = name
    ctx.refresh()
    output_result({"profile": name, "current": ctx.conn.as_dict()}, json_mode=ctx.json_mode)


@session.command("undo")
@pass_ctx
def session_undo(ctx: Context):
    try:
        state = ctx.config_mgr.undo()
    except ValueError as exc:
        _handle_error(ctx, exc)
    ctx.refresh()
    output_result({"undone_to": state, "current": ctx.conn.as_dict()}, json_mode=ctx.json_mode)


@session.command("redo")
@pass_ctx
def session_redo(ctx: Context):
    try:
        state = ctx.config_mgr.redo()
    except ValueError as exc:
        _handle_error(ctx, exc)
    ctx.refresh()
    output_result({"redone_to": state, "current": ctx.conn.as_dict()}, json_mode=ctx.json_mode)


@main.group()
@pass_ctx
def server(ctx: Context):
    """Media Saber 服务与本地后端进程管理。"""


@server.command("ping")
@pass_ctx
def server_ping(ctx: Context):
    try:
        result = {"reachable": True, "init_admin_status": ctx.client.ping()}
        output_result(result, json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@server.command("start")
@click.option("--config-file", help="传给 mediasaber.go 的配置文件")
@pass_ctx
def server_start(ctx: Context, config_file):
    try:
        result = BackendManager().start(ctx.conn.source_path, config_file=config_file)
        output_result(result, json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@server.command("stop")
@pass_ctx
def server_stop(ctx: Context):
    try:
        result = BackendManager().stop()
        output_result(result, json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@server.command("backend-status")
@pass_ctx
def server_backend_status(ctx: Context):
    output_result(BackendManager().status(), json_mode=ctx.json_mode)


@server.command("logs")
@click.option("--lines", default=40, show_default=True, type=int)
@pass_ctx
def server_logs(ctx: Context, lines):
    output_result(BackendManager().logs(lines=lines), json_mode=ctx.json_mode)


@main.group()
@pass_ctx
def auth(ctx: Context):
    """认证相关命令。"""


@auth.command("init-admin")
@pass_ctx
def auth_init_admin(ctx: Context):
    try:
        output_result({"initialized": ctx.auth_mgr.init_admin_status()}, json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@auth.command("login")
@click.argument("user_name")
@click.argument("password")
@click.option("--device-type", default="cli", show_default=True)
@click.option("--device-name")
@click.option("--backend-domain")
@click.option("--no-save", is_flag=True, help="不要把 token 写入本地配置")
@pass_ctx
def auth_login(ctx: Context, user_name, password, device_type, device_name, backend_domain, no_save):
    try:
        token = ctx.auth_mgr.login(
            user_name,
            password,
            device_type=device_type,
            device_name=device_name,
            backend_domain=backend_domain,
        )
        if not no_save:
            ctx.config_mgr.update_state(token=token)
            ctx.refresh()
        output_result({"token": token, "saved": not no_save}, json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@auth.command("whoami")
@pass_ctx
def auth_whoami(ctx: Context):
    try:
        output_result(ctx.auth_mgr.whoami(), json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@auth.command("logout")
@pass_ctx
def auth_logout(ctx: Context):
    try:
        result = ctx.auth_mgr.logout()
        ctx.config_mgr.clear_state("token")
        ctx.refresh()
        output_result({"result": result, "token_cleared": True}, json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@auth.command("tokens")
@pass_ctx
def auth_tokens(ctx: Context):
    try:
        output_result(ctx.auth_mgr.tokens(), json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@main.group()
@pass_ctx
def system(ctx: Context):
    """系统配置和系统状态。"""


@system.command("status")
@pass_ctx
def system_status(ctx: Context):
    try:
        output_result(ctx.system_mgr.status(), json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@system.command("space")
@pass_ctx
def system_space(ctx: Context):
    try:
        output_result(ctx.system_mgr.space(), json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@system.command("basic-config")
@pass_ctx
def system_basic_config(ctx: Context):
    try:
        output_result(ctx.system_mgr.basic_config(), json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@system.command("basic-config-part")
@click.argument("keys", nargs=-1)
@pass_ctx
def system_basic_config_part(ctx: Context, keys):
    try:
        output_result(ctx.system_mgr.basic_config_part(list(keys)), json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@system.command("task-schedule")
@pass_ctx
def system_task_schedule(ctx: Context):
    try:
        output_result(ctx.system_mgr.task_schedule(), json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@system.command("upgrade-version")
@pass_ctx
def system_upgrade_version(ctx: Context):
    try:
        output_result(ctx.system_mgr.upgrade_version(), json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@system.command("path-ls")
@click.argument("path")
@pass_ctx
def system_path_ls(ctx: Context, path):
    try:
        output_result(ctx.system_mgr.path_ls(path), json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@main.group()
@pass_ctx
def downloader(ctx: Context):
    """下载器相关命令。"""


@downloader.command("list")
@pass_ctx
def downloader_list(ctx: Context):
    try:
        output_result(ctx.downloader_mgr.list_downloaders(), json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@downloader.command("detail")
@click.argument("downloader_id", type=int)
@pass_ctx
def downloader_detail(ctx: Context, downloader_id):
    try:
        output_result(ctx.downloader_mgr.detail(downloader_id), json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@downloader.command("types")
@pass_ctx
def downloader_types(ctx: Context):
    try:
        output_result(ctx.downloader_mgr.types(), json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@downloader.command("delete-qb-tags")
@pass_ctx
def downloader_delete_qb_tags(ctx: Context):
    try:
        output_result(ctx.downloader_mgr.delete_qb_tags(), json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@main.group()
@pass_ctx
def directory(ctx: Context):
    """目录与分类相关命令。"""


@directory.command("list")
@click.option("--name")
@click.option("--tag")
@pass_ctx
def directory_list(ctx: Context, name, tag):
    try:
        output_result(ctx.downloader_mgr.directory_list(name=name, tag=tag), json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@directory.command("match")
@click.option("--tmdb-id", "tmdb_id", type=int, required=True)
@click.option("--media-type", required=True)
@click.option("--dir-tag")
@pass_ctx
def directory_match(ctx: Context, tmdb_id, media_type, dir_tag):
    try:
        output_result(
            ctx.downloader_mgr.directory_match(tmdb_id=tmdb_id, media_type=media_type, dir_tag=dir_tag),
            json_mode=ctx.json_mode,
        )
    except Exception as exc:
        _handle_error(ctx, exc)


@directory.command("tags")
@pass_ctx
def directory_tags(ctx: Context):
    try:
        output_result(ctx.downloader_mgr.directory_tags(), json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@directory.command("mkdir")
@click.argument("directory_id", type=int)
@pass_ctx
def directory_mkdir(ctx: Context, directory_id):
    try:
        output_result(ctx.downloader_mgr.directory_mkdir(directory_id), json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@directory.command("categories")
@pass_ctx
def directory_categories(ctx: Context):
    try:
        output_result(ctx.downloader_mgr.directory_categories(), json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@directory.command("subcategory-options")
@pass_ctx
def directory_subcategory_options(ctx: Context):
    try:
        output_result(ctx.downloader_mgr.directory_subcategory_options(), json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@directory.command("subcategory-list")
@click.option("--category-id", type=int)
@pass_ctx
def directory_subcategory_list(ctx: Context, category_id):
    try:
        output_result(ctx.downloader_mgr.directory_subcategory_list(category_id=category_id), json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@main.group()
@pass_ctx
def site(ctx: Context):
    """站点相关命令。"""


@site.command("list")
@click.option("--name")
@click.option("--enabled/--disabled", default=None)
@click.option("--type", "site_type", type=int)
@pass_ctx
def site_list(ctx: Context, name, enabled, site_type):
    try:
        output_result(
            ctx.site_mgr.list_sites(name=name, enabled=enabled, site_type=site_type),
            json_mode=ctx.json_mode,
        )
    except Exception as exc:
        _handle_error(ctx, exc)


@site.command("options")
@pass_ctx
def site_options(ctx: Context):
    try:
        output_result(ctx.site_mgr.options(), json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@site.command("rss")
@click.argument("site_id", type=int)
@pass_ctx
def site_rss(ctx: Context, site_id):
    try:
        output_result(ctx.site_mgr.rss(site_id), json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@site.command("rss-torrents")
@click.argument("site_id", type=int)
@pass_ctx
def site_rss_torrents(ctx: Context, site_id):
    try:
        output_result(ctx.site_mgr.rss_torrents(site_id), json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@main.group()
@pass_ctx
def media(ctx: Context):
    """媒体搜索相关命令。"""


@media.command("sources")
@pass_ctx
def media_sources(ctx: Context):
    try:
        output_result(ctx.media_mgr.sources(), json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@media.command("search")
@click.argument("keyword")
@click.option("--media-source", default=1, show_default=True, type=int)
@click.option("--page-num", default=1, show_default=True, type=int)
@click.option("--page-size", default=20, show_default=True, type=int)
@pass_ctx
def media_search(ctx: Context, keyword, media_source, page_num, page_size):
    try:
        output_result(
            ctx.media_mgr.search(keyword, media_source=media_source, page_num=page_num, page_size=page_size),
            json_mode=ctx.json_mode,
        )
    except Exception as exc:
        _handle_error(ctx, exc)


@media.command("search-all")
@click.argument("keyword")
@click.option("--page-num", default=1, show_default=True, type=int)
@click.option("--page-size", default=20, show_default=True, type=int)
@pass_ctx
def media_search_all(ctx: Context, keyword, page_num, page_size):
    try:
        output_result(
            ctx.media_mgr.search_all(keyword, page_num=page_num, page_size=page_size),
            json_mode=ctx.json_mode,
        )
    except Exception as exc:
        _handle_error(ctx, exc)


@media.command("autosuggest")
@click.argument("query")
@pass_ctx
def media_autosuggest(ctx: Context, query):
    try:
        output_result(ctx.media_mgr.autosuggest(query), json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@main.group(name="ai")
@pass_ctx
def ai_group(ctx: Context):
    """AI 能力。"""


@ai_group.command("models")
@click.option("--timeout", default=30, show_default=True, type=int)
@pass_ctx
def ai_models(ctx: Context, timeout):
    try:
        result = ctx.client.request_result("GET", "/ai/v1/models", response_mode="json", unwrap_envelope=False, timeout=timeout)
        output_result(result, json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@ai_group.command("completions")
@click.option("--body", help="JSON 字符串 body")
@click.option("--body-file", type=click.Path(exists=True), help="从文件读取 JSON body")
@click.option("--timeout", default=300, show_default=True, type=int)
@pass_ctx
def ai_completions(ctx: Context, body, body_file, timeout):
    try:
        payload = read_json_payload(body, body_file)
        result = ctx.client.request_result(
            "POST",
            "/ai/v1/chat/completions",
            response_mode="json",
            unwrap_envelope=False,
            json_data=payload,
            timeout=timeout,
        )
        output_result(result, json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)


@main.command("api")
@click.argument("method", type=click.Choice(["GET", "POST", "PUT", "PATCH", "DELETE"], case_sensitive=False))
@click.argument("path")
@click.option("--public", is_flag=True, help="不带认证头")
@click.option("--query", "query_pairs", multiple=True, help="query 参数，格式 key=value")
@click.option("--header", "header_pairs", multiple=True, help="请求头，格式 key=value")
@click.option("--form", "form_pairs", multiple=True, help="表单字段，格式 key=value")
@click.option("--file", "file_pairs", multiple=True, help="上传文件，格式 field=/path/to/file")
@click.option("--body", help="JSON 字符串 body")
@click.option("--body-file", type=click.Path(exists=True), help="从文件读取 JSON body")
@click.option("--response-mode", type=click.Choice(["auto", "json", "text", "content", "redirect"]), default="auto", show_default=True)
@click.option("-o", "--output", "output_path", type=click.Path(), help="保存响应到文件")
@click.option("--timeout", default=30, show_default=True, type=int)
@pass_ctx
def api_call(ctx: Context, method, path, public, query_pairs, header_pairs, form_pairs, file_pairs, body, body_file, response_mode, output_path, timeout):
    files = None
    try:
        params = parse_key_value_pairs(query_pairs) if query_pairs else None
        headers = parse_key_value_pairs(header_pairs) if header_pairs else None
        raw_body = read_json_payload(body, body_file)
        form_data = parse_key_value_pairs(form_pairs) if form_pairs else None
        file_map = parse_file_pairs(file_pairs) if file_pairs else None
        if raw_body is not None and form_data:
            raise click.ClickException("use JSON body or form fields, not both")
        if file_map and raw_body is not None:
            raise click.ClickException("file upload cannot be combined with JSON body")
        if file_map:
            files = {field: open(file_path, "rb") for field, file_path in file_map.items()}
        result = ctx.client.request_result(
            method,
            path,
            response_mode=response_mode,
            unwrap_envelope=not ctx.raw_mode,
            params=params,
            json_data=raw_body,
            data=form_data,
            files=files,
            headers=headers,
            public=public,
            timeout=timeout,
            output_path=output_path,
            allow_redirects=response_mode != "redirect",
        )
        output_result(result, json_mode=ctx.json_mode)
    except Exception as exc:
        _handle_error(ctx, exc)
    finally:
        _close_files(files)


_register_group_specs(
    main,
    {
        "system": system,
        "downloader": downloader,
        "directory": directory,
        "site": site,
        "media": media,
    },
)


if __name__ == "__main__":
    main()
