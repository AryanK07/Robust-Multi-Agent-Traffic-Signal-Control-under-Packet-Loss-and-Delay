"""Reproducible final evaluation and statistical analysis for Phase 11."""

from dataclasses import dataclass
import hashlib
import json
from math import sqrt
from pathlib import Path
from statistics import mean, median, stdev
from typing import Any, Iterable

import numpy as np

from .phase7 import Phase7Condition, Phase7Config, generate_phase7_conditions


COMMUNICATION_POLICIES = (
    "ideal_trained_communication_aware_iql",
    "robust_trained_communication_aware_iql",
)
COMMUNICATION_STRATEGIES = ("always", "periodic", "adaptive")


@dataclass(frozen=True)
class Phase11Config:
    """Validated frozen design for the final campaign."""

    name: str
    master_seeds: tuple[int, ...]
    training_episodes: int
    max_steps_per_episode: int
    evaluation_output_directory: Path
    checkpoint_directory: Path
    periodic_interval_ms: float
    adaptive_change_threshold: float
    adaptive_max_silence_ms: float
    freshness_decay_tau_ms: float
    max_message_age_ms: float
    stale_message_threshold_ms: float


def validate_phase11_config(config: dict[str, Any]) -> Phase11Config:
    section = config.get("phase11")
    if not isinstance(section, dict):
        raise ValueError("Missing phase11 configuration mapping")
    name = section.get("name")
    seeds = section.get("master_seeds")
    if not isinstance(name, str) or not name:
        raise ValueError("phase11.name must be a non-empty string")
    if not isinstance(seeds, list) or not seeds or any(
        not isinstance(seed, int) or isinstance(seed, bool) or seed < 0 for seed in seeds
    ):
        raise ValueError("phase11.master_seeds must contain non-negative integers")
    if len(set(seeds)) != len(seeds):
        raise ValueError("phase11.master_seeds must not contain duplicates")
    training_episodes = _positive_int(section.get("training_episodes"), "training_episodes")
    max_steps = _positive_int(section.get("max_steps_per_episode"), "max_steps_per_episode")
    output = _path_value(section.get("evaluation_output_directory"), "evaluation_output_directory")
    checkpoints = _path_value(section.get("checkpoint_directory"), "checkpoint_directory")
    scheduler = section.get("scheduler", {})
    freshness = section.get("freshness", {})
    periodic = _positive_float(scheduler.get("periodic_interval_ms"), "periodic_interval_ms")
    threshold = float(scheduler.get("adaptive_change_threshold"))
    silence = _positive_float(
        scheduler.get("adaptive_max_silence_ms"), "adaptive_max_silence_ms"
    )
    if not 0 <= threshold <= 1:
        raise ValueError("adaptive_change_threshold must be between 0 and 1")
    tau = _positive_float(freshness.get("freshness_decay_tau_ms"), "freshness_decay_tau_ms")
    max_age = _positive_float(freshness.get("max_message_age_ms"), "max_message_age_ms")
    stale = float(freshness.get("stale_message_threshold_ms"))
    if stale < 0:
        raise ValueError("stale_message_threshold_ms must be non-negative")
    return Phase11Config(
        name,
        tuple(seeds),
        training_episodes,
        max_steps,
        output,
        checkpoints,
        periodic,
        threshold,
        silence,
        tau,
        max_age,
        stale,
    )


def generate_phase11_runs(
    phase7_config: Phase7Config, phase11_config: Phase11Config
) -> tuple[dict[str, Any], ...]:
    """Generate the complete deterministic 755-episode evaluation design."""
    conditions = generate_phase7_conditions(phase7_config)
    runs: list[dict[str, Any]] = []
    for policy in COMMUNICATION_POLICIES:
        for strategy in COMMUNICATION_STRATEGIES:
            for condition in conditions:
                for replicate, master_seed in enumerate(phase11_config.master_seeds, 1):
                    runs.append(
                        _run_spec(
                            policy,
                            strategy,
                            condition,
                            master_seed,
                            replicate,
                        )
                    )
    for replicate, master_seed in enumerate(phase11_config.master_seeds, 1):
        runs.append(
            _run_spec(
                "local_only_phase3_iql",
                "none",
                Phase7Condition(0.0, 0.0),
                master_seed,
                replicate,
            )
        )
    return tuple(runs)


def derive_evaluation_seeds(master_seed: int, replicate: int) -> dict[str, int]:
    """Derive stable independent streams for one evaluation replicate."""
    if master_seed < 0 or replicate < 1:
        raise ValueError("invalid master seed or replicate")
    values = np.random.SeedSequence([master_seed, replicate]).generate_state(
        4, dtype=np.uint32
    )
    return {
        "evaluation_seed": int(values[0] % 2_147_483_647),
        "traffic_demand_seed": int(values[1] % 2_147_483_647),
        "packet_loss_seed": int(values[2] % 2_147_483_647),
        "scheduler_seed": int(values[3] % 2_147_483_647),
    }


def run_id(spec: dict[str, Any]) -> str:
    """Return a deterministic identifier from the complete run specification."""
    encoded = json.dumps(spec, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:20]


def checkpoint_sha256(directory: Path, agent_ids: tuple[str, ...]) -> str:
    """Hash all agent files in deterministic topology order."""
    digest = hashlib.sha256()
    for agent_id in agent_ids:
        path = directory / f"{agent_id}.npz"
        if not path.is_file():
            raise FileNotFoundError(f"Missing checkpoint file: {path}")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def write_raw_result(result: dict[str, Any], directory: Path) -> Path:
    """Write an immutable raw result, refusing replacement."""
    run = result.get("run_id")
    if not isinstance(run, str) or not run:
        raise ValueError("result must contain run_id")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{run}.json"
    if path.exists():
        raise FileExistsError(f"Raw result already exists: {path}")
    path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return path


def load_valid_raw_results(directory: Path) -> dict[str, dict[str, Any]]:
    """Load successful or failed raw records while rejecting corrupted JSON."""
    results: dict[str, dict[str, Any]] = {}
    if not directory.exists():
        return results
    for path in sorted(directory.glob("*.json")):
        try:
            result = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"Corrupted raw result: {path}") from error
        if result.get("run_id") != path.stem:
            raise ValueError(f"Raw result filename does not match run_id: {path}")
        results[path.stem] = result
    return results


def aggregate_phase11_results(results: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate successful records by policy, strategy, and condition."""
    groups: dict[tuple[str, str, float, float], list[dict[str, Any]]] = {}
    for result in results:
        if result.get("status") != "success":
            continue
        key = (
            str(result["policy_variant"]),
            str(result["communication_strategy"]),
            float(result["packet_loss_probability"]),
            float(result["delay_ms"]),
        )
        groups.setdefault(key, []).append(result)
    summaries: list[dict[str, Any]] = []
    for key, rows in sorted(groups.items()):
        policy, strategy, loss, delay = key
        summary: dict[str, Any] = {
            "policy_variant": policy,
            "communication_strategy": strategy,
            "packet_loss_probability": loss,
            "delay_ms": delay,
            "sample_count": len(rows),
        }
        for metric in (
            "average_waiting_time",
            "total_waiting_time",
            "mean_queue_length",
            "max_queue_length",
            "completed_trips",
            "episode_reward",
            "send_attempts",
            "successful_transmissions",
            "dropped_messages",
            "delivered_messages",
            "observed_packet_loss_rate",
            "average_message_age_ms",
            "maximum_message_age_ms",
            "stale_message_proportion",
            "pending_messages",
            "scheduling_opportunities",
            "suppressed_transmissions",
            "communication_reduction",
        ):
            values = [float(row[metric]) for row in rows if row.get(metric) is not None]
            if values:
                summary[f"{metric}_mean"] = mean(values)
                summary[f"{metric}_std"] = stdev(values) if len(values) > 1 else 0.0
                summary[f"{metric}_median"] = median(values)
        summaries.append(summary)
    return summaries


def paired_differences(
    results: Iterable[dict[str, Any]],
    left_policy: str,
    right_policy: str,
    metric: str,
) -> dict[str, Any]:
    """Calculate matched-seed differences without treating episodes as independent."""
    left: dict[int, list[float]] = {}
    right: dict[int, list[float]] = {}
    for result in results:
        if result.get("status") != "success" or result.get(metric) is None:
            continue
        if result["policy_variant"] == left_policy:
            left.setdefault(int(result["master_seed"]), []).append(float(result[metric]))
        elif result["policy_variant"] == right_policy:
            right.setdefault(int(result["master_seed"]), []).append(float(result[metric]))
    differences = [
        mean(left[seed]) - mean(right[seed])
        for seed in left.keys() & right.keys()
    ]
    return _descriptive_difference(differences, metric, left_policy, right_policy)


def _descriptive_difference(
    values: list[float], metric: str, left_policy: str, right_policy: str
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "metric": metric,
        "left": left_policy,
        "right": right_policy,
        "sample_count": len(values),
        "mean_difference": mean(values) if values else None,
        "median_difference": median(values) if values else None,
        "standard_deviation": stdev(values) if len(values) > 1 else 0.0 if values else None,
        "confidence_interval_95": None,
        "inference_note": "Five master-seed replicates provide limited statistical power.",
    }
    if len(values) > 1:
        standard_error = stdev(values) / sqrt(len(values))
        result["confidence_interval_95"] = [
            mean(values) - 1.96 * standard_error,
            mean(values) + 1.96 * standard_error,
        ]
    return result


def _run_spec(
    policy: str,
    strategy: str,
    condition: Phase7Condition,
    master_seed: int,
    replicate: int,
) -> dict[str, Any]:
    seeds = derive_evaluation_seeds(master_seed, replicate)
    spec = {
        "policy_variant": policy,
        "communication_strategy": strategy,
        "packet_loss_probability": condition.packet_loss_probability,
        "delay_ms": condition.delay_ms,
        "master_seed": master_seed,
        "replicate": replicate,
        **seeds,
    }
    spec["run_id"] = run_id(spec)
    return spec


def _positive_int(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _positive_float(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be a positive finite number") from error
    if not np.isfinite(number) or number <= 0:
        raise ValueError(f"{name} must be a positive finite number")
    return number


def _path_value(value: Any, name: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty path")
    return Path(value)
