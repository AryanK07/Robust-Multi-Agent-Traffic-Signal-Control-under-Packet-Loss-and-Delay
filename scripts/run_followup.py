"""Run a versioned exploratory follow-up; original Phase 11 is never writable."""

import argparse
import json
from pathlib import Path

from traffic_control.experiments.artifacts import CampaignStore
from traffic_control.experiments.followup import ROOT, run_followup, source_manifest
from traffic_control.experiments.followup_analysis import analyze_followup
from traffic_control.experiments.followup_design import load_design, evaluation_specs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('audit', 'pilot', 'run', 'analyze'), default='audit')
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/followup_v2.yaml')
    parser.add_argument('--output', type=Path, default=ROOT / 'results/followup_v2/development_001')
    parser.add_argument('--retry-failed', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to((ROOT / 'results/followup_v2').resolve()):
        raise ValueError('Follow-up outputs must be inside results/followup_v2')
    if args.mode == 'analyze':
        manifest = json.loads((output / 'manifest.json').read_text(encoding='utf-8'))
        design = manifest['design']
        store = CampaignStore(output, manifest)
    else:
        design = load_design(args.config, pilot=args.mode in ('audit', 'pilot'))
        if args.mode == 'audit':
            print(json.dumps(dict(purpose=design['purpose'], training_sets=len(design['variants'])*len(design['master_seeds']),
                                  training_episodes=design['training_episodes'], evaluations=len(evaluation_specs(design)),
                                  output=str(output), read_only=True), indent=2))
            return
        store = CampaignStore(output, source_manifest(design))
        run_followup(store, design, args.retry_failed)
    result = analyze_followup(store, design)
    print(json.dumps({k: v for k, v in result.items() if k not in ('summaries', 'paired_comparisons')}, indent=2))
    if result['successful_evaluations'] != result['expected_evaluations']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
