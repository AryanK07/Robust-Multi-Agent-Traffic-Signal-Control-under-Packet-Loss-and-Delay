"""Run the small Phase 2 train-save-load-evaluate smoke pipeline."""

from pathlib import Path
import csv
import json
import random
import subprocess

import numpy as np
import yaml

from traffic_control.rl import (
    LinearQAgent,
    SingleAgentEnvironment,
    SingleAgentEnvironmentConfig,
)


ROOT = Path(__file__).parents[1]


def make_environment(config: dict, seed: int) -> SingleAgentEnvironment:
    phase2 = config["phase2"]
    return SingleAgentEnvironment(
        SingleAgentEnvironmentConfig(
            sumo_config_file=ROOT / "sumo/simulation/grid.sumocfg",
            controlled_intersection=phase2["controlled_intersection"],
            seed=seed,
            max_steps=phase2["max_steps_per_episode"],
            queue_reward_weight=phase2["queue_reward_weight"],
            waiting_reward_weight=phase2["waiting_reward_weight"],
        )
    )


def train(config: dict, git_commit: str) -> None:
    phase2 = config["phase2"]
    seed = phase2["seed"]
    random.seed(seed)
    np.random.seed(seed)
    agent = LinearQAgent(
        observation_size=SingleAgentEnvironment.observation_size,
        action_size=SingleAgentEnvironment.action_size,
        learning_rate=phase2["learning_rate"],
        discount_factor=phase2["discount_factor"],
        seed=seed,
    )
    environment = make_environment(config, seed)
    rows = []
    try:
        epsilon = phase2["epsilon_start"]
        for episode in range(1, phase2["episodes"] + 1):
            observation = environment.reset()
            total_reward = 0.0
            last_info = {}
            for step in range(phase2["max_steps_per_episode"]):
                action = agent.select_action(observation, epsilon)
                next_observation, reward, terminated, last_info = environment.step(action)
                agent.update(observation, action, reward, next_observation, terminated)
                observation = next_observation
                total_reward += reward
                if terminated:
                    break
            rows.append(
                {
                    "episode": episode,
                    "reward": total_reward,
                    "length": step + 1,
                    "waiting_time": last_info["waiting_time"],
                    "queue_length": last_info["queue_length"],
                }
            )
            epsilon = max(phase2["epsilon_end"], epsilon * phase2["epsilon_decay"])
    finally:
        environment.close()

    checkpoint = ROOT / phase2["checkpoint"]
    agent.save(checkpoint)
    log_path = ROOT / phase2["training_log"]
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    loaded_agent = LinearQAgent.load(checkpoint, seed=seed)
    evaluation = evaluate(config, loaded_agent)
    output = {
        "git_commit": git_commit,
        "algorithm": "linear_q_learning",
        "seed": seed,
        "controlled_intersection": phase2["controlled_intersection"],
        "training_episodes": phase2["episodes"],
        "evaluation": evaluation,
    }
    output_path = ROOT / phase2["evaluation_output"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


def evaluate(config: dict, agent: LinearQAgent) -> dict[str, float]:
    phase2 = config["phase2"]
    environment = make_environment(config, phase2["seed"] + 1000)
    rewards = []
    waiting_times = []
    queues = []
    durations = []
    completed_trips = []
    try:
        for _ in range(phase2["evaluation_episodes"]):
            observation = environment.reset()
            total_reward = 0.0
            info = {}
            for _ in range(phase2["max_steps_per_episode"]):
                observation, reward, terminated, info = environment.step(
                    agent.select_action(observation)
                )
                total_reward += reward
                if terminated:
                    break
            metrics = info["metrics"]
            rewards.append(total_reward)
            waiting_times.append(metrics.average_waiting_time)
            queues.append(metrics.mean_queue_length)
            durations.append(metrics.simulation_duration)
            completed_trips.append(metrics.completed_trips)
    finally:
        environment.close()
    return {
        "average_reward": float(np.mean(rewards)),
        "average_waiting_time": float(np.mean(waiting_times)),
        "average_queue_length": float(np.mean(queues)),
        "average_simulation_duration": float(np.mean(durations)),
        "average_completed_trips": float(np.mean(completed_trips)),
    }


if __name__ == "__main__":
    config_path = ROOT / "configs/phase2.yaml"
    with config_path.open(encoding="utf-8") as stream:
        configuration = yaml.safe_load(stream)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    train(configuration, commit)
