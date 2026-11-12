import json
from pathlib import Path

import pytest

from traffic_control.environment.trip_metrics import read_trip_metrics
from traffic_control.experiments.artifacts import CampaignStore


def test_trip_metrics_include_unfinished_and_expose_uninserted_demand(tmp_path):
    path = tmp_path / "trip.xml"
    path.write_text('''<tripinfos>
      <tripinfo id="a" depart="0" arrival="20" waitingTime="3" duration="20"
        departDelay="0" timeLoss="4" waitingCount="1"/>
      <tripinfo id="b" depart="2" arrival="-1" waitingTime="5" duration="18"
        departDelay="2" timeLoss="7" waitingCount="2"/>
    </tripinfos>''')
    metrics = read_trip_metrics(path, 3)
    assert metrics["total_waiting_time"] == 8
    assert metrics["average_waiting_time"] == 4
    assert metrics["average_completed_travel_time"] == 20
    assert metrics["unfinished_trips"] == metrics["uninserted_vehicles"] == 1
    assert metrics["completion_fraction"] == pytest.approx(1 / 3)
    assert metrics["horizon_censored"]
    with pytest.raises(ValueError):
        read_trip_metrics(path, 1)


def test_empty_demand_output_is_not_zero_wait_success(tmp_path):
    path = tmp_path / "trip.xml"
    path.write_text("<tripinfos/>")
    result = read_trip_metrics(path, 4)
    assert result["average_waiting_time"] is None
    assert result["average_completed_travel_time"] is None
    assert result["uninserted_vehicles"] == 4


def test_campaign_identity_covers_configuration_source_and_checkpoints(tmp_path):
    manifest = {"config": {"horizon": 120}, "source": "abc", "checkpoint": "xyz"}
    store = CampaignStore(tmp_path / "campaign", manifest)
    for key, value in [("config", {"horizon": 121}), ("source", "def"), ("checkpoint", "uvw")]:
        with pytest.raises(ValueError, match="identity mismatch"):
            CampaignStore(store.directory, {**manifest, key: value})
    assert CampaignStore(store.directory, manifest).identity == store.identity


def test_retry_preserves_failure_and_counts_success_once(tmp_path):
    store = CampaignStore(tmp_path / "campaign", {"schema": 2})
    spec = {"seed": 1, "loss": 0.1}
    assert store.should_run(spec)
    store.record(spec, "failed", {"error": "example failure"})
    assert not store.should_run(spec)
    assert store.should_run(spec, retry_failed=True)
    store.record(spec, "success", {"waiting": 3})
    assert not store.should_run(spec, retry_failed=True)
    assert len(store.attempts(spec)) == 2
    assert len(store.successful()) == 1
    with pytest.raises(FileExistsError):
        store.record(spec, "success", {})


def test_cannot_adopt_legacy_results(tmp_path):
    (tmp_path / "old.json").write_text(json.dumps({"result": 123}))
    with pytest.raises(ValueError, match="unversioned"):
        CampaignStore(tmp_path, {"schema": 2})


def test_legacy_audit_is_read_only_and_mutation_is_blocked(monkeypatch, capsys):
    import importlib.util
    import sys
    spec = importlib.util.spec_from_file_location("legacy_runner", "scripts/run_phase11_final_experiments.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    path = Path("results/phase11/config.yaml")
    before = path.read_bytes() if path.exists() else None
    monkeypatch.setattr(sys, "argv", ["runner", "--mode", "audit"])
    module.main()
    assert json.loads(capsys.readouterr().out)["read_only"]
    assert (path.read_bytes() if path.exists() else None) == before
    with pytest.raises(ValueError, match="read-only"):
        module._protect_original_campaign(module.ROOT / "results/phase11/checkpoints")
