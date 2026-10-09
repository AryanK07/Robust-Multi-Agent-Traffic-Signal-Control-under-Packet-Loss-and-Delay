"""Run a deterministic Phase 5 packet-loss functional smoke test."""

import json

from traffic_control.communication import CommunicationChannel


def run_channel(packet_loss_probability: float, seed: int) -> dict[str, object]:
    channel = CommunicationChannel(packet_loss_probability=packet_loss_probability, seed=seed)
    for index in range(20):
        channel.send("A0", "A1", {"index": index}, 0.0)
    telemetry = channel.telemetry()
    return {
        "configured_packet_loss_probability": telemetry.configured_packet_loss_probability,
        "seed": telemetry.packet_loss_seed,
        "send_attempts": telemetry.send_attempts,
        "delivered_messages": telemetry.delivered_messages,
        "dropped_messages": telemetry.dropped_messages,
        "observed_loss_rate": telemetry.observed_loss_rate,
    }


def main() -> None:
    first = run_channel(0.0, 42)
    reproducible_first = run_channel(0.2, 42)
    reproducible_second = run_channel(0.2, 42)
    if reproducible_first != reproducible_second:
        raise RuntimeError("Seeded packet-loss smoke sequence was not reproducible")
    print(
        json.dumps(
            {
                "functional_verification": True,
                "delay_ms": 0,
                "zero_loss": first,
                "intermediate_loss": reproducible_first,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
