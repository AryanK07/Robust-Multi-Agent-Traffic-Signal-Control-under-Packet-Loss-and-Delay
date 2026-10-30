"""Run the Phase 6 communication-delay functional smoke test."""

import json

from traffic_control.communication import CommunicationChannel


def main() -> None:
    channel = CommunicationChannel(
        packet_loss_probability=0.0,
        delay_model="fixed",
        delay_ms=250,
        seed=42,
    )
    message = channel.send("A0", "A1", {"queue": 3}, 10.0)
    before = channel.receive("A1", 10.0)
    near_delivery = channel.receive("A1", 10.249)
    delivered = channel.receive("A1", 10.25)
    telemetry = channel.telemetry()

    if before or near_delivery or len(delivered) != 1:
        raise RuntimeError("Fixed-delay delivery boundary was incorrect")
    received = delivered[0]
    if (
        received.payload != message.payload
        or received.generation_timestamp != 10.0
        or received.delivery_timestamp != 10.25
    ):
        raise RuntimeError("Message metadata was not preserved")

    loss_channel = CommunicationChannel(
        packet_loss_probability=1.0,
        delay_model="fixed",
        delay_ms=250,
        seed=42,
    )
    loss_channel.send("A0", "A1", {"queue": 3}, 10.0)
    loss_telemetry = loss_channel.telemetry()
    print(
        json.dumps(
            {
                "functional_verification": True,
                "configured_delay_ms": telemetry.configured_delay_ms,
                "packet_loss_probability": telemetry.configured_packet_loss_probability,
                "send_attempts": telemetry.send_attempts,
                "successful_transmissions": telemetry.successful_transmissions,
                "dropped_messages": telemetry.dropped_messages,
                "pending_messages": telemetry.pending_messages,
                "delivered_messages": telemetry.delivered_messages,
                "delivery_timestamps": [received.delivery_timestamp],
                "observed_packet_loss_rate": telemetry.observed_loss_rate,
                "packet_loss_compatibility": {
                    "send_attempts": loss_telemetry.send_attempts,
                    "successful_transmissions": loss_telemetry.successful_transmissions,
                    "dropped_messages": loss_telemetry.dropped_messages,
                    "pending_messages": loss_telemetry.pending_messages,
                    "observed_packet_loss_rate": loss_telemetry.observed_loss_rate,
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
