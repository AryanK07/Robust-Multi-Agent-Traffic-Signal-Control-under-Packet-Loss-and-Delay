"""Configuration and comparison helpers for adaptive communication."""

from dataclasses import dataclass
from math import isfinite
from typing import Any


@dataclass(frozen=True)
class Phase10Config:
    """Validated communication scheduling configuration."""

    strategy: str
    change_threshold: float
    max_silence_ms: float
    periodic_interval_ms: float


def validate_phase10_config(config: dict[str, Any]) -> Phase10Config:
    section = config.get("phase10")
    if not isinstance(section, dict):
        raise ValueError("Missing phase10 configuration mapping")
    communication = section.get("communication", {})
    adaptive = section.get("adaptive", {})
    periodic = section.get("periodic", {})
    strategy = communication.get("strategy", "always")
    if strategy not in {"always", "periodic", "adaptive"}:
        raise ValueError("unsupported communication strategy")
    probability = communication.get("packet_loss_probability", 0.0)
    if not isfinite(float(probability)) or not 0 <= float(probability) <= 1:
        raise ValueError("packet_loss_probability must be between 0 and 1")
    if communication.get("delay_model", "fixed") != "fixed":
        raise ValueError("delay_model must be fixed")
    if not isfinite(float(communication.get("delay_ms", 0))) or float(communication.get("delay_ms", 0)) < 0:
        raise ValueError("delay_ms must be non-negative")
    threshold = adaptive.get("change_threshold", 0.10)
    silence = adaptive.get("max_silence_ms", 1000.0)
    interval = periodic.get("interval_ms", 1000.0)
    if not isfinite(float(threshold)) or not 0 <= float(threshold) <= 1:
        raise ValueError("change_threshold must be between 0 and 1")
    if not isfinite(float(silence)) or float(silence) <= 0:
        raise ValueError("max_silence_ms must be positive")
    if not isfinite(float(interval)) or float(interval) <= 0:
        raise ValueError("periodic interval_ms must be positive")
    return Phase10Config(strategy, float(threshold), float(silence), float(interval))


def communication_reduction(opportunities: int, scheduled: int) -> float:
    """Return suppressed scheduling opportunities as a fraction."""
    if opportunities < 0 or scheduled < 0 or scheduled > opportunities:
        raise ValueError("invalid scheduling counts")
    return (opportunities - scheduled) / opportunities if opportunities else 0.0
