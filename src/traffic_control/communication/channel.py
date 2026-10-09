"""Deterministic ideal communication channel for Phase 4."""

from collections import defaultdict
from dataclasses import dataclass, replace
from math import isfinite
import random
from typing import Callable, Mapping

from .message import CommunicationMessage
from .topology import AGENT_IDS, NeighborTopology


@dataclass(frozen=True)
class CommunicationEvent:
    """Metadata for one valid message send attempt."""

    message_id: str
    sender_id: str
    receiver_id: str
    generation_timestamp: float
    delivered: bool


@dataclass(frozen=True)
class CommunicationTelemetry:
    """Bounded counters describing channel behavior."""

    send_attempts: int
    delivered_messages: int
    dropped_messages: int
    configured_packet_loss_probability: float
    packet_loss_seed: int | None

    @property
    def observed_loss_rate(self) -> float:
        """Return drops divided by attempts, or zero when no sends occurred."""
        if self.send_attempts == 0:
            return 0.0
        return self.dropped_messages / self.send_attempts


class CommunicationChannel:
    """Queue messages for explicit neighbors with configurable packet loss.

    Delay remains unsupported and must be zero. Dropped messages are not queued;
    the returned message is an attempted message identity, while telemetry and
    ``last_event`` expose whether it was delivered.
    """

    def __init__(
        self,
        agent_ids: tuple[str, ...] = AGENT_IDS,
        neighbors: Mapping[str, tuple[str, ...]] | None = None,
        *,
        enabled: bool = True,
        packet_loss_probability: float = 0.0,
        delay_ms: float = 0.0,
        seed: int | None = None,
        event_sink: Callable[[CommunicationEvent], None] | None = None,
    ) -> None:
        if not 0.0 <= packet_loss_probability <= 1.0:
            raise ValueError("packet_loss_probability must be between 0 and 1")
        if seed is not None and (not isinstance(seed, int) or seed < 0):
            raise ValueError("seed must be a non-negative integer or None")
        if delay_ms < 0 or not isfinite(delay_ms):
            raise ValueError("delay_ms must be a finite non-negative value")
        if delay_ms != 0.0:
            raise NotImplementedError(
                "Communication delay is deferred to Phase 6"
            )
        self.enabled = enabled
        self.topology = NeighborTopology(agent_ids, neighbors)
        self.packet_loss_probability = packet_loss_probability
        self.delay_ms = delay_ms
        self.seed = seed
        self._rng = random.Random(seed)
        self._event_sink = event_sink
        self._pending: dict[str, list[CommunicationMessage]] = defaultdict(list)
        self._next_message_number = 0
        self._send_attempts = 0
        self._delivered_messages = 0
        self._dropped_messages = 0
        self.last_event: CommunicationEvent | None = None

    def send(
        self,
        sender_id: str,
        receiver_id: str,
        payload: Mapping[str, object],
        timestamp: float,
    ) -> CommunicationMessage:
        """Queue a message for an explicit neighbor at simulation time."""
        self._validate_timestamp(timestamp)
        self._validate_agent(sender_id)
        self._validate_agent(receiver_id)
        if not self.topology.contains(sender_id, receiver_id):
            raise ValueError(f"{receiver_id} is not a neighbor of {sender_id}")
        if not self.enabled:
            raise RuntimeError("Communication is disabled")
        message = CommunicationMessage(
            message_id=f"{sender_id}->{receiver_id}:{self._next_message_number}",
            sender_id=sender_id,
            receiver_id=receiver_id,
            generation_timestamp=timestamp,
            payload=payload,
        )
        self._next_message_number += 1
        self._send_attempts += 1
        delivered = (
            self.packet_loss_probability == 0.0
            or (
                self.packet_loss_probability < 1.0
                and self._rng.random() >= self.packet_loss_probability
            )
        )
        if delivered:
            self._pending[receiver_id].append(message)
            self._delivered_messages += 1
        else:
            self._dropped_messages += 1
        self.last_event = CommunicationEvent(
            message_id=message.message_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            generation_timestamp=timestamp,
            delivered=delivered,
        )
        if self._event_sink is not None:
            self._event_sink(self.last_event)
        return message

    def receive(
        self, receiver_id: str, current_time: float
    ) -> tuple[CommunicationMessage, ...]:
        """Return all messages available at ``current_time`` in send order."""
        self._validate_timestamp(current_time)
        self._validate_agent(receiver_id)
        if not self.enabled:
            return ()
        pending = self._pending[receiver_id]
        available = [message for message in pending if message.generation_timestamp <= current_time]
        self._pending[receiver_id] = [
            message for message in pending if message.generation_timestamp > current_time
        ]
        available.sort(key=lambda message: (message.generation_timestamp, message.message_id))
        return tuple(
            replace(message, delivery_timestamp=message.generation_timestamp)
            for message in available
        )

    def clear(self) -> None:
        """Discard queued messages and reset message identity, not telemetry/RNG."""
        self._pending.clear()
        self._next_message_number = 0

    def reset_telemetry(self) -> None:
        """Reset counters without resetting the seeded RNG sequence."""
        self._send_attempts = 0
        self._delivered_messages = 0
        self._dropped_messages = 0
        self.last_event = None

    def telemetry(self) -> CommunicationTelemetry:
        """Return a snapshot of packet-loss counters and configuration."""
        return CommunicationTelemetry(
            send_attempts=self._send_attempts,
            delivered_messages=self._delivered_messages,
            dropped_messages=self._dropped_messages,
            configured_packet_loss_probability=self.packet_loss_probability,
            packet_loss_seed=self.seed,
        )

    def pending_count(self, receiver_id: str | None = None) -> int:
        """Return queued message count globally or for one receiver."""
        if receiver_id is None:
            return sum(len(messages) for messages in self._pending.values())
        self._validate_agent(receiver_id)
        return len(self._pending[receiver_id])

    def _validate_agent(self, agent_id: str) -> None:
        if agent_id not in self.topology.agent_ids:
            raise ValueError(f"Unknown agent: {agent_id}")

    @staticmethod
    def _validate_timestamp(timestamp: float) -> None:
        if not isfinite(timestamp) or timestamp < 0:
            raise ValueError("simulation timestamp must be finite and non-negative")
