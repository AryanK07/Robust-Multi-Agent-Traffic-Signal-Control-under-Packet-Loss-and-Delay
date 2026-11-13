"""Verify saved follow-up records; write only a derived integrity report."""
import argparse
import json
from pathlib import Path
from traffic_control.experiments.followup import ROOT
from traffic_control.experiments.research_audit import audit_campaign


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    args = parser.parse_args()
    result = audit_campaign(args.directory.resolve(), ROOT)
    output = args.directory/'processed/integrity_audit.json'
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
