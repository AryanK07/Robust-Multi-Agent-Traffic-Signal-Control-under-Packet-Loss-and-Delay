"""Synchronized four-intersection independent-learning environment."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from traffic_control.environment import SumoEnvironment, SumoEnvironmentConfig


AGENT_IDS = ("A0", "A1", "B0", "B1")


@dataclass(frozen=True)
class MultiAgentEnvironmentConfig:
    """Runtime settings shared by all independent intersection agents."""

    sumo_config_file: Path
    agent_ids: tuple[str, ...] = AGENT_IDS
    sumo_binary: str = "sumo"
    sumo_gui_binary: str = "sumo-gui"
    seed: int = 42
    step_length: float = 1.0
    max_steps: int = 20
    queue_normalization: float = 10.0
    waiting_time_normalization: float = 100.0
    vehicle_normalization: float = 20.0
    queue_reward_weight: float = 1.0
    waiting_reward_weight: float = 0.1


class MultiAgentEnvironment:
    """Control all configured intersections with one synchronized SUMO step."""

    observation_size = 5
    action_size = 2

    def __init__(self, config: MultiAgentEnvironmentConfig) -> None:
        if tuple(config.agent_ids) != AGENT_IDS:
            raise ValueError(f"Phase 3 requires agent IDs {AGENT_IDS}")
        self.config = config
        self._simulator = SumoEnvironment(
            SumoEnvironmentConfig(
                config_file=config.sumo_config_file,
                sumo_binary=config.sumo_binary,
                sumo_gui_binary=config.sumo_gui_binary,
                seed=config.seed,
                step_length=config.step_length,
            )
        )
        self._step_count = 0
        self._previous: dict[str, tuple[float, float]] = {}

    @property
    def agent_ids(self) -> tuple[str, ...]:
        """Return the authoritative deterministic agent IDs."""
        return self.config.agent_ids

    def reset(self) -> dict[str, np.ndarray]:
        """Reset SUMO and return one local observation per agent."""
        self._simulator.reset()
        actual = set(self._simulator.traffic_light_ids)
        expected = set(self.agent_ids)
        if actual != expected:
            self.close()
            raise RuntimeError(
                f"SUMO traffic lights {sorted(actual)} do not match expected {self.agent_ids}"
            )
        self._step_count = 0
        self._previous = {}
        observations: dict[str, np.ndarray] = {}
        for agent_id in self.agent_ids:
            state = self._simulator.intersection_state(agent_id)
            self._previous[agent_id] = (float(state.queue_length), state.waiting_time)
            observations[agent_id] = self._observation(agent_id, state)
        return observations

    def step(
        self, actions: dict[str, int]
    ) -> tuple[dict[str, np.ndarray], dict[str, float], bool, dict[str, Any]]:
        """Apply a joint action and advance SUMO exactly once."""
        self._validate_actions(actions)
        for agent_id in self.agent_ids:
            if actions[agent_id] == 1:
                phase_count = self._simulator.signals.phase_count(agent_id)
                current_phase = self._simulator.signals.current_phase(agent_id)
                green_phases = (0, 2) if phase_count >= 4 else tuple(range(phase_count))
                if current_phase in green_phases:
                    next_phase = green_phases[
                        (green_phases.index(current_phase) + 1) % len(green_phases)
                    ]
                else:
                    next_phase = green_phases[0]
                self._simulator.signals.set_phase(agent_id, next_phase)

        self._simulator.step()
        self._step_count += 1
        observations: dict[str, np.ndarray] = {}
        rewards: dict[str, float] = {}
        per_agent: dict[str, dict[str, Any]] = {}
        for agent_id in self.agent_ids:
            state = self._simulator.intersection_state(agent_id)
            previous_queue, previous_waiting = self._previous[agent_id]
            rewards[agent_id] = float(
                self.config.queue_reward_weight * (previous_queue - state.queue_length)
                + self.config.waiting_reward_weight
                * (previous_waiting - state.waiting_time)
            )
            self._previous[agent_id] = (float(state.queue_length), state.waiting_time)
            observations[agent_id] = self._observation(agent_id, state)
            per_agent[agent_id] = {
                "queue_length": state.queue_length,
                "waiting_time": state.waiting_time,
                "vehicle_count": state.vehicle_count,
                "lane_occupancy": state.lane_occupancy,
                "phase": state.phase,
            }
        terminated = self._step_count >= self.config.max_steps
        info = {
            "agent_ids": self.agent_ids,
            "simulation_time": self._simulator.simulation_time,
            "metrics": self._simulator.metrics(),
            "per_agent": per_agent,
        }
        return observations, rewards, terminated, info

    def close(self) -> None:
        """Close SUMO cleanly."""
        self._simulator.close()

    @property
    def simulation_time(self) -> float:
        """Return the shared simulation time."""
        return self._simulator.simulation_time

    def _validate_actions(self, actions: dict[str, int]) -> None:
        if set(actions) != set(self.agent_ids):
            missing = sorted(set(self.agent_ids) - set(actions))
            extra = sorted(set(actions) - set(self.agent_ids))
            raise ValueError(f"Actions must contain exactly {self.agent_ids}; missing={missing}, extra={extra}")
        for agent_id in self.agent_ids:
            if actions[agent_id] not in (0, 1):
                raise ValueError(f"Action for {agent_id} must be 0 or 1")

    def _observation(self, agent_id: str, state: Any) -> np.ndarray:
        phase_count = max(self._simulator.signals.phase_count(agent_id), 1)
        return np.asarray(
            [
                min(state.queue_length / self.config.queue_normalization, 1.0),
                min(state.waiting_time / self.config.waiting_time_normalization, 1.0),
                min(state.vehicle_count / self.config.vehicle_normalization, 1.0),
                min(state.lane_occupancy / 100.0, 1.0),
                state.phase / max(phase_count - 1, 1),
            ],
            dtype=np.float32,
        )
