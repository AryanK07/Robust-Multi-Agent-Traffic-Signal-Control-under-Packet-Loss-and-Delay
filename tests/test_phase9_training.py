import json
from pathlib import Path

import pytest

from traffic_control.experiments import (
    BalancedConditionSchedule,
    Phase9TrainingConfig,
    derive_episode_seeds,
    generate_phase7_conditions,
    load_phase7_config,
    load_phase9_metadata,
    phase9_metadata,
    save_phase9_checkpoint,
    validate_phase9_config,
)
from traffic_control.rl import CommunicationAwareLinearQAgent


def test_balanced_schedule_is_reproducible_and_covers_each_condition() -> None:
    phase7 = load_phase7_config("configs/phase7.yaml")
    conditions = generate_phase7_conditions(phase7)
    first = BalancedConditionSchedule(conditions, 7)
    second = BalancedConditionSchedule(conditions, 7)
    first_cycle = [first.next() for _ in conditions]
    second_cycle = [second.next() for _ in conditions]
    assert first_cycle == second_cycle
    assert set(first_cycle) == set(conditions)
    assert sum(first.exposure_counts.values()) == 25


def test_schedule_seed_and_incomplete_cycle_are_recorded() -> None:
    phase7 = load_phase7_config("configs/phase7.yaml")
    schedule = BalancedConditionSchedule(generate_phase7_conditions(phase7), 7)
    selected = [schedule.next() for _ in range(3)]
    assert len(selected) == 3
    assert sum(schedule.exposure_counts.values()) == 3
    assert schedule.seed == 7


def test_ideal_schedule_is_only_ideal_and_robust_schedule_is_not() -> None:
    phase7 = load_phase7_config("configs/phase7.yaml")
    conditions = generate_phase7_conditions(phase7)
    ideal = BalancedConditionSchedule(conditions, 7, ideal_only=True)
    assert [ideal.next() for _ in range(3)] == [(conditions[0])] * 3
    robust = BalancedConditionSchedule(conditions, 7)
    assert any(
        condition.packet_loss_probability > 0 or condition.delay_ms > 0
        for condition in [robust.next(), robust.next()]
    )


def test_episode_seed_streams_are_stable_and_distinct() -> None:
    config = Phase9TrainingConfig(42, 7, 8, 9, 2, 1, Path("results"), "robust_trained_communication_aware_iql")
    assert derive_episode_seeds(config, 1) == derive_episode_seeds(config, 1)
    assert derive_episode_seeds(config, 1) != derive_episode_seeds(config, 2)


def test_phase9_checkpoint_metadata_and_separation(tmp_path: Path) -> None:
    phase7 = load_phase7_config("configs/phase7.yaml")
    config = Phase9TrainingConfig(42, 7, 8, 9, 2, 1, tmp_path, "robust_trained_communication_aware_iql")
    learners = {
        "A0": CommunicationAwareLinearQAgent(neighbor_ids=("A1", "B0")),
    }
    metadata = phase9_metadata(
        config, phase7, {"loss_0p00__delay_0ms": 1},
        agent_ids=("A0",), freshness={
            "freshness_decay_tau_ms": 500.0,
            "max_message_age_ms": 2000.0,
            "stale_message_threshold_ms": 1000.0,
        }, episode_records=1,
    )
    save_phase9_checkpoint(tmp_path, learners, metadata)
    restored = load_phase9_metadata(tmp_path / "metadata.json")
    assert restored["policy_variant"] == "robust_trained_communication_aware_iql"
    with pytest.raises(FileExistsError):
        save_phase9_checkpoint(tmp_path, learners, metadata)


def test_phase9_configuration_validation() -> None:
    with open("configs/phase9.yaml", encoding="utf-8") as stream:
        config = json.loads(json.dumps(__import__("yaml").safe_load(stream)))
    assert validate_phase9_config(config)["episodes"] > 0
    with pytest.raises(ValueError):
        validate_phase9_config({"phase9": {"episodes": 1}})
