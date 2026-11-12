# Experiment Log

No experiments have been run. This file will record configurations, seeds,
Git commits, measured metrics, observations, and limitations for each
subsequent experiment.

The Phase 3 smoke-training run is functional verification only, not a research
experiment. It uses seed 42, two training episodes, one evaluation episode,
agents A0/A1/B0/B1, and ideal communication conditions (0% packet loss, 0 ms
delay). Its machine-readable outputs are ignored under `results/phase3/`.

The Phase 4 communication smoke test is functional verification only, not a
research experiment. It verifies an A0-to-A1 message at simulation time 10.0,
including payload, generation timestamp, and immediate delivery timestamp.

The Phase 5 packet-loss smoke test is functional verification only, not a
research experiment. It checks deterministic 0% delivery and reproducibility
of an intermediate seeded packet-loss sequence. No traffic-performance or
robustness conclusion is drawn.

The Phase 6 communication-delay smoke test is functional verification only, not
a research experiment. It checks an A0-to-A1 message generated at simulation
time 10.0 with a fixed 250 ms delay, including unavailable-before-boundary,
exact-boundary delivery, timestamp preservation, telemetry, and compatibility
with complete packet loss. No traffic-performance or robustness conclusion is
drawn. Combined packet-loss and delay evaluation remains Phase 7 work.

Phase 7 framework status: no full research matrix has been run. The configured
matrix contains 25 conditions and five replicate seeds. The runner preserves
run-level JSON results and aggregates successful numeric metrics without
replacing failures. The Phase 7 smoke script exercises four representative
conditions as functional verification only. A causal-path audit found that
Phase 3 policies use local observations only; no communicated messages are
currently generated or consumed by action selection, so no traffic-performance
degradation is claimed from packet loss or delay. Robustness and
message-age-aware policy inputs remain Phase 8 work.

A bounded one-condition frozen-checkpoint pilot was executed for 10% loss and
250 ms delay using seed 42. It is functional framework validation, not a final
benchmark or research conclusion; its raw output is kept under the ignored
Phase 7 results directory.

Phase 8 status: a separate freshness-aware communication policy now consumes
neighbor traffic snapshots. Its 23-feature observation includes availability,
simulation-time age, exponential freshness, stale status, and freshness-weighted
neighbor features. The original five-feature Phase 3 policy and checkpoints are
preserved. The Phase 8 smoke test is functional verification only; no robust
training, superiority claim, or final performance experiment has been run.

Phase 9 status: the robust-training framework uses the Phase 7 25-condition
matrix with a balanced shuffled-cycle schedule. The ideal-trained
communication-aware baseline is restricted to 0% loss and 0 ms delay; the
robust-trained policy uses the impairment distribution and remains a separate
fresh initialization. SeedSequence-derived episode streams separate learner,
condition-schedule, packet-loss, and SUMO randomness. A two-episode-per-variant
smoke run with master seed 42 completed as functional software verification
only. No production robust training, convergence claim, superiority claim, or
statistical evaluation has been performed. Phase 10 adaptive communication
has not started.

Phase 10 status: deterministic rule-based always, periodic, and adaptive
event-triggered transmission scheduling is implemented separately from the
policy, channel, and freshness cache. The scheduler compares normalized
five-feature snapshots against the last transmission attempt and uses a
simulation-time heartbeat. Acknowledgements are not available, so attempted
transmissions update scheduler reference state even if packet loss drops them.
The Phase 10 smoke test is functional verification only; no communication
efficiency or traffic-performance conclusion has been drawn. Phase 11 and
Phase 12 have not started.

Phase 11 final evaluation:

- Design: 2 communication-aware policies x 3 strategies x 25 Phase 7
  conditions x 5 master seeds, plus 5 local-only reference episodes.
- Training: fresh frozen checkpoints, 25 episodes per seed and policy; ideal
  communication-aware training used 0% loss/0 ms delay, robust training used
  one balanced 25-condition cycle, and local-only training disabled
  communication.
- Evaluation: deterministic actions, matched traffic-demand seeds, separate
  packet-loss streams, fixed 20-step episodes, and no policy updates.
- Coverage: 755 required, 755 successful, 0 failed, 0 pending.
- Primary metric: average vehicle waiting time. Secondary metrics include
  total waiting, queue lengths, completed trips, reward, send attempts,
  delivery/drop telemetry, message age, stale proportion, pending messages,
  scheduler opportunities, suppression, and reduction.
- Statistical method: descriptive mean, standard deviation, median, and
  95% normal-approximation intervals. Paired comparisons aggregate across
  conditions per frozen master-seed checkpoint; five seeds limit inference.
- Measured outcome: ideal-trained communication-aware mean waiting time was
  0.0942 s across conditions and strategies; robust-trained was 0.1530 s.
  Periodic and adaptive each made 160 sends per episode with zero suppression
  and zero communication reduction under the frozen 1000 ms settings, so
  their traffic metrics matched always transmission in this campaign.
- Interpretation: the result is mixed and specific to the small deterministic
  SUMO scenario and 25-episode training budget. It does not establish
  robustness superiority or adaptive communication benefit.
- Raw records and generated analysis are preserved locally under
  `results/phase11/` and are ignored by Git. Phase 12 has not started.
