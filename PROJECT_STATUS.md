# Project Status

## Current Phase

Phase 1 — SUMO Environment

## Completed

- Deterministic 2x2 SUMO grid with four signalized junctions created.
- Deterministic six-vehicle route demand and SUMO configuration added.
- TraCI environment wrapper supports start, reset, step, close, simulation
  time, traffic-light access, and programmatic phase selection.
- Traffic-state extraction provides vehicle count, waiting time, queue length,
  lane occupancy, and current phase.
- Reusable metrics collector provides waiting-time, queue, vehicle, completed
  trip, and simulation-duration summaries.
- Phase 1 tests and a headless smoke-test script added.
- GitHub remote verified as `origin`.

## In Progress

- None for Phase 1.

## Upcoming

- Phase 2: validate single-agent RL logic without adding it to Phase 1.

## Tests

Tests validate configuration loading, required SUMO files, package metadata,
YAML templates, and live SUMO start/step/signal-control/metrics/shutdown
behavior when SUMO is available.

## Experiments

No experiments have been run.

## Known Issues

- The scenario is intentionally small and uses deterministic internal grid
  routes; it is a functional foundation, not a realistic traffic benchmark.
- PyTorch remains an optional later-phase dependency and is not used here.

## Latest Commit

Phase 1 commit: to be recorded after verification.
