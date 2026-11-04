"""Run short ideal and impairment-randomized Phase 9 training verification."""

import json
from pathlib import Path
import tempfile

import numpy as np
import yaml

from traffic_control.communication import FreshnessConfig
from traffic_control.experiments import (
    BalancedConditionSchedule,
    Phase9TrainingConfig,
    derive_episode_seeds,
    generate_phase7_conditions,
    load_phase7_config,
    load_phase9_metadata,
    phase9_metadata,
    save_phase9_checkpoint,
)
from traffic_control.rl import (
    AGENT_IDS,
    CommunicationAwareEnvironmentConfig,
    CommunicationAwareLinearQAgent,
    CommunicationAwareMultiAgentEnvironment,
)

ROOT = Path(__file__).parents[1]


def train_variant(
    config: Phase9TrainingConfig,
    phase7_config,
    freshness: FreshnessConfig,
    output_directory: Path,
) -> dict[str, object]:
    conditions = generate_phase7_conditions(phase7_config)
    schedule = BalancedConditionSchedule(
        conditions, config.condition_schedule_seed, ideal_only=config.policy_variant.startswith("ideal")
    )
    learners = {
        agent_id: CommunicationAwareLinearQAgent(
            neighbor_ids=(
                ("A1", "B0") if agent_id == "A0" else
                ("A0", "B1") if agent_id == "A1" else
                ("A0", "B1") if agent_id == "B0" else ("A1", "B0")
            ),
            seed=config.training_seed + index,
        )
        for index, agent_id in enumerate(AGENT_IDS)
    }
    records: list[dict[str, object]] = []
    for episode in range(1, config.episodes + 1):
        condition = schedule.next()
        seeds = derive_episode_seeds(config, episode)
        environment = CommunicationAwareMultiAgentEnvironment(
            CommunicationAwareEnvironmentConfig(
                sumo_config_file=ROOT / "sumo/simulation/grid.sumocfg",
                max_steps=config.max_steps_per_episode,
                seed=seeds["sumo_seed"],
                communication_packet_loss_probability=condition.packet_loss_probability,
                communication_delay_ms=condition.delay_ms,
                communication_seed=seeds["packet_loss_seed"],
                freshness=freshness,
            )
        )
        try:
            observations = environment.reset()
            episode_reward = 0.0
            info: dict[str, object] = {}
            for step in range(config.max_steps_per_episode):
                actions = {
                    agent_id: learners[agent_id].select_action(observations[agent_id], epsilon=0.1)
                    for agent_id in AGENT_IDS
                }
                next_observations, rewards, terminated, info = environment.step(actions)
                for agent_id in AGENT_IDS:
                    learners[agent_id].update(
                        observations[agent_id], actions[agent_id], rewards[agent_id],
                        next_observations[agent_id], terminated,
                    )
                episode_reward += sum(rewards.values())
                observations = next_observations
                if terminated:
                    break
            metrics = info["metrics"]
            telemetry = info["communication"]
            records.append({
                "episode": episode,
                "policy_variant": config.policy_variant,
                "training_seed": config.training_seed,
                "packet_loss_probability": condition.packet_loss_probability,
                "delay_ms": condition.delay_ms,
                "condition_schedule_seed": config.condition_schedule_seed,
                "packet_loss_seed": seeds["packet_loss_seed"],
                "sumo_seed": seeds["sumo_seed"],
                "episode_reward": episode_reward,
                "average_waiting_time": metrics.average_waiting_time,
                "total_waiting_time": metrics.total_waiting_time,
                "average_queue_length": metrics.mean_queue_length,
                "max_queue_length": metrics.max_queue_length,
                "completed_trips": metrics.completed_trips,
                "simulation_duration": metrics.simulation_duration,
                "send_attempts": telemetry.send_attempts,
                "delivered_messages": telemetry.delivered_messages,
                "dropped_messages": telemetry.dropped_messages,
                "observed_packet_loss_rate": telemetry.observed_loss_rate,
                "pending_messages": telemetry.pending_messages,
                "status": "success",
            })
        finally:
            environment.close()
    metadata = phase9_metadata(
        config, phase7_config, schedule.exposure_counts, agent_ids=AGENT_IDS,
        freshness={
            "freshness_decay_tau_ms": freshness.freshness_decay_tau_ms,
            "max_message_age_ms": freshness.max_message_age_ms,
            "stale_message_threshold_ms": freshness.stale_message_threshold_ms,
        },
        episode_records=len(records),
    )
    save_phase9_checkpoint(output_directory, learners, metadata)
    (output_directory / "episodes.json").write_text(
        json.dumps(records, indent=2), encoding="utf-8"
    )
    loaded_metadata = load_phase9_metadata(output_directory / "metadata.json")
    return {
        "policy_variant": config.policy_variant,
        "episodes": records,
        "exposure_counts": schedule.exposure_counts,
        "checkpoint_metadata_valid": loaded_metadata["phase"] == 9,
    }


def main() -> None:
    with (ROOT / "configs/phase7.yaml").open(encoding="utf-8") as stream:
        phase7_yaml = yaml.safe_load(stream)
    with (ROOT / "configs/phase9.yaml").open(encoding="utf-8") as stream:
        phase9_yaml = yaml.safe_load(stream)["phase9"]
    phase7_config = load_phase7_config(ROOT / "configs/phase7.yaml")
    freshness = FreshnessConfig(**phase9_yaml["freshness"])
    base = dict(
        training_seed=phase9_yaml["training_seed"],
        packet_loss_seed=phase9_yaml["packet_loss_seed"],
        sumo_seed=phase9_yaml["sumo_seed"],
        episodes=phase9_yaml["episodes"],
        max_steps_per_episode=phase9_yaml["max_steps_per_episode"],
        output_directory=ROOT / phase9_yaml["output_directory"],
    )
    with tempfile.TemporaryDirectory(prefix="phase9-smoke-") as directory:
        ideal = train_variant(
            Phase9TrainingConfig(
                **base,
                condition_schedule_seed=phase9_yaml["condition_schedule_seed"],
                policy_variant="ideal_trained_communication_aware_iql",
            ),
            phase7_config, freshness, Path(directory) / "ideal",
        )
        robust = train_variant(
            Phase9TrainingConfig(
                **base,
                condition_schedule_seed=phase9_yaml["condition_schedule_seed"],
                policy_variant="robust_trained_communication_aware_iql",
            ),
            phase7_config, freshness, Path(directory) / "robust",
        )
    if any(
        episode["packet_loss_probability"] != 0.0 or episode["delay_ms"] != 0.0
        for episode in ideal["episodes"]
    ):
        raise RuntimeError("Ideal training schedule used an impaired condition")
    if not any(
        episode["packet_loss_probability"] > 0.0 or episode["delay_ms"] > 0.0
        for episode in robust["episodes"]
    ):
        raise RuntimeError("Robust schedule did not use an impaired condition")
    print(json.dumps({
        "functional_verification": True,
        "training_episodes_per_variant": phase9_yaml["episodes"],
        "ideal_training": ideal,
        "robust_training": robust,
        "phase7_matrix_conditions": len(generate_phase7_conditions(phase7_config)),
        "note": "Smoke training only; not research evidence.",
    }, indent=2))


if __name__ == "__main__":
    main()
