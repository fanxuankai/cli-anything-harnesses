from __future__ import annotations

import json
from typing import Any

import click
import yaml


def _sanitize(data: Any) -> Any:
    try:
        json.dumps(data)
        return data
    except TypeError:
        if isinstance(data, dict):
            return {str(key): _sanitize(value) for key, value in data.items()}
        if isinstance(data, (list, tuple, set)):
            return [_sanitize(item) for item in data]
        return str(data)


def output_json(data: Any) -> None:
    click.echo(json.dumps(_sanitize(data), ensure_ascii=False, indent=2, sort_keys=True))


def output_text(data: Any) -> None:
    if isinstance(data, str):
        click.echo(data)
        return
    click.echo(yaml.safe_dump(_sanitize(data), allow_unicode=True, sort_keys=False).rstrip())


def output_result(data: Any, *, json_mode: bool = False) -> None:
    if json_mode:
        output_json(data)
    else:
        output_text(data)


def output_error(message: str, *, json_mode: bool = False) -> None:
    if json_mode:
        output_json({"error": message})
    else:
        click.echo(message, err=True)


def fail(message: str, *, json_mode: bool = False, code: int = 1) -> None:
    output_error(message, json_mode=json_mode)
    raise SystemExit(code)
