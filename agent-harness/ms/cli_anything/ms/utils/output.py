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


def output_subscribe_operation(result: dict[str, Any]) -> None:
    console.print(f"[bold green]订阅操作 {result.get('action', '')} 已提交[/bold green]")
    console.print(f"Subscribe ID: {result.get('subscribe_id', '')}")
    if result.get("media_type"):
        console.print(f"Type: {result.get('media_type')}")
    if result.get("message"):
        console.print(f"Message: {result.get('message')}")


def output_subscribe_detail(result: dict[str, Any]) -> None:
    console.print("[bold]Subscribe Detail[/bold]")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Year")
    table.add_column("Season")
    table.add_column("Status")
    table.add_column("TMDB")
    status_value = result.get("status")
    status_text = SUBSCRIBE_STATUS_LABELS.get(status_value, "" if status_value in (None, "") else str(status_value))
    table.add_row(
        _text(result.get("id")),
        _text(result.get("name")),
        _text(result.get("type")),
        _text(result.get("year")),
        _text(result.get("season")),
        status_text,
        _text(result.get("tmdbId")),
    )
    console.print(table)


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
    console.print("[bold green]云资源任务已提交[/bold green]")
    items = result.get("items") or []
    console.print(f"Count: {len(items)}")
    for item in items:
        status = str(item.get("status", "") or "")
        message = str(item.get("message", "") or "")
        line = f"- [{status or 'unknown'}] csHash {item.get('cs_hash_id', '')}"
        if item.get("task_id"):
            line += f" / Task {item.get('task_id')}"
        if message:
            line += f" / {message}"
        console.print(line)
    if result.get("message"):
        console.print(f"Message: {result.get('message')}")
    if items:
        console.print("[dim]任务已提交，进度请用 cloud-resource tasks 查询[/dim]")


def output_cloud_resource_download_site(result: dict[str, Any]) -> None:
    console.print("[bold green]站点种子下载任务已提交[/bold green]")
    console.print(f"Site ID: {result.get('site_id', '')}")
    if result.get("title"):
        console.print(f"Title: {result.get('title')}")
    if result.get("message"):
        console.print(f"Message: {result.get('message')}")
    console.print("[dim]任务已提交，进度请用 download downloading 查询[/dim]")


def output_cloud_resource_tasks(result: dict[str, Any]) -> None:
    console.print("[bold]Cloud Storage Tasks[/bold]")
    items = result.get("list") or []
    console.print(
        f"Page: {result.get('pageNum', 1)} / Page Size: {result.get('pageSize', len(items))} / Total: {result.get('total', 0)}"
    )
    if not items:
        console.print("[dim](空)[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Name")
    table.add_column("State")
    table.add_column("Progress")
    table.add_column("Speed")
    table.add_column("Size")
    table.add_column("Error")
    for item in items:
        table.add_row(
            _text(item.get("name") or item.get("file_name") or item.get("tmdb_title")),
            _text(item.get("state_text") or item.get("status")),
            f"{item.get('progress_percent', 0)}%",
            _text(item.get("speed_text")),
            _text(item.get("total_bytes_text")),
            _text(item.get("error")),
        )
    console.print(table)


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


def output_system_workbench(result: dict[str, Any]) -> None:
    console.print("[bold]Workbench Overview[/bold]")

    def _section(key: str) -> dict[str, Any]:
        value = result.get(key)
        return value if isinstance(value, dict) else {}

    site = _section("site")
    system = _section("system")
    library = _section("library")
    play = _section("play")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Section")
    table.add_column("Data")
    rows: list[tuple[str, str]] = []
    if site:
        rows.append(("站点", " / ".join(f"{k}: {v}" for k, v in site.items() if v not in (None, "", 0))))
    if system:
        rows.append(("系统", " / ".join(f"{k}: {v}" for k, v in system.items() if v not in (None, "", 0))))
    if library:
        rows.append(("媒体库", " / ".join(f"{k}: {v}" for k, v in library.items() if v not in (None, "", 0))))
    if play:
        rows.append(("播放", " / ".join(f"{k}: {v}" for k, v in play.items() if v not in (None, "", 0))))
    if not rows:
        console.print("[dim](空)[/dim]")
        return
    for section, data in rows:
        table.add_row(section, data)
    console.print(table)


def output_system_health_overview(result: dict[str, Any]) -> None:
    console.print("[bold]System Health Overview[/bold]")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("CPU")
    table.add_column("Memory")
    table.add_column("Disk")
    table.add_column("Queue Pending", justify="right")
    table.add_column("Queue Failed", justify="right")
    table.add_column("Sites", justify="right")
    table.add_column("Downloaders", justify="right")
    table.add_column("Media Servers", justify="right")
    table.add_column("Cloud Drives", justify="right")
    table.add_row(
        _format_percent(result.get("cpuUsedPercent")),
        _format_percent(result.get("memUsedPercent")),
        _format_percent(result.get("diskUsedPercent")),
        _text(result.get("queuePending")),
        _text(result.get("queueFailed")),
        _text(result.get("siteCount")),
        _text(result.get("downloaderCount")),
        _text(result.get("mediaServerCount")),
        _text(result.get("cloudCount")),
    )
    console.print(table)


def output_system_health_report(result: dict[str, Any]) -> None:
    console.print("[bold]System Health Report[/bold]")
    overall = str(result.get("overall", "") or "")
    overall_label = {"ok": "正常", "warn": "警告", "error": "异常"}.get(overall, overall)
    console.print(
        f"Overall: {overall_label} / Score: {result.get('score', 0)} / "
        f"OK {result.get('okCount', 0)} / Warn {result.get('warnCount', 0)} / Error {result.get('errorCount', 0)}"
    )

    groups = result.get("groups") or []
    if not groups:
        console.print("[dim](空)[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Group")
    table.add_column("Status")
    table.add_column("Item")
    table.add_column("Summary")
    table.add_column("Suggestion")
    for group in groups:
        if not isinstance(group, dict):
            continue
        for item in group.get("items") or []:
            if not isinstance(item, dict):
                continue
            status = str(item.get("status", "") or "")
            if status == "ok":
                continue
            table.add_row(
                _text(item.get("group_title") or group.get("title")),
                status,
                _text(item.get("title")),
                _text(item.get("summary")),
                _text(item.get("suggestion")),
            )
    console.print(table)
    console.print("[dim]只列出非正常检查项；全部正常时表格为空[/dim]")


def output_system_version(result: dict[str, Any]) -> None:
    console.print("[bold]System Version[/bold]")
    if result.get("has_update"):
        console.print(f"[yellow]有可用更新[/yellow]: {result.get('latest_version', '')}")
    else:
        console.print("[green]已是最新版本[/green]")


def output_calendar_list(result: dict[str, Any]) -> None:
    console.print("[bold]Subscribe Calendar[/bold]")
    console.print(f"[cyan]Start[/cyan]: {result.get('start', '')} / [cyan]Days[/cyan]: {result.get('days', '')} / [cyan]Total[/cyan]: {result.get('total', 0)}")

    days_list = result.get("days_list") or []
    if not days_list:
        console.print("[dim](空)[/dim]")
        return

    for day in days_list:
        console.print(f"[cyan]{day.get('date', '')}[/cyan]")
        for item in day.get("items") or []:
            season = item.get("season") or 0
            episode = item.get("episode") or 0
            season_episode = f"S{season:02d}E{episode:02d}" if season or episode else ""
            title = str(item.get("name", "") or "")
            year = item.get("year")
            header = title if year in (None, "") else f"{title} ({year})"
            line = f"  {header}"
            if season_episode:
                line += f" {season_episode}"
            if item.get("air_time_text"):
                line += f" · {item.get('air_time_text')}"
            console.print(line)


def output_calendar_ical_urls(result: dict[str, Any]) -> None:
    console.print("[bold]Calendar iCal URLs[/bold]")
    items = result.get("items") or []
    if not items:
        reason = str(result.get("empty_reason", "") or "")
        reason_text = {
            "missingDomain": "系统尚未配置外部访问域名，请先在系统设置中填写",
            "missingApiKey": "尚未创建 API Key，请先在安全中心创建",
        }.get(reason, reason or "(空)")
        console.print(f"[dim]{reason_text}[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Title")
    table.add_column("iCal URL")
    for item in items:
        table.add_row(_text(item.get("title")), _text(item.get("ical_url")))
    console.print(table)


def output_media_health_page(result: dict[str, Any]) -> None:
    console.print("[bold]Media Health[/bold]")
    summary = result.get("summary") if isinstance(result.get("summary"), dict) else {}
    summary_text = " / ".join(
        f"{label} {summary.get(key, 0)}"
        for key, label in (
            ("missing", "缺集"),
            ("unmatched", "未匹配"),
            ("upgrade", "可升级"),
            ("subtitle_missing", "缺字幕"),
            ("processing", "处理中"),
            ("ignored", "已忽略"),
        )
    )
    console.print(f"[cyan]Summary[/cyan]: {summary_text}")
    items = result.get("list") or []
    console.print(
        f"Page: {result.get('pageNum', 1)} / Page Size: {result.get('pageSize', len(items))} / Total: {result.get('total', 0)}"
    )
    _print_media_health_items(items)


def output_media_health_detail(item: dict[str, Any]) -> None:
    console.print("[bold]Media Health Detail[/bold]")
    _print_media_health_items([item])


def output_media_health_preview(result: dict[str, Any]) -> None:
    console.print("[bold]Subscribe Missing Preview[/bold]")
    console.print(f"[cyan]Action[/cyan]: {result.get('action_text', '')} ({result.get('action', '')})")
    console.print(f"[cyan]Season[/cyan]: {result.get('season', '')}")
    console.print(f"[cyan]Episodes[/cyan]: {result.get('episodes_text', '')}")
    subscribe_id = result.get("subscribe_id")
    if subscribe_id:
        console.print(f"[cyan]Subscribe ID[/cyan]: {subscribe_id}")
    already_in_library = result.get("already_in_library") or []
    already_downloaded = result.get("already_downloaded") or []
    if already_in_library:
        console.print(f"[cyan]已入库被剔除[/cyan]: {', '.join(str(ep) for ep in already_in_library)}")
    if already_downloaded:
        console.print(f"[cyan]已下载被剔除[/cyan]: {', '.join(str(ep) for ep in already_downloaded)}")


def output_media_health_operation(result: dict[str, Any]) -> None:
    console.print(f"[bold green]媒体健康操作 {result.get('action', '')} 已提交[/bold green]")
    console.print(f"Issue Key: {result.get('issue_key', '')}")
    if result.get("message"):
        console.print(f"Message: {result.get('message')}")


def _print_media_health_items(items: list[dict[str, Any]]) -> None:
    if not items:
        console.print("[dim](空)[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Title")
    table.add_column("Type")
    table.add_column("Status")
    table.add_column("Seasons")
    table.add_column("Library")
    table.add_column("Issue Key")
    for item in items:
        seasons = item.get("seasons") if isinstance(item.get("seasons"), list) else []
        season_text = "\n".join(
            f"S{season.get('season', 0):02d} 缺 {season.get('missing_text', '-')}"
            for season in seasons
            if isinstance(season, dict)
        )
        table.add_row(
            _text(item.get("title")),
            _text(item.get("issue_type")),
            _text(item.get("status")),
            season_text,
            _text(item.get("library_name")),
            _text(item.get("issue_key")),
        )
    console.print(table)


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


def output_media_server_search(result: dict[str, Any]) -> None:
    console.print("[bold]Media Server Search[/bold]")
    items = result.get("list") or []
    console.print(f"Total: {result.get('total', len(items))}")
    if not items:
        console.print("[dim](空)[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Title")
    table.add_column("Type")
    table.add_column("Year")
    table.add_column("Rating")
    table.add_column("TMDB")
    table.add_column("Poster")
    for item in items:
        rating = item.get("rating")
        table.add_row(
            _text(item.get("title")),
            _text(item.get("media_type")),
            _text(item.get("year")),
            "-" if rating in (None, "") else f"{float(rating):.1f}",
            _text(item.get("tmdb_id")),
            _text(item.get("image")),
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


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)
