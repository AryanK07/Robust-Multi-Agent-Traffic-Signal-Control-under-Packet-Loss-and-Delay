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
    telemetry = channel.telemetry()
    assert (telemetry.send_attempts, telemetry.delivered_messages, telemetry.dropped_messages) == (2, 2, 0)
    assert telemetry.observed_loss_rate == 0.0


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


def test_full_packet_loss_drops_every_message_and_records_event() -> None:
    channel = CommunicationChannel(packet_loss_probability=1.0, seed=7)
    message = channel.send("A0", "A1", {"queue": 1}, 2.0)

    assert channel.receive("A1", 2.0) == ()
    assert channel.last_event is not None
    assert channel.last_event.message_id == message.message_id
    assert channel.last_event.delivered is False
    telemetry = channel.telemetry()
    assert (telemetry.send_attempts, telemetry.delivered_messages, telemetry.dropped_messages) == (1, 0, 1)
    assert telemetry.observed_loss_rate == 1.0


def test_intermediate_packet_loss_is_reproducible_with_isolated_seed() -> None:
    first = CommunicationChannel(packet_loss_probability=0.5, seed=42)
    second = CommunicationChannel(packet_loss_probability=0.5, seed=42)
    first_results = [first.send("A0", "A1", {"index": i}, 0.0) and first.last_event.delivered for i in range(20)]
    second_results = [second.send("A0", "A1", {"index": i}, 0.0) and second.last_event.delivered for i in range(20)]

    assert first_results == second_results
    assert first.telemetry() == second.telemetry()


def test_telemetry_reset_does_not_reset_rng_sequence() -> None:
    channel = CommunicationChannel(packet_loss_probability=0.5, seed=42)
    channel.send("A0", "A1", {}, 0.0)
    first_event = channel.last_event
    channel.reset_telemetry()
    channel.send("A0", "A1", {}, 0.0)

    fresh = CommunicationChannel(packet_loss_probability=0.5, seed=42)
    fresh.send("A0", "A1", {}, 0.0)
    fresh_first = fresh.last_event
    fresh.send("A0", "A1", {}, 0.0)
    fresh_second = fresh.last_event
    assert channel.last_event is not None
    assert first_event is not None
    assert channel.last_event.delivered == fresh_second.delivered
    assert fresh_first is not None
    assert first_event.delivered == fresh_first.delivered
    assert channel.telemetry().send_attempts == 1
    assert channel.telemetry().dropped_messages + channel.telemetry().delivered_messages == 1


@pytest.mark.parametrize(
    ("packet_loss_probability", "delay_ms"),
    [(-0.1, 0.0), (1.1, 0.0)],
)
def test_invalid_or_deferred_impairments_are_rejected(
    packet_loss_probability: float, delay_ms: float
) -> None:
    with pytest.raises(ValueError):
        CommunicationChannel(packet_loss_probability=packet_loss_probability, delay_ms=delay_ms)


def test_invalid_timestamps_and_payload_are_rejected() -> None:
    with pytest.raises(ValueError):
        CommunicationChannel().send("A0", "A1", {}, -1.0)
    with pytest.raises(TypeError):
        CommunicationMessage("message-1", "A0", "A1", 0.0, [])  # type: ignore[arg-type]


def test_fixed_delay_uses_milliseconds_and_simulation_time() -> None:
    channel = CommunicationChannel(delay_ms=250)
    message = channel.send("A0", "A1", {"value": 1}, 10.0)

    assert message.delivery_timestamp is None
    assert channel.pending_count("A1") == 1
    assert channel.receive("A1", 10.249) == ()
    delivered = channel.receive("A1", 10.25)
    assert len(delivered) == 1
    assert delivered[0].delivery_timestamp == 10.25
    assert delivered[0].generation_timestamp == 10.0
    assert delivered[0].age_at(10.25) == pytest.approx(0.25)


def test_multiple_pending_messages_are_ordered_by_delivery_then_send_order() -> None:
    channel = CommunicationChannel(delay_ms=100)
    later = channel.send("A0", "A1", {"index": "later"}, 2.0)
    first = channel.send("A0", "A1", {"index": "first"}, 1.0)
    tied = channel.send("A0", "A1", {"index": "tied"}, 1.0)

    assert channel.receive("A1", 1.099) == ()
    first_received = channel.receive("A1", 1.1)
    assert [message.message_id for message in first_received] == [first.message_id, tied.message_id]
    second_received = channel.receive("A1", 2.1)
    assert [message.message_id for message in second_received] == [later.message_id]
    assert channel.receive("A1", 2.1) == ()


def test_multiple_receivers_have_independent_pending_queues() -> None:
    channel = CommunicationChannel(delay_ms=250)
    channel.send("A0", "A1", {"receiver": "A1"}, 10.0)
    channel.send("A0", "B0", {"receiver": "B0"}, 10.0)

    assert channel.receive("A1", 10.25)[0].receiver_id == "A1"
    assert channel.receive("B0", 10.249) == ()
    assert channel.receive("B0", 10.25)[0].receiver_id == "B0"


def test_dropped_messages_are_not_scheduled_and_do_not_consume_delay_behavior() -> None:
    channel = CommunicationChannel(packet_loss_probability=1.0, delay_ms=250, seed=42)
    message = channel.send("A0", "A1", {}, 10.0)

    assert message.delivery_timestamp is None
    assert channel.pending_count() == 0
    assert channel.receive("A1", 100.0) == ()
    telemetry = channel.telemetry()
    assert telemetry.successful_transmissions == 0
    assert telemetry.delivered_messages == 0
    assert telemetry.dropped_messages == 1


def test_delay_and_packet_loss_are_reproducible_with_same_seed() -> None:
    channels = [
        CommunicationChannel(packet_loss_probability=0.5, delay_ms=250, seed=42),
        CommunicationChannel(packet_loss_probability=0.5, delay_ms=250, seed=42),
    ]
    results = []
    for channel in channels:
        messages = [
            channel.send("A0", "A1", {"index": index}, 0.0)
            for index in range(20)
        ]
        results.append(
            (
                [channel.last_event.delivered for _ in [0]],
                channel.telemetry(),
                channel.receive("A1", 0.25),
                messages,
            )
        )
    assert results[0][1] == results[1][1]
    assert [m.message_id for m in results[0][2]] == [m.message_id for m in results[1][2]]


def test_invalid_delay_model_and_negative_delay_are_rejected() -> None:
    with pytest.raises(ValueError):
        CommunicationChannel(delay_ms=-1)
    with pytest.raises(ValueError):
        CommunicationChannel(delay_model="stochastic")
