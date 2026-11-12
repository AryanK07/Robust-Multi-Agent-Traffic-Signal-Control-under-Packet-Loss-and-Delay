import json
from pathlib import Path

import pytest

from traffic_control.config import load_phase11_config
from traffic_control.experiments import (
    Phase11Config,
    aggregate_phase11_results,
    derive_evaluation_seeds,
    generate_phase11_runs,
    load_valid_raw_results,
    paired_differences,
    write_phase11_raw_result,
)
from traffic_control.experiments.phase7 import load_phase7_config


ROOT = Path(__file__).parents[1]


def test_phase11_design_has_755_runs_and_shared_seed_mapping() -> None:
    phase11 = Phase11Config(
        "test", (42, 123, 456, 789, 1011), 25, 20, Path("results/phase11"), Path("checkpoints"),
        1000, 0.1, 1000, 500, 2000, 1000,
    )
    phase7 = load_phase7_config(ROOT / "configs/phase7.yaml")
    runs = generate_phase11_runs(phase7, phase11)
    assert len(runs) == 755
    comparable = [
        run for run in runs
        if run["policy_variant"] == "ideal_trained_communication_aware_iql"
        and run["communication_strategy"] == "always"
        and run["packet_loss_probability"] == 0.1
        and run["delay_ms"] == 250
    ]
    assert len({run["traffic_demand_seed"] for run in comparable}) == 5
    assert derive_evaluation_seeds(42, 1) == derive_evaluation_seeds(42, 1)


def test_run_ids_and_raw_results_are_deterministic_and_immutable(tmp_path: Path) -> None:
    result = {"run_id": "abc", "status": "success", "value": 1}
    write_phase11_raw_result(result, tmp_path)
    with pytest.raises(FileExistsError):
        write_phase11_raw_result(result, tmp_path)
    assert load_valid_raw_results(tmp_path)["abc"]["value"] == 1


def test_aggregation_and_paired_difference() -> None:
    rows = [
        {
            "status": "success", "policy_variant": "left", "communication_strategy": "always",
            "packet_loss_probability": 0.0, "delay_ms": 0, "average_waiting_time": 4,
            "master_seed": 1,
        },
        {
            "status": "success", "policy_variant": "right", "communication_strategy": "always",
            "packet_loss_probability": 0.0, "delay_ms": 0, "average_waiting_time": 3,
            "master_seed": 1,
        },
    ]
    assert aggregate_phase11_results(rows)[0]["sample_count"] == 1
    comparison = paired_differences(rows, "left", "right", "average_waiting_time")
    assert comparison["mean_difference"] == 1
    assert comparison["sample_count"] == 1


def test_phase11_config_loads() -> None:
    config = load_phase11_config(ROOT / "configs/phase11.yaml")
    assert config["master_seeds"] == [42, 123, 456, 789, 1011]
