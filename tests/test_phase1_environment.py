from pathlib import Path
import shutil
import importlib.util

import pytest

from traffic_control.config import load_network_config


ROOT = Path(__file__).parents[1]
NETWORK_CONFIG = ROOT / "configs" / "network.yaml"
SUMO_AVAILABLE = shutil.which("sumo") is not None
TRACI_AVAILABLE = importlib.util.find_spec("traci") is not None


def test_network_configuration_loads() -> None:
    config = load_network_config(NETWORK_CONFIG)

    assert config["config_file"] == "sumo/simulation/grid.sumocfg"
    assert config["grid_size"] == 2
    assert config["seed"] == 42


def test_sumo_files_exist() -> None:
    assert (ROOT / "sumo/network/grid.net.xml").is_file()
    assert (ROOT / "sumo/routes/grid.rou.xml").is_file()
    assert (ROOT / "sumo/simulation/grid.sumocfg").is_file()


@pytest.mark.sumo
@pytest.mark.skipif(not SUMO_AVAILABLE or not TRACI_AVAILABLE, reason="SUMO and TraCI are required")
def test_environment_can_start_step_control_and_close() -> None:
    from traffic_control.environment import SumoEnvironment, SumoEnvironmentConfig

    environment = SumoEnvironment(
        SumoEnvironmentConfig(config_file=ROOT / "sumo/simulation/grid.sumocfg")
    )
    try:
        environment.start()
        assert environment.traffic_light_ids == ("A0", "A1", "B0", "B1")
        assert environment.simulation_time == 0.0
        first_id = environment.traffic_light_ids[0]
        phase_count = environment.signals.phase_count(first_id)
        environment.signals.set_phase(first_id, min(1, phase_count - 1))
        environment.step()
        assert environment.simulation_time == 1.0
        state = environment.intersection_state(first_id)
        metrics = environment.metrics()
        assert state.traffic_light_id == first_id
        assert metrics.simulation_duration == 1.0
    finally:
        environment.close()

    environment.reset()
    environment.close()
