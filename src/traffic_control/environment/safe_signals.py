"""Minimum-green and yellow transitions for the existing two-green program."""

from math import isfinite


class SafeSignalTransitions:
    """Explicitly hold green; action 1 requests a yellow-mediated switch.

    This is a simulator transition constraint, not a road-safety certification.
    The follow-up network uses 0/2 greens and 1/3 yellow phases.
    """

    def __init__(self, connection, agent_ids, minimum_green: float, yellow: float):
        if not all(isfinite(v) and v > 0 for v in (minimum_green, yellow)):
            raise ValueError("minimum green and yellow must be positive")
        self.connection = connection
        self.minimum_green = minimum_green
        self.yellow = yellow
        self.state = {agent: (0, 0.0, None) for agent in agent_ids}
        self.switches = 0
        for agent in agent_ids:
            self._set(agent, 0)

    def _set(self, agent, phase):
        self.connection.trafficlight.setPhase(agent, phase)
        self.connection.trafficlight.setPhaseDuration(agent, 1_000_000.0)

    def advance(self, time: float) -> None:
        for agent, (green, since, deadline) in tuple(self.state.items()):
            if deadline is not None and time + 1e-9 >= deadline:
                target = 2 if green == 0 else 0
                self._set(agent, target)
                self.state[agent] = (target, time, None)

    def request(self, agent: str, action: int, time: float) -> bool:
        if action not in (0, 1):
            raise ValueError("action must be 0 or 1")
        green, since, deadline = self.state[agent]
        if action == 0 or deadline is not None or time - since + 1e-9 < self.minimum_green:
            return False
        self._set(agent, green + 1)
        self.state[agent] = (green, since, time + self.yellow)
        self.switches += 1
        return True
