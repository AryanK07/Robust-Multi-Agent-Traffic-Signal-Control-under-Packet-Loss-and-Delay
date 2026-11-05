"""Communication-aware multi-agent environment for Phase 8."""

from dataclasses import dataclass
from typing import Any

import numpy as np

from traffic_control.communication import CommunicationMessage, CommunicationScheduler
from traffic_control.communication.freshness import (
    FreshnessConfig,
    LOCAL_FEATURE_COUNT,
    NEIGHBOR_FEATURE_COUNT,
    NeighborInformationCache,
    TrafficSnapshot,
)

from .multi_agent_env import AGENT_IDS, MultiAgentEnvironment, MultiAgentEnvironmentConfig


@dataclass(frozen=True)
class CommunicationAwareEnvironmentConfig(MultiAgentEnvironmentConfig):
    """Phase 8 settings while preserving the Phase 3 environment defaults."""

    freshness: FreshnessConfig = FreshnessConfig()
    communication_strategy: str = "always"
    periodic_interval_ms: float = 1000.0
    adaptive_change_threshold: float = 0.10
    adaptive_max_silence_ms: float = 1000.0


class CommunicationAwareMultiAgentEnvironment(MultiAgentEnvironment):
    """Independent-learning environment with freshness-aware neighbor inputs."""

    observation_size = LOCAL_FEATURE_COUNT + 2 * NEIGHBOR_FEATURE_COUNT
    feature_schema_version = "local_plus_neighbor_freshness_v1"

    def __init__(self, config: CommunicationAwareEnvironmentConfig) -> None:
        super().__init__(config)
        self.config = config
        self._cache = NeighborInformationCache(self.communication.topology)
        self._scheduler = CommunicationScheduler(
            self.agent_ids,
            strategy=config.communication_strategy,
            periodic_interval_ms=config.periodic_interval_ms,
            change_threshold=config.adaptive_change_threshold,
            max_silence_ms=config.adaptive_max_silence_ms,
        )

    def reset(self) -> dict[str, np.ndarray]:
        observations = super().reset()
        self._cache.clear()
        self._scheduler.reset()
        return self._communicate_and_observe(observations)

    def step(
        self, actions: dict[str, int]
    ) -> tuple[dict[str, np.ndarray], dict[str, float], bool, dict[str, Any]]:
        observations, rewards, terminated, info = super().step(actions)
        aware_observations = self._communicate_and_observe(observations)
        info["communication_aware"] = True
        info["message_cache"] = self.cache_snapshot()
        info["communication_scheduler"] = self._scheduler.telemetry()
        return aware_observations, rewards, terminated, info

    def communication_observation(self, agent_id: str) -> np.ndarray:
        """Return one deterministic observation from the current cache."""
        if agent_id not in self.agent_ids:
            raise ValueError(f"Unknown agent: {agent_id}")
        local = self._local_observation(agent_id)
        neighbor = self._cache.observation(
            agent_id, self.simulation_time, self.config.freshness
        )
        return np.asarray((*local, *neighbor), dtype=np.float32)

    def cache_snapshot(self) -> dict[str, dict[str, dict[str, object]]]:
        """Return bounded cache metadata for telemetry and smoke tests."""
        result: dict[str, dict[str, dict[str, object]]] = {}
        for receiver_id in self.agent_ids:
            result[receiver_id] = {}
            for neighbor_id in self.communication.topology.for_agent(receiver_id):
                state = self._cache.get(receiver_id, neighbor_id)
                if state is not None:
                    result[receiver_id][neighbor_id] = {
                        "message_id": state.message_id,
                        "generation_timestamp": state.generation_timestamp,
                        "delivery_timestamp": state.delivery_timestamp,
                    }
        return result

    def _communicate_and_observe(
        self, local_observations: dict[str, np.ndarray]
    ) -> dict[str, np.ndarray]:
        current_time = self.simulation_time
        self._receive_available(current_time)
        snapshots = {
            agent_id: TrafficSnapshot(
                agent_id,
                tuple(float(value) for value in local_observations[agent_id]),
                current_time,
            )
            for agent_id in self.agent_ids
        }
        for sender_id in self.agent_ids:
            decision = self._scheduler.should_transmit(
                sender_id, local_observations[sender_id], current_time
            )
            if decision.transmit:
                for receiver_id in self.communication.topology.for_agent(sender_id):
                    self.communication.send(
                        sender_id,
                        receiver_id,
                        snapshots[sender_id].to_payload(),
                        current_time,
                    )
        self._receive_available(current_time)
        return {
            agent_id: self.communication_observation(agent_id)
            for agent_id in self.agent_ids
        }

    def _receive_available(self, current_time: float) -> None:
        for receiver_id in self.agent_ids:
            messages = self.communication.receive(receiver_id, current_time)
            for message in messages:
                self._cache.update(receiver_id, message)

    def _local_observation(self, agent_id: str) -> np.ndarray:
        state = self._simulator.intersection_state(agent_id)
        return self._observation(agent_id, state)
