# Project Status

## Current Phase

Phase 5 — Packet Loss Simulation

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
- Four-agent synchronized environment added for `A0`, `A1`, `B0`, and `B1`.
- Independent Q-Learning learners and per-agent checkpoints added.
- Joint action stepping advances SUMO exactly once and returns local rewards.
- Phase 3 smoke training, evaluation, logging, and save/load verification added.
- Ideal communication channel added with typed messages and simulation timestamps.
- Explicit cardinal neighbor topology added for the 2x2 grid.
- Phase 3 environment exposes send/receive operations without changing its
  observation, action, reward, or learning interfaces.
- Phase 4 communication smoke test and SUMO time-preservation test added.
- Seeded stochastic packet-loss model added to the communication channel.
- Bounded send/delivery/drop telemetry and observed-loss-rate reporting added.
- Phase 5 packet-loss smoke test added; zero-delay behavior is preserved.
- GitHub remote verified as `origin`.

## In Progress

- None for Phase 5.

## Upcoming

- Phase 6: implement configurable communication delay.

## Tests

Tests validate configuration loading, required SUMO files, package metadata,
YAML templates, and live SUMO start/step/signal-control/metrics/shutdown
behavior when SUMO is available, Phase 2 observation/action validation and
model persistence, Phase 3 four-agent validation, synchronized stepping,
independent learners, and checkpoint restoration, plus Phase 4 message
construction, topology validation, ideal delivery, SUMO time preservation, and
Phase 5 seeded packet-loss validation and telemetry.

## Experiments

No experiments have been run.

## Known Issues

- The scenario is intentionally small and uses deterministic internal grid
  routes; it is a functional foundation, not a realistic traffic benchmark.
- The Phase 2 baseline uses NumPy-only linear Q-learning; no ML framework was
  installed for Python 3.14 compatibility.
- The smoke training is a functional check only; no performance conclusion
  has been drawn.
- Phase 3 uses local observations and local rewards; agents do not exchange
  observations or learned information.
- Communication delay remains unsupported and must be zero.
- Communication metadata is not included in the Phase 3 RL observation.
- Combined impairment, stale-information robustness, adaptive communication,
  and robust training remain future phases.

## Latest Commit

Phase 5 implementation commit: `a04c8e6`.
