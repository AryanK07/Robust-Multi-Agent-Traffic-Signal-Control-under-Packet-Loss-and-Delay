"""Deterministic ideal communication channel for Phase 4."""

from collections import defaultdict
from dataclasses import replace
from math import isfinite
from typing import Mapping

from .message import CommunicationMessage
from .topology import AGENT_IDS, NeighborTopology


class CommunicationChannel:
    """Queue messages for explicit neighbors with zero loss and zero delay.

    Non-zero packet loss or delay is rejected until its dedicated phase is
    implemented. This keeps Phase 4 behavior explicit instead of providing
    inactive-looking impairment settings.
    """

    def __init__(
        self,
        agent_ids: tuple[str, ...] = AGENT_IDS,
        neighbors: Mapping[str, tuple[str, ...]] | None = None,
        *,
        enabled: bool = True,
        packet_loss_probability: float = 0.0,
        delay_ms: float = 0.0,
    ) -> None:
        if not 0.0 <= packet_loss_probability <= 1.0:
            raise ValueError("packet_loss_probability must be between 0 and 1")
        if delay_ms < 0 or not isfinite(delay_ms):
            raise ValueError("delay_ms must be a finite non-negative value")
        if packet_loss_probability != 0.0 or delay_ms != 0.0:
            raise NotImplementedError(
                "Packet loss and delay are deferred to later communication phases"
            )
        self.enabled = enabled
        self.topology = NeighborTopology(agent_ids, neighbors)
        self.packet_loss_probability = packet_loss_probability
        self.delay_ms = delay_ms
        self._pending: dict[str, list[CommunicationMessage]] = defaultdict(list)
        self._next_message_number = 0

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
        self._pending[receiver_id].append(message)
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
        return tuple(replace(message, delivery_timestamp=current_time) for message in available)

    def clear(self) -> None:
        """Discard queued messages and reset deterministic message identity."""
        self._pending.clear()
        self._next_message_number = 0

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
