"""Seed-clustered effects and a declared family of exact paired tests."""

from itertools import product
from math import sqrt
from statistics import mean, stdev

import numpy as np
from scipy.stats import t


def seed_effect(values):
    """One already-aggregated paired difference per independent master seed.

    Sign-flip inference assumes exchangeability/symmetry of paired differences.
    With five seeds the smallest two-sided exact p is 0.0625. Intervals are
    descriptive t intervals, not simultaneous or noninferiority guarantees.
    """
    values = list(map(float, values))
    if not values or not np.isfinite(values).all():
        raise ValueError('finite seed differences are required')
    n, average = len(values), mean(values)
    radius = float(t.ppf(.975, n-1)) * stdev(values)/sqrt(n) if n > 1 else None
    observed = abs(average)
    exceed = sum(abs(mean(s*v for s, v in zip(signs, values))) >= observed-1e-12
                 for signs in product((-1, 1), repeat=n))
    return dict(n=n, seed_differences=values, mean_difference=average,
                standard_deviation=stdev(values) if n > 1 else None,
                descriptive_t_interval_95=[average-radius, average+radius] if radius is not None else None,
                exact_sign_flip_p=exceed/(2**n))


def holm_adjust(p_values):
    """Holm familywise correction, returned in original hypothesis order."""
    p_values = list(p_values)
    if any(not np.isfinite(p) or not 0 <= p <= 1 for p in p_values):
        raise ValueError('p-values must lie in [0,1]')
    order = sorted(range(len(p_values)), key=p_values.__getitem__)
    result, previous = [0.] * len(order), 0.
    for rank, index in enumerate(order):
        previous = max(previous, min(1., (len(order)-rank)*p_values[index]))
        result[index] = previous
    return result


def planned_comparisons(rows, design):
    records = {(s['variant'], s['strategy'], s['master_seed'], s['packet_loss'], s['delay_ms']): r['payload']
               for r in rows for s in [r['specification']]}
    seeds = design['master_seeds']
    conditions = design['evaluation_conditions']
    held_out = design['held_out_conditions']

    def value(variant, strategy, seed, condition, metric):
        row = records[(variant, strategy, seed, *condition)]
        return row['communication']['send_attempts'] if metric == 'send_attempts' else row[metric]

    results = []
    def add(name, terms, cells, metric='average_waiting_time'):
        diffs = [mean(sum(coef*value(variant, strategy, seed, fixed if fixed is not None else cell, metric)
                          for coef, variant, strategy, fixed in terms) for cell in cells) for seed in seeds]
        results.append(dict(name=name, metric=metric, conditions=cells, **seed_effect(diffs)))

    for name, cell in [('loss_only', (0.3, 0)), ('delay_only', (0, 1000)), ('combined', (0.3, 1000))]:
        add(name, [(1, 'plain_ideal', 'always', cell), (-1, 'plain_ideal', 'always', (0, 0))], [cell])
    add('loss_delay_interaction', [(1, 'plain_ideal', 'always', (.3, 1000)),
                                  (-1, 'plain_ideal', 'always', (.3, 0)),
                                  (-1, 'plain_ideal', 'always', (0, 1000)),
                                  (1, 'plain_ideal', 'always', (0, 0))], [[.3, 1000]])
    add('freshness_same_robust_training', [(1, 'full_robust', 'always', None),
                                         (-1, 'plain_robust', 'always', None)], conditions)
    add('robust_training_held_out', [(1, 'full_robust', 'always', None),
                                    (-1, 'full_ideal', 'always', None)], held_out)
    for metric in ('average_waiting_time', 'send_attempts', 'completion_fraction'):
        add('action_gate_vs_periodic_pull_' + metric, [(1, 'full_robust', 'action_sensitive', None),
                                                     (-1, 'full_robust', 'periodic_pull', None)], conditions, metric)
    for variant in ('no_age_robust', 'no_availability_robust', 'no_decay_robust', 'no_stale_robust'):
        add(variant + '_minus_full', [(1, variant, 'always', None),
                                     (-1, 'full_robust', 'always', None)], conditions)
    for row, adjusted in zip(results, holm_adjust(r['exact_sign_flip_p'] for r in results)):
        row['holm_adjusted_p'] = adjusted
        row['reject_at_familywise_05'] = adjusted <= .05
    return results
