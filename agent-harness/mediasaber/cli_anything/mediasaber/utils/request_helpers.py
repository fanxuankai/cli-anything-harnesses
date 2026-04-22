from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click


def parse_key_value_pairs(items: tuple[str, ...], *, item_name: str = "key=value pair") -> dict[str, str]:
    payload = {}
    for item in items:
        if "=" not in item:
            raise click.ClickException(f"invalid {item_name}: {item}")
        key, value = item.split("=", 1)
        payload[key] = value
    return payload


def parse_file_pairs(items: tuple[str, ...]) -> dict[str, str]:
    return parse_key_value_pairs(items, item_name="field=path pair")


def read_body_text(body: str | None, body_file: str | None) -> str | None:
    if body and body_file:
        raise click.ClickException("use either --body or --body-file, not both")
    if body_file:
        return Path(body_file).read_text(encoding="utf-8")
    return body


def read_json_payload(body: str | None, body_file: str | None) -> Any | None:
    raw = read_body_text(body, body_file)
    if raw is None or raw == "":
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"invalid JSON body: {exc}") from exc


def write_output_file(path: str, content: bytes) -> dict[str, Any]:
    output_path = Path(path).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(content)
    return {
        "output": str(output_path),
        "bytes": len(content),
    }
