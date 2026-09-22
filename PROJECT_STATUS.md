# Project Status

## Current Phase

Phase 2 — Single-Agent RL

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
- Single-agent RL environment added for intersection `A0`.
- Five-component normalized local observation and two-action phase-control
  interface added.
- Configurable delta queue/waiting-time reward added.
- NumPy-only linear Q-learning agent with `.npz` save/load added.
- Reproducible smoke training, CSV logging, JSON evaluation, and tests added.
- GitHub remote verified as `origin`.

## In Progress

- None for Phase 2.

## Upcoming

- Phase 3: expand to multiple cooperating agents.

## Tests

Tests validate configuration loading, required SUMO files, package metadata,
YAML templates, and live SUMO start/step/signal-control/metrics/shutdown
behavior when SUMO is available, as well as Phase 2 observation/action
validation, model construction, persistence, environment lifecycle, and
episode termination.

## Experiments

No experiments have been run.

## Known Issues

- The scenario is intentionally small and uses deterministic internal grid
  routes; it is a functional foundation, not a realistic traffic benchmark.
- The Phase 2 baseline uses NumPy-only linear Q-learning; no ML framework was
  installed for Python 3.14 compatibility.
- The smoke training is a functional check only; no performance conclusion
  has been drawn.

## Latest Commit

Phase 2 commit: to be recorded after verification.
