"""Fresh, matched linear-IQL training and immutable follow-up evaluation."""

from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import subprocess
import traceback

import numpy as np

from traffic_control.communication import FreshnessConfig
from traffic_control.environment.trip_metrics import read_trip_metrics
from traffic_control.rl import AGENT_IDS, LinearQAgent
from traffic_control.rl.followup_env import FollowupEnvironment, FollowupEnvironmentConfig
from .artifacts import CampaignStore, write_json_exclusive
from .followup_design import episode_seeds, evaluation_specs, training_schedule, write_scenario


ROOT = Path(__file__).resolve().parents[3]


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_manifest(design: dict) -> dict:
    """Require committed source before collecting even the development pilot."""
    status = subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True)
    if status.strip():
        raise ValueError("Commit the reviewed source/configuration before running a campaign")
    files = [*ROOT.glob('src/**/*.py'), *ROOT.glob('scripts/*.py'),
             *ROOT.glob('configs/*.yaml'), ROOT / 'sumo/network/grid.net.xml',
             ROOT / 'pyproject.toml', *ROOT.glob('requirements-research-lock.txt')]
    return {
        "schema": "campaign_v2",
        "design": design,
        "git_commit": subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        "source_sha256": {p.relative_to(ROOT).as_posix(): file_hash(p) for p in sorted(files)},
        "python": platform.python_version(),
        "packages": {name: version(name) for name in ('numpy', 'scipy', 'PyYAML', 'matplotlib') +
                     (('libsumo', 'traci', 'sumolib', 'sumo-data')
                      if design['environment'].get('backend') == 'libsumo' else ())},
        "sumo": subprocess.check_output(['sumo', '--version'], text=True).splitlines()[0],
        "metric_schema": "tripinfo_v2",
        "reward": "negative_local_queue_integral_v2",
    }


def training_spec(variant: str, master: int) -> dict:
    return {"kind": "training", "variant": variant, "master_seed": master}


def _artifact_directory(store, spec):
    attempt = max((row['attempt'] for row in store.attempts(spec)), default=0) + 1
    directory = store.directory / 'artifacts' / store.run_id(spec) / f'{attempt:04d}'
    while directory.exists():
        # Preserve files left by an interrupted process instead of overwriting
        # them or pretending the previous attempt completed.
        store.record(spec, 'failed', {
            'error': 'Incomplete artifacts found without a completed result record',
            'artifact_directory': str(directory),
            'timestamp_utc': datetime.now(timezone.utc).isoformat()})
        attempt += 1
        directory = store.directory / 'artifacts' / store.run_id(spec) / f'{attempt:04d}'
    directory.mkdir(parents=True, exist_ok=False)
    return directory


def _episode(design, variant, policies, seeds, loss, delay, strategy, directory, training):
    horizon = design['environment']['horizon_seconds']
    sumocfg, count = write_scenario(directory, ROOT / 'sumo/network/grid.net.xml',
                                    seeds['traffic'], design['demand_seconds'],
                                    design['vehicle_period'], horizon)
    config = FollowupEnvironmentConfig(
        sumo_config_file=sumocfg.resolve(), tripinfo_output=(directory / 'trips.xml').resolve(),
        seed=seeds['traffic'], packet_loss_seed=seeds['packet_loss'],
        packet_loss=float(loss), delay_ms=float(delay), strategy=strategy,
        feature_mode=design['variants'][variant]['features'],
        freshness=FreshnessConfig(**design['freshness']), **design['environment'])
    environment = FollowupEnvironment(config, policies)
    before = {a: (p.weights.copy(), p.bias.copy()) for a, p in policies.items()}
    total_reward, errors = 0., []
    neighbor_action_changes = agent_decisions = 0
    try:
        observations = environment.reset()
        terminal = False
        while not terminal:
            actions = {a: policies[a].select_action(observations[a], design['epsilon'] if training else 0.)
                       for a in AGENT_IDS}
            if not training:
                for agent in AGENT_IDS:
                    agent_decisions += 1
                    if observations[agent].size > 5:
                        local_only = observations[agent].copy()
                        local_only[5:] = 0
                        neighbor_action_changes += int(np.argmax(policies[agent].q_values(local_only)) != actions[agent])
            next_obs, rewards, terminal, telemetry = environment.step(actions)
            if training and design.get('training_stop_when_clear', False):
                terminal = terminal or environment.simulator._require_started().simulation.getMinExpectedNumber() == 0
            if training:
                for agent in AGENT_IDS:
                    errors.append(policies[agent].update(observations[agent], actions[agent],
                                                        rewards[agent], next_obs[agent], terminal))
            total_reward += sum(rewards.values())
            observations = next_obs
        if any(not np.isfinite(p.weights).all() or not np.isfinite(p.bias).all() for p in policies.values()):
            raise ValueError("Nonfinite learned parameters")
        if not training and any(not np.array_equal(p.weights, before[a][0]) or
                                not np.array_equal(p.bias, before[a][1]) for a, p in policies.items()):
            raise AssertionError("Evaluation modified policy parameters")
    finally:
        environment.close()
    metrics = read_trip_metrics(directory / 'trips.xml', count)
    return {
        **metrics, **telemetry, "episode_reward": total_reward,
        "mean_absolute_td_error": float(np.mean(np.abs(errors))) if errors else None,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "seeds": seeds, "packet_loss": loss, "delay_ms": delay,
        "demand_sha256": file_hash(directory / 'demand.rou.xml'),
        "tripinfo_sha256": file_hash(directory / 'trips.xml'),
        "neighbor_action_changes": neighbor_action_changes,
        "agent_decisions": agent_decisions,
    }


def train_one(store: CampaignStore, design: dict, variant: str, master: int) -> dict:
    spec = training_spec(variant, master)
    directory = _artifact_directory(store, spec)
    feature_mode = design['variants'][variant]['features']
    seed = episode_seeds(master, 'training', 0)['learner']
    learners = {a: LinearQAgent(5 if feature_mode == 'local' else 23, 2,
                               design['learning_rate'], design['discount_factor'], seed + index)
                for index, a in enumerate(AGENT_IDS)}
    schedule = training_schedule(design, master, variant)
    records = []
    try:
        for index, (loss, delay) in enumerate(schedule, 1):
            record = _episode(design, variant, learners, episode_seeds(master, 'training', index),
                              loss, delay, 'always', directory / f'episode_{index:04d}', True)
            write_json_exclusive(directory / f'episode_{index:04d}.json', record)
            records.append(record)
            if index in design.get('validation_budgets', []):
                stage = directory / f'validation_{index:04d}'
                for agent, learner in learners.items():
                    learner.save(stage / 'checkpoints' / f'{agent}.npz')
                validation = []
                for cell, (v_loss, v_delay) in enumerate(design['validation_conditions']):
                    # Load separate policies so epsilon-zero calls cannot advance
                    # the continuing training learner's exploration RNG.
                    frozen = {a: LinearQAgent.load(stage / 'checkpoints' / f'{a}.npz') for a in AGENT_IDS}
                    result = _episode(design, variant, frozen,
                                      episode_seeds(master, 'validation', 0),
                                      v_loss, v_delay, 'always', stage / f'cell_{cell:02d}', False)
                    validation.append(result)
                write_json_exclusive(stage / 'metrics.json', {
                    'training_episodes': index, 'results': validation,
                    'checkpoint_sha256': {a: file_hash(stage / 'checkpoints' / f'{a}.npz') for a in AGENT_IDS}})
                print(f"validation {variant} seed={master} episodes={index}: "
                      f"completion={[r['completion_fraction'] for r in validation]}", flush=True)
        checkpoints = directory / 'checkpoints'
        for agent, learner in learners.items():
            learner.save(checkpoints / f'{agent}.npz')
        hashes = {a: file_hash(checkpoints / f'{a}.npz') for a in AGENT_IDS}
        payload = {
            "checkpoint_directory": checkpoints.relative_to(store.directory).as_posix(),
            "checkpoint_sha256": hashes, "feature_mode": feature_mode,
            "training_episodes": len(records), "condition_schedule": schedule,
            "learner_seed": seed, "freshness": design['freshness'],
            "observation_schema": design['environment'].get('observation_schema', 'traffic_observation_v1'),
            "metadata_scale": design['environment'].get('metadata_scale', 1.0),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
        write_json_exclusive(directory / 'metadata.json', payload)
        return store.record(spec, 'success', payload)
    except Exception as error:
        write_json_exclusive(directory / 'failure.json', {'error': repr(error), 'traceback': traceback.format_exc()})
        return store.record(spec, 'failed', {'error': repr(error), 'artifact_directory': str(directory),
                                           'timestamp_utc': datetime.now(timezone.utc).isoformat()})


def evaluate_one(store: CampaignStore, design: dict, spec: dict, checkpoint: dict) -> dict:
    # Include exact training checkpoint bytes in the run's identity.
    spec = {**spec, 'checkpoint_sha256': checkpoint['checkpoint_sha256']}
    directory = _artifact_directory(store, spec)
    try:
        checkpoint_dir = store.directory / checkpoint['checkpoint_directory']
        if (checkpoint['feature_mode'] != design['variants'][spec['variant']]['features'] or
            checkpoint.get('metadata_scale', 1.0) != design['environment'].get('metadata_scale', 1.0) or
            checkpoint.get('observation_schema', 'traffic_observation_v1') !=
                design['environment'].get('observation_schema', 'traffic_observation_v1')):
            raise ValueError('checkpoint observation semantics differ from evaluation')
        if {a: file_hash(checkpoint_dir / f'{a}.npz') for a in AGENT_IDS} != checkpoint['checkpoint_sha256']:
            raise ValueError("Checkpoint files changed after training")
        learners = {a: LinearQAgent.load(checkpoint_dir / f'{a}.npz') for a in AGENT_IDS}
        result = _episode(design, spec['variant'], learners, spec['seeds'],
                          spec['packet_loss'], spec['delay_ms'], spec['strategy'], directory, False)
        return store.record(spec, 'success', result)
    except Exception as error:
        write_json_exclusive(directory / 'failure.json', {'error': repr(error), 'traceback': traceback.format_exc()})
        return store.record(spec, 'failed', {'error': repr(error), 'artifact_directory': str(directory),
                                           'timestamp_utc': datetime.now(timezone.utc).isoformat()})


def run_followup(store: CampaignStore, design: dict, retry_failed: bool = False) -> None:
    # Processes isolate TraCI/libsumo state. At most four SUMO
    # instances run; every logical job has a distinct immutable artifact path.
    with ProcessPoolExecutor(max_workers=design['workers']) as executor:
        futures = {}
        for master in design['master_seeds']:
            for variant in design['variants']:
                spec = training_spec(variant, master)
                if store.should_run(spec, retry_failed):
                    futures[executor.submit(train_one, store, design, variant, master)] = spec
        for future in as_completed(futures):
            spec = futures[future]
            record = future.result()
            print(f"training {spec['variant']} seed={spec['master_seed']}: {record['status']}", flush=True)
    trained = {(r['specification']['variant'], r['specification']['master_seed']): r['payload']
               for r in store.successful() if r['specification']['kind'] == 'training'}
    with ProcessPoolExecutor(max_workers=design['workers']) as executor:
        futures = {}
        for spec in evaluation_specs(design):
            checkpoint = trained.get((spec['variant'], spec['master_seed']))
            if checkpoint is None:
                continue
            identity = {**spec, 'checkpoint_sha256': checkpoint['checkpoint_sha256']}
            if store.should_run(identity, retry_failed):
                futures[executor.submit(evaluate_one, store, design, spec, checkpoint)] = spec
        for future in as_completed(futures):
            spec = futures[future]
            record = future.result()
            print(f"evaluation {spec['variant']} seed={spec['master_seed']} "
                  f"{spec['strategy']} loss={spec['packet_loss']} delay={spec['delay_ms']}: "
                  f"{record['status']}", flush=True)
