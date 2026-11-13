from importlib.util import find_spec
from pathlib import Path
import pytest
from traffic_control.experiments.followup import _episode
from traffic_control.experiments.followup_design import load_design, episode_seeds
from traffic_control.rl import AGENT_IDS, LinearQAgent


@pytest.mark.sumo
@pytest.mark.skipif(find_spec('libsumo') is None, reason='libsumo required')
def test_clear_termination_includes_future_departures_and_terminal_update(tmp_path, monkeypatch):
    design = load_design(Path('configs/training_validation_v3.yaml'))
    design['training_stop_when_clear'] = True
    learners = {a: LinearQAgent(23, 2, .01, .95, 17+i) for i, a in enumerate(AGENT_IDS)}
    endings = []
    update = learners['A0'].update
    def observe(*args):
        endings.append(args[-1])
        return update(*args)
    monkeypatch.setattr(learners['A0'], 'update', observe)
    result = _episode(design, 'full_robust', learners, episode_seeds(31001, 'training', 1),
                      .1, 250, 'always', tmp_path, True)
    assert result['completed_trips'] == result['expected_vehicles'] == 20
    assert design['demand_seconds'] < result['simulation_time'] < 120
    assert endings[-1] and not any(endings[:-1])
