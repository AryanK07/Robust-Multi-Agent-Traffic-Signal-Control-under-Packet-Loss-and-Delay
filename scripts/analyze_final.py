"""Audit and regenerate Phase 11 statistics/figures from a frozen campaign."""

import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
from statistics import mean, stdev

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from traffic_control.experiments.artifacts import CampaignStore
from traffic_control.experiments.confirmatory_analysis import planned_comparisons
from traffic_control.experiments.followup import ROOT
from traffic_control.experiments.followup_analysis import analyze_followup
from traffic_control.experiments.research_audit import audit_campaign


def analyze(directory):
    integrity = audit_campaign(directory, ROOT)
    manifest = json.loads((directory/'manifest.json').read_text())
    design = manifest['design']
    store = CampaignStore(directory, manifest)
    summary = analyze_followup(store, design)
    rows = [r for r in store.successful() if r['specification']['kind']=='evaluation']
    lookup = {(s['variant'],s['strategy'],s['master_seed'],s['packet_loss'],s['delay_ms']):r['payload']
              for r in rows for s in [r['specification']]}
    degradation = []
    for row in rows:
        s,p = row['specification'],row['payload']
        base = lookup[(s['variant'],s['strategy'],s['master_seed'],0,0)]
        for metric,direction in [('average_waiting_time',1),('completion_fraction',-1)]:
            reference = base[metric]
            degradation.append(dict(variant=s['variant'],strategy=s['strategy'],master_seed=s['master_seed'],
                                    packet_loss=s['packet_loss'],delay_ms=s['delay_ms'],metric=metric,
                                    absolute=p[metric],ideal=reference,
                                    degradation_percent=100*direction*(p[metric]-reference)/reference if reference else None))
    grouped = defaultdict(lambda:defaultdict(list))
    for row in rows:
        s,p = row['specification'],row['payload']
        fields = {k:p[k] for k in ('average_waiting_time','completion_fraction','average_completed_travel_time',
                                   'mean_queue_length','total_stops','neighbor_action_changes','agent_decisions',
                                   'mean_message_age_ms','max_message_age_ms','mean_delivered_delay_ms','payload_bytes')}
        fields['send_attempts'] = p['communication']['send_attempts']
        for metric,value in fields.items():
            if value is not None:
                grouped[(s['variant'],s['strategy'],metric)][s['master_seed']].append(value)
    estimates = []
    for (variant,strategy,metric), by_seed in sorted(grouped.items()):
        values = [mean(cells) for _,cells in sorted(by_seed.items())]
        estimates.append(dict(variant=variant,strategy=strategy,metric=metric,n=len(values),
                              seed_means=values,mean=mean(values),sd=stdev(values) if len(values)>1 else None))
    result = dict(integrity=integrity,method_estimates=estimates,
                  planned_test_family=planned_comparisons(rows,design),
                  inference_limitations='Independent units are master seeds. Five-seed exact two-sided tests cannot attain p<0.05. Holm adjusts all 13 planned tests. Descriptive intervals do not prove equivalence.',
                  censoring_warning='Interpret waiting with completion; unfinished vehicles contribute only waiting until the horizon.')
    diagnostics = []
    traffic_fields = ('average_waiting_time','completion_fraction','average_completed_travel_time',
                      'mean_queue_length','total_stops','completed_trips','uninserted_vehicles')
    for variant,strategy in sorted({(r['specification']['variant'],r['specification']['strategy']) for r in rows}):
        selected = [r for r in rows if (r['specification']['variant'],r['specification']['strategy'])==(variant,strategy)]
        triggers = Counter()
        for row in selected:
            triggers.update(row['payload']['trigger_counts'])
        diagnostics.append(dict(variant=variant,strategy=strategy,episodes=len(selected),
                                censored=sum(r['payload']['horizon_censored'] for r in selected),
                                trigger_totals=dict(triggers),
                                neighbor_action_changes=sum(r['payload']['neighbor_action_changes'] for r in selected),
                                agent_decisions=sum(r['payload']['agent_decisions'] for r in selected),
                                seed_results=[dict(master_seed=seed,
                                    waiting_mean=mean(r['payload']['average_waiting_time'] for r in selected if r['specification']['master_seed']==seed),
                                    completion_mean=mean(r['payload']['completion_fraction'] for r in selected if r['specification']['master_seed']==seed))
                                    for seed in design['master_seeds']]))
    result['descriptive_diagnostics'] = diagnostics
    result['full_robust_vs_local_traffic_fields'] = traffic_fields
    result['full_robust_vs_local_differing_records'] = sum(
        any(r['payload'][metric] != lookup[('local','always',r['specification']['master_seed'],0,0)][metric] for metric in traffic_fields)
        for r in rows if r['specification']['variant']=='full_robust')
    processed = directory/'processed'
    (processed/'final_statistics.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    (processed/'integrity_audit.json').write_text(json.dumps(integrity,indent=2)+'\n')
    write_tables(processed/'tables.md', result, design)
    with (processed/'degradation.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(degradation[0])); writer.writeheader(); writer.writerows(degradation)
    figures(directory, summary, estimates, store, design)
    return result


def write_tables(path, result, design):
    """Generate reviewable tables directly from the audited seed-level estimates."""
    values = {(r['variant'],r['strategy'],r['metric']):r for r in result['method_estimates']}
    lines = ['# Reserved-seed Phase 11 measured tables', '',
             f"Frozen source: `{result['integrity']['source_commit']}`.", '',
             'Values are means ± sample SD across five master-seed means. Each',
             'communicating seed mean averages all 25 conditions; local is evaluated',
             'once per seed. Waiting includes unfinished trips only until the horizon.', '',
             '| Variant | Strategy | Waiting (s/vehicle) | Completed fraction | Packet attempts |',
             '|---|---|---:|---:|---:|']
    def cell(variant, strategy, metric):
        r = values[(variant,strategy,metric)]
        return f"{r['mean']:.4f} ± {r['sd']:.4f}"
    for variant in design['variants']:
        for strategy in design['strategies'] if variant == 'full_robust' else ['always']:
            lines.append(f'| {variant} | {strategy} | '+ ' | '.join(
                cell(variant,strategy,m) for m in ('average_waiting_time','completion_fraction','send_attempts'))+' |')
    lines += ['', '## Prespecified paired comparisons', '',
              'One difference per master seed. Intervals are descriptive, not simultaneous',
              'or equivalence bounds. Sign-flip inference assumes exchangeability/symmetry.', '',
              '| Comparison | Mean difference | Descriptive 95% interval | Exact p | Holm p |',
              '|---|---:|---:|---:|---:|']
    for r in result['planned_test_family']:
        lo,hi = r['descriptive_t_interval_95']
        lines.append(f"| {r['name']} | {r['mean_difference']:.4f} | [{lo:.4f}, {hi:.4f}] | {r['exact_sign_flip_p']:.4f} | {r['holm_adjusted_p']:.4f} |")
    lines += ['', result['inference_limitations'], '', '## Verified coverage', '',
              '```json',json.dumps(result['integrity'],indent=2),'```','']
    path.write_text('\n'.join(lines), encoding='utf-8')


def figures(directory, summary, estimates, store, design):
    plots=directory/'plots'; plots.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':10,'figure.dpi':130})
    losses=sorted({c[0] for c in design['evaluation_conditions']})
    delays=sorted({c[1] for c in design['evaluation_conditions']})
    variants=['plain_ideal','plain_robust','full_ideal','full_robust']
    cells={(r['variant'],r['strategy'],r['packet_loss'],r['delay_ms']):r for r in summary['summaries']}
    for metric,label,filename in [('average_waiting_time_mean','Mean waiting to horizon (s/vehicle)','waiting_heatmaps'),
                                  ('completion_fraction_mean','Fraction of demand completed','completion_heatmaps')]:
        matrices=[np.asarray([[cells[(v,'always',p,d)][metric] for d in delays] for p in losses]) for v in variants]
        fig,axes=plt.subplots(2,2,figsize=(11,8),layout='constrained')
        vmax=1 if metric.startswith('completion') else max(float(m.max()) for m in matrices)
        for ax,v,matrix in zip(axes.flat,variants,matrices):
            chart=ax.imshow(matrix,vmin=0,vmax=vmax,cmap='viridis')
            ax.set(title=v,xlabel='Delay (ms)',ylabel='Packet-loss probability',
                   xticks=range(len(delays)),xticklabels=delays,yticks=range(len(losses)),yticklabels=losses)
            for i in range(len(losses)):
                for j in range(len(delays)):
                    ax.text(j,i,f'{matrix[i,j]:.2f}',ha='center',va='center',
                            color='white' if matrix[i,j]<vmax*.5 else 'black',fontsize=9)
        fig.colorbar(chart,ax=axes,label=label,shrink=.8)
        fig.suptitle(f'{label}; {len(design["master_seeds"])} master seeds')
        fig.savefig(plots/f'{filename}.png'); plt.close(fig)
    values={(r['variant'],r['strategy'],r['metric']):r for r in estimates}
    fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained')
    for strategy in design['strategies']:
        x=values[('full_robust',strategy,'send_attempts')]
        for ax,metric,title in zip(axes,('average_waiting_time','completion_fraction'),('Waiting (s/vehicle)','Completed fraction')):
            y=values[('full_robust',strategy,metric)]
            ax.errorbar(x['mean'],y['mean'],xerr=x['sd'],yerr=y['sd'],fmt='o',capsize=3,label=strategy)
            ax.set(xlabel='Packet attempts per 120-second episode',ylabel=title)
            ax.grid(alpha=.2)
    axes[1].legend(fontsize=8); axes[1].set_ylim(0,1.05)
    if all(values[('full_robust','action_sensitive',metric)]['mean'] ==
           values[('full_robust','periodic_pull',metric)]['mean']
           for metric in ('send_attempts','average_waiting_time','completion_fraction')):
        axes[0].text(.42,.94,'Periodic pull and action-sensitive\npoints coincide',
                     transform=axes[0].transAxes,va='top',fontsize=9)
    fig.suptitle('Communication trade-off; bars show between-seed SD, not confidence bounds')
    fig.savefig(plots/'communication_tradeoff.png'); plt.close(fig)
    variants=['full_robust','no_age_robust','no_availability_robust','no_decay_robust','no_stale_robust']
    fig,ax=plt.subplots(figsize=(9,4),layout='constrained')
    points=[values[(v,'always','average_waiting_time')] for v in variants]
    ax.barh(variants,[r['mean'] for r in points],xerr=[r['sd'] for r in points],capsize=3)
    ax.set(xlabel='Mean waiting to horizon (s/vehicle); between-seed SD',title='Component ablations, all 25 conditions')
    fig.savefig(plots/'ablations.png'); plt.close(fig)
    curves=defaultdict(list)
    for row in store.successful():
        if row['specification']['kind']=='training':
            folder=(directory/row['payload']['checkpoint_directory']).parent
            curves[row['specification']['variant']].append([json.loads(p.read_text()) for p in sorted(folder.glob('episode_*.json'))])
    fig,axes=plt.subplots(1,2,figsize=(13,5),layout='constrained')
    for variant,runs in sorted(curves.items()):
        for ax,metric in zip(axes,('episode_reward','mean_absolute_td_error')):
            data=np.asarray([[r[metric] for r in run] for run in runs]); x=np.arange(1,data.shape[1]+1)
            ax.plot(x,data.mean(axis=0),label=variant); ax.set(xlabel='Training episode',ylabel=metric)
    axes[1].legend(fontsize=7); fig.suptitle('Exploratory training curves; not proof of greedy-policy convergence')
    fig.savefig(plots/'training_curves.png'); plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('directory',type=Path)
    args=parser.parse_args(); result=analyze(args.directory.resolve())
    print(json.dumps(result['integrity'],indent=2))
