"""Versioned per-vehicle metrics from SUMO's authoritative tripinfo output.

Keep the original snapshot collector for historical Phase 11 reproduction.
Version 2 uses waitingTime, not a sum of consecutive-wait snapshots.
"""

from math import isfinite
from pathlib import Path
from statistics import mean
import xml.etree.ElementTree as ET


def read_trip_metrics(path: Path, expected_vehicles: int) -> dict[str, object]:
    """Summarize all departed vehicles, explicitly reporting horizon censoring.

    SUMO must run with --tripinfo-output.write-unfinished. Waiting includes
    unfinished vehicles up to the horizon; travel time includes arrivals only.
    Departure delay is separate, and uninserted demand is never hidden.
    """
    if expected_vehicles <= 0:
        raise ValueError("expected_vehicles must be positive")
    rows = ET.parse(path).getroot().findall("tripinfo")
    ids = [row.attrib["id"] for row in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate tripinfo vehicle IDs")
    departed = [row for row in rows if float(row.attrib["depart"]) >= 0]
    if len(departed) > expected_vehicles:
        raise ValueError("trip count exceeds configured demand")
    completed = [row for row in departed if float(row.attrib["arrival"]) >= 0]

    def numbers(records, field):
        values = [float(row.attrib[field]) for row in records]
        if any(not isfinite(value) or value < 0 for value in values):
            raise ValueError(f"invalid tripinfo {field}")
        return values

    waits = numbers(departed, "waitingTime")
    durations = numbers(completed, "duration")
    return {
        "metric_schema": "tripinfo_v2",
        "expected_vehicles": expected_vehicles,
        "departed_vehicles": len(departed),
        "completed_trips": len(completed),
        "unfinished_trips": len(departed) - len(completed),
        "uninserted_vehicles": expected_vehicles - len(departed),
        "completion_fraction": len(completed) / expected_vehicles,
        "horizon_censored": len(completed) != expected_vehicles,
        "total_waiting_time": sum(waits),
        "average_waiting_time": mean(waits) if waits else None,
        "average_completed_travel_time": mean(durations) if durations else None,
        "total_departure_delay": sum(numbers(departed, "departDelay")),
        "total_time_loss": sum(numbers(departed, "timeLoss")),
        "total_stops": sum(numbers(departed, "waitingCount")),
    }
