"""Ideal inter-agent communication primitives for Phase 4."""

from .channel import CommunicationChannel, CommunicationEvent, CommunicationTelemetry
from .message import CommunicationMessage
from .topology import AGENT_IDS, DEFAULT_NEIGHBORS, NeighborTopology

__all__ = [
    "AGENT_IDS",
    "DEFAULT_NEIGHBORS",
    "CommunicationChannel",
    "CommunicationEvent",
    "CommunicationMessage",
    "CommunicationTelemetry",
    "NeighborTopology",
]
