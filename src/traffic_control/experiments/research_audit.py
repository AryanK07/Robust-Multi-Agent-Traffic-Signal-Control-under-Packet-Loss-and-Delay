"""Read-only campaign verification before research interpretation/archiving."""

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np

from .artifacts import CampaignStore, canonical_hash
from .followup_design import evaluation_specs, training_schedule, episode_seeds
from traffic_control.environment.trip_metrics import read_trip_metrics


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_campaign(directory: Path, repository: Path):
    manifest = json.loads((directory/'manifest.json').read_text())
    design = manifest['design']
    store = CampaignStore(directory, manifest)
    rows = store.successful()
    training = [r for r in rows if r['specification']['kind'] == 'training']
    evaluation = [r for r in rows if r['specification']['kind'] == 'evaluation']
    expected_training = {(v,s) for v in design['variants'] for s in design['master_seeds']}
    observed = {(r['specification']['variant'],r['specification']['master_seed']):r for r in training}
    if set(observed) != expected_training:
        raise ValueError('training design coverage is incomplete')
    expected = {canonical_hash({**s, 'checkpoint_sha256':observed[(s['variant'],s['master_seed'])]['payload']['checkpoint_sha256']})
                for s in evaluation_specs(design)}
    if expected != {canonical_hash(r['specification']) for r in evaluation}:
        raise ValueError('evaluation design coverage is incomplete or unexpected')

    counts = defaultdict(int)
    demands = defaultdict(set)
    seed_streams = defaultdict(set)
    def check_episode(record, folder, role, master, index):
        if record['seeds'] != episode_seeds(master, role, index):
            raise ValueError('episode seed mapping differs from declared stream')
        metrics = read_trip_metrics(folder/'trips.xml', record['expected_vehicles'])
        if any(record[key] != value for key,value in metrics.items()):
            raise ValueError(f'trip metrics mismatch: {folder}')
        for file,key in [('trips.xml','tripinfo_sha256'),('demand.rou.xml','demand_sha256')]:
            if digest(folder/file) != record[key]:
                raise ValueError(f'artifact hash mismatch: {folder/file}')
        channel = record['communication']
        if channel['send_attempts'] != channel['dropped_messages']+channel['successful_transmissions']:
            raise ValueError('send/drop accounting mismatch')
        if channel['successful_transmissions'] != channel['delivered_messages']+channel['pending_messages']:
            raise ValueError('delivery/pending accounting mismatch')
        attempts = sum(record['trigger_counts'].get(key,0) for key in
                       ('snapshot_attempts','request_attempts','response_attempts'))
        if attempts != channel['send_attempts']:
            raise ValueError('scheduler/channel accounting mismatch')
        demands[(role, master, index)].add(record['demand_sha256'])
        seed_streams[role].add(record['seeds']['traffic'])
        counts[role+'_episodes'] += 1
        counts[role+'_censored'] += record['horizon_censored']

    def check_weights(folder, hashes):
        for agent, expected_hash in hashes.items():
            path = folder/f'{agent}.npz'
            if digest(path) != expected_hash:
                raise ValueError(f'checkpoint changed: {path}')
            with np.load(path, allow_pickle=False) as data:
                if not np.isfinite(data['weights']).all() or not np.isfinite(data['bias']).all():
                    raise ValueError('nonfinite policy parameters')
            counts['checkpoint_files'] += 1

    for row in training:
        spec, payload = row['specification'], row['payload']
        checkpoints = directory/payload['checkpoint_directory']
        check_weights(checkpoints,payload['checkpoint_sha256'])
        if payload['condition_schedule'] != training_schedule(design,spec['master_seed'],spec['variant']):
            raise ValueError('training condition schedule mismatch')
        episodes = sorted(checkpoints.parent.glob('episode_*.json'))
        if len(episodes) != design['training_episodes']:
            raise ValueError('training episode count mismatch')
        for index,path in enumerate(episodes,1):
            episode = json.loads(path.read_text())
            if [episode['packet_loss'],episode['delay_ms']] != payload['condition_schedule'][index-1]:
                raise ValueError('episode impairment differs from schedule')
            check_episode(episode,path.with_suffix(''), 'training',spec['master_seed'],index)
        validations = sorted(checkpoints.parent.glob('validation_*/metrics.json'))
        if len(validations) != len(design.get('validation_budgets', [])):
            raise ValueError('validation checkpoint coverage mismatch')
        for path in validations:
            record = json.loads(path.read_text())
            if len(record['results']) != len(design['validation_conditions']):
                raise ValueError('validation cell coverage mismatch')
            check_weights(path.parent/'checkpoints',record['checkpoint_sha256'])
            for index,result in enumerate(record['results']):
                check_episode(result,path.parent/f'cell_{index:02d}','validation',spec['master_seed'],0)
    for row in evaluation:
        folder = directory/'artifacts'/row['run_id']/f"{row['attempt']:04d}"
        check_episode(row['payload'],folder,'evaluation',row['specification']['master_seed'],0)
    if any(len(values)!=1 for values in demands.values()):
        raise ValueError('paired demand mismatch')
    roles = list(seed_streams)
    if any(seed_streams[a] & seed_streams[b] for i,a in enumerate(roles) for b in roles[:i]):
        raise ValueError('training/validation/evaluation traffic seed overlap')
    for path, expected_hash in manifest['source_sha256'].items():
        blob = subprocess.check_output(['git','show',f"{manifest['git_commit']}:{path}"],cwd=repository)
        # Git normalizes text; Windows checkout bytes may use CRLF.
        candidates = (blob, blob.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n'))
        if expected_hash not in {hashlib.sha256(value).hexdigest() for value in candidates}:
            raise ValueError(f'source hash not attributable to commit: {path}')
    attempts = [json.loads(p.read_text()) for p in (directory/'raw').glob('*/*.json')]
    return dict(campaign_identity=store.identity,source_commit=manifest['git_commit'],
                expected_evaluations=len(expected),successful_evaluations=len(evaluation),
                training_sets=len(training),failed_attempts=sum(r['status']=='failed' for r in attempts),
                source_files_verified=len(manifest['source_sha256']),paired_demand_verified=True,
                seed_domains_disjoint=True,**counts)
