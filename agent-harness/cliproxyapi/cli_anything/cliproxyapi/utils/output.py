"""输出格式化工具。"""

from __future__ import annotations

import json
from typing import Any, List, Dict

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()
error_console = Console(stderr=True)


def output_json(data: Any) -> None:
    """输出 JSON 格式。"""
    console.print(json.dumps(data, indent=2, ensure_ascii=False))


def output_result(data: Any, json_mode: bool = False) -> None:
    """统一输出入口。"""
    if json_mode:
        output_json(data)
    elif isinstance(data, str):
        console.print(data)
    elif isinstance(data, dict):
        _output_dict(data)
    elif isinstance(data, list):
        _output_list(data)
    else:
        console.print(str(data))


def _output_dict(data: dict) -> None:
    if "value" in data and len(data) <= 2:
        console.print(str(data["value"]))
    elif "status" in data and data["status"] == "ok":
        console.print("[green]OK[/green]")
    elif "error" in data:
        console.print(f"[red]错误: {data['error']}[/red]")
    else:
        console.print_json(json.dumps(data, ensure_ascii=False))


def _output_list(data: list) -> None:
    if not data:
        console.print("[dim](空)[/dim]")
        return
    for item in data:
        if isinstance(item, dict):
            _output_dict(item)
        else:
            console.print(str(item))


def output_table(headers: List[str], rows: List[List[str]], title: str = "") -> None:
    """输出 Rich 表格。"""
    table = Table(title=title, show_header=True, header_style="bold cyan")
    for h in headers:
        table.add_column(h)
    for row in rows:
        table.add_row(*[str(c) for c in row])
    console.print(table)


def output_kv(data: dict, title: str = "") -> None:
    """输出键值对。"""
    if title:
        console.print(f"[bold]{title}[/bold]")
    for k, v in data.items():
        console.print(f"  [cyan]{k}[/cyan]: {v}")


def output_error(msg: str) -> None:
    error_console.print(f"[red]错误: {msg}[/red]")
