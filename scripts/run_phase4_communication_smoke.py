"""Run a deterministic Phase 4 message delivery smoke test."""

import json

from traffic_control.communication import CommunicationChannel


def main() -> None:
    channel = CommunicationChannel()
    sent = channel.send("A0", "A1", {"queue_length": 3, "phase": 0}, 10.0)
    received = channel.receive("A1", 10.0)
    if (
        len(received) != 1
        or received[0].message_id != sent.message_id
        or received[0].sender_id != sent.sender_id
        or received[0].receiver_id != sent.receiver_id
        or received[0].generation_timestamp != sent.generation_timestamp
        or dict(received[0].payload) != dict(sent.payload)
        or received[0].delivery_timestamp != 10.0
    ):
        raise RuntimeError("Phase 4 message was not delivered with preserved metadata")
    print(
        json.dumps(
            {
                "functional_verification": True,
                "sender": sent.sender_id,
                "receiver": sent.receiver_id,
                "generation_timestamp": sent.generation_timestamp,
                "delivery_timestamp": received[0].delivery_timestamp,
                "payload": dict(received[0].payload),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
