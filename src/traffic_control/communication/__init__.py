"""Ideal inter-agent communication primitives for Phase 4."""

from .channel import CommunicationChannel, CommunicationEvent, CommunicationTelemetry
from .message import CommunicationMessage
from .freshness import (
    FEATURE_SCHEMA_VERSION,
    FreshnessConfig,
    NeighborInformationCache,
    TrafficSnapshot,
)
from .scheduler import CommunicationScheduler, SchedulerTelemetry, TransmissionDecision
from .topology import AGENT_IDS, DEFAULT_NEIGHBORS, NeighborTopology

__all__ = [
    "AGENT_IDS",
    "DEFAULT_NEIGHBORS",
    "CommunicationChannel",
    "CommunicationEvent",
    "CommunicationMessage",
    "CommunicationTelemetry",
    "FEATURE_SCHEMA_VERSION",
    "FreshnessConfig",
    "NeighborInformationCache",
    "TrafficSnapshot",
    "CommunicationScheduler",
    "SchedulerTelemetry",
    "TransmissionDecision",
    "NeighborTopology",
]
