"""RL-facing single-intersection environment built on the Phase 1 wrapper."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from traffic_control.environment import SumoEnvironment, SumoEnvironmentConfig


@dataclass(frozen=True)
class SingleAgentEnvironmentConfig:
    """Configuration for one learning-controlled intersection."""

    sumo_config_file: Path
    controlled_intersection: str = "A0"
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


class SingleAgentEnvironment:
    """Expose one SUMO signal as a small discrete-action RL environment."""

    observation_size = 5
    action_size = 2

    def __init__(self, config: SingleAgentEnvironmentConfig) -> None:
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
        self._previous_queue = 0.0
        self._previous_waiting = 0.0

    def reset(self) -> np.ndarray:
        """Start a fresh episode and return the normalized local observation."""
        self._simulator.reset()
        if self.config.controlled_intersection not in self._simulator.traffic_light_ids:
            self.close()
            raise ValueError(
                f"Unknown controlled intersection: {self.config.controlled_intersection}"
            )
        state = self._simulator.intersection_state(self.config.controlled_intersection)
        self._step_count = 0
        self._previous_queue = float(state.queue_length)
        self._previous_waiting = state.waiting_time
        return self._observation(state)

    def step(self, action: int) -> tuple[np.ndarray, float, bool, dict[str, Any]]:
        """Apply action, advance SUMO, and return observation, reward, and diagnostics."""
        if action not in (0, 1):
            raise ValueError("Action must be 0 (maintain) or 1 (select next phase)")

        traffic_light_id = self.config.controlled_intersection
        if action == 1:
            phase_count = self._simulator.signals.phase_count(traffic_light_id)
            current_phase = self._simulator.signals.current_phase(traffic_light_id)
            green_phases = (0, 2) if phase_count >= 4 else tuple(range(phase_count))
            next_phase = green_phases[
                (green_phases.index(current_phase) + 1) % len(green_phases)
            ] if current_phase in green_phases else green_phases[0]
            self._simulator.signals.set_phase(
                traffic_light_id, next_phase
            )

        self._simulator.step()
        state = self._simulator.intersection_state(traffic_light_id)
        queue_change = self._previous_queue - state.queue_length
        waiting_change = self._previous_waiting - state.waiting_time
        reward = (
            self.config.queue_reward_weight * queue_change
            + self.config.waiting_reward_weight * waiting_change
        )
        self._previous_queue = float(state.queue_length)
        self._previous_waiting = state.waiting_time
        self._step_count += 1
        terminated = self._step_count >= self.config.max_steps
        info = {
            "traffic_light_id": traffic_light_id,
            "queue_length": state.queue_length,
            "waiting_time": state.waiting_time,
            "vehicle_count": state.vehicle_count,
            "lane_occupancy": state.lane_occupancy,
            "phase": state.phase,
            "simulation_time": self._simulator.simulation_time,
            "metrics": self._simulator.metrics(),
        }
        return self._observation(state), float(reward), terminated, info

    def close(self) -> None:
        """Close the underlying SUMO simulation."""
        self._simulator.close()

    @property
    def phase_count(self) -> int:
        """Return the number of signal phases for the controlled intersection."""
        return self._simulator.signals.phase_count(self.config.controlled_intersection)

    def _observation(self, state: Any) -> np.ndarray:
        phase_count = max(self.phase_count, 1)
        phase_scale = max(phase_count - 1, 1)
        return np.asarray(
            [
                min(state.queue_length / self.config.queue_normalization, 1.0),
                min(state.waiting_time / self.config.waiting_time_normalization, 1.0),
                min(state.vehicle_count / self.config.vehicle_normalization, 1.0),
                min(state.lane_occupancy / 100.0, 1.0),
                state.phase / phase_scale,
            ],
            dtype=np.float32,
        )
