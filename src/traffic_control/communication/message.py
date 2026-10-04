"""Typed messages exchanged by traffic-signal agents."""

from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class CommunicationMessage:
    """A message with simulation-time metadata and a structured payload."""

    message_id: str
    sender_id: str
    receiver_id: str
    generation_timestamp: float
    payload: Mapping[str, object]
    delivery_timestamp: float | None = None

    def __post_init__(self) -> None:
        if not self.message_id:
            raise ValueError("message_id must not be empty")
        if not self.sender_id or not self.receiver_id:
            raise ValueError("sender_id and receiver_id must not be empty")
        if not isfinite(self.generation_timestamp) or self.generation_timestamp < 0:
            raise ValueError("generation_timestamp must be a finite non-negative value")
        if self.delivery_timestamp is not None and (
            not isfinite(self.delivery_timestamp)
            or self.delivery_timestamp < self.generation_timestamp
        ):
            raise ValueError("delivery_timestamp must not precede generation_timestamp")
        if not isinstance(self.payload, Mapping):
            raise TypeError("payload must be a mapping")
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))

    def age_at(self, current_timestamp: float) -> float:
        """Return message age in simulation seconds at a given time."""
        if not isfinite(current_timestamp) or current_timestamp < self.generation_timestamp:
            raise ValueError("current_timestamp must be finite and not precede generation_timestamp")
        return current_timestamp - self.generation_timestamp
