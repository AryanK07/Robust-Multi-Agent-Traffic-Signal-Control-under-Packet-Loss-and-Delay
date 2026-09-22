from pathlib import Path
import importlib.util

import numpy as np
import pytest

from traffic_control.rl import AGENT_IDS, LinearQAgent, MultiAgentEnvironment


ROOT = Path(__file__).parents[1]
SUMO_AVAILABLE = importlib.util.find_spec("traci") is not None


def test_authoritative_agent_ids_and_independent_learners() -> None:
    assert AGENT_IDS == ("A0", "A1", "B0", "B1")
    learners = {agent_id: LinearQAgent(5, 2, seed=index) for index, agent_id in enumerate(AGENT_IDS)}
    assert tuple(learners) == AGENT_IDS
    learners["A0"].update(np.ones(5), 0, 1.0, np.ones(5), True)
    assert not np.array_equal(learners["A0"].weights, learners["A1"].weights)


def test_multi_agent_configuration_rejects_wrong_ids(tmp_path: Path) -> None:
    from traffic_control.rl import MultiAgentEnvironmentConfig

    with pytest.raises(ValueError):
        MultiAgentEnvironment(
            MultiAgentEnvironmentConfig(
                sumo_config_file=tmp_path / "missing.sumocfg",
                agent_ids=("A0",),
            )
        )


@pytest.mark.sumo
@pytest.mark.skipif(not SUMO_AVAILABLE, reason="TraCI is required")
def test_joint_step_returns_four_agents_and_one_transition() -> None:
    from traffic_control.rl import MultiAgentEnvironmentConfig

    environment = MultiAgentEnvironment(
        MultiAgentEnvironmentConfig(
            sumo_config_file=ROOT / "sumo/simulation/grid.sumocfg",
            max_steps=2,
        )
    )
    try:
        observations = environment.reset()
        assert tuple(observations) == AGENT_IDS
        assert all(value.shape == (5,) and value.dtype == np.float32 for value in observations.values())
        with pytest.raises(ValueError):
            environment.step({"A0": 0, "A1": 0, "B0": 0})
        with pytest.raises(ValueError):
            environment.step({agent_id: 0 for agent_id in (*AGENT_IDS, "extra")})
        next_observations, rewards, terminated, info = environment.step(
            {agent_id: 0 for agent_id in AGENT_IDS}
        )
        assert tuple(next_observations) == AGENT_IDS
        assert tuple(rewards) == AGENT_IDS
        assert all(isinstance(value, float) for value in rewards.values())
        assert info["simulation_time"] == 1.0
        assert info["agent_ids"] == AGENT_IDS
        assert not terminated
        _, _, terminated, _ = environment.step({agent_id: 1 for agent_id in AGENT_IDS})
        assert terminated
    finally:
        environment.close()
