"""Output helpers for the ms CLI."""

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

    console.print("[bold]ms Connection[/bold]")
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


def output_cloud_resource_search(result: dict[str, Any]) -> None:
    total = result.get("total", 0)
    page_num = result.get("pageNum", 1)
    page_size = result.get("pageSize", 25)
    items = result.get("list") or []

    console.print("[bold]Cloud Resource Search[/bold]")
    console.print(f"[cyan]Page[/cyan]: {page_num} / [cyan]Page Size[/cyan]: {page_size} / [cyan]Total[/cyan]: {total}")

    if not items:
        console.print("[dim](空)[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Title")
    table.add_column("Size")
    table.add_column("Driver")
    table.add_column("Creator")
    table.add_column("TMDB")
    table.add_column("Type")
    table.add_column("CS Hash")
    table.add_column("Download")

    for item in items:
        link = item.get("link") if isinstance(item.get("link"), dict) else {}
        creator = item.get("creator") if isinstance(item.get("creator"), dict) else {}
        driver = item.get("driver") if isinstance(item.get("driver"), dict) else {}
        table.add_row(
            str(item.get("title", "") or ""),
            _format_bytes(item.get("size")),
            str(driver.get("name", "") or ""),
            _format_creator(creator),
            "" if item.get("tmdb_id") is None else str(item.get("tmdb_id")),
            str(link.get("type_name", "") or ""),
            "" if item.get("cs_hash_id") is None else str(item.get("cs_hash_id")),
            "yes" if item.get("downloadable") else "no",
        )

    console.print(table)


def output_cloud_resource_download(result: dict[str, Any]) -> None:
    console.print("[bold green]Cloud Resource Download Submitted[/bold green]")
    console.print(f"[cyan]type[/cyan]: {result.get('type', '')}")
    console.print(f"[cyan]count[/cyan]: {result.get('count', '')}")
    dir_path = result.get("dir")
    console.print(f"[cyan]dir[/cyan]: {dir_path or '(backend default)'}")
    message = result.get("message")
    if message:
        console.print(f"[cyan]message[/cyan]: {message}")


def output_cloud_resource_rank(result: dict[str, Any]) -> None:
    range_type = str(result.get("range_type", "") or "")
    stat_type = str(result.get("stat_type", "") or "")
    items = result.get("items") or []
    mine = result.get("mine") if isinstance(result.get("mine"), dict) else {}

    range_label = {"today": "今日榜", "week": "7天榜", "all": "总榜"}.get(range_type, range_type)
    stat_label = {"count": "荣耀数量榜", "size": "洪荒封神榜"}.get(stat_type, stat_type)
    console.print("[bold]Cloud Resource Rank[/bold]")
    console.print(f"[cyan]Range[/cyan]: {range_label} / [cyan]Stat[/cyan]: {stat_label}")

    if not items:
        console.print("[dim](空)[/dim]")
    else:
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Rank")
        table.add_column("Creator")
        table.add_column("Count")
        table.add_column("Size")
        table.add_column("Value")

        for item in items:
            creator_id = item.get("creator_id")
            creator = str(item.get("creator", "") or "")
            creator_text = creator if creator_id in (None, "", 0) else f"{creator} ({creator_id})"
            table.add_row(
                str(item.get("rank", "") or ""),
                creator_text,
                f"{item.get('count', 0)} 次",
                str(item.get("size_text", "") or _format_bytes(item.get("size"))),
                str(item.get("value_text", "") or item.get("value", "")),
            )

        console.print(table)

    if mine:
        rank = mine.get("rank") or "--"
        surpass = _format_percent(mine.get("surpass_percent"))
        console.print(
            f"[cyan]Mine[/cyan]: {mine.get('creator', '我')} / "
            f"Rank {rank} / {mine.get('value_text', '')} / "
            f"Surpass {surpass}"
        )


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


def _format_creator(creator: dict[str, Any]) -> str:
    name = str(creator.get("name", "") or "")
    creator_id = creator.get("id")
    if creator_id in (None, ""):
        return name
    if not name:
        return str(creator_id)
    return f"{name} ({creator_id})"


def _format_bytes(value: Any) -> str:
    try:
        size = float(value or 0)
    except (TypeError, ValueError):
        return ""
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_idx = 0
    while size >= 1024 and unit_idx < len(units) - 1:
        size /= 1024
        unit_idx += 1
    if unit_idx == 0:
        return f"{int(size)} {units[unit_idx]}"
    return f"{size:.2f} {units[unit_idx]}"


def _format_percent(value: Any) -> str:
    try:
        percent = float(value or 0)
    except (TypeError, ValueError):
        percent = 0.0
    percent = min(100.0, max(0.0, percent))
    text = f"{percent:.2f}".rstrip("0").rstrip(".")
    return f"{text}%"


def _print_data(data: Any) -> None:
    if data is None:
        return
    if isinstance(data, (dict, list)):
        console.print_json(json.dumps(data, ensure_ascii=False))
        return
    console.print(str(data))


def _parse_embedded_raw(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str) or not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _format_rate(value: Any) -> str:
    return f"{_format_bytes(value)}/s"


def _format_nas_cpu(item: dict[str, Any]) -> str:
    cpu = item.get("cpu") if isinstance(item.get("cpu"), dict) else {}
    used = _format_percent(cpu.get("usedPercent"))
    temp = cpu.get("temperature")
    temp_text = "-" if temp in (None, "") else f"{temp} C"
    return f"{used} / {temp_text}"


def _format_nas_memory(item: dict[str, Any]) -> str:
    memory = item.get("memory") if isinstance(item.get("memory"), dict) else {}
    total = _format_bytes(memory.get("totalBytes"))
    used = _format_percent(memory.get("usedPercent"))
    return f"{used} / {total}"


def _format_nas_storage(item: dict[str, Any], raw: dict[str, Any]) -> str:
    storage = item.get("storage") if isinstance(item.get("storage"), dict) else {}
    total = storage.get("totalBytes") or 0
    used = storage.get("usedBytes") or 0
    percent = storage.get("usedPercent")

    if not total:
        widget = raw.get("storage_widget") if isinstance(raw.get("storage_widget"), dict) else {}
        volumes = widget.get("storage_list") if isinstance(widget.get("storage_list"), list) else []
        total = sum(int(volume.get("size") or 0) for volume in volumes if isinstance(volume, dict))
        used = sum(int(volume.get("used") or 0) for volume in volumes if isinstance(volume, dict))
        percent = (used / total * 100) if total else 0

    if not total:
        return "-"
    return f"{_format_bytes(used)} / {_format_bytes(total)} ({_format_percent(percent)})"


def _format_nas_network(item: dict[str, Any]) -> str:
    network = item.get("network") if isinstance(item.get("network"), dict) else {}
    ipv4 = str(network.get("ipv4") or "-")
    up = _format_rate(network.get("uploadBytesPerSec"))
    down = _format_rate(network.get("downloadBytesPerSec"))
    return f"{ipv4}\n↑ {up} ↓ {down}"


def _format_nas_fans(item: dict[str, Any]) -> str:
    fans = item.get("fans") if isinstance(item.get("fans"), list) else []
    values = []
    for fan in fans:
        if not isinstance(fan, dict):
            continue
        name = str(fan.get("name") or fan.get("role") or "fan")
        rpm = fan.get("rpm")
        rpm_text = "-" if rpm in (None, "") else f"{rpm} rpm"
        values.append(f"{name}: {rpm_text}")
    return "\n".join(values) if values else "-"


def _format_nas_ups(item: dict[str, Any]) -> str:
    ups = item.get("ups") if isinstance(item.get("ups"), dict) else {}
    if not ups:
        return "-"
    status = str(ups.get("status") or "-")
    vendor = str(ups.get("vendor") or "")
    product = str(ups.get("product") or ups.get("model") or "")
    name = " ".join(part for part in (vendor, product) if part).strip() or "-"
    return f"{status}\n{name}"


def output_system_nas_info(items: list[dict[str, Any]]) -> None:
    console.print("[bold]NAS Info[/bold]")

    if not items:
        console.print("[dim](空)[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Device")
    table.add_column("Vendor")
    table.add_column("Status")
    table.add_column("CPU")
    table.add_column("Memory")
    table.add_column("Storage")
    table.add_column("Network")
    table.add_column("Fan")
    table.add_column("UPS")

    for item in items:
        if not isinstance(item, dict):
            continue
        raw = _parse_embedded_raw(item.get("raw"))
        table.add_row(
            str(item.get("instanceName") or item.get("model") or "-"),
            str(item.get("vendor") or "-"),
            str(item.get("status") or "-"),
            _format_nas_cpu(item),
            _format_nas_memory(item),
            _format_nas_storage(item, raw),
            _format_nas_network(item),
            _format_nas_fans(item),
            _format_nas_ups(item),
        )

    console.print(table)


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


def output_media_server_list(result: dict[str, Any]) -> None:
    console.print("[bold]Media Servers[/bold]")
    items = result.get("items") or []
    console.print(f"Total: {result.get('total', len(items))}")

    if not items:
        console.print("[dim](空)[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID")
    table.add_column("Type")
    table.add_column("Name")
    table.add_column("Enabled")
    table.add_column("Default")
    table.add_column("Movies", justify="right")
    table.add_column("TV", justify="right")
    table.add_column("Time")
    table.add_column("Synced At")
    table.add_column("Updated At")

    for item in items:
        statistics = item.get("statistics") if isinstance(item.get("statistics"), dict) else {}
        table.add_row(
            _text(item.get("id")),
            _text(item.get("type_text")),
            _text(item.get("name")),
            "yes" if item.get("enabled") else "no",
            "yes" if item.get("default") else "no",
            _text(statistics.get("movie_count")),
            _text(statistics.get("tv_count")),
            f"{statistics.get('time_seconds', 0)}s",
            _text(statistics.get("updated_at_text")),
            _text(item.get("updated_at_text")),
        )

    console.print(table)


def output_media_server_detail(result: dict[str, Any]) -> None:
    console.print("[bold]Media Server Detail[/bold]")
    output_media_server_list({"total": 1, "items": [result]})


def output_media_server_libraries(result: dict[str, Any]) -> None:
    console.print("[bold]Media Server Libraries[/bold]")
    console.print(f"Server ID: {result.get('server_id', '')} / Total: {result.get('total', 0)}")
    items = result.get("items") or []
    if not items:
        console.print("[dim](空)[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Paths")
    table.add_column("Link")
    for item in items:
        paths = item.get("paths") if isinstance(item.get("paths"), list) else []
        table.add_row(
            _text(item.get("id")),
            _text(item.get("name")),
            _text(item.get("media_type")),
            "\n".join(str(path) for path in paths),
            _text(item.get("link")),
        )
    console.print(table)


def output_media_server_statistics(result: dict[str, Any]) -> None:
    console.print("[bold]Media Server Statistics[/bold]")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Server ID")
    table.add_column("Movies", justify="right")
    table.add_column("TV", justify="right")
    table.add_column("Time")
    table.add_column("Synced At")
    table.add_row(
        _text(result.get("media_server_id")),
        _text(result.get("movie_count")),
        _text(result.get("tv_count")),
        f"{result.get('time_seconds', 0)}s",
        _text(result.get("updated_at_text")),
    )
    console.print(table)


def output_media_server_sync_items(result: dict[str, Any]) -> None:
    console.print("[bold]Media Server Sync Items[/bold]")
    items = result.get("list") or []
    console.print(
        f"Page: {result.get('pageNum', 1)} / Page Size: {result.get('pageSize', len(items))} / Total: {result.get('total', 0)}"
    )
    if not items:
        console.print("[dim](空)[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Title")
    table.add_column("Type")
    table.add_column("Year")
    table.add_column("TMDB")
    table.add_column("Library")
    table.add_column("Size")
    table.add_column("Miss")
    table.add_column("Path")
    for item in items:
        table.add_row(
            _text(item.get("title")),
            _text(item.get("item_type")),
            _text(item.get("year")),
            _text(item.get("tmdb_id")),
            _text(item.get("library_name")),
            _text(item.get("size_text")),
            "yes" if item.get("miss_eps") else "no",
            _text(item.get("path")),
        )
    console.print(table)


def output_media_server_media_items(result: dict[str, Any], title: str) -> None:
    console.print(f"[bold]{title}[/bold]")
    items = result.get("items") or []
    console.print(f"Server ID: {result.get('server_id', '')} / Total: {result.get('total', len(items))}")
    if not items:
        console.print("[dim](空)[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Percent")
    table.add_column("Link")
    for item in items:
        percent = item.get("percent")
        table.add_row(
            _text(item.get("id")),
            _text(item.get("name")),
            _text(item.get("type")),
            "" if percent is None else f"{percent}%",
            _text(item.get("link")),
        )
    console.print(table)


def output_media_server_sync_run(result: dict[str, Any]) -> None:
    console.print("[bold green]媒体服务器同步任务已发起[/bold green]")
    console.print(f"Server ID: {result.get('server_id', '')}")
    if result.get("message"):
        console.print(f"Message: {result.get('message')}")


def output_site_list(result: dict[str, Any]) -> None:
    console.print("[bold]Sites[/bold]")
    items = result.get("items") or []
    console.print(f"Total: {result.get('total', len(items))}")
    if not items:
        console.print("[dim](空)[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Code")
    table.add_column("Enabled")
    table.add_column("Search")
    table.add_column("RSS")
    table.add_column("Statistic")
    table.add_column("Sign In")
    table.add_column("Message")
    table.add_column("Domain")
    for item in items:
        switches = item.get("switches") if isinstance(item.get("switches"), dict) else {}
        table.add_row(
            _text(item.get("id")),
            _text(item.get("name")),
            _text(item.get("code")),
            "yes" if item.get("enabled") else "no",
            "yes" if switches.get("search") else "no",
            "yes" if switches.get("rss") else "no",
            "yes" if switches.get("statistic") else "no",
            "yes" if switches.get("sign_in") else "no",
            "yes" if switches.get("message") else "no",
            _text(item.get("domain")),
        )
    console.print(table)


def output_site_data_total(result: dict[str, Any]) -> None:
    console.print("[bold]Site Data Total[/bold]")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Uploaded")
    table.add_column("Downloaded")
    table.add_column("Bonus")
    table.add_column("Seeding Count", justify="right")
    table.add_column("Seeding Size")
    table.add_row(
        _text(result.get("uploaded_text")),
        _text(result.get("downloaded_text")),
        _text(result.get("bonus")),
        _text(result.get("seeding_count")),
        _text(result.get("seeding_size_text")),
    )
    console.print(table)


def output_site_data_latest(result: dict[str, Any]) -> None:
    console.print("[bold]Site Data Latest[/bold]")
    items = result.get("items") or []
    console.print(f"Total: {result.get('total', len(items))}")
    if not items:
        console.print("[dim](空)[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Site")
    table.add_column("Login")
    table.add_column("Signed")
    table.add_column("Ratio")
    table.add_column("Uploaded")
    table.add_column("Downloaded")
    table.add_column("Bonus")
    table.add_column("Seed")
    table.add_column("Seeding Size")
    table.add_column("Date")
    for item in items:
        table.add_row(
            _text(item.get("site_name")),
            "yes" if item.get("is_login") else "no",
            "yes" if item.get("signed_in") else "no",
            _text(item.get("ratio")),
            _text(item.get("uploaded_text")),
            _text(item.get("downloaded_text")),
            _text(item.get("bonus")),
            _text(item.get("seeding_count")),
            _text(item.get("seeding_size_text")),
            _text(item.get("statistic_date") or item.get("created_at_text")),
        )
    console.print(table)


def output_site_sign_in_history(result: dict[str, Any]) -> None:
    console.print("[bold]Site Sign-In History[/bold]")
    items = result.get("list") or []
    console.print(
        f"Page: {result.get('pageNum', 1)} / Page Size: {result.get('pageSize', len(items))} / Total: {result.get('total', 0)}"
    )
    if not items:
        console.print("[dim](空)[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Site")
    table.add_column("Code")
    table.add_column("Message")
    table.add_column("Time")
    for item in items:
        table.add_row(
            _text(item.get("site_name")),
            _text(item.get("code_text")),
            _text(item.get("message")),
            _text(item.get("created_at_text")),
        )
    console.print(table)


def output_site_sign_in(result: dict[str, Any]) -> None:
    console.print("[bold green]站点签到任务已提交[/bold green]")
    site_ids = result.get("site_ids") or []
    if site_ids:
        console.print(f"Site IDs: {', '.join(str(item) for item in site_ids)}")
    elif result.get("all_enabled"):
        console.print("Scope: all enabled sign-in sites")
    if result.get("message"):
        console.print(f"Message: {result.get('message')}")


def output_downloaders(result: dict[str, Any]) -> None:
    console.print("[bold]Downloaders[/bold]")
    items = result.get("items") or []
    console.print(f"Total: {result.get('total', len(items))}")
    if not items:
        console.print("[dim](空)[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Enabled")
    table.add_column("Default")
    table.add_column("URL")
    table.add_column("Monitor")
    table.add_column("Remark")
    for item in items:
        table.add_row(
            _text(item.get("id")),
            _text(item.get("name")),
            _text(item.get("type")),
            "yes" if item.get("enabled") else "no",
            "yes" if item.get("default") else "no",
            _text(item.get("url")),
            _text(item.get("monitor")),
            _text(item.get("remark")),
        )
    console.print(table)


def output_downloading(result: dict[str, Any]) -> None:
    console.print("[bold]Downloading[/bold]")
    items = result.get("items") or []
    console.print(f"Total: {result.get('total', len(items))}")
    if not items:
        console.print("[dim](空)[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID")
    table.add_column("Title")
    table.add_column("Progress")
    table.add_column("Speed")
    table.add_column("State")
    table.add_column("Paused")
    table.add_column("Site")
    table.add_column("Save Path")
    for item in items:
        table.add_row(
            _text(item.get("id")),
            _text(item.get("title") or item.get("torrent_title")),
            f"{item.get('progress_percent', 0)}%",
            _text(item.get("speed_text")),
            _text(item.get("state")),
            "yes" if item.get("paused") else "no",
            _text(item.get("site_name")),
            _text(item.get("save_path")),
        )
    console.print(table)


def output_download_history(result: dict[str, Any]) -> None:
    console.print("[bold]Download History[/bold]")
    items = result.get("list") or []
    console.print(
        f"Page: {result.get('pageNum', 1)} / Page Size: {result.get('pageSize', len(items))} / Total: {result.get('total', 0)}"
    )
    if not items:
        console.print("[dim](空)[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID")
    table.add_column("Title")
    table.add_column("Type")
    table.add_column("Year")
    table.add_column("Site")
    table.add_column("Torrent")
    table.add_column("Download ID")
    table.add_column("Created At")
    for item in items:
        table.add_row(
            _text(item.get("id")),
            _text(item.get("title")),
            _text(item.get("media_type")),
            _text(item.get("year")),
            _text(item.get("site_name")),
            _text(item.get("torrent_title")),
            _text(item.get("download_id")),
            _text(item.get("created_at_text")),
        )
    console.print(table)


def output_download_operation(result: dict[str, Any]) -> None:
    action = _text(result.get("action"))
    console.print(f"[bold green]下载任务 {action} 已提交[/bold green]")
    console.print(f"Download ID: {result.get('download_id', '')}")
    if result.get("message"):
        console.print(f"Message: {result.get('message')}")


def _format_missing_episodes(episodes: list[Any], limit: int = 20) -> str:
    normalized = [str(item) for item in episodes]
    if len(normalized) <= limit:
        return ", ".join(normalized)
    return f"{', '.join(normalized[:limit])} ... ({len(normalized)} total)"


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)
