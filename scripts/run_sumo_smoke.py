"""Run a short Phase 1 SUMO/TraCI smoke test."""

from pathlib import Path

from traffic_control.config import load_network_config
from traffic_control.environment import SumoEnvironment, SumoEnvironmentConfig


ROOT = Path(__file__).parents[1]


def main() -> None:
    network = load_network_config(ROOT / "configs" / "network.yaml")
    environment = SumoEnvironment(
        SumoEnvironmentConfig(
            config_file=ROOT / network["config_file"],
            sumo_binary=network["sumo_binary"],
            sumo_gui_binary=network["sumo_gui_binary"],
            seed=network["seed"],
            step_length=network["step_length"],
        )
    )
    try:
        environment.start()
        initial_ids = environment.traffic_light_ids
        if not initial_ids:
            raise RuntimeError("Smoke test found no controlled intersections")
        first_id = initial_ids[0]
        environment.signals.set_phase(first_id, 0)
        for _ in range(12):
            environment.step()
        print(f"traffic_lights={initial_ids}")
        print(f"simulation_time={environment.simulation_time}")
        print(f"metrics={environment.metrics()}")
    finally:
        environment.close()


if __name__ == "__main__":
    main()
