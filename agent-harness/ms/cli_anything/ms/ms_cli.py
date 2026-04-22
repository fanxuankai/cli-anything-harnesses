"""CLI entrypoint for the Media Saber harness."""

from __future__ import annotations

import json
from pathlib import Path
import shlex
import sys
from typing import Optional

import click

from . import __version__
from .core.client import ConnectionConfig, MSClient
from .core.media import MEDIA_SOURCE_MAP, MediaManager
from .core.subscribe import MEDIA_TYPE_CHOICES, SubscribeManager
from .utils.output import (
    output_connection,
    output_error,
    output_json,
    output_media_search,
    output_response,
    output_subscribe_add,
)


class Context:
    """CLI runtime context."""

    def __init__(self) -> None:
        self.json_mode = False
        self.in_repl = False
        self.conn: Optional[ConnectionConfig] = None
        self.client: Optional[MSClient] = None
        self._media_mgr: Optional[MediaManager] = None
        self._subscribe_mgr: Optional[SubscribeManager] = None

    def setup(self, url: Optional[str], apikey: Optional[str]) -> None:
        self.conn = ConnectionConfig.resolve(url=url, api_key=apikey)
        self.client = MSClient(self.conn)
        self._media_mgr = None
        self._subscribe_mgr = None

    @property
    def media_mgr(self) -> MediaManager:
        if self.client is None:
            raise ValueError("Client is not initialized")
        if self._media_mgr is None:
            self._media_mgr = MediaManager(self.client)
        return self._media_mgr

    @property
    def subscribe_mgr(self) -> SubscribeManager:
        if self.client is None:
            raise ValueError("Client is not initialized")
        if self._subscribe_mgr is None:
            self._subscribe_mgr = SubscribeManager(self.client)
        return self._subscribe_mgr


pass_ctx = click.make_pass_decorator(Context, ensure=True)


def handle_error(ctx: Context, exc: Exception) -> None:
    if ctx.json_mode:
        output_json({"error": str(exc)})
    else:
        output_error(str(exc))
    raise SystemExit(1)


def _parse_kv_pairs(pairs: tuple[str, ...], option_name: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in pairs:
        if "=" not in item:
            raise click.UsageError(f"{option_name} expects key=value, got: {item}")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise click.UsageError(f"{option_name} key cannot be empty")
        parsed[key] = value
    return parsed


@click.group(invoke_without_command=True)
@click.option("--url", "-u", envvar="MS_URL", help="Media Saber base URL")
@click.option("--apikey", "-k", envvar="MS_API_KEY", help="Media Saber API key")
@click.option("--json", "json_mode", is_flag=True, help="Output normalized JSON")
@click.option("--repl", "repl_mode", is_flag=True, help="Enter interactive REPL")
@click.version_option(version=__version__, prog_name="cli-anything-ms")
@click.pass_context
def main(click_ctx: click.Context, url: Optional[str], apikey: Optional[str], json_mode: bool, repl_mode: bool) -> None:
    """Media Saber minimal CLI harness."""
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
    ctx.in_repl = True
    click.echo("Media Saber REPL. 输入 help 查看帮助，exit 退出。")

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


@main.group()
@pass_ctx
def config(ctx: Context) -> None:
    """Connection config commands."""


@config.command("save-connection")
@click.option("--url", "-u", required=True, help="Media Saber base URL")
@click.option("--apikey", "-k", required=True, help="Media Saber API key")
@pass_ctx
def save_connection(ctx: Context, url: str, apikey: str) -> None:
    """Persist connection config to ~/.ms-cli.yaml."""
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
    """Show the resolved connection settings."""
    try:
        if ctx.conn is None:
            raise ValueError("Connection state is unavailable")
        output_connection(ctx.conn.as_display_dict(), json_mode=ctx.json_mode)
    except Exception as exc:
        handle_error(ctx, exc)


@main.group()
@pass_ctx
def media(ctx: Context) -> None:
    """Media search commands."""


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
    """Search media by source and keyword."""
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


@main.group()
@pass_ctx
def subscribe(ctx: Context) -> None:
    """Subscribe add commands."""


@subscribe.command("add")
@click.option(
    "--type",
    "media_type",
    type=click.Choice(MEDIA_TYPE_CHOICES, case_sensitive=False),
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
    """Add a minimal movie or TV subscription using default config."""
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


@main.command("request", hidden=True)
@click.argument("method")
@click.argument("path")
@click.option("--query", "query_items", multiple=True, help="Add query parameter as key=value")
@click.option("--header", "header_items", multiple=True, help="Add header as key=value")
@click.option("--json-body", help="Inline JSON request body")
@click.option("--body-file", type=click.Path(exists=True, dir_okay=False, path_type=Path), help="Read JSON body from file")
@click.option("--raw", is_flag=True, help="Print raw response body instead of normalized output")
@pass_ctx
def request_command(
    ctx: Context,
    method: str,
    path: str,
    query_items: tuple[str, ...],
    header_items: tuple[str, ...],
    json_body: Optional[str],
    body_file: Optional[Path],
    raw: bool,
) -> None:
    """Perform a generic HTTP request against Media Saber."""
    try:
        if json_body and body_file:
            raise click.UsageError("--json-body and --body-file cannot be used together")
        if ctx.conn is None or ctx.client is None:
            raise ValueError("Client is not initialized")

        ctx.conn.require_configured()
        query = _parse_kv_pairs(query_items, "--query")
        headers = _parse_kv_pairs(header_items, "--header")

        payload = None
        if body_file is not None:
            payload = json.loads(body_file.read_text(encoding="utf-8"))
        elif json_body:
            payload = json.loads(json_body)

        response = ctx.client.request(
            method=method,
            path=path,
            params=query or None,
            headers=headers or None,
            json_body=payload,
        )
        output_response(response, json_mode=ctx.json_mode, raw=raw)
        if not response.ok:
            raise SystemExit(1)
    except SystemExit:
        raise
    except Exception as exc:
        handle_error(ctx, exc)
