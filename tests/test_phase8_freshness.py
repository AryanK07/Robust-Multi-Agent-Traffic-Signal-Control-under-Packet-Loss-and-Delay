from pathlib import Path
import importlib.util

import numpy as np
import pytest

from traffic_control.communication import CommunicationChannel, FreshnessConfig
from traffic_control.communication.freshness import (
    NeighborInformationCache,
    TrafficSnapshot,
)
from traffic_control.rl import CommunicationAwareLinearQAgent
from traffic_control.rl import (
    AGENT_IDS,
    CommunicationAwareEnvironmentConfig,
    CommunicationAwareMultiAgentEnvironment,
)
from traffic_control.config import load_phase8_config


def payload(features: list[float], sender_id: str = "A0") -> dict[str, object]:
    return {
        "schema_version": "traffic_observation_v1",
        "sender_id": sender_id,
        "features": features,
    }


def test_freshness_age_weight_and_stale_boundary() -> None:
    config = FreshnessConfig(500.0, 2000.0, 1000.0)
    assert config.age_ms(10.0, 10.0) == 0.0
    assert config.weight(0.0) == 1.0
    assert config.weight(1000.0) == pytest.approx(np.exp(-2.0))
    assert config.normalized_age(5000.0) == 1.0
    assert not config.is_stale(999.999)
    assert config.is_stale(1000.0)
    with pytest.raises(ValueError):
        config.age_ms(2.0, 1.0)
    with pytest.raises(ValueError):
        FreshnessConfig(0.0, 1.0, 1.0)
    with pytest.raises(ValueError):
        FreshnessConfig(1.0, 1.0, -1.0)


def test_cache_preserves_latest_message_and_rejects_out_of_order() -> None:
    channel = CommunicationChannel()
    cache = NeighborInformationCache(channel.topology)
    first = channel.send("A0", "A1", payload([1.0] * 5), 1.0)
    second = channel.send("A0", "A1", payload([2.0] * 5), 2.0)
    assert cache.update("A1", first)
    assert cache.update("A1", second)
    assert not cache.update("A1", first)
    state = cache.get("A1", "A0")
    assert state is not None
    assert state.features == (2.0,) * 5


def test_cache_observation_has_sentinels_and_decay_weighted_payload() -> None:
    channel = CommunicationChannel()
    cache = NeighborInformationCache(channel.topology)
    no_message = cache.observation("A0", 0.0, FreshnessConfig())
    assert len(no_message) == 18
    assert no_message[:4] == (0.0, 1.0, 0.0, 1.0)
    message = channel.send("A1", "A0", payload([0.5] * 5, "A1"), 0.0)
    cache.update("A0", message)
    fresh = cache.observation("A0", 0.0, FreshnessConfig())
    old = cache.observation("A0", 1.0, FreshnessConfig())
    assert fresh[0:4] == (1.0, 0.0, 1.0, 0.0)
    assert old[2] < fresh[2]
    assert old[4] < fresh[4]


def test_dropped_messages_do_not_erase_cache() -> None:
    reliable = CommunicationChannel()
    cache = NeighborInformationCache(reliable.topology)
    message = reliable.send("A0", "A1", payload([0.3] * 5), 0.0)
    cache.update("A1", message)
    dropped = CommunicationChannel(packet_loss_probability=1.0, seed=3)
    dropped_message = dropped.send("A0", "A1", payload([0.9] * 5), 1.0)
    assert dropped.receive("A1", 2.0) == ()
    state = cache.get("A1", "A0")
    assert state is not None
    assert state.features == (0.3,) * 5
    assert dropped_message.delivery_timestamp is None


def test_communication_aware_checkpoint_metadata_is_separate_and_validated(
    tmp_path: Path,
) -> None:
    path = tmp_path / "aware.npz"
    agent = CommunicationAwareLinearQAgent(neighbor_ids=("A1", "B0"))
    agent.save(path)
    restored = CommunicationAwareLinearQAgent.load(
        path, expected_neighbor_ids=("A1", "B0")
    )
    assert restored.observation_size == 23
    assert restored.neighbor_ids == ("A1", "B0")
    with pytest.raises(ValueError):
        CommunicationAwareLinearQAgent.load(path, expected_neighbor_ids=("B0", "A1"))


def test_snapshot_requires_meaningful_typed_features() -> None:
    snapshot = TrafficSnapshot("A0", (0.0,) * 5, 2.0)
    assert snapshot.to_payload()["schema_version"] == "traffic_observation_v1"
    with pytest.raises(ValueError):
        TrafficSnapshot("A0", (0.0,) * 4, 2.0)


def test_phase8_yaml_configuration_is_validated() -> None:
    config = load_phase8_config("configs/phase8.yaml")
    assert config["policy"]["variant"] == "freshness_aware_iql"


@pytest.mark.sumo
@pytest.mark.skipif(
    importlib.util.find_spec("traci") is None, reason="TraCI is required"
)
def test_communication_aware_environment_sends_once_and_preserves_joint_step() -> None:
    environment = CommunicationAwareMultiAgentEnvironment(
        CommunicationAwareEnvironmentConfig(
            sumo_config_file=Path("sumo/simulation/grid.sumocfg"),
            max_steps=1,
            communication_delay_ms=0.0,
            communication_seed=42,
        )
    )
    try:
        observations = environment.reset()
        assert all(value.shape == (23,) for value in observations.values())
        assert environment.communication.telemetry().send_attempts == 8
        _, rewards, terminated, info = environment.step(
            {agent_id: 0 for agent_id in AGENT_IDS}
        )
        assert tuple(rewards) == AGENT_IDS
        assert terminated
        assert info["simulation_time"] == 1.0
        assert environment.communication.telemetry().send_attempts == 16
        assert len(info["message_cache"]["A0"]) == 2
    finally:
        environment.close()


@pytest.mark.sumo
@pytest.mark.skipif(
    importlib.util.find_spec("traci") is None, reason="TraCI is required"
)
@pytest.mark.parametrize("delay_ms,loss", [(0.0, 0.0), (250.0, 0.0), (250.0, 1.0)])
def test_step_reports_channel_counters_after_communication(
    delay_ms: float, loss: float
) -> None:
    """Channel and scheduler telemetry must describe the same completed step."""
    environment = CommunicationAwareMultiAgentEnvironment(
        CommunicationAwareEnvironmentConfig(
            sumo_config_file=Path("sumo/simulation/grid.sumocfg"),
            max_steps=2,
            communication_delay_ms=delay_ms,
            communication_packet_loss_probability=loss,
            communication_seed=42,
        )
    )
    try:
        environment.reset()
        for step in (1, 2):
            _, _, terminated, info = environment.step(
                {agent_id: 0 for agent_id in AGENT_IDS}
            )
            telemetry = info["communication"]
            assert telemetry == environment.communication.telemetry()
            assert telemetry.send_attempts == 8 * (step + 1)
            assert telemetry.send_attempts == (
                2 * info["communication_scheduler"].scheduled_transmissions
            )
            assert telemetry.send_attempts == (
                telemetry.successful_transmissions + telemetry.dropped_messages
            )
            assert telemetry.successful_transmissions == (
                telemetry.delivered_messages + telemetry.pending_messages
            )
            assert terminated == (step == 2)
    finally:
        environment.close()
