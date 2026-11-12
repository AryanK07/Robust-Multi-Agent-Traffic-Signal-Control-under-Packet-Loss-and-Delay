# Changelog

## [Unreleased]

### Fixed

- Communication-aware environment step telemetry now snapshots channel
  counters after its send/receive round, matching scheduler and cache timing.
  Three regression cases cover immediate delivery, delay, and complete loss.
  Original Phase 11 outputs and checkpoints were preserved.

### Audited

- Independently verified the 755-record design, all 15 production checkpoint
  hashes, 151 summaries, and six stored comparisons. Recorded metric,
  timing, provenance, baseline, and statistical limitations in
  `docs/PHASE11_AUDIT.md`; Phase 12 remains unstarted.
- Validated five original replays and five separately stored corrected
  replays; all 870 original artifact file hashes remained unchanged.

### Added

- Phase 0 Python project configuration and package scaffold.
- Phase 1 deterministic SUMO grid, routes, configuration, and TraCI wrapper.
- Traffic-state extraction, signal control, metrics, integration tests, and
  smoke-test tooling.
- Phase 2 single-agent RL environment, NumPy-only linear Q-learning baseline,
  model persistence, smoke training, and evaluation logging.
- Phase 3 synchronized four-agent Independent Q-Learning baseline with local
  observations/rewards, independent checkpoints, and evaluation logging.
- Phase 4 ideal communication channel with typed messages, explicit 2x2
  neighbors, deterministic zero-delay delivery, and Phase 3 integration hooks.
- Phase 5 configurable seeded packet loss with delivery/drop telemetry and
  zero-delay-only validation.
- Phase 6 deterministic fixed communication delay driven by simulation
  timestamps, pending-message queues, and delay telemetry.
- Phase 7 configurable combined packet-loss/delay matrix, frozen-checkpoint
  runner, raw run storage, and summary aggregation.
- Phase 8 separate freshness-aware communication policy, latest-neighbor cache,
  simulation-time age decay, 23-feature observations, and checkpoint metadata.
- Phase 9 condition-randomized robust-training pipeline with balanced-cycle
  scheduling, isolated seed streams, episode metrics, and separate checkpoint
  metadata.
- Phase 10 deterministic always/periodic/adaptive transmission scheduler with
  heartbeat, trigger, suppression, and communication-reduction telemetry.
- Phase 11 reproducible final-evaluation runner, frozen checkpoint audit,
  resumable raw results, statistical summaries, paired comparisons, and plots.
- Phase 11 campaign completed 755/755 required evaluation episodes without
  failures; measured outcomes are documented without superiority claims.
