from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from traffic_control.experiments.followup_design import (
    load_design, training_schedule, evaluation_specs, episode_seeds, write_scenario)
from traffic_control.experiments.followup_analysis import paired_comparison


def test_pilot_is_explicitly_bounded_and_test_streams_are_separate():
    design = load_design(Path('configs/followup_v2.yaml'), pilot=True)
    assert design['purpose'] == 'development_pilot'
    assert len(design['master_seeds']) == 2
    assert len(design['variants']) == 5
    assert len(evaluation_specs(design)) == 50
    for master in design['master_seeds']:
        training = {v for episode in range(5) for v in episode_seeds(master, 'training', episode).values()}
        evaluation = set(episode_seeds(master, 'evaluation', 0).values())
        assert not training & evaluation
        assert training_schedule(design, master, 'full_ideal') == [[0., 0.]] * 4
        assert all(tuple(c) not in {tuple(h) for h in design['held_out_conditions']}
                   for c in training_schedule(design, master, 'full_robust'))
    specs = evaluation_specs(design)
    assert len({tuple(sorted(s['seeds'].items())) for s in specs if s['master_seed'] == 20261}) == 1


def test_balanced_full_schedule_and_all_feature_ablations_present():
    design = load_design(Path('configs/followup_v2.yaml'))
    schedule = training_schedule(design, 20261, 'full_robust')
    assert len(schedule) == 25
    assert {tuple(c) for c in schedule[:9]} == {tuple(c) for c in design['training_conditions']}
    assert len(design['variants']) == 9
    assert any(s['extreme_holdout'] for s in evaluation_specs(design))


def test_generated_demand_is_paired_and_does_not_overwrite(tmp_path):
    kwargs = dict(network=Path('sumo/network/grid.net.xml'), seed=15,
                  demand_seconds=30, vehicle_period=6, horizon=120)
    first, count = write_scenario(tmp_path / 'a', **kwargs)
    second, again = write_scenario(tmp_path / 'b', **kwargs)
    assert count == again == 20
    assert (first.parent / 'demand.rou.xml').read_bytes() == (second.parent / 'demand.rou.xml').read_bytes()
    departures = [float(v.attrib['depart']) for v in ET.parse(first.parent / 'demand.rou.xml').getroot().findall('vehicle')]
    assert departures == sorted(departures)
    with pytest.raises(FileExistsError):
        write_scenario(tmp_path / 'a', **kwargs)


def test_paired_analysis_uses_seeds_not_condition_count():
    rows = []
    for seed, difference in ((1, 1.), (2, 3.)):
        for loss in (0, .1, .2):
            for variant, waiting in (('left', 10 + difference), ('right', 10)):
                rows.append({'specification': dict(variant=variant, strategy='always', master_seed=seed,
                                                   packet_loss=loss, delay_ms=0),
                             'payload': {'average_waiting_time': waiting}})
    result = paired_comparison(rows, 'left', 'right', 'average_waiting_time')
    assert result['master_seed_count'] == 2
    assert result['paired_cells'] == 6
    assert result['mean_difference'] == 2


def test_training_validation_is_balanced_and_separate():
    design = load_design(Path('configs/training_validation_v1.yaml'))
    assert design['validation_budgets'] == [9, 27, 81]
    assert not set(design['master_seeds']) & {20261, 20262, 20263, 20264, 20265}
    for seed in design['master_seeds']:
        streams = [set(episode_seeds(seed, role, 0).values())
                   for role in ('training', 'validation', 'evaluation')]
        assert all(not streams[i] & streams[j] for i in range(3) for j in range(i))
        schedule = training_schedule(design, seed, 'full_robust')
        for budget in design['validation_budgets']:
            from collections import Counter
            assert set(Counter(map(tuple, schedule[:budget])).values()) == {budget // 9}
