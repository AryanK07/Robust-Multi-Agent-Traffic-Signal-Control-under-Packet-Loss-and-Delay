from copy import deepcopy
from importlib.util import find_spec
from pathlib import Path
import shutil

import numpy as np
import pytest

from traffic_control.experiments.followup import _episode
from traffic_control.experiments.followup_design import load_design, episode_seeds
from traffic_control.rl import AGENT_IDS, LinearQAgent


@pytest.mark.sumo
@pytest.mark.skipif(find_spec('libsumo') is None or shutil.which('sumo') is None,
                    reason='libsumo and SUMO required')
def test_libsumo_preserves_complete_training_trajectory(tmp_path):
    design = load_design(Path('configs/followup_v2.yaml'), pilot=True)
    outputs, parameters = [], []
    for backend in ('traci', 'libsumo'):
        current = deepcopy(design)
        current['environment']['backend'] = backend
        learners = {a: LinearQAgent(23, 2, .01, .95, index + 17)
                    for index, a in enumerate(AGENT_IDS)}
        result = _episode(current, 'full_robust', learners,
                          episode_seeds(20261, 'training', 1), .1, 250,
                          'always', tmp_path / backend, True)
        for key in ('timestamp_utc', 'tripinfo_sha256'):
            result.pop(key)
        outputs.append(result)
        parameters.append([(p.weights.copy(), p.bias.copy()) for p in learners.values()])
    assert outputs[0] == outputs[1]
    for before, after in zip(parameters[0], parameters[1]):
        np.testing.assert_array_equal(before[0], after[0])
        np.testing.assert_array_equal(before[1], after[1])
