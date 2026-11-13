"""Freshness-aware neighbor state caching for communication-aware policies."""

from dataclasses import dataclass
from math import exp, isfinite
from typing import Mapping

from .message import CommunicationMessage
from .topology import NeighborTopology


FEATURE_SCHEMA_VERSION = "traffic_observation_v1"
PHASE_FEATURE_SCHEMA = "phase_relative_observation_v3"
LOCAL_FEATURE_COUNT = 5
NEIGHBOR_FEATURE_COUNT = 9


@dataclass(frozen=True)
class FreshnessConfig:
    """Parameters controlling age normalization and exponential decay."""

    freshness_decay_tau_ms: float = 500.0
    max_message_age_ms: float = 2000.0
    stale_message_threshold_ms: float = 1000.0

    def __post_init__(self) -> None:
        if not isfinite(self.freshness_decay_tau_ms) or self.freshness_decay_tau_ms <= 0:
            raise ValueError("freshness_decay_tau_ms must be positive and finite")
        if not isfinite(self.max_message_age_ms) or self.max_message_age_ms <= 0:
            raise ValueError("max_message_age_ms must be positive and finite")
        if not isfinite(self.stale_message_threshold_ms) or self.stale_message_threshold_ms < 0:
            raise ValueError("stale_message_threshold_ms must be finite and non-negative")

    def age_ms(self, generation_timestamp: float, current_timestamp: float) -> float:
        """Return simulation-time message age in milliseconds."""
        if not isfinite(generation_timestamp) or not isfinite(current_timestamp):
            raise ValueError("timestamps must be finite")
        if current_timestamp < generation_timestamp:
            raise ValueError("current_timestamp must not precede generation_timestamp")
        return (current_timestamp - generation_timestamp) * 1000.0

    def weight(self, age_ms: float) -> float:
        """Return exponential freshness in (0, 1]."""
        if not isfinite(age_ms) or age_ms < 0:
            raise ValueError("age_ms must be finite and non-negative")
        return exp(-age_ms / self.freshness_decay_tau_ms)

    def normalized_age(self, age_ms: float) -> float:
        """Return clipped age using the configured maximum age scale."""
        if not isfinite(age_ms) or age_ms < 0:
            raise ValueError("age_ms must be finite and non-negative")
        return min(age_ms / self.max_message_age_ms, 1.0)

    def is_stale(self, age_ms: float) -> bool:
        """Return whether age is at or beyond the stale threshold."""
        if not isfinite(age_ms) or age_ms < 0:
            raise ValueError("age_ms must be finite and non-negative")
        return age_ms >= self.stale_message_threshold_ms


@dataclass(frozen=True)
class TrafficSnapshot:
    """Typed five-feature traffic snapshot exchanged between neighbors."""

    sender_id: str
    features: tuple[float, ...]
    generation_timestamp: float
    schema_version: str = FEATURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version not in (FEATURE_SCHEMA_VERSION, PHASE_FEATURE_SCHEMA):
            raise ValueError("unsupported traffic snapshot schema")
        if len(self.features) != LOCAL_FEATURE_COUNT:
            raise ValueError("traffic snapshot must contain exactly five features")
        if not all(isfinite(value) for value in self.features):
            raise ValueError("traffic snapshot features must be finite")
        if not isfinite(self.generation_timestamp) or self.generation_timestamp < 0:
            raise ValueError("generation_timestamp must be finite and non-negative")

    def to_payload(self) -> Mapping[str, object]:
        return {
            "schema_version": self.schema_version,
            "sender_id": self.sender_id,
            "features": list(self.features),
        }

    @classmethod
    def from_message(cls, message: CommunicationMessage) -> "TrafficSnapshot":
        payload = message.payload
        if payload.get("schema_version") not in (FEATURE_SCHEMA_VERSION, PHASE_FEATURE_SCHEMA):
            raise ValueError("unsupported traffic snapshot schema")
        if payload.get("sender_id") != message.sender_id:
            raise ValueError("traffic snapshot sender does not match message sender")
        features = payload.get("features")
        if not isinstance(features, (list, tuple)) or len(features) != LOCAL_FEATURE_COUNT:
            raise ValueError("traffic snapshot payload must contain five features")
        try:
            normalized = tuple(float(value) for value in features)
        except (TypeError, ValueError) as error:
            raise ValueError("traffic snapshot features must be numeric") from error
        return cls(message.sender_id, normalized, message.generation_timestamp, payload['schema_version'])


@dataclass(frozen=True)
class CachedNeighborState:
    """The latest valid message for one receiver-neighbor pair."""

    message_id: str
    sender_id: str
    features: tuple[float, ...]
    generation_timestamp: float
    delivery_timestamp: float | None


class NeighborInformationCache:
    """Bounded latest-message cache keyed by receiver and configured neighbor."""

    def __init__(self, topology: NeighborTopology, schema_version: str = FEATURE_SCHEMA_VERSION) -> None:
        self.topology = topology
        self.schema_version = schema_version
        self._states: dict[tuple[str, str], CachedNeighborState] = {}

    def update(self, receiver_id: str, message: CommunicationMessage) -> bool:
        """Cache a valid newer message and reject out-of-order information."""
        if not self.topology.contains(message.sender_id, receiver_id):
            raise ValueError("message sender is not a configured neighbor")
        snapshot = TrafficSnapshot.from_message(message)
        if snapshot.schema_version != self.schema_version:
            raise ValueError("traffic snapshot does not match cache schema")
        key = (receiver_id, message.sender_id)
        current = self._states.get(key)
        if current is not None and snapshot.generation_timestamp <= current.generation_timestamp:
            return False
        self._states[key] = CachedNeighborState(
            message.message_id,
            snapshot.sender_id,
            snapshot.features,
            snapshot.generation_timestamp,
            message.delivery_timestamp,
        )
        return True

    def get(self, receiver_id: str, neighbor_id: str) -> CachedNeighborState | None:
        if neighbor_id not in self.topology.for_agent(receiver_id):
            raise ValueError("neighbor_id is not configured for receiver")
        return self._states.get((receiver_id, neighbor_id))

    def clear(self) -> None:
        self._states.clear()

    def observation(
        self, receiver_id: str, current_timestamp: float, freshness: FreshnessConfig
    ) -> tuple[float, ...]:
        """Build ordered neighbor blocks for one receiver."""
        values: list[float] = []
        for neighbor_id in self.topology.for_agent(receiver_id):
            state = self.get(receiver_id, neighbor_id)
            if state is None:
                values.extend((0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0))
                continue
            age_ms = freshness.age_ms(state.generation_timestamp, current_timestamp)
            weight = freshness.weight(age_ms)
            values.extend(
                (
                    1.0,
                    freshness.normalized_age(age_ms),
                    weight,
                    float(freshness.is_stale(age_ms)),
                    *(feature * weight for feature in state.features),
                )
            )
        return tuple(values)
