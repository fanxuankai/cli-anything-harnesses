"""Output helpers for the Media Saber CLI."""

from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.table import Table

from ..core.client import ApiResponse

console = Console()
error_console = Console(stderr=True)
MEDIA_SOURCE_LABELS = {
    100: "豆瓣",
    200: "TMDB",
}


def output_json(data: Any) -> None:
    console.file.write(json.dumps(data, indent=2, ensure_ascii=False))
    console.file.write("\n")


def output_error(message: str) -> None:
    error_console.print(f"[red]错误:[/red] {message}")


def output_connection(data: dict[str, Any], json_mode: bool = False) -> None:
    if json_mode:
        output_json(data)
        return

    console.print("[bold]Media Saber Connection[/bold]")
    for key, value in data.items():
        console.print(f"[cyan]{key}[/cyan]: {value}")


def output_response(response: ApiResponse, json_mode: bool = False, raw: bool = False) -> None:
    if raw:
        raw_payload = response.raw_body
        if json_mode:
            output_json(raw_payload)
        elif isinstance(raw_payload, (dict, list)):
            console.print_json(json.dumps(raw_payload, ensure_ascii=False))
        else:
            console.print("" if raw_payload is None else str(raw_payload))
        return

    if json_mode:
        output_json(response.to_dict())
        return

    if response.is_standard_response:
        if response.message:
            style = "green" if response.ok else "yellow"
            console.print(f"[{style}]{response.message}[/{style}]")
        _print_data(response.data)
        if not response.ok:
            console.print(f"[red]HTTP {response.status_code}[/red]")
        return

    if not response.ok:
        console.print(f"[red]HTTP {response.status_code}[/red]")
    _print_data(response.data)


def output_media_search(result: dict[str, Any], source: str, keyword: str) -> None:
    total = result.get("total", 0)
    page_num = result.get("pageNum", 1)
    page_size = result.get("pageSize", 20)
    items = result.get("list") or []

    console.print("[bold]Media Search[/bold]")
    console.print(f"[cyan]Source[/cyan]: {source}")
    console.print(f"[cyan]Keyword[/cyan]: {keyword}")
    console.print(f"[cyan]Page[/cyan]: {page_num} / [cyan]Page Size[/cyan]: {page_size} / [cyan]Total[/cyan]: {total}")

    if not items:
        console.print("[dim](空)[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Title")
    table.add_column("Year")
    table.add_column("Type")
    table.add_column("Source")
    table.add_column("Vote")

    for item in items:
        title = str(item.get("title", "") or "")
        subtitle = str(item.get("subtitle", "") or "")
        title_cell = title if not subtitle else f"{title}\n[dim]{subtitle}[/dim]"
        year = "" if item.get("year") is None else str(item.get("year", ""))
        media_type = str(item.get("type", "") or "")
        source_label = MEDIA_SOURCE_LABELS.get(item.get("source"), str(item.get("source", "")))
        vote_value = item.get("vote")
        vote = "-" if vote_value in (None, "") else f"{float(vote_value):.1f}"
        table.add_row(title_cell, year, media_type, source_label, vote)

    console.print(table)


def output_subscribe_add(result: dict[str, Any]) -> None:
    subscribe = result.get("subscribe", {})
    console.print("[bold green]Subscribe Added[/bold green]")
    console.print(f"[cyan]type[/cyan]: {subscribe.get('type', '')}")
    console.print(f"[cyan]name[/cyan]: {subscribe.get('name', '')}")
    console.print(f"[cyan]year[/cyan]: {subscribe.get('year', '')}")
    if subscribe.get("type") == "tv":
        console.print(f"[cyan]season[/cyan]: {subscribe.get('season', '')}")
    console.print("[cyan]status[/cyan]: 已按默认配置提交")


def _print_data(data: Any) -> None:
    if data is None:
        return
    if isinstance(data, (dict, list)):
        console.print_json(json.dumps(data, ensure_ascii=False))
        return
    console.print(str(data))


def output_plugin_call(result: Any) -> None:
    if result is None:
        console.print("[bold green]插件调用成功[/bold green]")
        return

    if not isinstance(result, dict):
        _print_data(result)
        return

    message = result.get("message")
    data = result.get("data")

    if message:
        console.print(f"[green]{message}[/green]")

    if data is not None:
        _print_data(data)
    elif not message:
        console.print("[bold green]插件调用成功[/bold green]")
