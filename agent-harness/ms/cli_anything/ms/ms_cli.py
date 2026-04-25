"""ms CLI 入口 - 基于 Click 的命令行工具。

支持 REPL 模式和一次性命令，所有业务命令支持 --json 输出。
"""

from __future__ import annotations

import json
import shlex
import sys
from typing import Optional

import click

from . import __version__
from .core.client import ConnectionConfig, MSClient
from .core.cloud_resource import MEDIA_TYPE_CHOICES as CLOUD_RESOURCE_MEDIA_TYPE_CHOICES
from .core.cloud_resource import CloudResourceManager
from .core.media import MEDIA_RANK_SOURCE_MAP, MEDIA_RECOMMEND_SOURCE_MAP, MEDIA_SOURCE_MAP, MediaManager
from .core.media_server import MediaServerManager
from .core.subscribe import MEDIA_TYPE_CHOICES as SUBSCRIBE_MEDIA_TYPE_CHOICES
from .core.subscribe import SubscribeManager
from .utils.output import (
    output_cloud_resource_download,
    output_cloud_resource_search,
    output_connection,
    output_error,
    output_json,
    output_media_rank_categories,
    output_media_rank_items,
    output_media_rank_sources,
    output_media_rank_subjects,
    output_media_recommend_channels,
    output_media_recommend_items,
    output_media_recommend_options,
    output_media_recommend_sources,
    output_media_search,
    output_media_server_miss_episodes,
    output_plugin_call,
    output_subscribe_add,
    output_subscribe_page,
)


# ---- 全局上下文 ----


class Context:
    """CLI 运行时上下文。"""

    def __init__(self) -> None:
        self.json_mode = False
        self.in_repl = False
        self.conn: Optional[ConnectionConfig] = None
        self.client: Optional[MSClient] = None
        self._media_mgr: Optional[MediaManager] = None
        self._media_server_mgr: Optional[MediaServerManager] = None
        self._subscribe_mgr: Optional[SubscribeManager] = None
        self._cloud_resource_mgr: Optional[CloudResourceManager] = None

    def setup(self, url: Optional[str], apikey: Optional[str]) -> None:
        self.conn = ConnectionConfig.resolve(url=url, api_key=apikey)
        self.client = MSClient(self.conn)
        self._media_mgr = None
        self._media_server_mgr = None
        self._subscribe_mgr = None
        self._cloud_resource_mgr = None

    @property
    def media_mgr(self) -> MediaManager:
        if self.client is None:
            raise ValueError("Client is not initialized")
        if self._media_mgr is None:
            self._media_mgr = MediaManager(self.client)
        return self._media_mgr

    @property
    def media_server_mgr(self) -> MediaServerManager:
        if self.client is None:
            raise ValueError("Client is not initialized")
        if self._media_server_mgr is None:
            self._media_server_mgr = MediaServerManager(self.client)
        return self._media_server_mgr

    @property
    def subscribe_mgr(self) -> SubscribeManager:
        if self.client is None:
            raise ValueError("Client is not initialized")
        if self._subscribe_mgr is None:
            self._subscribe_mgr = SubscribeManager(self.client)
        return self._subscribe_mgr

    @property
    def cloud_resource_mgr(self) -> CloudResourceManager:
        if self.client is None:
            raise ValueError("Client is not initialized")
        if self._cloud_resource_mgr is None:
            self._cloud_resource_mgr = CloudResourceManager(self.client)
        return self._cloud_resource_mgr


pass_ctx = click.make_pass_decorator(Context, ensure=True)


def handle_error(ctx: Context, exc: Exception) -> None:
    if ctx.json_mode:
        output_json({"error": str(exc)})
    else:
        output_error(str(exc))
    raise SystemExit(1)


def _parse_plugin_body(body: str) -> dict:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise click.UsageError(f"--body must be valid JSON: {exc.msg}") from exc

    if not isinstance(payload, dict):
        raise click.UsageError("--body must be a JSON object")

    action = payload.get("action")
    if not isinstance(action, str) or not action.strip():
        raise click.UsageError("--body.action must be a non-empty string")

    nested_body = payload.get("body")
    if nested_body is not None and not isinstance(nested_body, dict):
        raise click.UsageError("--body.body must be a JSON object")

    payload["action"] = action.strip()
    return payload


def _parse_json_object_option(raw: str, option_name: str) -> dict:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise click.UsageError(f"{option_name} must be valid JSON: {exc.msg}") from exc

    if not isinstance(payload, dict):
        raise click.UsageError(f"{option_name} must be a JSON object")

    return payload


# ---- 根命令组 ----

@click.group(invoke_without_command=True)
@click.option("--url", "-u", envvar="MS_URL", help="ms base URL")
@click.option("--apikey", "-k", envvar="MS_API_KEY", help="ms API key")
@click.option("--json", "json_mode", is_flag=True, help="Output normalized JSON")
@click.option("--repl", "repl_mode", is_flag=True, help="Enter interactive REPL")
@click.version_option(version=__version__, prog_name="cli-anything-ms")
@click.pass_context
def main(click_ctx: click.Context, url: Optional[str], apikey: Optional[str], json_mode: bool, repl_mode: bool) -> None:
    """ms 命令行工具。

    通过本地 CLI 统一调用 ms 能力，当前聚焦连接配置、媒体搜索、媒体服务检查、插件调用和影视订阅。

    连接参数优先级: --url/--apikey > 环境变量 MS_URL/MS_API_KEY > ~/.ms-cli.yaml
    """
    ctx = click_ctx.ensure_object(Context)
    ctx.json_mode = json_mode
    ctx.setup(url, apikey)

    interactive = sys.stdin.isatty() and sys.stdout.isatty()
    should_repl = repl_mode or (
        click_ctx.invoked_subcommand is None and interactive and not ctx.in_repl
    )

    if should_repl:
        _enter_repl(ctx)
    elif click_ctx.invoked_subcommand is None:
        click.echo(click_ctx.get_help())


def _enter_repl(ctx: Context) -> None:
    """交互式 REPL 模式。"""
    ctx.in_repl = True
    click.echo("ms REPL. 输入 help 查看帮助，exit 退出。")

    while True:
        try:
            line = input("ms> ")
        except (EOFError, KeyboardInterrupt):
            click.echo()
            break

        line = line.strip()
        if not line:
            continue
        if line in {"exit", "quit"}:
            break
        if line == "help":
            click.echo(main.get_help(click.Context(main, obj=ctx)))
            continue

        try:
            args = shlex.split(line)
            main(args, standalone_mode=False, obj=ctx)
        except SystemExit:
            continue
        except Exception as exc:  # pragma: no cover - safety path
            output_error(str(exc))


#
# config 命令组
#

@main.group()
@pass_ctx
def config(ctx: Context) -> None:
    """连接配置管理。"""


@config.command("save-connection")
@click.option("--url", "-u", required=True, help="ms base URL")
@click.option("--apikey", "-k", required=True, help="ms API key")
@pass_ctx
def save_connection(ctx: Context, url: str, apikey: str) -> None:
    """保存连接参数到 ~/.ms-cli.yaml。"""
    try:
        config_path = ConnectionConfig.save(url, apikey)
        output_connection(
            {
                "status": "ok",
                "saved_to": str(config_path),
                "base_url": url.rstrip("/"),
                "api_key": ConnectionConfig.resolve(url=url, api_key=apikey).masked_api_key,
            },
            json_mode=ctx.json_mode,
        )
    except Exception as exc:
        handle_error(ctx, exc)


@config.command("show-connection")
@pass_ctx
def show_connection(ctx: Context) -> None:
    """显示当前生效的连接配置。"""
    try:
        if ctx.conn is None:
            raise ValueError("Connection state is unavailable")
        output_connection(ctx.conn.as_display_dict(), json_mode=ctx.json_mode)
    except Exception as exc:
        handle_error(ctx, exc)


#
# media 命令组
#

@main.group()
@pass_ctx
def media(ctx: Context) -> None:
    """媒体搜索命令。"""


@media.command("search")
@click.option(
    "--source",
    type=click.Choice(sorted(MEDIA_SOURCE_MAP.keys()), case_sensitive=False),
    required=True,
    help="Media source name",
)
@click.option("--keyword", required=True, help="Search keyword")
@click.option("--page", type=click.IntRange(min=1), default=1, show_default=True, help="Page number")
@click.option(
    "--page-size",
    type=click.IntRange(min=1),
    default=20,
    show_default=True,
    help="Page size",
)
@pass_ctx
def media_search(ctx: Context, source: str, keyword: str, page: int, page_size: int) -> None:
    """按来源和关键字搜索媒体。"""
    try:
        if ctx.conn is None:
            raise ValueError("Connection state is unavailable")
        ctx.conn.require_configured()
        if not keyword.strip():
            raise click.UsageError("--keyword cannot be empty")

        source_key = source.lower()
        result = ctx.media_mgr.search(
            source_code=MEDIA_SOURCE_MAP[source_key],
            keyword=keyword.strip(),
            page=page,
            page_size=page_size,
        )

        if ctx.json_mode:
            output_json(result)
        else:
            output_media_search(result, source=source_key, keyword=keyword)
    except SystemExit:
        raise
    except Exception as exc:
        handle_error(ctx, exc)


@media.group("rank")
@pass_ctx
def media_rank(ctx: Context) -> None:
    """媒体榜单命令。"""


@media_rank.command("sources")
@pass_ctx
def media_rank_sources(ctx: Context) -> None:
    """获取榜单来源。"""
    try:
        if ctx.conn is None:
            raise ValueError("Connection state is unavailable")
        ctx.conn.require_configured()

        result = ctx.media_mgr.rank_sources()

        if ctx.json_mode:
            output_json(result)
        else:
            output_media_rank_sources(result)
    except SystemExit:
        raise
    except Exception as exc:
        handle_error(ctx, exc)


@media_rank.command("categories")
@click.option(
    "--source",
    type=click.Choice(sorted(MEDIA_RANK_SOURCE_MAP.keys()), case_sensitive=False),
    required=True,
    help="Media rank source name",
)
@pass_ctx
def media_rank_categories(ctx: Context, source: str) -> None:
    """按榜单来源获取分类。"""
    try:
        if ctx.conn is None:
            raise ValueError("Connection state is unavailable")
        ctx.conn.require_configured()

        source_key = source.lower()
        result = ctx.media_mgr.rank_categories(MEDIA_RANK_SOURCE_MAP[source_key])

        if ctx.json_mode:
            output_json(result)
        else:
            output_media_rank_categories(result, source=source_key)
    except SystemExit:
        raise
    except Exception as exc:
        handle_error(ctx, exc)


@media_rank.command("subjects")
@click.option("--category-code", required=True, help="Media rank category code")
@pass_ctx
def media_rank_subjects(ctx: Context, category_code: str) -> None:
    """按榜单分类获取主题。"""
    try:
        if ctx.conn is None:
            raise ValueError("Connection state is unavailable")
        ctx.conn.require_configured()

        category_code = category_code.strip()
        if not category_code:
            raise click.UsageError("--category-code cannot be empty")

        result = ctx.media_mgr.rank_subjects(category_code)

        if ctx.json_mode:
            output_json(result)
        else:
            output_media_rank_subjects(result, category_code=category_code)
    except SystemExit:
        raise
    except Exception as exc:
        handle_error(ctx, exc)


@media_rank.command("items")
@click.option("--category-code", required=True, help="Media rank category code")
@click.option("--code", required=True, help="Media rank subject code")
@click.option("--page", type=click.IntRange(min=1), default=1, show_default=True, help="Page number")
@click.option(
    "--page-size",
    type=click.IntRange(min=1),
    default=20,
    show_default=True,
    help="Page size",
)
@pass_ctx
def media_rank_items(ctx: Context, category_code: str, code: str, page: int, page_size: int) -> None:
    """按榜单主题获取条目。"""
    try:
        if ctx.conn is None:
            raise ValueError("Connection state is unavailable")
        ctx.conn.require_configured()

        category_code = category_code.strip()
        code = code.strip()
        if not category_code:
            raise click.UsageError("--category-code cannot be empty")
        if not code:
            raise click.UsageError("--code cannot be empty")

        result = ctx.media_mgr.rank_items(
            category_code=category_code,
            code=code,
            page=page,
            page_size=page_size,
        )

        if ctx.json_mode:
            output_json(result)
        else:
            output_media_rank_items(result, category_code=category_code, code=code)
    except SystemExit:
        raise
    except Exception as exc:
        handle_error(ctx, exc)


@media.group("recommend")
@pass_ctx
def media_recommend(ctx: Context) -> None:
    """媒体推荐命令。"""


@media_recommend.command("sources")
@pass_ctx
def media_recommend_sources(ctx: Context) -> None:
    """获取推荐来源。"""
    try:
        if ctx.conn is None:
            raise ValueError("Connection state is unavailable")
        ctx.conn.require_configured()

        result = ctx.media_mgr.recommend_sources()

        if ctx.json_mode:
            output_json(result)
        else:
            output_media_recommend_sources(result)
    except SystemExit:
        raise
    except Exception as exc:
        handle_error(ctx, exc)


@media_recommend.command("channels")
@click.option(
    "--source",
    type=click.Choice(sorted(MEDIA_RECOMMEND_SOURCE_MAP.keys()), case_sensitive=False),
    required=True,
    help="Media recommend source name",
)
@pass_ctx
def media_recommend_channels(ctx: Context, source: str) -> None:
    """按推荐来源获取频道。"""
    try:
        if ctx.conn is None:
            raise ValueError("Connection state is unavailable")
        ctx.conn.require_configured()

        source_key = source.lower()
        result = ctx.media_mgr.recommend_channels(MEDIA_RECOMMEND_SOURCE_MAP[source_key])

        if ctx.json_mode:
            output_json(result)
        else:
            output_media_recommend_channels(result, source=source_key)
    except SystemExit:
        raise
    except Exception as exc:
        handle_error(ctx, exc)


@media_recommend.command("options")
@click.option(
    "--source",
    type=click.Choice(sorted(MEDIA_RECOMMEND_SOURCE_MAP.keys()), case_sensitive=False),
    required=True,
    help="Media recommend source name",
)
@click.option("--channel", required=True, help="Media recommend channel")
@pass_ctx
def media_recommend_options(ctx: Context, source: str, channel: str) -> None:
    """按推荐来源和频道获取动态选项。"""
    try:
        if ctx.conn is None:
            raise ValueError("Connection state is unavailable")
        ctx.conn.require_configured()

        source_key = source.lower()
        channel = channel.strip()
        if not channel:
            raise click.UsageError("--channel cannot be empty")

        result = ctx.media_mgr.recommend_options(
            media_source=MEDIA_RECOMMEND_SOURCE_MAP[source_key],
            channel=channel,
        )

        if ctx.json_mode:
            output_json(result)
        else:
            output_media_recommend_options(result, source=source_key, channel=channel)
    except SystemExit:
        raise
    except Exception as exc:
        handle_error(ctx, exc)


@media_recommend.command("items")
@click.option(
    "--source",
    type=click.Choice(sorted(MEDIA_RECOMMEND_SOURCE_MAP.keys()), case_sensitive=False),
    required=True,
    help="Media recommend source name",
)
@click.option("--channel", required=True, help="Media recommend channel")
@click.option("--options", "options_json", help="Media recommend options JSON object")
@click.option("--page", type=click.IntRange(min=1), default=1, show_default=True, help="Page number")
@click.option(
    "--page-size",
    type=click.IntRange(min=1),
    default=20,
    show_default=True,
    help="Page size",
)
@pass_ctx
def media_recommend_items(
    ctx: Context,
    source: str,
    channel: str,
    options_json: Optional[str],
    page: int,
    page_size: int,
) -> None:
    """按推荐来源、频道和动态选项获取推荐条目。"""
    try:
        if ctx.conn is None:
            raise ValueError("Connection state is unavailable")
        ctx.conn.require_configured()

        source_key = source.lower()
        channel = channel.strip()
        if not channel:
            raise click.UsageError("--channel cannot be empty")

        options = {} if not options_json else _parse_json_object_option(options_json, "--options")
        result = ctx.media_mgr.recommend_items(
            media_source=MEDIA_RECOMMEND_SOURCE_MAP[source_key],
            channel=channel,
            options=options,
            page=page,
            page_size=page_size,
        )

        if ctx.json_mode:
            output_json(result)
        else:
            output_media_recommend_items(result, source=source_key, channel=channel)
    except SystemExit:
        raise
    except Exception as exc:
        handle_error(ctx, exc)


#
# media-server 命令组
#

@main.group("media-server")
@pass_ctx
def media_server(ctx: Context) -> None:
    """媒体服务命令。"""


@media_server.command("miss-episodes-check")
@pass_ctx
def media_server_miss_episodes_check(ctx: Context) -> None:
    """检查媒体服务中的电视剧漏集情况。"""
    try:
        if ctx.conn is None:
            raise ValueError("Connection state is unavailable")
        ctx.conn.require_configured()

        result = ctx.media_server_mgr.miss_episodes_check()

        if ctx.json_mode:
            output_json(result)
        else:
            output_media_server_miss_episodes(result)
    except SystemExit:
        raise
    except Exception as exc:
        handle_error(ctx, exc)


#
# cloud-resource 命令组
#

@main.group("cloud-resource")
@pass_ctx
def cloud_resource(ctx: Context) -> None:
    """云端资源搜索和下载命令。"""


@cloud_resource.command("search")
@click.option("--keyword", help="Keyword filter")
@click.option("--tmdb-id", type=click.IntRange(min=1), help="TMDB ID")
@click.option(
    "--type",
    "media_type",
    type=click.Choice(CLOUD_RESOURCE_MEDIA_TYPE_CHOICES, case_sensitive=False),
    help="Media type for TMDB searches",
)
@click.option("--season", type=click.IntRange(min=1), help="Season number")
@click.option("--episode", type=click.IntRange(min=1), help="Episode number")
@click.option("--begin-episode", type=click.IntRange(min=1), help="Begin episode number")
@click.option("--end-episode", type=click.IntRange(min=1), help="End episode number")
@click.option("--creator-id", type=click.IntRange(min=1), help="Cloud resource creator ID")
@click.option("--page", type=click.IntRange(min=1), default=1, show_default=True, help="Page number")
@click.option(
    "--page-size",
    type=click.IntRange(min=1),
    default=25,
    show_default=True,
    help="Page size",
)
@pass_ctx
def cloud_resource_search(
    ctx: Context,
    keyword: Optional[str],
    tmdb_id: Optional[int],
    media_type: Optional[str],
    season: Optional[int],
    episode: Optional[int],
    begin_episode: Optional[int],
    end_episode: Optional[int],
    creator_id: Optional[int],
    page: int,
    page_size: int,
) -> None:
    """搜索云端资源。"""
    try:
        if ctx.conn is None:
            raise ValueError("Connection state is unavailable")
        ctx.conn.require_configured()

        result = ctx.cloud_resource_mgr.search(
            keyword=keyword,
            tmdb_id=tmdb_id,
            media_type=media_type.lower() if media_type else None,
            season=season,
            episode=episode,
            begin_episode=begin_episode,
            end_episode=end_episode,
            creator_id=creator_id,
            page=page,
            page_size=page_size,
        )

        if ctx.json_mode:
            output_json(result)
        else:
            output_cloud_resource_search(result)
    except SystemExit:
        raise
    except Exception as exc:
        handle_error(ctx, exc)


@cloud_resource.command("download")
@click.option("--request", "request_json", required=True, help="Download request JSON from search result")
@click.option("--dir", "dir_path", help="Target cloud storage directory. Empty uses backend default")
@pass_ctx
def cloud_resource_download(ctx: Context, request_json: str, dir_path: Optional[str]) -> None:
    """提交云端资源下载或转存任务。"""
    try:
        if ctx.conn is None:
            raise ValueError("Connection state is unavailable")
        ctx.conn.require_configured()

        request = _parse_json_object_option(request_json, "--request")
        result = ctx.cloud_resource_mgr.submit_download(request, dir_path=(dir_path or "").strip() or None)

        if ctx.json_mode:
            output_json(result)
        else:
            output_cloud_resource_download(result)
    except SystemExit:
        raise
    except Exception as exc:
        handle_error(ctx, exc)


#
# plugin 命令组
#

@main.group()
@pass_ctx
def plugin(ctx: Context) -> None:
    """插件调用命令。"""


@plugin.command("call")
@click.option("--code", required=True, help="Plugin code")
@click.option("--body", required=True, help="Plugin request JSON body")
@pass_ctx
def plugin_call(ctx: Context, code: str, body: str) -> None:
    """按插件 code 调用 pluginsInstance/callByCode。"""
    try:
        if ctx.conn is None or ctx.client is None:
            raise ValueError("Connection state is unavailable")
        ctx.conn.require_configured()

        code = code.strip()
        if not code:
            raise click.UsageError("--code cannot be empty")

        payload = _parse_plugin_body(body)
        response = ctx.client.request(
            "POST",
            f"/api/v1/pluginsInstance/callByCode/{code}",
            json_body=payload,
        )
        if not response.ok:
            message = response.message or f"Plugin call failed with HTTP {response.status_code}"
            raise ValueError(message)

        if ctx.json_mode:
            output_json(response.data)
        else:
            output_plugin_call(response.data)
    except SystemExit:
        raise
    except Exception as exc:
        handle_error(ctx, exc)


#
# subscribe 命令组
#

@main.group()
@pass_ctx
def subscribe(ctx: Context) -> None:
    """影视订阅命令。"""


@subscribe.command("add")
@click.option(
    "--type",
    "media_type",
    type=click.Choice(SUBSCRIBE_MEDIA_TYPE_CHOICES, case_sensitive=False),
    required=True,
    help="Subscribe media type",
)
@click.option("--name", required=True, help="Subscribe title")
@click.option("--year", type=click.IntRange(min=1), required=True, help="Release year")
@click.option("--season", type=click.IntRange(min=1), help="Season number for TV subscriptions")
@pass_ctx
def subscribe_add(
    ctx: Context,
    media_type: str,
    name: str,
    year: int,
    season: Optional[int],
) -> None:
    """使用默认配置新增最小电影或电视剧订阅。"""
    try:
        if ctx.conn is None:
            raise ValueError("Connection state is unavailable")
        ctx.conn.require_configured()

        media_type = media_type.lower()
        name = name.strip()
        if not name:
            raise click.UsageError("--name cannot be empty")
        if media_type == "movie" and season is not None:
            raise click.UsageError("--season is only valid for tv subscriptions")
        if media_type == "tv" and season is None:
            season = 1

        result = ctx.subscribe_mgr.add(
            name=name,
            media_type=media_type,
            year=year,
            season=season,
        )

        if ctx.json_mode:
            output_json(result)
        else:
            output_subscribe_add(result)
    except SystemExit:
        raise
    except Exception as exc:
        handle_error(ctx, exc)


@subscribe.command("page")
@click.option(
    "--type",
    "media_type",
    type=click.Choice(SUBSCRIBE_MEDIA_TYPE_CHOICES, case_sensitive=False),
    required=True,
    help="Subscribe media type",
)
@click.option("--page", type=click.IntRange(min=1), default=1, show_default=True, help="Page number")
@click.option(
    "--page-size",
    type=click.IntRange(min=1),
    default=20,
    show_default=True,
    help="Page size",
)
@pass_ctx
def subscribe_page(ctx: Context, media_type: str, page: int, page_size: int) -> None:
    """按类型分页查询订阅。"""
    try:
        if ctx.conn is None:
            raise ValueError("Connection state is unavailable")
        ctx.conn.require_configured()

        media_type = media_type.lower()
        result = ctx.subscribe_mgr.page(media_type=media_type, page=page, page_size=page_size)

        if ctx.json_mode:
            output_json(result)
        else:
            output_subscribe_page(result, media_type=media_type)
    except SystemExit:
        raise
    except Exception as exc:
        handle_error(ctx, exc)
