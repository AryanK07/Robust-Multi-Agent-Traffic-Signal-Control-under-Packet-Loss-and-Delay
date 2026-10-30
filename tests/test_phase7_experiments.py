import json

import pytest

from traffic_control.experiments import (
    Phase7Condition,
    aggregate_phase7_results,
    generate_phase7_conditions,
    load_phase7_config,
    validate_phase7_config,
    write_raw_result,
)


def test_phase7_config_generates_complete_matrix_and_baseline() -> None:
    config = load_phase7_config("configs/phase7.yaml")
    conditions = generate_phase7_conditions(config)

    assert len(conditions) == 25
    assert Phase7Condition(0.0, 0.0) in conditions
    assert Phase7Condition(0.10, 0.0) in conditions
    assert Phase7Condition(0.0, 250.0) in conditions
    assert Phase7Condition(0.10, 250.0) in conditions


def test_condition_generation_is_deterministic_and_classifies_cells() -> None:
    config = validate_phase7_config(
        {
            "phase7": {
                "name": "test",
                "packet_loss_levels": [0.0, 0.1],
                "delay_levels_ms": [0, 250],
                "seeds": [42],
            }
        }
    )
    first = generate_phase7_conditions(config)
    second = generate_phase7_conditions(config)
    assert first == second
    assert first[0].condition_id == "loss_0p00__delay_0ms"
    assert first[-1].condition_id == "loss_0p10__delay_250ms"


@pytest.mark.parametrize(
    "section",
    [
        {"packet_loss_levels": [-0.1], "delay_levels_ms": [0], "seeds": [1]},
        {"packet_loss_levels": [1.1], "delay_levels_ms": [0], "seeds": [1]},
        {"packet_loss_levels": [0], "delay_levels_ms": [-1], "seeds": [1]},
        {"packet_loss_levels": [0, 0], "delay_levels_ms": [0], "seeds": [1]},
        {"packet_loss_levels": [0], "delay_levels_ms": [0], "seeds": [1, 1]},
    ],
)
def test_phase7_configuration_rejects_invalid_values(section: dict) -> None:
    with pytest.raises(ValueError):
        validate_phase7_config({"phase7": {"name": "test", **section}})


def test_result_serialization_refuses_overwrite_and_aggregation(tmp_path) -> None:
    result = {
        "run_id": "loss_0p00__delay_0ms__seed_42",
        "status": "success",
        "packet_loss_probability": 0.0,
        "delay_ms": 0,
        "average_waiting_time": 1.0,
        "mean_queue_length": 2.0,
        "completed_trips": 3,
        "episode_reward": 4.0,
        "observed_loss_rate": 0.0,
        "message_age_mean": None,
    }
    path = write_raw_result(result, tmp_path)
    assert json.loads(path.read_text(encoding="utf-8"))["run_id"] == result["run_id"]
    with pytest.raises(FileExistsError):
        write_raw_result(result, path.parent)
    summary = aggregate_phase7_results([result, {**result, "run_id": "other", "average_waiting_time": 3.0}])
    assert summary[0]["sample_count"] == 2
    assert summary[0]["average_waiting_time_mean"] == 2.0
