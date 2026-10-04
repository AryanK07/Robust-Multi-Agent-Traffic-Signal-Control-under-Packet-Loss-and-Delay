"""Configurable neighbor relationships for the Phase 4 grid."""

from dataclasses import dataclass
from typing import Mapping


AGENT_IDS = ("A0", "A1", "B0", "B1")
DEFAULT_NEIGHBORS: dict[str, tuple[str, ...]] = {
    "A0": ("A1", "B0"),
    "A1": ("A0", "B1"),
    "B0": ("A0", "B1"),
    "B1": ("A1", "B0"),
}


@dataclass(frozen=True)
class NeighborTopology:
    """Validate and expose directed communication neighbors."""

    agent_ids: tuple[str, ...] = AGENT_IDS
    neighbors: Mapping[str, tuple[str, ...]] | None = None

    def __post_init__(self) -> None:
        agent_ids = tuple(self.agent_ids)
        if not agent_ids or len(set(agent_ids)) != len(agent_ids):
            raise ValueError("agent_ids must contain unique non-empty IDs")
        if any(not agent_id for agent_id in agent_ids):
            raise ValueError("agent_ids must contain non-empty IDs")
        configured = self.neighbors or DEFAULT_NEIGHBORS
        if set(configured) != set(agent_ids):
            raise ValueError("neighbors must define every configured agent exactly once")
        normalized: dict[str, tuple[str, ...]] = {}
        for agent_id in agent_ids:
            values = tuple(configured[agent_id])
            if len(set(values)) != len(values):
                raise ValueError(f"neighbors for {agent_id} must be unique")
            if any(neighbor not in agent_ids or neighbor == agent_id for neighbor in values):
                raise ValueError(f"neighbors for {agent_id} contain an invalid agent")
            normalized[agent_id] = values
        object.__setattr__(self, "agent_ids", agent_ids)
        object.__setattr__(self, "neighbors", normalized)

    def contains(self, sender_id: str, receiver_id: str) -> bool:
        """Return whether sender and receiver have an explicit link."""
        return receiver_id in self.neighbors[sender_id]

    def for_agent(self, agent_id: str) -> tuple[str, ...]:
        """Return the configured outgoing neighbors for one agent."""
        if agent_id not in self.neighbors:
            raise ValueError(f"Unknown agent: {agent_id}")
        return self.neighbors[agent_id]
