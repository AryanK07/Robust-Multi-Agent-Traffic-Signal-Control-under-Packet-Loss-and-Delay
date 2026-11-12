"""Train frozen Phase 11 checkpoints and run the reproducible final campaign."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any
from dataclasses import replace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml

from traffic_control.communication import FreshnessConfig
from traffic_control.config import load_phase11_config
from traffic_control.experiments import (
    COMMUNICATION_POLICIES,
    Phase11Config,
    aggregate_phase11_results,
    checkpoint_sha256,
    derive_evaluation_seeds,
    generate_phase11_runs,
    load_valid_raw_results,
    paired_differences,
    validate_phase11_config,
    write_phase11_raw_result,
)
from traffic_control.experiments.phase7 import generate_phase7_conditions, load_phase7_config
from traffic_control.experiments.phase9 import (
    BalancedConditionSchedule,
    Phase9TrainingConfig,
    phase9_metadata,
)
from traffic_control.rl import (
    AGENT_IDS,
    CommunicationAwareEnvironmentConfig,
    CommunicationAwareLinearQAgent,
    CommunicationAwareMultiAgentEnvironment,
    LinearQAgent,
    MultiAgentEnvironment,
    MultiAgentEnvironmentConfig,
)


ROOT = Path(__file__).parents[1]
NEIGHBORS = {
    "A0": ("A1", "B0"),
    "A1": ("A0", "B1"),
    "B0": ("A0", "B1"),
    "B1": ("A1", "B0"),
}


def _git_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def _make_phase9_training_config(
    phase11: Phase11Config, seed: int, variant: str, output: Path
) -> Phase9TrainingConfig:
    return Phase9TrainingConfig(
        training_seed=seed,
        condition_schedule_seed=seed + 1000,
        packet_loss_seed=seed + 2000,
        sumo_seed=seed + 3000,
        episodes=phase11.training_episodes,
        max_steps_per_episode=phase11.max_steps_per_episode,
        output_directory=output,
        policy_variant=variant,
    )


def train_checkpoints(
    phase11: Phase11Config, phase7_config, *, selected_seed: int | None = None
) -> dict[str, Any]:
    """Train one frozen checkpoint set per policy and master seed."""
    seeds = (selected_seed,) if selected_seed is not None else phase11.master_seeds
    freshness = FreshnessConfig(
        phase11.freshness_decay_tau_ms,
        phase11.max_message_age_ms,
        phase11.stale_message_threshold_ms,
    )
    conditions = generate_phase7_conditions(phase7_config)
    records: list[dict[str, Any]] = []
    for seed in seeds:
        for variant in ("local_only_phase3_iql", *COMMUNICATION_POLICIES):
            output = ROOT / phase11.checkpoint_directory / variant / f"seed_{seed}"
            metadata_path = output / "metadata.json"
            if metadata_path.exists():
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                if metadata.get("training_episodes") != phase11.training_episodes:
                    raise ValueError(f"Existing checkpoint has incompatible budget: {output}")
                records.append({"policy_variant": variant, "seed": seed, "status": "reused"})
                continue
            output.mkdir(parents=True, exist_ok=True)
            if variant == "local_only_phase3_iql":
                learners, training_records = _train_local(phase11, seed, output)
                metadata = {
                    "phase": 11,
                    "policy_variant": variant,
                    "training_seed": seed,
                    "training_episodes": phase11.training_episodes,
                    "max_steps_per_episode": phase11.max_steps_per_episode,
                    "observation_dimension": 5,
                    "observation_schema_version": "local_v1",
                    "training_condition_distribution": "no communication",
                    "episode_records": phase11.training_episodes,
                }
            else:
                training = _make_phase9_training_config(phase11, seed, variant, output)
                learners, exposure, episode_records, training_records = _train_communication(
                    training, phase7_config, freshness, output
                )
                metadata = phase9_metadata(
                    training,
                    phase7_config,
                    exposure,
                    agent_ids=AGENT_IDS,
                    freshness={
                        "freshness_decay_tau_ms": freshness.freshness_decay_tau_ms,
                        "max_message_age_ms": freshness.max_message_age_ms,
                        "stale_message_threshold_ms": freshness.stale_message_threshold_ms,
                    },
                    episode_records=episode_records,
                )
                metadata["phase11_checkpoint"] = True
            _save_metadata(output, metadata)
            (output / "training.json").write_text(
                json.dumps(training_records, indent=2, sort_keys=True), encoding="utf-8"
            )
            records.append({"policy_variant": variant, "seed": seed, "status": "trained"})
    return {"checkpoints": records}


def _train_local(
    phase11: Phase11Config, seed: int, output: Path
) -> tuple[dict[str, LinearQAgent], list[dict[str, Any]]]:
    learners = {
        agent_id: LinearQAgent(5, 2, seed=seed + index)
        for index, agent_id in enumerate(AGENT_IDS)
    }
    records: list[dict[str, Any]] = []
    for episode in range(phase11.training_episodes):
        environment = MultiAgentEnvironment(
            MultiAgentEnvironmentConfig(
                sumo_config_file=ROOT / "sumo/simulation/grid.sumocfg",
                seed=(seed + episode) % 2_147_483_647,
                max_steps=phase11.max_steps_per_episode,
                communication_enabled=False,
            )
        )
        try:
            observations = environment.reset()
            epsilon = max(0.1, 1.0 * 0.95**episode)
            episode_reward = 0.0
            for _ in range(phase11.max_steps_per_episode):
                actions = {
                    agent_id: learners[agent_id].select_action(observations[agent_id], epsilon)
                    for agent_id in AGENT_IDS
                }
                next_observations, rewards, terminated, _ = environment.step(actions)
                for agent_id in AGENT_IDS:
                    learners[agent_id].update(
                        observations[agent_id], actions[agent_id], rewards[agent_id],
                        next_observations[agent_id], terminated,
                    )
                episode_reward += sum(rewards.values())
                observations = next_observations
                if terminated:
                    break
            records.append({"episode": episode + 1, "episode_reward": episode_reward, "epsilon": epsilon})
        finally:
            environment.close()
    for agent_id, learner in learners.items():
        learner.save(output / f"{agent_id}.npz")
    return learners, records


def _train_communication(
    config: Phase9TrainingConfig, phase7_config, freshness: FreshnessConfig, output: Path
) -> tuple[
    dict[str, CommunicationAwareLinearQAgent], dict[str, int], int, list[dict[str, Any]]
]:
    schedule = BalancedConditionSchedule(
        generate_phase7_conditions(phase7_config),
        config.condition_schedule_seed,
        ideal_only=config.policy_variant.startswith("ideal"),
    )
    learners = {
        agent_id: CommunicationAwareLinearQAgent(
            neighbor_ids=NEIGHBORS[agent_id], seed=config.training_seed + index
        )
        for index, agent_id in enumerate(AGENT_IDS)
    }
    records: list[dict[str, Any]] = []
    for episode in range(1, config.episodes + 1):
        condition = schedule.next()
        seeds = np.random.SeedSequence(
            [config.training_seed, config.packet_loss_seed, config.sumo_seed, episode]
        ).generate_state(3, dtype=np.uint32)
        environment = CommunicationAwareMultiAgentEnvironment(
            CommunicationAwareEnvironmentConfig(
                sumo_config_file=ROOT / "sumo/simulation/grid.sumocfg",
                max_steps=config.max_steps_per_episode,
                seed=int(seeds[2] % 2_147_483_647),
                communication_packet_loss_probability=condition.packet_loss_probability,
                communication_delay_ms=condition.delay_ms,
                communication_seed=int(seeds[1] % 2_147_483_647),
                freshness=freshness,
            )
        )
        try:
            observations = environment.reset()
            episode_reward = 0.0
            for _ in range(config.max_steps_per_episode):
                actions = {
                    agent_id: learners[agent_id].select_action(observations[agent_id], epsilon=0.1)
                    for agent_id in AGENT_IDS
                }
                next_observations, rewards, terminated, _ = environment.step(actions)
                for agent_id in AGENT_IDS:
                    learners[agent_id].update(
                        observations[agent_id], actions[agent_id], rewards[agent_id],
                        next_observations[agent_id], terminated,
                    )
                episode_reward += sum(rewards.values())
                observations = next_observations
                if terminated:
                    break
            records.append({
                "episode": episode,
                "episode_reward": episode_reward,
                "packet_loss_probability": condition.packet_loss_probability,
                "delay_ms": condition.delay_ms,
            })
        finally:
            environment.close()
    for agent_id, learner in learners.items():
        learner.save(output / f"{agent_id}.npz")
    return learners, schedule.exposure_counts, config.episodes, records


def evaluate_run(
    spec: dict[str, Any], phase11: Phase11Config, checkpoint_root: Path
) -> dict[str, Any]:
    """Evaluate one frozen episode with deterministic actions and seeds."""
    policy = spec["policy_variant"]
    checkpoint = checkpoint_root / policy / f"seed_{spec['master_seed']}"
    digest = checkpoint_sha256(checkpoint, AGENT_IDS)
    freshness = FreshnessConfig(
        phase11.freshness_decay_tau_ms,
        phase11.max_message_age_ms,
        phase11.stale_message_threshold_ms,
    )
    age_samples: list[float] = []
    stale_samples: list[float] = []
    if policy == "local_only_phase3_iql":
        learners = {
            agent_id: LinearQAgent.load(checkpoint / f"{agent_id}.npz")
            for agent_id in AGENT_IDS
        }
        environment = MultiAgentEnvironment(
            MultiAgentEnvironmentConfig(
                sumo_config_file=ROOT / "sumo/simulation/grid.sumocfg",
                seed=spec["traffic_demand_seed"],
                max_steps=phase11.max_steps_per_episode,
                communication_enabled=False,
            )
        )
    else:
        learners = {
            agent_id: CommunicationAwareLinearQAgent.load(
                checkpoint / f"{agent_id}.npz", expected_neighbor_ids=NEIGHBORS[agent_id]
            )
            for agent_id in AGENT_IDS
        }
        environment = CommunicationAwareMultiAgentEnvironment(
            CommunicationAwareEnvironmentConfig(
                sumo_config_file=ROOT / "sumo/simulation/grid.sumocfg",
                seed=spec["traffic_demand_seed"],
                max_steps=phase11.max_steps_per_episode,
                communication_packet_loss_probability=spec["packet_loss_probability"],
                communication_delay_ms=spec["delay_ms"],
                communication_seed=spec["packet_loss_seed"],
                freshness=freshness,
                communication_strategy=spec["communication_strategy"],
                periodic_interval_ms=phase11.periodic_interval_ms,
                adaptive_change_threshold=phase11.adaptive_change_threshold,
                adaptive_max_silence_ms=phase11.adaptive_max_silence_ms,
            )
        )
    try:
        observations = environment.reset()
        total_reward = 0.0
        info: dict[str, Any] = {}
        for _ in range(phase11.max_steps_per_episode):
            actions = {
                agent_id: learners[agent_id].select_action(observations[agent_id], epsilon=0.0)
                for agent_id in AGENT_IDS
            }
            observations, rewards, terminated, info = environment.step(actions)
            total_reward += sum(rewards.values())
            if policy != "local_only_phase3_iql":
                _collect_age_samples(info, age_samples, stale_samples, float(info["simulation_time"]), freshness)
            if terminated:
                break
        metrics = info["metrics"]
        telemetry = info["communication"]
        scheduler = info.get("communication_scheduler")
        result = {
            **spec,
            "status": "success",
            "checkpoint_sha256": digest,
            "checkpoint_path": str(checkpoint),
            "episode_reward": total_reward,
            "average_waiting_time": metrics.average_waiting_time,
            "total_waiting_time": metrics.total_waiting_time,
            "mean_queue_length": metrics.mean_queue_length,
            "max_queue_length": metrics.max_queue_length,
            "completed_trips": metrics.completed_trips,
            "simulation_duration": metrics.simulation_duration,
            "configured_packet_loss_probability": telemetry.configured_packet_loss_probability,
            "configured_delay_ms": telemetry.configured_delay_ms,
            "send_attempts": telemetry.send_attempts,
            "successful_transmissions": telemetry.successful_transmissions,
            "dropped_messages": telemetry.dropped_messages,
            "delivered_messages": telemetry.delivered_messages,
            "observed_packet_loss_rate": telemetry.observed_loss_rate,
            "pending_messages": telemetry.pending_messages,
            "average_message_age_ms": float(np.mean(age_samples)) if age_samples else None,
            "maximum_message_age_ms": float(max(age_samples)) if age_samples else None,
            "stale_message_proportion": float(np.mean(stale_samples)) if stale_samples else None,
            "scheduling_opportunities": scheduler.scheduling_opportunities if scheduler else 0,
            "suppressed_transmissions": scheduler.suppressed_transmissions if scheduler else 0,
            "communication_reduction": (
                scheduler.communication_reduction if scheduler else 0.0
            ),
            "trigger_counts": dict(scheduler.trigger_counts) if scheduler else {},
            "git_commit": _git_commit(),
        }
        return result
    finally:
        environment.close()


def _collect_age_samples(
    info: dict[str, Any],
    ages: list[float],
    stale: list[float],
    current_time: float,
    freshness: FreshnessConfig,
) -> None:
    cache = info.get("message_cache", {})
    for receiver in cache.values():
        for state in receiver.values():
            age = freshness.age_ms(float(state["generation_timestamp"]), current_time)
            ages.append(age)
            stale.append(float(freshness.is_stale(age)))


def run_campaign(
    phase11: Phase11Config,
    phase7_config,
    *,
    selected_policy: str | None = None,
    selected_strategy: str | None = None,
    selected_seed: int | None = None,
    condition_id: str | None = None,
    retry_failed: bool = False,
) -> dict[str, int]:
    """Run selected resumable batch and preserve every failure."""
    all_specs = generate_phase11_runs(phase7_config, phase11)
    specs = tuple(
        spec for spec in all_specs
        if (selected_policy is None or spec["policy_variant"] == selected_policy)
        and (selected_strategy is None or spec["communication_strategy"] == selected_strategy)
        and (selected_seed is None or spec["master_seed"] == selected_seed)
        and (condition_id is None or _condition_id(spec) == condition_id)
    )
    raw_directory = ROOT / phase11.evaluation_output_directory / "raw"
    existing = load_valid_raw_results(raw_directory)
    counts = {"required": len(specs), "completed": 0, "failed": 0, "skipped": 0}
    for spec in specs:
        prior = existing.get(spec["run_id"])
        if prior is not None and not retry_failed:
            counts["completed" if prior.get("status") == "success" else "failed"] += 1
            counts["skipped"] += 1
            continue
        try:
            result = evaluate_run(spec, phase11, ROOT / phase11.checkpoint_directory)
        except Exception as error:
            result = {
                **spec,
                "status": "failed",
                "failure": f"{type(error).__name__}: {error}",
                "git_commit": _git_commit(),
            }
        if prior is not None:
            result["retry_of"] = spec["run_id"]
            result["retry_number"] = int(prior.get("retry_number", 0)) + 1
            result["run_id"] = hashlib.sha256(
                json.dumps(result, sort_keys=True, default=str).encode()
            ).hexdigest()[:20]
        write_phase11_raw_result(result, raw_directory)
        counts["completed" if result["status"] == "success" else "failed"] += 1
    return counts


def analyze(phase11: Phase11Config) -> dict[str, Any]:
    """Generate machine-readable summaries, paired comparisons, and figures."""
    output = ROOT / phase11.evaluation_output_directory
    results = list(load_valid_raw_results(output / "raw").values())
    summaries = aggregate_phase11_results(results)
    comparisons = [
        paired_differences(
            results,
            "robust_trained_communication_aware_iql",
            "ideal_trained_communication_aware_iql",
            "average_waiting_time",
        ),
        _paired_strategy_difference(
            results, "adaptive", "always", "average_waiting_time"
        ),
        _paired_strategy_difference(
            results, "adaptive", "periodic", "average_waiting_time"
        ),
        _paired_strategy_difference(
            results, "adaptive", "always", "communication_reduction"
        ),
        _paired_baseline_difference(results, "ideal_trained_communication_aware_iql"),
        _paired_baseline_difference(results, "robust_trained_communication_aware_iql"),
    ]
    _add_degradation(summaries)
    (output / "summaries.json").write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    with (output / "summaries.csv").open("w", newline="", encoding="utf-8") as stream:
        if summaries:
            writer = csv.DictWriter(stream, fieldnames=sorted(summaries[0]))
            writer.writeheader()
            writer.writerows(summaries)
    report = {
        "phase": 11,
        "required_runs": len(generate_phase11_runs(load_phase7_config(ROOT / "configs/phase7.yaml"), phase11)),
        "successful_runs": sum(row.get("status") == "success" for row in results),
        "failed_runs": sum(row.get("status") == "failed" for row in results),
        "summaries": summaries,
        "paired_comparisons": comparisons,
        "statistical_note": "Descriptive statistics and 95% normal-approximation intervals are reported; five seeds limit inference.",
    }
    (output / "statistical_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    _plot_waiting_time(summaries, output / "figures")
    return report


def _paired_strategy_difference(
    results: list[dict[str, Any]], left_strategy: str, right_strategy: str, metric: str
) -> dict[str, Any]:
    left: dict[tuple[Any, int], list[float]] = {}
    right: dict[tuple[Any, int], list[float]] = {}
    for row in results:
        if row.get("status") != "success" or row.get(metric) is None:
            continue
        key = (row["policy_variant"], int(row["master_seed"]))
        if row["communication_strategy"] == left_strategy:
            left.setdefault(key, []).append(float(row[metric]))
        elif row["communication_strategy"] == right_strategy:
            right.setdefault(key, []).append(float(row[metric]))
    differences = [
        float(np.mean(left[key])) - float(np.mean(right[key]))
        for key in left.keys() & right.keys()
    ]
    result = {
        "metric": metric,
        "left_strategy": left_strategy,
        "right_strategy": right_strategy,
        "sample_count": len(differences),
        "mean_difference": float(np.mean(differences)) if differences else None,
        "standard_deviation": (
            float(np.std(differences, ddof=1)) if len(differences) > 1 else 0.0 if differences else None
        ),
        "confidence_interval_95": None,
        "inference_note": "Values are first averaged across conditions per frozen training seed; five seeds limit statistical power.",
    }
    if len(differences) > 1:
        standard_error = float(np.std(differences, ddof=1)) / np.sqrt(len(differences))
        result["confidence_interval_95"] = [
            float(np.mean(differences) - 1.96 * standard_error),
            float(np.mean(differences) + 1.96 * standard_error),
        ]
    return result


def _add_degradation(summaries: list[dict[str, Any]]) -> None:
    """Add waiting-time degradation relative to each policy's ideal reference."""
    references = {
        row["policy_variant"]: row["average_waiting_time_mean"]
        for row in summaries
        if row["communication_strategy"] == "always"
        and row["packet_loss_probability"] == 0.0
        and row["delay_ms"] == 0.0
        and "average_waiting_time_mean" in row
    }
    for row in summaries:
        reference = references.get(row["policy_variant"])
        value = row.get("average_waiting_time_mean")
        row["waiting_time_degradation_percent"] = (
            ((value - reference) / abs(reference)) * 100.0
            if reference is not None and value is not None and reference != 0
            else None
        )


def _paired_baseline_difference(
    results: list[dict[str, Any]], communication_policy: str
) -> dict[str, Any]:
    """Compare each communication-aware policy with the local-only reference."""
    left: dict[int, float] = {}
    right: dict[int, float] = {}
    for row in results:
        if (
            row.get("status") != "success"
            or row["packet_loss_probability"] != 0.0
            or row["delay_ms"] != 0.0
            or row.get("average_waiting_time") is None
        ):
            continue
        if row["policy_variant"] == communication_policy and row["communication_strategy"] == "always":
            left[row["master_seed"]] = float(row["average_waiting_time"])
        elif row["policy_variant"] == "local_only_phase3_iql":
            right[row["master_seed"]] = float(row["average_waiting_time"])
    differences = [left[seed] - right[seed] for seed in left.keys() & right.keys()]
    return {
        "metric": "average_waiting_time",
        "left": communication_policy,
        "right": "local_only_phase3_iql",
        "sample_count": len(differences),
        "mean_difference": float(np.mean(differences)) if differences else None,
        "inference_note": "Canonical ideal-condition comparison; local-only policy does not consume communication.",
    }


def _plot_waiting_time(summaries: list[dict[str, Any]], directory: Path) -> None:
    if not summaries:
        return
    directory.mkdir(parents=True, exist_ok=True)
    for strategy in ("always", "periodic", "adaptive"):
        rows = [row for row in summaries if row["communication_strategy"] == strategy]
        if not rows:
            continue
        figure, axis = plt.subplots(figsize=(8, 5))
        for policy in COMMUNICATION_POLICIES:
            points = sorted(
                (row for row in rows if row["policy_variant"] == policy),
                key=lambda row: (row["packet_loss_probability"], row["delay_ms"]),
            )
            if points:
                axis.plot(
                    range(len(points)),
                    [row["average_waiting_time_mean"] for row in points],
                    marker="o",
                    label=policy,
                )
        axis.set_title(f"Average waiting time by condition ({strategy})")
        axis.set_xlabel("Condition index (loss-major, delay-minor)")
        axis.set_ylabel("Average vehicle waiting time (s)")
        axis.legend()
        figure.tight_layout()
        figure.savefig(directory / f"waiting_time_{strategy}.png", dpi=150)
        plt.close(figure)


def _condition_id(spec: dict[str, Any]) -> str:
    loss = f"{float(spec['packet_loss_probability']):.2f}".replace(".", "p")
    delay = f"{float(spec['delay_ms']):g}".replace(".", "p")
    return f"loss_{loss}__delay_{delay}ms"


def _save_metadata(output: Path, metadata: dict[str, Any]) -> None:
    path = output / "metadata.json"
    if path.exists():
        raise FileExistsError(f"Refusing checkpoint metadata overwrite: {path}")
    path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("audit", "train", "pilot", "evaluate", "analyze", "all"), default="audit")
    parser.add_argument("--policy", choices=("local_only_phase3_iql", *COMMUNICATION_POLICIES))
    parser.add_argument("--strategy", choices=("none", "always", "periodic", "adaptive"))
    parser.add_argument("--seed", type=int)
    parser.add_argument("--condition")
    parser.add_argument("--retry-failed", action="store_true")
    args = parser.parse_args()
    phase11 = validate_phase11_config(
        yaml.safe_load((ROOT / "configs/phase11.yaml").read_text(encoding="utf-8"))
    )
    phase7 = load_phase7_config(ROOT / "configs/phase7.yaml")
    output = ROOT / phase11.evaluation_output_directory
    output.mkdir(parents=True, exist_ok=True)
    (output / "config.yaml").write_text(
        (ROOT / "configs/phase11.yaml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    if args.mode == "pilot":
        pilot = replace(
            phase11,
            training_episodes=min(5, phase11.training_episodes),
            checkpoint_directory=Path("results/phase11/pilot_checkpoints"),
        )
        print(json.dumps(train_checkpoints(pilot, phase7, selected_seed=args.seed or phase11.master_seeds[0]), indent=2))
    elif args.mode in {"train", "all"}:
        train_checkpoints(phase11, phase7, selected_seed=args.seed)
    if args.mode in {"evaluate", "all"}:
        print(run_campaign(
            phase11, phase7, selected_policy=args.policy, selected_strategy=args.strategy,
            selected_seed=args.seed, condition_id=args.condition,
            retry_failed=args.retry_failed,
        ))
    if args.mode in {"analyze", "all"}:
        print(json.dumps(analyze(phase11), indent=2))
    if args.mode == "audit":
        print(json.dumps({
            "required_runs": len(generate_phase11_runs(phase7, phase11)),
            "checkpoint_directory": str(ROOT / phase11.checkpoint_directory),
            "output_directory": str(output),
            "phase": 11,
        }, indent=2))


if __name__ == "__main__":
    main()
