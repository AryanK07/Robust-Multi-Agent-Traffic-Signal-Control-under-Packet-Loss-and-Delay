"""Programmatic traffic-signal control over TraCI."""

from typing import Any


class SignalController:
    """Inspect and select phases for SUMO traffic lights."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def traffic_light_ids(self) -> tuple[str, ...]:
        """Return controlled traffic-light IDs in deterministic order."""
        return tuple(sorted(self._connection.trafficlight.getIDList()))

    def current_phase(self, traffic_light_id: str) -> int:
        """Return the currently active phase index."""
        self._validate_id(traffic_light_id)
        return self._connection.trafficlight.getPhase(traffic_light_id)

    def phase_count(self, traffic_light_id: str) -> int:
        """Return the number of phases in the active signal program."""
        self._validate_id(traffic_light_id)
        programs = self._connection.trafficlight.getAllProgramLogics(traffic_light_id)
        if not programs:
            raise RuntimeError(f"Traffic light {traffic_light_id!r} has no signal program")
        return len(programs[0].phases)

    def set_phase(self, traffic_light_id: str, phase: int) -> None:
        """Select a valid phase for a controlled traffic light."""
        count = self.phase_count(traffic_light_id)
        if not isinstance(phase, int) or not 0 <= phase < count:
            raise ValueError(f"Phase must be an integer in [0, {count})")
        self._connection.trafficlight.setPhase(traffic_light_id, phase)

    def _validate_id(self, traffic_light_id: str) -> None:
        if traffic_light_id not in self.traffic_light_ids():
            raise KeyError(f"Unknown traffic light: {traffic_light_id}")
