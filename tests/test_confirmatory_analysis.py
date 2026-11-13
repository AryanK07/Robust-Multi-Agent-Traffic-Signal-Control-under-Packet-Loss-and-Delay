import pytest
from traffic_control.experiments.confirmatory_analysis import seed_effect, holm_adjust
from traffic_control.experiments.confirmatory_analysis import planned_comparisons


def test_exact_small_sample_inference_and_zero_effect():
    assert seed_effect([1]*5)['exact_sign_flip_p'] == .0625
    assert seed_effect([0]*5)['exact_sign_flip_p'] == 1
    assert seed_effect([1,-1,2,-2,0])['mean_difference'] == 0
    assert seed_effect([1,2,3,4,5])['n'] == 5


def test_holm_restores_order_and_is_monotone():
    assert holm_adjust([.04,.001,.03]) == pytest.approx([.06,.003,.06])
    with pytest.raises(ValueError):
        holm_adjust([float('nan')])


def test_planned_family_aggregates_conditions_before_seed_inference():
    conditions = [[p,d] for p in (0,.05,.1,.2,.3) for d in (0,100,250,500,1000)]
    variants = ['plain_ideal','plain_robust','full_ideal','full_robust',
                'no_age_robust','no_availability_robust','no_decay_robust','no_stale_robust']
    rows = []
    for seed in range(5):
        for variant in variants:
            for strategy in ('always','periodic_pull','action_sensitive'):
                for loss, delay in conditions:
                    rows.append({'specification': dict(variant=variant,strategy=strategy,master_seed=seed,
                                                       packet_loss=loss,delay_ms=delay),
                                 'payload': dict(average_waiting_time=seed+100*loss+delay/1000,
                                                 completion_fraction=1.,communication={'send_attempts':100})})
    results = planned_comparisons(rows, {'master_seeds':list(range(5)),
                                         'evaluation_conditions':conditions,'held_out_conditions':[[.3,1000]]})
    assert len(results) == 13
    assert all(r['n'] == 5 for r in results)
    assert results[0]['mean_difference'] == 30
    assert results[3]['mean_difference'] == 0
