"""Run Phase 7 evaluation with frozen Phase 3 checkpoints."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
import yaml

from traffic_control.experiments import (
    aggregate_phase7_results,
    generate_phase7_conditions,
    load_phase7_config,
    write_raw_result,
)
from traffic_control.rl import AGENT_IDS, LinearQAgent, MultiAgentEnvironment, MultiAgentEnvironmentConfig


ROOT = Path(__file__).parents[1]


def _checkpoint_identity(directory: Path) -> str:
    digest = hashlib.sha256()
    for agent_id in AGENT_IDS:
        path = directory / f"{agent_id}.npz"
        if not path.is_file():
            raise FileNotFoundError(f"Missing frozen checkpoint: {path}")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _evaluate(config: dict, condition, seed: int, checkpoints: Path) -> dict:
    phase3 = config["phase3"]
    environment = MultiAgentEnvironment(
        MultiAgentEnvironmentConfig(
            sumo_config_file=ROOT / "sumo/simulation/grid.sumocfg",
            agent_ids=tuple(phase3["agent_ids"]),
            seed=seed,
            max_steps=phase3["max_steps_per_episode"],
            queue_reward_weight=phase3["queue_reward_weight"],
            waiting_reward_weight=phase3["waiting_reward_weight"],
            communication_enabled=True,
            communication_packet_loss_probability=condition.packet_loss_probability,
            communication_seed=seed,
            communication_delay_ms=condition.delay_ms,
            communication_delay_model="fixed",
        )
    )
    learners = {
        agent_id: LinearQAgent.load(checkpoints / f"{agent_id}.npz", seed=seed + index)
        for index, agent_id in enumerate(AGENT_IDS)
    }
    try:
        observations = environment.reset()
        episode_reward = 0.0
        info = {}
        for _ in range(phase3["max_steps_per_episode"]):
            actions = {
                agent_id: learners[agent_id].select_action(observations[agent_id])
                for agent_id in AGENT_IDS
            }
            observations, rewards, terminated, info = environment.step(actions)
            episode_reward += sum(rewards.values())
            if terminated:
                break
        metrics = info["metrics"]
        telemetry = info["communication"]
        return {
            "average_waiting_time": metrics.average_waiting_time,
            "total_waiting_time": metrics.total_waiting_time,
            "mean_queue_length": metrics.mean_queue_length,
            "max_queue_length": metrics.max_queue_length,
            "completed_trips": metrics.completed_trips,
            "simulation_duration": metrics.simulation_duration,
            "episode_reward": episode_reward,
            "send_attempts": telemetry.send_attempts,
            "successful_transmissions": telemetry.successful_transmissions,
            "dropped_messages": telemetry.dropped_messages,
            "delivered_messages": telemetry.delivered_messages,
            "pending_messages": telemetry.pending_messages,
            "observed_loss_rate": telemetry.observed_loss_rate,
            "message_age_mean": None,
        }
    finally:
        environment.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "configs/phase7.yaml")
    parser.add_argument("--phase3-config", type=Path, default=ROOT / "configs/phase3.yaml")
    parser.add_argument("--condition", help="Condition ID, or omit for all conditions")
    parser.add_argument("--seed", type=int, action="append", dest="selected_seeds")
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()
    phase7 = load_phase7_config(args.config)
    with args.phase3_config.open(encoding="utf-8") as stream:
        phase3_config = yaml.safe_load(stream)
    checkpoint_directory = ROOT / phase3_config["phase3"]["checkpoint_directory"]
    checkpoint_id = _checkpoint_identity(checkpoint_directory)
    conditions = generate_phase7_conditions(phase7)
    if args.condition:
        conditions = tuple(condition for condition in conditions if condition.condition_id == args.condition)
        if not conditions:
            raise ValueError(f"Unknown condition: {args.condition}")
    seeds = tuple(args.selected_seeds or phase7.seeds)
    raw_directory = ROOT / phase7.output_directory / "raw"
    for condition in conditions:
        for seed in seeds:
            run_id = f"{condition.condition_id}__seed_{seed}"
            if args.summary_only:
                continue
            result = {
                "experiment_name": phase7.name,
                "run_id": run_id,
                "status": "success",
                "packet_loss_probability": condition.packet_loss_probability,
                "delay_ms": condition.delay_ms,
                "rl_seed": seed,
                "communication_seed": seed,
                "sumo_seed": seed,
                "episode": 1,
                "checkpoint_identity": checkpoint_id,
                "policy_uses_communication": False,
                "causal_policy_dependency": False,
                "limitations": [
                    "Phase 3 policy consumes local observations only; no messages are generated or consumed."
                ],
                "git_commit": subprocess.run(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                    capture_output=True, text=True
                ).stdout.strip(),
            }
            try:
                result.update(_evaluate(phase3_config, condition, seed, checkpoint_directory))
            except Exception as error:
                result["status"] = "failed"
                result["failure"] = f"{type(error).__name__}: {error}"
            write_raw_result(result, raw_directory)
    raw_results = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(raw_directory.glob("*.json"))
    ] if raw_directory.exists() else []
    summaries = aggregate_phase7_results(raw_results)
    output_directory = ROOT / phase7.output_directory
    output_directory.mkdir(parents=True, exist_ok=True)
    (output_directory / "summary.json").write_text(
        json.dumps(summaries, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps({"conditions": len(conditions), "seeds": list(seeds), "summaries": summaries}, indent=2))


if __name__ == "__main__":
    main()
