from pathlib import Path
import shutil

import numpy as np
import pytest

from traffic_control.environment.trip_metrics import read_trip_metrics
from traffic_control.rl import AGENT_IDS, LinearQAgent
from traffic_control.rl.followup_env import FollowupEnvironment, FollowupEnvironmentConfig


pytestmark = [pytest.mark.sumo, pytest.mark.skipif(shutil.which('sumo') is None, reason='SUMO required')]


def make_env(tmp_path, **changes):
    config = FollowupEnvironmentConfig(
        sumo_config_file=Path('sumo/simulation/grid.sumocfg').resolve(),
        tripinfo_output=tmp_path / 'trip.xml', horizon_seconds=2, **changes)
    policies = {agent: LinearQAgent(5 if config.feature_mode == 'local' else 23, 2) for agent in AGENT_IDS}
    return FollowupEnvironment(config, policies)


@pytest.mark.parametrize('delay,age', [(100, 100), (250, 300), (500, 500), (1000, 1000)])
def test_distinct_subsecond_delays_reach_policy_with_distinct_ages(tmp_path, delay, age):
    env = make_env(tmp_path, delay_ms=delay)
    try:
        env.reset()
        obs, _, done, info = env.step(dict.fromkeys(AGENT_IDS, 0))
        assert not done
        state = env.cache.get('A0', 'A1')
        assert (env.time - state.generation_timestamp) * 1000 == pytest.approx(age)
        assert obs['A0'][6] == pytest.approx(age / 2000)
        assert info['communication']['send_attempts'] == 88
        env.step(dict.fromkeys(AGENT_IDS, 0))
        # No gratuitous terminal snapshot round: t=0 through t=1.9.
        assert env.channel.telemetry().send_attempts == 160
    finally:
        env.close()
    metrics = read_trip_metrics(tmp_path / 'trip.xml', 6)
    assert metrics['metric_schema'] == 'tripinfo_v2'
    assert metrics['horizon_censored']


def test_pull_uses_two_delayed_legs_and_counts_both(tmp_path):
    env = make_env(tmp_path, delay_ms=250, strategy='action_sensitive')
    try:
        env.reset()
        assert env.cache.get('A0', 'A1') is None
        _, _, _, info = env.step(dict.fromkeys(AGENT_IDS, 0))
        state = env.cache.get('A0', 'A1')
        assert state.generation_timestamp == .25
        assert state.delivery_timestamp == .5
        assert info['trigger_counts']['request_attempts'] == 8
        assert info['trigger_counts']['response_attempts'] == 8
        assert info['communication']['send_attempts'] == 16
        assert info['trigger_counts']['request_suppressed'] > 0
    finally:
        env.close()


def test_lost_requests_never_create_free_responses_or_cache_updates(tmp_path):
    env = make_env(tmp_path, packet_loss=1, strategy='action_sensitive')
    try:
        env.reset()
        _, _, _, info = env.step(dict.fromkeys(AGENT_IDS, 0))
        assert info['communication']['dropped_messages'] == 8
        assert info['trigger_counts'].get('response_attempts', 0) == 0
        assert env.cache.get('A0', 'A1') is None
        assert info['missing_message_fraction'] == 1
    finally:
        env.close()


@pytest.mark.parametrize('mode,indices', [('plain', [5,6,7,8,14,15,16,17]),
                                        ('no_age', [6,15]), ('no_availability',[5,14]),
                                        ('no_decay',[7,16]), ('no_stale',[8,17])])
def test_component_ablations_have_fixed_zero_coordinates(tmp_path, mode, indices):
    env = make_env(tmp_path, feature_mode=mode)
    try:
        obs = env.reset()['A0']
        assert np.all(obs[indices] == 0)
        lower, upper = env._bounds(obs)
        assert np.all(lower[indices] == 0) and np.all(upper[indices] == 0)
    finally:
        env.close()
