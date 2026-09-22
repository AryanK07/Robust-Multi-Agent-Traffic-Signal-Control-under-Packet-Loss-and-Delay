"""Configuration loading helpers for the simulator environment."""

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML mapping from a repository-relative or absolute path."""
    config_path = Path(path)
    with config_path.open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)

    if not isinstance(config, dict):
        raise ValueError(f"Expected a YAML mapping in {config_path}")
    return config


def load_network_config(path: str | Path) -> dict[str, Any]:
    """Load and validate the Phase 1 network configuration section."""
    config = load_yaml(path)
    network = config.get("network")
    if not isinstance(network, dict):
        raise ValueError(f"Missing network mapping in {path}")

    required = ("config_file", "sumo_binary", "sumo_gui_binary")
    missing = [key for key in required if key not in network]
    if missing:
        raise ValueError(f"Missing network configuration keys: {', '.join(missing)}")
    return network
