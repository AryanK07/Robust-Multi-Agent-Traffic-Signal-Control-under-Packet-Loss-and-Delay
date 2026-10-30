"""Configuration and result handling for Phase 7 impairment experiments."""

from dataclasses import dataclass
import json
from pathlib import Path
from statistics import mean, stdev
from typing import Any, Iterable

import yaml


@dataclass(frozen=True)
class Phase7Condition:
    """One packet-loss and fixed-delay condition in the experiment matrix."""

    packet_loss_probability: float
    delay_ms: float

    @property
    def condition_id(self) -> str:
        loss = f"{self.packet_loss_probability:.2f}".replace(".", "p")
        delay = f"{self.delay_ms:g}".replace(".", "p")
        return f"loss_{loss}__delay_{delay}ms"


@dataclass(frozen=True)
class Phase7Config:
    """Validated Phase 7 experiment configuration."""

    name: str
    packet_loss_levels: tuple[float, ...]
    delay_levels_ms: tuple[float, ...]
    seeds: tuple[int, ...]
    output_directory: Path


def validate_phase7_config(config: dict[str, Any]) -> Phase7Config:
    """Validate and normalize the phase7 YAML mapping."""
    section = config.get("phase7")
    if not isinstance(section, dict):
        raise ValueError("Missing phase7 configuration mapping")
    name = section.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError("phase7.name must be a non-empty string")
    loss_levels = _finite_unique_numbers(section.get("packet_loss_levels"), "packet_loss_levels")
    if any(value < 0 or value > 1 for value in loss_levels):
        raise ValueError("packet_loss_levels must be between 0 and 1")
    delay_levels = _finite_unique_numbers(section.get("delay_levels_ms"), "delay_levels_ms")
    if any(value < 0 for value in delay_levels):
        raise ValueError("delay_levels_ms must be non-negative")
    seeds_raw = section.get("seeds")
    if not isinstance(seeds_raw, list) or not seeds_raw:
        raise ValueError("seeds must be a non-empty list")
    if any(not isinstance(seed, int) or isinstance(seed, bool) or seed < 0 for seed in seeds_raw):
        raise ValueError("seeds must contain non-negative integers")
    seeds = tuple(seeds_raw)
    if len(set(seeds)) != len(seeds):
        raise ValueError("seeds must not contain duplicates")
    output = section.get("output_directory", "results/phase7")
    if not isinstance(output, str) or not output:
        raise ValueError("output_directory must be a non-empty string")
    return Phase7Config(name, loss_levels, delay_levels, seeds, Path(output))


def load_phase7_config(path: str | Path) -> Phase7Config:
    """Load and validate a Phase 7 YAML configuration."""
    with Path(path).open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    if not isinstance(config, dict):
        raise ValueError("Expected a YAML mapping")
    return validate_phase7_config(config)


def generate_phase7_conditions(config: Phase7Config) -> tuple[Phase7Condition, ...]:
    """Generate the complete deterministic Cartesian product."""
    return tuple(
        Phase7Condition(loss, delay)
        for loss in config.packet_loss_levels
        for delay in config.delay_levels_ms
    )


def write_raw_result(result: dict[str, Any], directory: Path) -> Path:
    """Write one immutable run result, refusing accidental replacement."""
    directory.mkdir(parents=True, exist_ok=True)
    run_id = result.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("result must contain a non-empty run_id")
    path = directory / f"{run_id}.json"
    if path.exists():
        raise FileExistsError(f"Raw result already exists: {path}")
    path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return path


def aggregate_phase7_results(results: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate successful numeric results by communication condition."""
    grouped: dict[tuple[float, float], list[dict[str, Any]]] = {}
    for result in results:
        if result.get("status") != "success":
            continue
        key = (
            float(result["packet_loss_probability"]),
            float(result["delay_ms"]),
        )
        grouped.setdefault(key, []).append(result)
    summaries = []
    for (loss, delay), rows in sorted(grouped.items()):
        summary: dict[str, Any] = {
            "packet_loss_probability": loss,
            "delay_ms": delay,
            "sample_count": len(rows),
        }
        for key in (
            "average_waiting_time",
            "mean_queue_length",
            "completed_trips",
            "episode_reward",
            "observed_loss_rate",
            "message_age_mean",
        ):
            values = [float(row[key]) for row in rows if row.get(key) is not None]
            if values:
                summary[f"{key}_mean"] = mean(values)
                summary[f"{key}_std"] = stdev(values) if len(values) > 1 else 0.0
        summaries.append(summary)
    return summaries


def _finite_unique_numbers(value: Any, name: str) -> tuple[float, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{name} must be a non-empty list")
    normalized = tuple(float(item) for item in value)
    if any(item != item or item in (float("inf"), float("-inf")) for item in normalized):
        raise ValueError(f"{name} must contain finite numbers")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must not contain duplicates")
    return normalized
