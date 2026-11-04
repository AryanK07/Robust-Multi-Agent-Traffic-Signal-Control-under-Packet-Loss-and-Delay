"""Reproducible robust-training utilities for the Phase 8 policy."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import numpy as np

from .phase7 import Phase7Condition, Phase7Config, generate_phase7_conditions


@dataclass(frozen=True)
class Phase9TrainingConfig:
    """Validated training settings for ideal and robust policies."""

    training_seed: int
    condition_schedule_seed: int
    packet_loss_seed: int
    sumo_seed: int
    episodes: int
    max_steps_per_episode: int
    output_directory: Path
    policy_variant: str

    def __post_init__(self) -> None:
        if self.policy_variant not in {
            "ideal_trained_communication_aware_iql",
            "robust_trained_communication_aware_iql",
        }:
            raise ValueError("unsupported Phase 9 policy variant")
        for name in ("training_seed", "condition_schedule_seed", "packet_loss_seed", "sumo_seed"):
            if not isinstance(getattr(self, name), int) or getattr(self, name) < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.episodes <= 0 or self.max_steps_per_episode <= 0:
            raise ValueError("episodes and max_steps_per_episode must be positive")


def validate_phase9_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate the YAML phase9 section without running training."""
    section = config.get("phase9")
    if not isinstance(section, dict):
        raise ValueError("Missing phase9 configuration mapping")
    for key in (
        "episodes",
        "max_steps_per_episode",
        "training_seed",
        "condition_schedule_seed",
        "packet_loss_seed",
        "sumo_seed",
    ):
        if key not in section:
            raise ValueError(f"Missing phase9.{key}")
    freshness = section.get("freshness")
    if not isinstance(freshness, dict):
        raise ValueError("Missing phase9.freshness mapping")
    if any(key not in freshness for key in (
        "freshness_decay_tau_ms",
        "max_message_age_ms",
        "stale_message_threshold_ms",
    )):
        raise ValueError("Incomplete phase9 freshness configuration")
    return section


class BalancedConditionSchedule:
    """Reproducibly shuffle one complete condition cycle at a time."""

    def __init__(
        self,
        conditions: tuple[Phase7Condition, ...],
        seed: int,
        *,
        ideal_only: bool = False,
    ) -> None:
        if not conditions:
            raise ValueError("conditions must not be empty")
        self._conditions = conditions
        self._rng = np.random.default_rng(seed)
        self.seed = seed
        self.ideal_only = ideal_only
        self._order: list[Phase7Condition] = []
        self._position = 0
        self.exposure_counts = {condition.condition_id: 0 for condition in conditions}

    def next(self) -> Phase7Condition:
        if self.ideal_only:
            condition = Phase7Condition(0.0, 0.0)
        else:
            if self._position >= len(self._order):
                permutation = self._rng.permutation(len(self._conditions))
                self._order = [self._conditions[index] for index in permutation]
                self._position = 0
            condition = self._order[self._position]
            self._position += 1
        self.exposure_counts[condition.condition_id] = (
            self.exposure_counts.get(condition.condition_id, 0) + 1
        )
        return condition


def derive_episode_seeds(config: Phase9TrainingConfig, episode: int) -> dict[str, int]:
    """Derive independent, stable streams without process-randomized hashing."""
    if episode < 1:
        raise ValueError("episode must be positive")
    sequence = np.random.SeedSequence(
        [config.training_seed, config.packet_loss_seed, config.sumo_seed, episode]
    )
    values = sequence.generate_state(3, dtype=np.uint32)
    return {
        "training_seed": int(values[0] % 2_147_483_647),
        "packet_loss_seed": int(values[1] % 2_147_483_647),
        "sumo_seed": int(values[2] % 2_147_483_647),
    }


def phase9_metadata(
    config: Phase9TrainingConfig,
    phase7_config: Phase7Config,
    exposure_counts: dict[str, int],
    *,
    agent_ids: tuple[str, ...],
    freshness: dict[str, float],
    episode_records: int,
) -> dict[str, Any]:
    """Build complete, explicit metadata for a Phase 9 checkpoint."""
    return {
        "policy_variant": config.policy_variant,
        "phase": 9,
        "training_seed": config.training_seed,
        "agent_ids": list(agent_ids),
        "observation_dimension": 23,
        "observation_schema_version": "local_plus_neighbor_freshness_v1",
        "ordered_neighbor_ids": {
            "A0": ["A1", "B0"],
            "A1": ["A0", "B1"],
            "B0": ["A0", "B1"],
            "B1": ["A1", "B0"],
        },
        "freshness": freshness,
        "action_definition": "0=maintain phase, 1=select next green phase",
        "reward_definition": "existing local queue/waiting-time delta reward",
        "learning_algorithm": "independent_linear_q_learning",
        "training_episodes": config.episodes,
        "max_steps_per_episode": config.max_steps_per_episode,
        "training_condition_distribution": {
            "packet_loss_levels": list(phase7_config.packet_loss_levels),
            "delay_levels_ms": list(phase7_config.delay_levels_ms),
        },
        "condition_scheduling_method": "balanced_shuffled_cycle",
        "condition_schedule_seed": config.condition_schedule_seed,
        "packet_loss_seed_strategy": "SeedSequence per episode",
        "sumo_seed_strategy": "SeedSequence per episode",
        "condition_exposure_counts": exposure_counts,
        "episode_records": episode_records,
    }


def save_phase9_checkpoint(
    directory: Path,
    learners: dict[str, Any],
    metadata: dict[str, Any],
) -> Path:
    """Save separate agent files and metadata, refusing accidental overwrite."""
    directory.mkdir(parents=True, exist_ok=True)
    metadata_path = directory / "metadata.json"
    if metadata_path.exists():
        raise FileExistsError(f"Checkpoint metadata already exists: {metadata_path}")
    for agent_id, learner in learners.items():
        learner.save(directory / f"{agent_id}.npz")
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return metadata_path


def load_phase9_metadata(path: Path) -> dict[str, Any]:
    """Load and validate essential Phase 9 checkpoint metadata."""
    metadata = json.loads(path.read_text(encoding="utf-8"))
    required = (
        "policy_variant",
        "phase",
        "observation_dimension",
        "observation_schema_version",
        "ordered_neighbor_ids",
        "condition_scheduling_method",
    )
    if any(key not in metadata for key in required):
        raise ValueError("incomplete Phase 9 checkpoint metadata")
    if metadata["phase"] != 9 or metadata["observation_dimension"] != 23:
        raise ValueError("incompatible Phase 9 checkpoint metadata")
    if metadata["policy_variant"] not in {
        "ideal_trained_communication_aware_iql",
        "robust_trained_communication_aware_iql",
    }:
        raise ValueError("unsupported Phase 9 checkpoint policy variant")
    return metadata
