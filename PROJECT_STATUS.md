# Project Status

## Current Phase

Phase 10 — Adaptive Inter-Agent Communication

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
- Fixed simulation-time communication delay added with deterministic
  millisecond-to-second scheduling, pending queues, tie-breaking, and
  delivery telemetry.
- Phase 6 delay and packet-loss compatibility smoke test added.
- Configurable 5x5 Phase 7 condition matrix and five replicate seeds added.
- Frozen-checkpoint experiment runner, immutable raw JSON results, and grouped
  summaries added.
- Causal-path audit documented: current Phase 3 policies do not consume
  communication messages.
- Separate freshness-aware communication policy and environment variant added
  with 23-dimensional observations.
- Simulation-time latest-neighbor cache, exponential freshness decay, stale
  threshold, typed traffic snapshot payloads, and incompatible checkpoint
  metadata validation added.
- Phase 8 functional smoke test added.
- Condition-randomized Phase 9 training utilities added using the Phase 7
  25-condition matrix.
- Separate ideal-trained and robust-trained communication-aware variants added
  with balanced-cycle scheduling, isolated seed streams, episode metrics, and
  checkpoint metadata.
- Phase 9 smoke training added; it does not run a production campaign.
- Rule-based always, periodic, and adaptive event-triggered communication
  scheduler added with heartbeat, trigger, suppression, and reduction
  telemetry.
- Phase 10 scheduler configuration, tests, and smoke verification added.
- GitHub remote verified as `origin`.

## In Progress

- None for Phase 10 implementation.

## Upcoming

- Phase 11: final experiments and evaluation.

## Tests

Tests validate configuration loading, required SUMO files, package metadata,
YAML templates, and live SUMO start/step/signal-control/metrics/shutdown
behavior when SUMO is available, Phase 2 observation/action validation and
model persistence, Phase 3 four-agent validation, synchronized stepping,
independent learners, and checkpoint restoration, plus Phase 4 message
construction, topology validation, ideal delivery, SUMO time preservation, and
Phase 5 seeded packet-loss validation and telemetry, plus Phase 7 matrix
generation, validation, serialization, and aggregation, plus Phase 8 freshness, cache, checkpoint, and policy-interface
tests, Phase 9 scheduler/seed/metadata/configuration tests, and Phase 10
scheduling/telemetry tests.

## Experiments

No final research experiment has been run. Phase 7 pilot, Phase 8 smoke, and
Phase 9 smoke training and Phase 10 smoke are functional verification only.

## Known Issues

- The scenario is intentionally small and uses deterministic internal grid
  routes; it is a functional foundation, not a realistic traffic benchmark.
- The Phase 2 baseline uses NumPy-only linear Q-learning; no ML framework was
  installed for Python 3.14 compatibility.
- The smoke training is a functional check only; no performance conclusion
  has been drawn.
- Phase 3 uses local observations and local rewards; agents do not exchange
  observations or learned information.
- Delay is currently deterministic fixed delay; variable/stochastic delay
  distributions are intentionally not implemented.
- Communication metadata is not included in the Phase 3 RL observation.
- Phase 3 policies do not generate or consume communication messages during
  action selection, so impairment cannot currently be attributed to traffic
  performance.
- Delay is fixed only; stochastic delay, robustness, adaptive communication,
  and robust training remain future phases.
- Phase 9 smoke training is not a robust-performance claim; final training and
  statistical evaluation remain pending.
- Adaptive communication is deterministic and rule-based; no learned
  communication policy or communication reward has been introduced.

## Latest Commit

Phase 10 implementation is currently uncommitted.
