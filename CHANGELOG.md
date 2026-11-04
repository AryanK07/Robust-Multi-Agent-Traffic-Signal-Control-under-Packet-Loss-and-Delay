# Changelog

## [Unreleased]

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
