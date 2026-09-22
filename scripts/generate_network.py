"""Generate the deterministic Phase 1 SUMO network."""

from pathlib import Path
import argparse
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

import yaml


ROOT = Path(__file__).parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "network.yaml",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "sumo" / "network" / "grid.net.xml",
    )
    args = parser.parse_args()

    with args.config.open(encoding="utf-8") as stream:
        network = yaml.safe_load(stream)["network"]
    netgenerate = shutil.which("netgenerate")
    if netgenerate is None:
        raise RuntimeError("netgenerate is required to generate the SUMO network")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        netgenerate,
        "--grid",
        "--grid.number",
        str(network["grid_size"]),
        "--grid.length",
        str(network["grid_length"]),
        "--default-junction-type",
        str(network["junction_type"]),
        "--output-file",
        str(args.output),
    ]
    subprocess.run(command, check=True)
    generated = args.output.read_text(encoding="utf-8")
    generated = re.sub(r"<!-- generated.*?-->\s*", "", generated, count=1, flags=re.DOTALL)
    args.output.write_text(generated, encoding="utf-8")
    tree = ET.parse(args.output)
    root = tree.getroot()
    phases = network.get("phases")
    if not isinstance(phases, list) or not phases:
        raise ValueError("network.phases must contain at least one phase")
    for tls_logic in root.findall("tlLogic"):
        for phase in list(tls_logic):
            tls_logic.remove(phase)
        for phase in phases:
            ET.SubElement(
                tls_logic,
                "phase",
                duration=str(phase["duration"]),
                state=str(phase["state"]),
            )
    tree.write(args.output, encoding="UTF-8", xml_declaration=True)
    print(f"Generated {args.output}")


if __name__ == "__main__":
    main()
