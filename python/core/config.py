import json
from pathlib import Path


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        config = json.load(f)
    config.setdefault("features", {})
    config.setdefault("media", {})
    return config


def feature_enabled(config: dict, name: str) -> bool:
    return bool(config["features"].get(name, False))


def media_type_enabled(config: dict, media_type: str) -> bool:
    return media_type in config["media"].get("enabled_types", [])
