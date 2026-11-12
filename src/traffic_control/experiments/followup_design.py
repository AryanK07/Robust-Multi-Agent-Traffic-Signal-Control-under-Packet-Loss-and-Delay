"""Resolved follow-up design, seed streams and generated small-network demand."""

from copy import deepcopy
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import yaml

from traffic_control.rl.followup_env import FEATURE_MODES, STRATEGIES


def load_design(path: Path, pilot: bool = False) -> dict:
    design = yaml.safe_load(path.read_text(encoding="utf-8"))["followup"]
    design = deepcopy(design)
    overrides = design.pop("pilot")
    if pilot:
        selected = overrides.pop("variants")
        design.update(overrides)
        design["variants"] = {name: design["variants"][name] for name in selected}
    design["purpose"] = "development_pilot" if pilot else "exploratory_followup"
    if type(design['workers']) is not int or design['workers'] not in (1, 2):
        raise ValueError('workers must be 1 or 2 for the bounded local runner')
    seeds = design["master_seeds"]
    if not seeds or len(set(seeds)) != len(seeds) or any(type(seed) is not int or seed < 0 for seed in seeds):
        raise ValueError("master seeds must be distinct nonnegative integers")
    if type(design["training_episodes"]) is not int or design["training_episodes"] <= 0:
        raise ValueError("training_episodes must be positive")
    if not 0 <= design["epsilon"] <= 1:
        raise ValueError("epsilon must lie in [0,1]")
    if not 0 < design["learning_rate"] <= 1 or not 0 <= design["discount_factor"] <= 1:
        raise ValueError("invalid learner hyperparameters")
    training = {tuple(c) for c in design["training_conditions"]}
    evaluation = {tuple(c) for c in design["evaluation_conditions"]}
    held_out = {tuple(c) for c in design["held_out_conditions"]}
    if not training or not evaluation or training & held_out or not held_out <= evaluation:
        raise ValueError("held-out conditions must be evaluated and excluded from training")
    for loss, delay in training | evaluation:
        if not np.isfinite([loss, delay]).all() or not 0 <= loss <= 1 or delay < 0:
            raise ValueError("invalid impairment condition")
    if design["demand_seconds"] >= design["environment"]["horizon_seconds"]:
        raise ValueError("horizon must extend beyond demand generation")
    if design["vehicle_period"] <= 0 or design["demand_seconds"] <= 0:
        raise ValueError("demand parameters must be positive")
    for variant in design["variants"].values():
        if variant["features"] not in FEATURE_MODES or variant["training"] not in ("ideal", "robust"):
            raise ValueError("invalid policy variant")
    if set(design["strategies"]) - set(STRATEGIES):
        raise ValueError("unsupported communication strategy")
    return design


def episode_seeds(master: int, role: str, episode: int) -> dict[str, int]:
    """Same traffic/exploration mapping for every variant, separate train/test."""
    domain = {"training": 101, "evaluation": 202}[role]
    values = np.random.SeedSequence([master, domain, episode]).generate_state(4)
    return {key: int(value % 2_147_483_647) for key, value in
            zip(("learner", "traffic", "packet_loss", "schedule"), values)}


def training_schedule(design: dict, master: int, variant: str) -> list[list[float]]:
    if design["variants"][variant]["training"] == "ideal":
        return [[0.0, 0.0] for _ in range(design["training_episodes"])]
    rng = np.random.default_rng(episode_seeds(master, "training", 0)["schedule"])
    conditions = design["training_conditions"]
    result = []
    while len(result) < design["training_episodes"]:
        result.extend(conditions[index] for index in rng.permutation(len(conditions)))
    return result[:design["training_episodes"]]


def evaluation_specs(design: dict) -> list[dict]:
    specs = []
    held_out = {tuple(c) for c in design["held_out_conditions"]}
    for master in design["master_seeds"]:
        for name, variant in design["variants"].items():
            seen = ({(0.0, 0.0)} if variant["training"] == "ideal" else
                    {tuple(c) for c in design["training_conditions"]})
            conditions = [[0.0, 0.0]] if variant["features"] == "local" else design["evaluation_conditions"]
            strategies = design["strategies"] if name == "full_robust" else ["always"]
            for loss, delay in conditions:
                for strategy in strategies:
                    specs.append(dict(kind="evaluation", variant=name, master_seed=master,
                                      strategy=strategy, packet_loss=loss, delay_ms=delay,
                                      held_out=(loss, delay) not in seen,
                                      extreme_holdout=(loss, delay) in held_out,
                                      seeds=episode_seeds(master, "evaluation", 0)))
    return specs


def write_scenario(directory: Path, network: Path, seed: int, demand_seconds: float,
                   vehicle_period: float, horizon: float) -> tuple[Path, int]:
    """Generate seeded departure jitter on the original four routes.

    Speed deviation remains explicitly 0.1. Each evaluation uses identical
    generated demand for a paired seed across all policy/condition variants.
    """
    directory.mkdir(parents=True, exist_ok=True)
    route_path, config_path = directory / "demand.rou.xml", directory / "scenario.sumocfg"
    if route_path.exists() or config_path.exists():
        raise FileExistsError("scenario artifacts already exist")
    routes = ET.Element("routes")
    ET.SubElement(routes, "vType", id="passenger", vClass="passenger", accel="2.6",
                  decel="4.5", sigma="0", speedDev="0.1", length="5", minGap="2.5", maxSpeed="13.9")
    paths = ("A0A1 A1B1 B1B0", "B0B1 B1A1 A1A0", "A0B0 B0B1 B1A1", "B0A0 A0A1 A1B1")
    rng = np.random.default_rng(seed)
    vehicles = []
    for route, edges in enumerate(paths):
        ET.SubElement(routes, "route", id=f"route_{route}", edges=edges)
        for index, base in enumerate(np.arange(0, demand_seconds, vehicle_period)):
            depart = float(base + rng.uniform(0, min(vehicle_period / 2, demand_seconds - base)))
            vehicles.append((depart, route, index))
    for depart, route, index in sorted(vehicles):
        ET.SubElement(routes, "vehicle", id=f"r{route}_v{index}", type="passenger",
                      route=f"route_{route}", depart=f"{depart:.3f}")
    ET.ElementTree(routes).write(route_path, encoding="utf-8", xml_declaration=True)
    config = ET.Element("configuration")
    inputs = ET.SubElement(config, "input")
    ET.SubElement(inputs, "net-file", value=network.resolve().as_posix())
    ET.SubElement(inputs, "route-files", value=route_path.resolve().as_posix())
    time = ET.SubElement(config, "time")
    ET.SubElement(time, "end", value=str(horizon + 1))
    processing = ET.SubElement(config, "processing")
    ET.SubElement(processing, "time-to-teleport", value="-1")
    ET.SubElement(processing, "collision.action", value="warn")
    report = ET.SubElement(config, "report")
    ET.SubElement(report, "no-step-log", value="true")
    ET.ElementTree(config).write(config_path, encoding="utf-8", xml_declaration=True)
    return config_path, len(vehicles)
