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


def load_phase8_config(path: str | Path) -> dict[str, Any]:
    """Load and validate the communication-aware Phase 8 configuration."""
    config = load_yaml(path)
    phase8 = config.get("phase8")
    if not isinstance(phase8, dict):
        raise ValueError(f"Missing phase8 mapping in {path}")
    policy = phase8.get("policy")
    communication = phase8.get("communication")
    freshness = phase8.get("freshness")
    if not isinstance(policy, dict) or policy.get("variant") != "freshness_aware_iql":
        raise ValueError("Phase 8 policy variant must be freshness_aware_iql")
    if policy.get("observation_size") != 23:
        raise ValueError("Phase 8 observation_size must be 23")
    if not isinstance(communication, dict):
        raise ValueError("Missing Phase 8 communication mapping")
    probability = communication.get("packet_loss_probability")
    if not isinstance(probability, (int, float)) or not 0 <= probability <= 1:
        raise ValueError("packet_loss_probability must be between 0 and 1")
    if communication.get("delay_model") != "fixed":
        raise ValueError("Phase 8 delay_model must be fixed")
    delay_ms = communication.get("delay_ms")
    if not isinstance(delay_ms, (int, float)) or delay_ms < 0:
        raise ValueError("Phase 8 delay_ms must be non-negative")
    if not isinstance(freshness, dict) or freshness.get("enabled") is not True:
        raise ValueError("Phase 8 freshness must be enabled")
    from traffic_control.communication import FreshnessConfig

    FreshnessConfig(
        float(freshness["freshness_decay_tau_ms"]),
        float(freshness["max_message_age_ms"]),
        float(freshness["stale_message_threshold_ms"]),
    )
    return phase8
