"""Small programmatic SUMO environment for Phase 1."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import uuid

import traci

from .metrics import MetricsCollector, TrafficMetrics
from .signal_controller import SignalController
from .traffic_state import IntersectionTrafficState, TrafficStateExtractor


@dataclass(frozen=True)
class SumoEnvironmentConfig:
    """Runtime settings for a deterministic SUMO scenario."""

    config_file: Path
    sumo_binary: str = "sumo"
    sumo_gui_binary: str = "sumo-gui"
    seed: int = 42
    step_length: float = 1.0


class SumoEnvironment:
    """Manage one headless or GUI SUMO simulation through TraCI."""

    def __init__(self, config: SumoEnvironmentConfig, use_gui: bool = False) -> None:
        self.config = config
        self.use_gui = use_gui
        self._connection: Any | None = None
        self._label = f"traffic-control-{uuid.uuid4().hex}"
        self._metrics = MetricsCollector()
        self._signals: SignalController | None = None
        self._state: TrafficStateExtractor | None = None

    def start(self) -> None:
        """Start SUMO and establish the TraCI connection."""
        if self._connection is not None:
            return
        binary = self.config.sumo_gui_binary if self.use_gui else self.config.sumo_binary
        command = [
            binary,
            "-c",
            str(self.config.config_file),
            "--seed",
            str(self.config.seed),
            "--step-length",
            str(self.config.step_length),
            "--quit-on-end",
        ]
        traci.start(command, label=self._label)
        self._connection = traci.getConnection(self._label)
        self._signals = SignalController(self._connection)
        self._state = TrafficStateExtractor(self._connection)
        self._metrics.reset()

    def reset(self) -> None:
        """Restart the configured scenario from simulation time zero."""
        self.close()
        self.start()

    def step(self) -> None:
        """Advance SUMO by one configured simulation step."""
        self._require_started().simulationStep()
        self._metrics.update(self._require_started(), self.config.step_length)

    def close(self) -> None:
        """Close the TraCI connection and SUMO process cleanly."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            self._signals = None
            self._state = None

    @property
    def simulation_time(self) -> float:
        """Return the current SUMO simulation time in seconds."""
        return self._require_started().simulation.getTime()

    @property
    def traffic_light_ids(self) -> tuple[str, ...]:
        """Return IDs of all controlled intersections."""
        return self.signals.traffic_light_ids()

    @property
    def signals(self) -> SignalController:
        """Return the programmatic signal-control interface."""
        if self._signals is None:
            raise RuntimeError("SUMO is not started")
        return self._signals

    @property
    def state(self) -> TrafficStateExtractor:
        """Return the traffic-state extraction interface."""
        if self._state is None:
            raise RuntimeError("SUMO is not started")
        return self._state

    def intersection_state(self, traffic_light_id: str) -> IntersectionTrafficState:
        """Return state for one controlled intersection."""
        return self.state.extract(traffic_light_id)

    def metrics(self) -> TrafficMetrics:
        """Return metrics accumulated by completed calls to :meth:`step`."""
        return self._metrics.snapshot()

    def _require_started(self) -> Any:
        if self._connection is None:
            raise RuntimeError("SUMO is not started")
        return self._connection
