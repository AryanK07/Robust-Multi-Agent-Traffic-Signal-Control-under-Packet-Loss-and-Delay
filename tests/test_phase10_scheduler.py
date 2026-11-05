from pathlib import Path

import numpy as np
import pytest

from traffic_control.communication import CommunicationScheduler
from traffic_control.config import load_phase10_config
from traffic_control.experiments import communication_reduction


OBSERVATION = np.zeros(5, dtype=np.float32)


def test_always_transmits_every_opportunity() -> None:
    scheduler = CommunicationScheduler(("A0",), strategy="always")
    assert scheduler.should_transmit("A0", OBSERVATION, 0.0).transmit
    assert scheduler.should_transmit("A0", OBSERVATION, 1.0).transmit
    assert scheduler.telemetry().scheduled_transmissions == 2


def test_periodic_mode_respects_simulation_interval() -> None:
    scheduler = CommunicationScheduler(("A0",), strategy="periodic", periodic_interval_ms=1000)
    assert scheduler.should_transmit("A0", OBSERVATION, 0.0).trigger_reason == "first"
    assert not scheduler.should_transmit("A0", OBSERVATION, 0.999).transmit
    assert scheduler.should_transmit("A0", OBSERVATION, 1.0).trigger_reason == "periodic"


def test_adaptive_uses_last_transmitted_state_and_heartbeat() -> None:
    scheduler = CommunicationScheduler(
        ("A0",), strategy="adaptive", change_threshold=0.1, max_silence_ms=1000
    )
    assert scheduler.should_transmit("A0", OBSERVATION, 0).transmit
    assert not scheduler.should_transmit("A0", np.full(5, 0.05), 0.1).transmit
    decision = scheduler.should_transmit("A0", np.full(5, 0.1), 0.2)
    assert decision.transmit and decision.trigger_reason == "change"
    assert not scheduler.should_transmit("A0", np.full(5, 0.15), 0.3).transmit
    heartbeat = scheduler.should_transmit("A0", np.full(5, 0.15), 1.2)
    assert heartbeat.transmit and heartbeat.trigger_reason == "heartbeat"


def test_scheduler_validation_and_determinism() -> None:
    with pytest.raises(ValueError):
        CommunicationScheduler(("A0",), strategy="unknown")
    with pytest.raises(ValueError):
        CommunicationScheduler(("A0",), max_silence_ms=0)
    scheduler = CommunicationScheduler(("A0",), strategy="adaptive")
    with pytest.raises(ValueError):
        scheduler.should_transmit("A0", np.zeros(4), 0)
    scheduler.should_transmit("A0", OBSERVATION, 1)
    with pytest.raises(ValueError):
        scheduler.should_transmit("A0", OBSERVATION, 0)


def test_phase10_config_and_reduction() -> None:
    phase10 = load_phase10_config(Path("configs/phase10.yaml"))
    assert phase10["communication"]["strategy"] == "always"
    assert communication_reduction(0, 0) == 0.0
    assert communication_reduction(10, 4) == 0.6
