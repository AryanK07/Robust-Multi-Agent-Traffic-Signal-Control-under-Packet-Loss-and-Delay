from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest

from traffic_control.rl.phase_features import phase_features
from traffic_control.communication import CommunicationChannel
from traffic_control.communication.freshness import TrafficSnapshot, NeighborInformationCache, PHASE_FEATURE_SCHEMA
from traffic_control.experiments.artifacts import CampaignStore
from traffic_control.experiments.followup_design import load_design
from traffic_control.experiments import followup
from traffic_control.rl import AGENT_IDS, LinearQAgent


def test_conflicting_demands_do_not_alias_and_clock_exposes_constraints():
    a = phase_features(5, 0, 5, 0, 5, 0, None, 5, 3)
    b = phase_features(0, 5, 0, 5, 5, 0, None, 5, 3)
    assert a[0] + a[1] == b[0] + b[1]
    assert not np.array_equal(a, b)
    assert a[4] == 1
    assert phase_features(0, 0, 0, 0, 0, 0, None, 5, 3)[4] == .5
    assert phase_features(0, 0, 0, 0, 5, 0, 8, 5, 3)[4] == 0
    assert phase_features(0, 0, 0, 0, 6.5, 0, 8, 5, 3)[4] == .25


def test_different_feature_semantics_cannot_enter_legacy_cache():
    channel = CommunicationChannel()
    payload = TrafficSnapshot('A0', (0.,)*5, 0., PHASE_FEATURE_SCHEMA).to_payload()
    message = channel.send('A0', 'A1', payload, 0.)
    with pytest.raises(ValueError, match='cache schema'):
        NeighborInformationCache(channel.topology).update('A1', message)
    assert NeighborInformationCache(channel.topology, PHASE_FEATURE_SCHEMA).update('A1', message)


def test_checkpoint_validation_does_not_advance_training_rng(tmp_path, monkeypatch):
    def fake_episode(design, variant, policies, seeds, loss, delay, strategy, directory, training):
        for agent in policies.values():
            obs = np.ones(agent.observation_size)
            for _ in range(12):
                action = agent.select_action(obs, .5 if training else 0.)
                if training:
                    agent.update(obs, action, -1., obs, False)
        return {'completion_fraction': 1.}
    monkeypatch.setattr(followup, '_episode', fake_episode)
    design = load_design(Path('configs/followup_v2.yaml'))
    design['training_episodes'] = 2
    results = []
    for validate in (False, True):
        current = deepcopy(design)
        current['validation_budgets'] = [1] if validate else []
        current['validation_conditions'] = [[0, 0]]
        store = CampaignStore(tmp_path / str(validate), {'validation': validate})
        result = followup.train_one(store, current, 'full_robust', 19)
        assert result['status'] == 'success'
        results.append({a: LinearQAgent.load(store.directory / result['payload']['checkpoint_directory'] / f'{a}.npz') for a in AGENT_IDS})
    for agent in AGENT_IDS:
        np.testing.assert_array_equal(results[0][agent].weights, results[1][agent].weights)
        np.testing.assert_array_equal(results[0][agent].bias, results[1][agent].bias)
