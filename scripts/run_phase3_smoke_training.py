"""Run the Phase 3 independent multi-agent smoke pipeline."""

from pathlib import Path
import csv
import json
import random
import subprocess

import numpy as np
import yaml

from traffic_control.rl import (
    AGENT_IDS,
    LinearQAgent,
    MultiAgentEnvironment,
    MultiAgentEnvironmentConfig,
)


ROOT = Path(__file__).parents[1]


def make_environment(config: dict, seed: int) -> MultiAgentEnvironment:
    phase3 = config["phase3"]
    return MultiAgentEnvironment(
        MultiAgentEnvironmentConfig(
            sumo_config_file=ROOT / "sumo/simulation/grid.sumocfg",
            agent_ids=tuple(phase3["agent_ids"]),
            seed=seed,
            max_steps=phase3["max_steps_per_episode"],
            queue_reward_weight=phase3["queue_reward_weight"],
            waiting_reward_weight=phase3["waiting_reward_weight"],
        )
    )


def build_learners(config: dict, seed: int) -> dict[str, LinearQAgent]:
    phase3 = config["phase3"]
    return {
        agent_id: LinearQAgent(
            MultiAgentEnvironment.observation_size,
            MultiAgentEnvironment.action_size,
            learning_rate=phase3["learning_rate"],
            discount_factor=phase3["discount_factor"],
            seed=seed + index,
        )
        for index, agent_id in enumerate(AGENT_IDS)
    }


def save_learners(learners: dict[str, LinearQAgent], directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for agent_id, learner in learners.items():
        learner.save(directory / f"{agent_id}.npz")


def load_learners(directory: Path, seed: int) -> dict[str, LinearQAgent]:
    return {
        agent_id: LinearQAgent.load(directory / f"{agent_id}.npz", seed=seed + index)
        for index, agent_id in enumerate(AGENT_IDS)
    }


def evaluate(config: dict, learners: dict[str, LinearQAgent]) -> dict:
    phase3 = config["phase3"]
    environment = make_environment(config, phase3["seed"] + 1000)
    rewards = {agent_id: [] for agent_id in AGENT_IDS}
    queue_lengths = {agent_id: [] for agent_id in AGENT_IDS}
    waiting_times = {agent_id: [] for agent_id in AGENT_IDS}
    global_metrics = []
    try:
        for _ in range(phase3["evaluation_episodes"]):
            observations = environment.reset()
            episode_rewards = {agent_id: 0.0 for agent_id in AGENT_IDS}
            info = {}
            for _ in range(phase3["max_steps_per_episode"]):
                actions = {
                    agent_id: learners[agent_id].select_action(observations[agent_id])
                    for agent_id in AGENT_IDS
                }
                observations, step_rewards, terminated, info = environment.step(actions)
                for agent_id in AGENT_IDS:
                    episode_rewards[agent_id] += step_rewards[agent_id]
                if terminated:
                    break
            for agent_id in AGENT_IDS:
                rewards[agent_id].append(episode_rewards[agent_id])
                queue_lengths[agent_id].append(info["per_agent"][agent_id]["queue_length"])
                waiting_times[agent_id].append(info["per_agent"][agent_id]["waiting_time"])
            global_metrics.append(info["metrics"])
    finally:
        environment.close()
    return {
        "average_reward": float(np.mean([sum(values) for values in rewards.values()])),
        "per_agent": {
            agent_id: {
                "average_reward": float(np.mean(rewards[agent_id])),
                "average_local_queue": float(np.mean(queue_lengths[agent_id])),
                "average_local_waiting_time": float(np.mean(waiting_times[agent_id])),
            }
            for agent_id in AGENT_IDS
        },
        "global": {
            "average_waiting_time": float(np.mean([m.average_waiting_time for m in global_metrics])),
            "average_queue_length": float(np.mean([m.mean_queue_length for m in global_metrics])),
            "average_simulation_duration": float(np.mean([m.simulation_duration for m in global_metrics])),
            "average_completed_trips": float(np.mean([m.completed_trips for m in global_metrics])),
        },
    }


def main() -> None:
    with (ROOT / "configs/phase3.yaml").open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    phase3 = config["phase3"]
    seed = phase3["seed"]
    random.seed(seed)
    np.random.seed(seed)
    learners = build_learners(config, seed)
    environment = make_environment(config, seed)
    rows = []
    try:
        epsilon = phase3["epsilon_start"]
        for episode in range(1, phase3["episodes"] + 1):
            observations = environment.reset()
            episode_rewards = {agent_id: 0.0 for agent_id in AGENT_IDS}
            info = {}
            for step in range(phase3["max_steps_per_episode"]):
                actions = {
                    agent_id: learners[agent_id].select_action(observations[agent_id], epsilon)
                    for agent_id in AGENT_IDS
                }
                next_observations, rewards, terminated, info = environment.step(actions)
                for agent_id in AGENT_IDS:
                    learners[agent_id].update(
                        observations[agent_id],
                        actions[agent_id],
                        rewards[agent_id],
                        next_observations[agent_id],
                        terminated,
                    )
                    episode_rewards[agent_id] += rewards[agent_id]
                observations = next_observations
                if terminated:
                    break
            rows.append({
                "episode": episode,
                "seed": seed,
                "episode_length": step + 1,
                "total_reward": sum(episode_rewards.values()),
                **{f"reward_{agent_id}": episode_rewards[agent_id] for agent_id in AGENT_IDS},
                "global_waiting_time": info["metrics"].average_waiting_time,
                "global_queue_length": info["metrics"].mean_queue_length,
                "completed_trips": info["metrics"].completed_trips,
            })
            epsilon = max(phase3["epsilon_end"], epsilon * phase3["epsilon_decay"])
    finally:
        environment.close()

    checkpoint_directory = ROOT / phase3["checkpoint_directory"]
    save_learners(learners, checkpoint_directory)
    loaded_learners = load_learners(checkpoint_directory, seed)
    evaluation = evaluate(config, loaded_learners)
    with (ROOT / phase3["training_log"]).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    git_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    output = {
        "git_commit": git_commit,
        "algorithm": "independent_q_learning",
        "seed": seed,
        "agent_ids": list(AGENT_IDS),
        "communication": phase3["communication"],
        "training_episodes": phase3["episodes"],
        "evaluation_episodes": phase3["evaluation_episodes"],
        "evaluation": evaluation,
    }
    output_path = ROOT / phase3["evaluation_output"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
