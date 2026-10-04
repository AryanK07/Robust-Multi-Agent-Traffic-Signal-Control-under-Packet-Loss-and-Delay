import pytest

from traffic_control.communication import (
    AGENT_IDS,
    DEFAULT_NEIGHBORS,
    CommunicationChannel,
    CommunicationMessage,
    NeighborTopology,
)


def test_message_preserves_identity_timestamp_and_payload() -> None:
    message = CommunicationMessage("message-1", "A0", "A1", 10.0, {"queue": 3})

    assert message.sender_id == "A0"
    assert message.receiver_id == "A1"
    assert message.generation_timestamp == 10.0
    assert dict(message.payload) == {"queue": 3}
    assert message.delivery_timestamp is None
    assert message.age_at(12.5) == 2.5


def test_ideal_channel_delivers_immediately_and_deterministically() -> None:
    channel = CommunicationChannel()
    first = channel.send("A0", "A1", {"queue": 3}, 10.0)
    second = channel.send("A0", "A1", {"queue": 4}, 10.0)

    messages = channel.receive("A1", 10.0)

    assert [message.message_id for message in messages] == [first.message_id, second.message_id]
    assert [dict(message.payload) for message in messages] == [{"queue": 3}, {"queue": 4}]
    assert all(message.delivery_timestamp == 10.0 for message in messages)
    assert channel.receive("A1", 10.0) == ()


def test_messages_are_available_only_at_or_after_generation_time() -> None:
    channel = CommunicationChannel()
    channel.send("A0", "A1", {"phase": 2}, 10.0)

    assert channel.receive("A1", 9.0) == ()
    assert channel.pending_count("A1") == 1
    assert channel.receive("A1", 10.0)[0].generation_timestamp == 10.0


def test_multiple_receivers_and_explicit_neighbors() -> None:
    channel = CommunicationChannel()
    channel.send("A0", "A1", {"value": 1}, 0.0)
    channel.send("A0", "B0", {"value": 2}, 0.0)

    assert dict(channel.receive("A1", 0.0)[0].payload) == {"value": 1}
    assert dict(channel.receive("B0", 0.0)[0].payload) == {"value": 2}


@pytest.mark.parametrize(
    ("sender", "receiver"),
    [("unknown", "A1"), ("A0", "unknown"), ("A0", "B1")],
)
def test_invalid_sender_receiver_or_neighbor_is_rejected(sender: str, receiver: str) -> None:
    with pytest.raises(ValueError):
        CommunicationChannel().send(sender, receiver, {}, 0.0)


def test_topology_is_configurable_and_validated() -> None:
    topology = NeighborTopology(
        agent_ids=("left", "right"),
        neighbors={"left": ("right",), "right": ("left",)},
    )
    assert topology.for_agent("left") == ("right",)
    with pytest.raises(ValueError):
        NeighborTopology(
            agent_ids=AGENT_IDS,
            neighbors={**DEFAULT_NEIGHBORS, "A0": ("missing",)},
        )


@pytest.mark.parametrize(
    ("packet_loss_probability", "delay_ms"),
    [(0.1, 0.0), (0.0, 1.0)],
)
def test_phase_four_rejects_deferred_impairments(
    packet_loss_probability: float, delay_ms: float
) -> None:
    with pytest.raises(NotImplementedError):
        CommunicationChannel(
            packet_loss_probability=packet_loss_probability,
            delay_ms=delay_ms,
        )


def test_invalid_timestamps_and_payload_are_rejected() -> None:
    with pytest.raises(ValueError):
        CommunicationChannel().send("A0", "A1", {}, -1.0)
    with pytest.raises(TypeError):
        CommunicationMessage("message-1", "A0", "A1", 0.0, [])  # type: ignore[arg-type]
