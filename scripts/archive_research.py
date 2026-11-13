"""Build or verify a research archive; never replace an existing archive."""

import argparse
import json
from pathlib import Path

from traffic_control.experiments.followup import ROOT
from traffic_control.experiments.research_archive import build_archive, verify_archive


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    result = verify_archive(args.archive) if args.verify else build_archive(ROOT, args.archive)
    print(json.dumps(result, indent=2))
