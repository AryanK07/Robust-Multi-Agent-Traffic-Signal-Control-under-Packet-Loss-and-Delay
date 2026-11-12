from types import SimpleNamespace
import numpy as np
import pytest

from traffic_control.communication import CommunicationChannel
from traffic_control.communication.action_margin import action_margin_certificate
from traffic_control.environment.safe_signals import SafeSignalTransitions


def test_margin_detects_joint_neighbor_flip_and_ignores_irrelevant_changes():
    obs = np.zeros(23); weights = np.zeros((2, 23)); bias = np.array([1.5, 0.])
    weights[1, [9, 18]] = 1
    lo = obs.copy(); hi = obs.copy(); hi[5:] = 1
    result = action_margin_certificate(obs, weights, bias, lo, hi)
    assert not result.invariant
    assert result.worst_case_margin == -.5
    assert result.neighbor_risks == (1, 1)
    weights[:, 5:] = 0
    assert action_margin_certificate(obs, weights, bias, lo, hi).invariant


def test_margin_certificate_matches_all_corners_on_small_active_subspace():
    from itertools import product
    rng = np.random.default_rng(17)
    for _ in range(30):
        obs = rng.uniform(size=23); w = rng.normal(size=(2, 23)); b = rng.normal(size=2)
        lo = obs.copy(); hi = obs.copy(); lo[[9, 18, 19]] = 0; hi[[9, 18, 19]] = 1
        result = action_margin_certificate(obs, w, b, lo, hi)
        margins = []
        for corner in product((0, 1), repeat=3):
            candidate = obs.copy(); candidate[[9, 18, 19]] = corner
            q = w @ candidate + b
            margins.append(q[result.action] - q[1-result.action])
        assert result.worst_case_margin == pytest.approx(min(margins))
        if result.invariant:
            assert min(margins) > 0


def test_signal_switch_cannot_skip_minimum_green_or_yellow():
    events = []
    connection = SimpleNamespace(trafficlight=SimpleNamespace(
        setPhase=lambda agent, phase: events.append((agent, phase)),
        setPhaseDuration=lambda *_: None))
    signals = SafeSignalTransitions(connection, ('A0',), 5, 3)
    assert not signals.request('A0', 1, 4.99)
    assert signals.request('A0', 1, 5)
    assert events[-1] == ('A0', 1)
    assert not signals.request('A0', 1, 6)
    signals.advance(7.99); assert events[-1] == ('A0', 1)
    signals.advance(8); assert events[-1] == ('A0', 2)
    assert not signals.request('A0', 1, 12.99)
    assert signals.request('A0', 1, 13)


def test_fractional_delay_boundary_and_episode_reset():
    channel = CommunicationChannel(delay_ms=100, packet_loss_probability=0.0, seed=7)
    channel.send('A0', 'A1', {}, .2)
    assert channel.receive('A1', .299) == ()
    assert len(channel.receive('A1', .3)) == 1
    channel.reset_episode()
    assert channel.telemetry().send_attempts == 0
    assert channel.pending_count() == 0
    lossy = CommunicationChannel(packet_loss_probability=.5, seed=7)
    patterns = []
    for _ in range(2):
        lossy.reset_episode()
        patterns.append([lossy.send('A0', 'A1', {}, i) and lossy.last_event.delivered for i in range(10)])
    assert patterns[0] == patterns[1]
