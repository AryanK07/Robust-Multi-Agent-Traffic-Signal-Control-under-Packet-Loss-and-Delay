"""Traffic-state extraction from a live TraCI connection."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IntersectionTrafficState:
    """Observable traffic state for one controlled intersection."""

    traffic_light_id: str
    vehicle_count: int
    waiting_time: float
    queue_length: int
    lane_occupancy: float
    phase: int


class TrafficStateExtractor:
    """Extract basic local state without introducing an RL observation model."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def extract(self, traffic_light_id: str) -> IntersectionTrafficState:
        """Return aggregated traffic state for lanes controlled by a signal."""
        lanes = tuple(dict.fromkeys(
            self._connection.trafficlight.getControlledLanes(traffic_light_id)
        ))
        vehicle_count = 0
        waiting_time = 0.0
        queue_length = 0
        occupancy_values: list[float] = []

        for lane_id in lanes:
            vehicle_count += self._connection.lane.getLastStepVehicleNumber(lane_id)
            waiting_time += self._connection.lane.getWaitingTime(lane_id)
            queue_length += self._connection.lane.getLastStepHaltingNumber(lane_id)
            occupancy_values.append(self._connection.lane.getLastStepOccupancy(lane_id))

        occupancy = sum(occupancy_values) / len(occupancy_values) if occupancy_values else 0.0
        phase = self._connection.trafficlight.getPhase(traffic_light_id)
        return IntersectionTrafficState(
            traffic_light_id=traffic_light_id,
            vehicle_count=vehicle_count,
            waiting_time=waiting_time,
            queue_length=queue_length,
            lane_occupancy=occupancy,
            phase=phase,
        )

    def all_intersections(self) -> dict[str, IntersectionTrafficState]:
        """Extract state for every traffic light in deterministic ID order."""
        return {
            traffic_light_id: self.extract(traffic_light_id)
            for traffic_light_id in self._connection.trafficlight.getIDList()
        }
