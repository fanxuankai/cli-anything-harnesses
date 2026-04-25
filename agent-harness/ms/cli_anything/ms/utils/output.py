"""Output helpers for the Media Saber CLI."""

from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.table import Table

from ..core.client import ApiResponse

console = Console()
error_console = Console(stderr=True)
SUBSCRIBE_STATUS_LABELS = {
    100: "订阅就绪",
    200: "订阅运行中",
    300: "订阅已完成",
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
    table.add_column("Subscribed")
    table.add_column("In Library")
    table.add_column("Poster")

    for item in items:
        title = str(item.get("title", "") or "")
        subtitle = str(item.get("subtitle", "") or "")
        title_cell = title if not subtitle else f"{title}\n[dim]{subtitle}[/dim]"
        year = "" if item.get("year") is None else str(item.get("year", ""))
        media_type = str(item.get("media_type", "") or "")
        source = item.get("source") or {}
        source_label = str(source.get("name", "") or "")
        vote_value = item.get("vote")
        vote = "-" if vote_value in (None, "") else f"{float(vote_value):.1f}"
        subscription = item.get("subscription") or {}
        subscribed = "yes" if subscription.get("subscribed") else "no"
        library = item.get("library") or {}
        in_library = "yes" if library.get("archived") else "no"
        poster = item.get("poster_url")
        table.add_row(title_cell, year, media_type, source_label, vote, subscribed, in_library, poster)

    console.print(table)


def output_media_rank_sources(items: list[dict[str, Any]]) -> None:
    console.print("[bold]Media Rank Sources[/bold]")

    if not items:
        console.print("[dim](空)[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Source")
    table.add_column("Value")

    for item in items:
        table.add_row(
            str(item.get("text", "") or ""),
            "" if item.get("value") is None else str(item.get("value")),
        )

    console.print(table)


def output_media_rank_categories(items: list[dict[str, Any]], source: str) -> None:
    console.print("[bold]Media Rank Categories[/bold]")
    console.print(f"[cyan]Source[/cyan]: {source}")

    if not items:
        console.print("[dim](空)[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Code")
    table.add_column("Name")
    table.add_column("Custom")

    for item in items:
        table.add_row(
            str(item.get("code", "") or ""),
            str(item.get("name", "") or ""),
            "yes" if item.get("custom") else "no",
        )

    console.print(table)


def output_media_rank_subjects(items: list[dict[str, Any]], category_code: str) -> None:
    console.print("[bold]Media Rank Subjects[/bold]")
    console.print(f"[cyan]Category[/cyan]: {category_code}")

    if not items:
        console.print("[dim](空)[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Code")
    table.add_column("Name")
    table.add_column("Custom")
    table.add_column("Landscape")

    for item in items:
        table.add_row(
            str(item.get("code", "") or ""),
            str(item.get("name", "") or ""),
            "yes" if item.get("custom") else "no",
            "yes" if item.get("landscape") else "no",
        )

    console.print(table)


def output_media_rank_items(result: dict[str, Any], category_code: str, code: str) -> None:
    total = result.get("total", 0)
    page_num = result.get("pageNum", 1)
    page_size = result.get("pageSize", 20)
    items = result.get("list") or []

    console.print("[bold]Media Rank Items[/bold]")
    console.print(f"[cyan]Category[/cyan]: {category_code}")
    console.print(f"[cyan]Subject[/cyan]: {code}")
    console.print(f"[cyan]Page[/cyan]: {page_num} / [cyan]Page Size[/cyan]: {page_size} / [cyan]Total[/cyan]: {total}")

    if not items:
        console.print("[dim](空)[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Title")
    table.add_column("Year")
    table.add_column("Type")
    table.add_column("Vote")
    table.add_column("Subscription")
    table.add_column("In Library")

    for item in items:
        title = str(item.get("title", "") or "")
        subtitle = str(item.get("subtitle", "") or "")
        title_cell = title if not subtitle else f"{title}\n[dim]{subtitle}[/dim]"
        year = "" if item.get("year") is None else str(item.get("year", ""))
        media_type = str(item.get("media_type", "") or "")
        vote_value = item.get("vote")
        vote = "-" if vote_value in (None, "") else f"{float(vote_value):.1f}"
        subscription = item.get("subscription") or {}
        rss_id = subscription.get("id")
        rss = "-" if rss_id in (None, "", 0) else str(rss_id)
        library = item.get("library") or {}
        in_library = "yes" if library.get("archived") else "no"
        table.add_row(title_cell, year, media_type, vote, rss, in_library)

    console.print(table)


def output_media_recommend_sources(items: list[dict[str, Any]]) -> None:
    console.print("[bold]Media Recommend Sources[/bold]")

    if not items:
        console.print("[dim](空)[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Source")
    table.add_column("Value")

    for item in items:
        table.add_row(
            str(item.get("text", "") or ""),
            "" if item.get("value") is None else str(item.get("value")),
        )

    console.print(table)


def output_media_recommend_channels(items: list[dict[str, Any]], source: str) -> None:
    console.print("[bold]Media Recommend Channels[/bold]")
    console.print(f"[cyan]Source[/cyan]: {source}")

    if not items:
        console.print("[dim](空)[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Channel")
    table.add_column("Value")

    for item in items:
        table.add_row(
            str(item.get("text", "") or ""),
            str(item.get("value", "") or ""),
        )

    console.print(table)


def output_media_recommend_options(items: list[dict[str, Any]], source: str, channel: str) -> None:
    console.print("[bold]Media Recommend Options[/bold]")
    console.print(f"[cyan]Source[/cyan]: {source}")
    console.print(f"[cyan]Channel[/cyan]: {channel}")

    if not items:
        console.print("[dim](空)[/dim]")
        return

    for group in items:
        group_text = str(group.get("text", "") or "")
        group_id = str(group.get("id", "") or "")
        options = group.get("options") or []

        console.print(f"[cyan]{group_text}[/cyan] ({group_id})")

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Text")
        table.add_column("Value")

        for option in options:
            table.add_row(
                str(option.get("text", "") or ""),
                str(option.get("value", "") or ""),
            )

        console.print(table)


def output_media_recommend_items(result: dict[str, Any], source: str, channel: str) -> None:
    total = result.get("total", 0)
    page_num = result.get("pageNum", 1)
    page_size = result.get("pageSize", 20)
    items = result.get("list") or []

    console.print("[bold]Media Recommend Items[/bold]")
    console.print(f"[cyan]Source[/cyan]: {source}")
    console.print(f"[cyan]Channel[/cyan]: {channel}")
    console.print(f"[cyan]Page[/cyan]: {page_num} / [cyan]Page Size[/cyan]: {page_size} / [cyan]Total[/cyan]: {total}")

    if not items:
        console.print("[dim](空)[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Title")
    table.add_column("Year")
    table.add_column("Type")
    table.add_column("Vote")
    table.add_column("Subscription")
    table.add_column("In Library")

    for item in items:
        title = str(item.get("title", "") or "")
        subtitle = str(item.get("subtitle", "") or "")
        title_cell = title if not subtitle else f"{title}\n[dim]{subtitle}[/dim]"
        year = "" if item.get("year") is None else str(item.get("year", ""))
        media_type = str(item.get("media_type", "") or "")
        vote_value = item.get("vote")
        vote = "-" if vote_value in (None, "") else f"{float(vote_value):.1f}"
        subscription = item.get("subscription") or {}
        rss_id = subscription.get("id")
        rss = "-" if rss_id in (None, "", 0) else str(rss_id)
        library = item.get("library") or {}
        in_library = "yes" if library.get("archived") else "no"
        table.add_row(title_cell, year, media_type, vote, rss, in_library)

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


def output_subscribe_page(result: dict[str, Any], media_type: str) -> None:
    total = result.get("total", 0)
    page_num = result.get("pageNum", 1)
    page_size = result.get("pageSize", 20)
    items = result.get("list") or []

    console.print("[bold]Subscribe Page[/bold]")
    console.print(f"[cyan]Type[/cyan]: {media_type}")
    console.print(f"[cyan]Page[/cyan]: {page_num} / [cyan]Page Size[/cyan]: {page_size} / [cyan]Total[/cyan]: {total}")

    if not items:
        console.print("[dim](空)[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Name")
    table.add_column("Year")
    table.add_column("Type")
    table.add_column("Season")
    table.add_column("Status")
    table.add_column("TMDB")

    for item in items:
        status_value = item.get("status")
        status_text = SUBSCRIBE_STATUS_LABELS.get(status_value, "" if status_value in (None, "") else str(status_value))
        season_value = item.get("season") if item.get("type") == "tv" else ""
        table.add_row(
            str(item.get("name", "") or ""),
            "" if item.get("year") is None else str(item.get("year", "")),
            str(item.get("type", "") or ""),
            "" if season_value in (None, "") else str(season_value),
            status_text,
            "" if item.get("tmdbId") is None else str(item.get("tmdbId", "")),
        )

    console.print(table)


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


def output_media_server_miss_episodes(result: dict[str, Any]) -> None:
    console.print("[bold]Miss Episodes Check[/bold]")

    total = int(result.get("total") or 0)
    items = result.get("items") or []

    console.print(f"Total: {total}")

    if not items:
        console.print("[green]✅ 无漏集[/green]")
        return

    if total > len(items):
        console.print(f"Showing first {len(items)} items")

    for item in items:
        title = str(item.get("title", "") or "")
        year = item.get("year")
        header = title if year in (None, "") else f"{title} ({year})"
        console.print(f"[cyan]{header}[/cyan]")

        episodes = item.get("episodes") or []
        for season_item in episodes:
            season = season_item.get("season", "")
            total = season_item.get("totalEpisodes", "")
            missing = season_item.get("missEpisodes") or []
            missing_text = _format_missing_episodes(missing)
            console.print(f"  Season {season} / Total {total} / Missing: {missing_text}")


def _format_missing_episodes(episodes: list[Any], limit: int = 20) -> str:
    normalized = [str(item) for item in episodes]
    if len(normalized) <= limit:
        return ", ".join(normalized)
    return f"{', '.join(normalized[:limit])} ... ({len(normalized)} total)"
