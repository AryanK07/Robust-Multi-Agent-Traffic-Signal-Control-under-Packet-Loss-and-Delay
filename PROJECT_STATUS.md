# Project Status

## Current Phase

Phase 11 — Authorized follow-up v2 implementation in progress.

Phase 12 has not started. See [the audit report](docs/PHASE11_AUDIT.md).

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
- Phase 11 final evaluation runner, frozen checkpoint audit, resumable raw
  results, statistical summaries, paired comparisons, and figures added.
- Production checkpoints trained for 25 episodes per seed for all three policy
  variants across five master seeds.
- Complete 755-run evaluation campaign completed successfully.
- GitHub remote verified as `origin`.

## In Progress

- Follow-up metric/storage foundations and action-sensitive environment are
  implemented. Distinct 100/250/500/1000 ms effects on policy message age,
  two-leg request delays, loss, feature ablations, and signal constraints have
  targeted regression coverage. The versioned training/evaluation pilot is next.

- The original Phase 11 campaign is complete and preserved, but the audit
  identified measurement and design limitations that prevent treating the
  full research acceptance criteria as satisfied.

## Upcoming

- Implement the user-approved correction and action-sensitive IQL scope in
  `docs/FOLLOWUP_PROTOCOL.md`; validate with a bounded development pilot.
- Phase 12 remains deferred; no paper drafting has started.

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

Independent audit execution: original suite 65 passed; post-correction suite
68 passed, including three new channel/scheduler timing regression cases.
Compilation and Phase 4–10 smoke checks passed. Five original and five
separate corrected 20-step replays validated frozen evaluation and confirmed
that the correction changes channel telemetry only.

## Experiments

The original Phase 11 directory contains exactly 755 required successful
evaluation records and zero failed records, with 15 production checkpoint
sets and 25 training records per set. Checkpoint hashes, 151 summaries, and
six stored statistical comparisons were independently verified. All 870
original artifact files remain unchanged. Audit evidence and corrected
bounded validation are separate under `results/phase11_audit_v1/`; this is
not a replacement final campaign. Earlier pilots/smokes remain functional
verification only.

## Known Issues

- The original waiting field averages consecutive-wait snapshots, not total
  waiting per vehicle. No metric definition was silently changed.
- All original episodes last 20 seconds and complete zero trips. Six fixed
  vehicle departures do not constitute a realistic demand benchmark; SUMO's
  default speed variation still depends on its seed.
- The 100–1000 ms positive delays collapse to one decision-time class under
  one-second decisions. Delay remains fixed, not stochastic.
- One-second periodic/heartbeat settings necessarily suppress no sends.
  The original 160-send field was a stale snapshot; actual completed episode
  operations include 168 sends. The reporting defect is now corrected.
- Both communication-aware policies contain the freshness mechanism;
  component ablations, a non-freshness communication baseline, and held-out
  impairment evaluation are absent. The local-only baseline uses a different
  exploration schedule.
- Five paired training seeds and 25 short training episodes limit inference.
  Original robust waiting-proxy mean exceeds ideal, but paired uncertainty
  crosses zero; no superiority or convergence is established.
- Original result Git hashes predate the Phase 11 runner. Full configuration,
  training provenance, dependency locking, and resume/retry safeguards need
  improvement before a new campaign.
- Channel counters persist across reused-environment resets; original Phase
  11 uses fresh environments. Signal actions bypass yellow/minimum-green
  transitions; replay emitted emergency-stop warnings.
- All raw results/checkpoints are local and ignored by Git; a separate
  research archive backup remains necessary.

## Latest Commit

Pre-audit HEAD and verified remote: `4161f42c13e0a1c89f8ce307579befcbbb530378`.
Phase 11 implementation: `bbfe2c2`. Original records name `9b8b212`.
The audit and telemetry correction are recorded in the commit containing
this status update; use `git log -1` for its resolved hash.
