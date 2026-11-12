"""Descriptive follow-up analysis with matched seed-level comparisons."""

from collections import defaultdict
import csv
import json
from math import sqrt
from statistics import mean, stdev

from scipy.stats import t

from .followup_design import evaluation_specs


def paired_comparison(rows, left, right, metric, left_strategy='always', right_strategy='always'):
    groups = {}
    for variant, strategy in ((left, left_strategy), (right, right_strategy)):
        groups[(variant, strategy)] = {
            (r['specification']['master_seed'], r['specification']['packet_loss'], r['specification']['delay_ms']): r['payload'][metric]
            for r in rows if r['specification']['variant'] == variant
            and r['specification']['strategy'] == strategy and r['payload'].get(metric) is not None}
    a, b = groups[(left, left_strategy)], groups[(right, right_strategy)]
    by_seed = defaultdict(list)
    for key in a.keys() & b.keys():
        by_seed[key[0]].append(a[key] - b[key])
    diffs = {str(seed): mean(values) for seed, values in sorted(by_seed.items())}
    values = list(diffs.values())
    n = len(values)
    interval = None
    if n > 1:
        radius = float(t.ppf(.975, n-1)) * stdev(values) / sqrt(n)
        interval = [mean(values)-radius, mean(values)+radius]
    return dict(left=left, right=right, left_strategy=left_strategy, right_strategy=right_strategy,
                metric=metric, master_seed_count=n, paired_cells=len(a.keys() & b.keys()),
                seed_differences=diffs, mean_difference=mean(values) if values else None,
                descriptive_t_interval_95=interval,
                note='Exploratory; no multiplicity-adjusted significance or equivalence claim.')


def analyze_followup(store, design):
    rows = [r for r in store.successful() if r['specification']['kind'] == 'evaluation']
    always = {(r['specification']['variant'], r['specification']['master_seed'],
               r['specification']['packet_loss'], r['specification']['delay_ms']): r
              for r in rows if r['specification']['strategy'] == 'always'}
    groups = defaultdict(list)
    for row in rows:
        spec, payload = row['specification'], dict(row['payload'])
        payload['send_attempts'] = payload['communication']['send_attempts']
        reference = always.get((spec['variant'], spec['master_seed'], spec['packet_loss'], spec['delay_ms']))
        sends = reference['payload']['communication']['send_attempts'] if reference else 0
        payload['communication_reduction'] = 1 - payload['send_attempts']/sends if sends else None
        row = {**row, 'payload': payload}
        groups[(spec['variant'], spec['strategy'], spec['packet_loss'], spec['delay_ms'])].append(row)
    summaries = []
    metrics = ('average_waiting_time', 'average_completed_travel_time', 'completion_fraction',
               'completed_trips', 'unfinished_trips', 'uninserted_vehicles', 'mean_queue_length',
               'send_attempts', 'payload_bytes', 'communication_reduction', 'episode_reward')
    for (variant, strategy, loss, delay), records in sorted(groups.items()):
        summary = dict(variant=variant, strategy=strategy, packet_loss=loss, delay_ms=delay,
                       seed_count=len(records), censored_runs=sum(r['payload']['horizon_censored'] for r in records))
        for metric in metrics:
            values = [r['payload'][metric] for r in records if r['payload'].get(metric) is not None]
            summary[metric + '_mean'] = mean(values) if values else None
            summary[metric + '_std'] = stdev(values) if len(values) > 1 else None
        summaries.append(summary)
    augmented = [r for group in groups.values() for r in group]
    comparisons = [paired_comparison(augmented, 'full_robust', 'full_ideal', 'average_waiting_time'),
                   paired_comparison(augmented, 'full_robust', 'plain_robust', 'average_waiting_time')]
    for metric in ('average_waiting_time', 'send_attempts', 'completion_fraction'):
        comparisons.append(paired_comparison(augmented, 'full_robust', 'full_robust', metric,
                                             'action_sensitive', 'periodic_pull'))
    raw = [json.loads(p.read_text()) for p in (store.directory / 'raw').glob('*/*.json')]
    result = dict(purpose=design['purpose'], campaign_identity=store.identity,
                  expected_evaluations=len(evaluation_specs(design)), successful_evaluations=len(rows),
                  failed_attempts=sum(r['status'] == 'failed' for r in raw),
                  summaries=summaries, paired_comparisons=comparisons,
                  warning='Development/exploratory results; inspect censoring and paired uncertainty. No final superiority claim.')
    output = store.directory / 'processed'
    output.mkdir(exist_ok=True)
    (output / 'summary.json').write_text(json.dumps(result, indent=2, allow_nan=False), encoding='utf-8')
    if summaries:
        with (output / 'summary.csv').open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(summaries[0]))
            writer.writeheader(); writer.writerows(summaries)
    return result
