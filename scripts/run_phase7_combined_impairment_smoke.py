"""Run a bounded Phase 7 communication-matrix functional smoke test."""

import json

from traffic_control.communication import CommunicationChannel
from traffic_control.experiments import Phase7Condition, load_phase7_config


def main() -> None:
    config = load_phase7_config("configs/phase7.yaml")
    selected = (
        Phase7Condition(0.0, 0.0),
        Phase7Condition(0.10, 0.0),
        Phase7Condition(0.0, 250.0),
        Phase7Condition(0.10, 250.0),
    )
    rows = []
    for condition in selected:
        channel = CommunicationChannel(
            packet_loss_probability=condition.packet_loss_probability,
            delay_ms=condition.delay_ms,
            seed=42,
        )
        message = channel.send("A0", "A1", {"condition": condition.condition_id}, 10.0)
        before = channel.receive("A1", 10.0)
        delivery_time = 10.0 + condition.delay_ms / 1000.0
        at_delivery = (
            before
            if condition.delay_ms == 0.0
            else channel.receive("A1", delivery_time)
        )
        telemetry = channel.telemetry()
        delivered = bool(at_delivery)
        if condition.packet_loss_probability == 0.0 and not delivered:
            raise RuntimeError("Reliable smoke condition did not deliver")
        if condition.packet_loss_probability == 0.0 and condition.delay_ms > 0 and before:
            raise RuntimeError("Message was available before its delivery timestamp")
        if delivered and at_delivery[0].payload != message.payload:
            raise RuntimeError("Message payload was not preserved")
        rows.append(
            {
                "condition": condition.condition_id,
                "packet_loss_probability": condition.packet_loss_probability,
                "delay_ms": condition.delay_ms,
                "send_attempts": telemetry.send_attempts,
                "successful_transmissions": telemetry.successful_transmissions,
                "dropped_messages": telemetry.dropped_messages,
                "delivered_messages": telemetry.delivered_messages,
                "pending_messages": telemetry.pending_messages,
                "observed_loss_rate": telemetry.observed_loss_rate,
                "message_id": message.message_id,
                "scheduled_delivery_timestamp": (
                    delivery_time
                    if telemetry.successful_transmissions
                    else None
                ),
                "delivered": delivered,
                "simulation_time_advanced": False,
                "functional_verification": True,
            }
        )
    print(json.dumps({"conditions_tested": len(rows), "results": rows}, indent=2))


if __name__ == "__main__":
    main()
