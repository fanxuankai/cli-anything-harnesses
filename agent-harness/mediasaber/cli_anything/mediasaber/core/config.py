from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


def _compact_dict(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value not in (None, "", {}, [])}


@dataclass
class HarnessConfig:
    url: str | None = None
    token: str | None = None
    api_key: str | None = None
    source_path: str | None = None
    profiles: dict[str, dict[str, Any]] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    future: list[dict[str, Any]] = field(default_factory=list)

    def current_state(self) -> dict[str, Any]:
        return _compact_dict(
            {
                "url": self.url,
                "token": self.token,
                "api_key": self.api_key,
                "source_path": self.source_path,
            }
        )


class ConfigManager:
    DEFAULT_CONFIG_PATH = Path.home() / ".mediasaber-cli.yaml"
    HISTORY_LIMIT = 20

    def __init__(self, path: Path | None = None):
        self.path = path or self.DEFAULT_CONFIG_PATH

    def load(self) -> HarnessConfig:
        if not self.path.exists():
            return HarnessConfig()
        data = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        return HarnessConfig(
            url=data.get("url"),
            token=data.get("token"),
            api_key=data.get("api_key"),
            source_path=data.get("source_path"),
            profiles=data.get("profiles") or {},
            history=data.get("history") or [],
            future=data.get("future") or [],
        )

    def save(self, config: HarnessConfig) -> HarnessConfig:
        payload = _compact_dict(
            {
                "url": config.url,
                "token": config.token,
                "api_key": config.api_key,
                "source_path": config.source_path,
                "profiles": config.profiles,
                "history": config.history,
                "future": config.future,
            }
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        return config

    def _push_history(self, config: HarnessConfig) -> None:
        snapshot = deepcopy(config.current_state())
        if snapshot:
            config.history.append(snapshot)
            config.history = config.history[-self.HISTORY_LIMIT :]
        config.future = []

    def update_state(self, **updates: Any) -> HarnessConfig:
        config = self.load()
        self._push_history(config)
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return self.save(config)

    def clear_state(self, *keys: str) -> HarnessConfig:
        config = self.load()
        self._push_history(config)
        for key in keys:
            if hasattr(config, key):
                setattr(config, key, None)
        return self.save(config)

    def save_profile(self, name: str, state: dict[str, Any]) -> HarnessConfig:
        config = self.load()
        config.profiles[name] = _compact_dict(deepcopy(state))
        return self.save(config)

    def get_profile(self, name: str) -> dict[str, Any] | None:
        return deepcopy(self.load().profiles.get(name))

    def use_profile(self, name: str) -> HarnessConfig:
        profile = self.get_profile(name)
        if not profile:
            raise KeyError(f"profile not found: {name}")
        return self.update_state(**profile)

    def undo(self) -> dict[str, Any]:
        config = self.load()
        if not config.history:
            raise ValueError("no session change to undo")
        config.future.append(deepcopy(config.current_state()))
        previous = config.history.pop()
        config.url = previous.get("url")
        config.token = previous.get("token")
        config.api_key = previous.get("api_key")
        config.source_path = previous.get("source_path")
        self.save(config)
        return previous

    def redo(self) -> dict[str, Any]:
        config = self.load()
        if not config.future:
            raise ValueError("no session change to redo")
        config.history.append(deepcopy(config.current_state()))
        next_state = config.future.pop()
        config.url = next_state.get("url")
        config.token = next_state.get("token")
        config.api_key = next_state.get("api_key")
        config.source_path = next_state.get("source_path")
        self.save(config)
        return next_state
