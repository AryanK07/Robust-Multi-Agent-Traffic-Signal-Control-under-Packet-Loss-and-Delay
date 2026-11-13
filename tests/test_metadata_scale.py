from pathlib import Path
import shutil
import numpy as np
import pytest
from traffic_control.rl import AGENT_IDS, LinearQAgent
from traffic_control.rl.followup_env import FollowupEnvironment, FollowupEnvironmentConfig
from traffic_control.communication.action_margin import action_margin_certificate


@pytest.mark.sumo
@pytest.mark.skipif(shutil.which('sumo') is None, reason='SUMO required')
def test_metadata_scaling_preserves_payload_and_certificate_bounds(tmp_path):
    results = {}
    for scale in (1., .1, .01):
        config = FollowupEnvironmentConfig(Path('sumo/simulation/grid.sumocfg').resolve(),
                                           tmp_path/f'{scale}.xml',metadata_scale=scale,horizon_seconds=2)
        policies = {a: LinearQAgent(23,2) for a in AGENT_IDS}
        env = FollowupEnvironment(config,policies)
        try:
            obs = env.reset()['A0']
            lo, hi = env._bounds(obs)
            assert np.all(obs >= lo) and np.all(obs <= hi)
            assert action_margin_certificate(obs,policies['A0'].weights,policies['A0'].bias,lo,hi).invariant
            results[scale] = obs
        finally:
            env.close()
    for scale in (.1,.01):
        np.testing.assert_array_equal(results[scale][:5],results[1.][:5])
        for start in (5,14):
            np.testing.assert_allclose(results[scale][start:start+4],results[1.][start:start+4]*scale)
            np.testing.assert_array_equal(results[scale][start+4:start+9],results[1.][start+4:start+9])
