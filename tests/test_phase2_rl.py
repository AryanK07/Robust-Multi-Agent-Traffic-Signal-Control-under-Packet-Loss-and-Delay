from pathlib import Path
import importlib.util

import numpy as np
import pytest

from traffic_control.rl import LinearQAgent, SingleAgentEnvironment


ROOT = Path(__file__).parents[1]
SUMO_AVAILABLE = importlib.util.find_spec("traci") is not None


def test_agent_model_construction_and_shape_validation() -> None:
    agent = LinearQAgent(5, 2)
    observation = np.zeros(5, dtype=np.float32)
    assert agent.q_values(observation).shape == (2,)
    with pytest.raises(ValueError):
        agent.q_values(np.zeros(4))


def test_agent_save_load_preserves_predictions(tmp_path: Path) -> None:
    agent = LinearQAgent(5, 2, seed=7)
    observation = np.arange(5, dtype=np.float32)
    agent.update(observation, 1, 2.0, observation, True)
    path = tmp_path / "model.npz"
    agent.save(path)
    restored = LinearQAgent.load(path)
    np.testing.assert_allclose(agent.q_values(observation), restored.q_values(observation))


def test_environment_observation_and_action_validation() -> None:
    assert SingleAgentEnvironment.observation_size == 5
    assert SingleAgentEnvironment.action_size == 2


@pytest.mark.sumo
@pytest.mark.skipif(not SUMO_AVAILABLE, reason="TraCI is required")
def test_single_agent_environment_reset_step_and_termination() -> None:
    from traffic_control.rl import SingleAgentEnvironmentConfig

    environment = SingleAgentEnvironment(
        SingleAgentEnvironmentConfig(
            sumo_config_file=ROOT / "sumo/simulation/grid.sumocfg",
            max_steps=2,
        )
    )
    try:
        observation = environment.reset()
        assert observation.shape == (5,)
        with pytest.raises(ValueError):
            environment.step(2)
        assert environment.phase_count == 4
        next_observation, reward, terminated, info = environment.step(0)
        assert next_observation.shape == (5,)
        assert isinstance(reward, float)
        assert not terminated
        assert info["traffic_light_id"] == "A0"
        _, _, terminated, _ = environment.step(1)
        assert terminated
    finally:
        environment.close()
