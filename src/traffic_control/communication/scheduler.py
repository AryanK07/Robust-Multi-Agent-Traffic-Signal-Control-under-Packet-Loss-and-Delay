"""Deterministic event-triggered communication scheduling."""

from dataclasses import dataclass
from math import isfinite
from typing import Mapping

import numpy as np


STRATEGIES = ("always", "periodic", "adaptive")


@dataclass(frozen=True)
class TransmissionDecision:
    """Decision and diagnostics for one agent at one simulation timestamp."""

    transmit: bool
    trigger_reason: str
    change_score: float
    time_since_last_transmission: float


@dataclass(frozen=True)
class SchedulerTelemetry:
    """Bounded scheduling counters independent of channel delivery telemetry."""

    scheduling_opportunities: int
    scheduled_transmissions: int
    suppressed_transmissions: int
    trigger_counts: Mapping[str, int]

    @property
    def communication_reduction(self) -> float:
        """Return the fraction of opportunities suppressed."""
        if self.scheduling_opportunities == 0:
            return 0.0
        return self.suppressed_transmissions / self.scheduling_opportunities


class CommunicationScheduler:
    """Schedule snapshots without knowing whether sends are delivered."""

    def __init__(
        self,
        agent_ids: tuple[str, ...],
        *,
        strategy: str = "always",
        periodic_interval_ms: float = 1000.0,
        change_threshold: float = 0.10,
        max_silence_ms: float = 1000.0,
    ) -> None:
        if not agent_ids or len(set(agent_ids)) != len(agent_ids):
            raise ValueError("agent_ids must be unique and non-empty")
        if strategy not in STRATEGIES:
            raise ValueError(f"strategy must be one of {STRATEGIES}")
        if not isfinite(periodic_interval_ms) or periodic_interval_ms <= 0:
            raise ValueError("periodic_interval_ms must be positive and finite")
        if not isfinite(change_threshold) or not 0 <= change_threshold <= 1:
            raise ValueError("change_threshold must be between 0 and 1")
        if not isfinite(max_silence_ms) or max_silence_ms <= 0:
            raise ValueError("max_silence_ms must be positive and finite")
        self.agent_ids = tuple(agent_ids)
        self.strategy = strategy
        self.periodic_interval_seconds = periodic_interval_ms / 1000.0
        self.change_threshold = float(change_threshold)
        self.max_silence_seconds = max_silence_ms / 1000.0
        self._last_observation: dict[str, np.ndarray] = {}
        self._last_transmission_time: dict[str, float] = {}
        self._opportunities = 0
        self._scheduled = 0
        self._suppressed = 0
        self._trigger_counts = {"first": 0, "periodic": 0, "change": 0, "heartbeat": 0, "suppressed": 0}

    def should_transmit(
        self, agent_id: str, observation: np.ndarray, simulation_time: float
    ) -> TransmissionDecision:
        """Return a deterministic decision for one normalized snapshot."""
        if agent_id not in self.agent_ids:
            raise ValueError(f"Unknown agent: {agent_id}")
        current = np.asarray(observation, dtype=np.float64)
        if current.shape != (5,) or not np.all(np.isfinite(current)):
            raise ValueError("observation must be a finite five-feature vector")
        if not isfinite(simulation_time) or simulation_time < 0:
            raise ValueError("simulation_time must be finite and non-negative")
        previous_time = self._last_transmission_time.get(agent_id)
        if previous_time is not None and simulation_time < previous_time:
            raise ValueError("simulation_time must not move backwards")
        self._opportunities += 1
        if previous_time is None:
            return self._record(agent_id, current, simulation_time, "first", 0.0, True)
        elapsed = simulation_time - previous_time
        score = float(np.mean(np.abs(current - self._last_observation[agent_id])))
        reason = "suppressed"
        transmit = False
        if self.strategy == "always":
            transmit, reason = True, "always"
        elif self.strategy == "periodic" and elapsed >= self.periodic_interval_seconds:
            transmit, reason = True, "periodic"
        elif self.strategy == "adaptive":
            if score >= self.change_threshold:
                transmit, reason = True, "change"
            elif elapsed >= self.max_silence_seconds:
                transmit, reason = True, "heartbeat"
        return self._record(agent_id, current, simulation_time, reason, score, transmit, elapsed)

    def telemetry(self) -> SchedulerTelemetry:
        return SchedulerTelemetry(
            self._opportunities,
            self._scheduled,
            self._suppressed,
            dict(self._trigger_counts),
        )

    def reset(self) -> None:
        """Clear episode scheduling state and counters."""
        self._last_observation.clear()
        self._last_transmission_time.clear()
        self._opportunities = 0
        self._scheduled = 0
        self._suppressed = 0
        self._trigger_counts = {"first": 0, "periodic": 0, "change": 0, "heartbeat": 0, "suppressed": 0}

    def _record(
        self,
        agent_id: str,
        observation: np.ndarray,
        simulation_time: float,
        reason: str,
        score: float,
        transmit: bool,
        elapsed: float = 0.0,
    ) -> TransmissionDecision:
        if transmit:
            self._last_observation[agent_id] = observation.copy()
            self._last_transmission_time[agent_id] = simulation_time
            self._scheduled += 1
            self._trigger_counts[reason] = self._trigger_counts.get(reason, 0) + 1
        else:
            self._suppressed += 1
            self._trigger_counts["suppressed"] += 1
        return TransmissionDecision(transmit, reason, score, elapsed)
