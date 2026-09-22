"""Reusable basic traffic metrics collected from TraCI."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TrafficMetrics:
    """Summary of metrics observed during the current simulation run."""

    simulation_duration: float
    vehicle_count: int
    completed_trips: int
    total_waiting_time: float
    average_waiting_time: float
    mean_queue_length: float
    max_queue_length: int


class MetricsCollector:
    """Accumulate lightweight traffic metrics without modifying simulation state."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self._waiting_time_exposure = 0.0
        self._waiting_observations = 0
        self._queue_total = 0
        self._queue_observations = 0
        self._max_queue_length = 0
        self._completed_trips = 0
        self._vehicle_count = 0
        self._simulation_duration = 0.0

    def update(self, connection: Any, step_length: float) -> None:
        """Record one post-step snapshot from a TraCI connection."""
        vehicle_ids = connection.vehicle.getIDList()
        waiting_time = sum(
            connection.vehicle.getWaitingTime(vehicle_id) for vehicle_id in vehicle_ids
        )
        queue_length = sum(
            connection.lane.getLastStepHaltingNumber(lane_id)
            for lane_id in connection.lane.getIDList()
        )
        self._vehicle_count = len(vehicle_ids)
        self._waiting_time_exposure += waiting_time * step_length
        self._waiting_observations += len(vehicle_ids)
        self._queue_total += queue_length
        self._queue_observations += 1
        self._max_queue_length = max(self._max_queue_length, queue_length)
        self._completed_trips += connection.simulation.getArrivedNumber()
        self._simulation_duration = connection.simulation.getTime()

    def snapshot(self) -> TrafficMetrics:
        """Return the metrics accumulated so far."""
        average_waiting = (
            self._waiting_time_exposure / self._waiting_observations
            if self._waiting_observations
            else 0.0
        )
        mean_queue = (
            self._queue_total / self._queue_observations
            if self._queue_observations
            else 0.0
        )
        return TrafficMetrics(
            simulation_duration=self._simulation_duration,
            vehicle_count=self._vehicle_count,
            completed_trips=self._completed_trips,
            total_waiting_time=self._waiting_time_exposure,
            average_waiting_time=average_waiting,
            mean_queue_length=mean_queue,
            max_queue_length=self._max_queue_length,
        )
