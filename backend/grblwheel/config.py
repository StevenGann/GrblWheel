"""Load and validate configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


DEFAULT_CONFIG: dict[str, Any] = {
    "server": {"host": "0.0.0.0", "port": 8765},
    "serial": {"baud": 115200, "port": None},
    "paths": {"upload_dir": "gcode", "config_dir": "."},
    "gpio_enabled": False,
    "macros": {
        "zero_xy": ["G10 L20 X0 Y0"],
        "zero_z": ["G10 L20 Z0"],
        "z_probe": ["G38.2 Z-50 F100", "G10 L20 Z0"],
    },
    "hardware": {
        "buttons": {},
        "encoder": {"clk": 5, "dt": 6, "sw": None},
        "jog_mode_switch": [],
    },
}


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load YAML config from path or from env GRBLWHEEL_CONFIG or default paths."""
    if path is None:
        path = os.environ.get("GRBLWHEEL_CONFIG")
    if path is None:
        for candidate in ("config.yaml", "config/config.yaml"):
            if Path(candidate).exists():
                path = candidate
                break
    if path is None:
        return dict(DEFAULT_CONFIG)

    path = Path(path)
    if not path.exists():
        return dict(DEFAULT_CONFIG)

    with open(path, encoding="utf-8") as f:
        loaded = yaml.safe_load(f) or {}

    config = _deep_merge(DEFAULT_CONFIG, loaded)
    # Resolve paths relative to config file directory
    config_dir = path.parent
    if "paths" in config:
        ud = config["paths"].get("upload_dir")
        if ud and not Path(ud).is_absolute():
            config["paths"]["upload_dir"] = str(config_dir / ud)
    return config
