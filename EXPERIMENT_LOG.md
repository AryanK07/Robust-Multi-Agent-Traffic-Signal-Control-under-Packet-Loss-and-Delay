# Experiment Log

## Finite metadata calibration — 2026-11-13

- IDs `metadata_calibration_01` and `metadata_calibration_001`, source
  `57d2b94`, scales 0.1 and 0.01 respectively. Seeds 31001/31002; two full
  variants; unchanged phase-relative/termination settings and 81 episodes.
- Each setting completed 324 training, 24 validation and 12 exploratory
  evaluation episodes without execution failure. Both completed 100% of
  trips in all eight episode-81 validation cells. Both settings are retained.
- The predeclared largest-passing-scale rule selects 0.1. No reserved seed
  informed this selection. The final configuration and analysis are frozen
  in `docs/PHASE11_RESERVED_PROTOCOL.md` before collection.

## Completion-terminated training validation — 2026-11-13

- ID `training_validation_004`, source `ac0cf6f`, configuration
  `configs/training_validation_v4.yaml`; same development seeds and budgets.
- Completed 810 training, 60 validation, 26 exploratory evaluation episodes;
  zero execution failures. Local/plain variants reached the episode-81
  validation criterion; full variants did not. All outcomes are retained.
- A finite two-setting metadata calibration is predeclared separately in
  `docs/METADATA_CALIBRATION_PROTOCOL.md`; no reserved test seeds were used.

## Phase-relative training validation — 2026-11-13

- ID `training_validation_003`, source `094b1f1`, configuration
  `configs/training_validation_v3.yaml`; same development seeds, budgets,
  reward, demand and evaluation cells as `training_validation_001`.
- Completed 810 training, 60 validation and 26 exploratory evaluation
  episodes; zero execution failures. Local validation completed all trips
  at 81 episodes, but the full-model failures kept the all-cell 95% criterion
  unmet. All observations are preserved; no final test streams were used.
- Mean last training arrival: 86.7115 seconds, leaving 33.2885 seconds of
  empty-network updates. A separate controlled termination study is defined
  in `docs/TRAFFIC_TERMINATION_VALIDATION.md` before collecting it.

## Aggregate-observation training validation — 2026-11-13

- ID `training_validation_001`, source `b3a2766`, configuration
  `configs/training_validation_v1.yaml`, seeds 31001/31002.
- Five variants, 81 training episodes each, frozen checks at 9/27/81 with
  separate validation streams; unchanged v2 settings and original network.
- Completed 810 training, 60 validation and 26 exploratory evaluation
  episodes with zero execution failures. The 95%-completion-in-every-cell
  criterion failed. No seeds/checkpoints were removed or budget extended.
- [Complete checkpoint table](docs/TRAINING_VALIDATION_RESULTS.md).
  A separate matched phase-relative feature comparison is predeclared in
  `docs/PHASE_RELATIVE_VALIDATION.md`; original and v2 data are preserved.

## Follow-up v2 development pilot — 2026-11-13

- Experiment ID: `followup_v2/development_001`; source commit
  `eada4cdc26ac7ca07791b4e48e1f1d7ab2ad3209`.
- Configuration: `configs/followup_v2.yaml`, resolved pilot overrides;
  master seeds 20261/20262, separate train/evaluation streams, original four
  junctions, 20 seeded departures over 30 seconds, 120-second episodes.
- Training: five variants, four episodes each, learning rate 0.01, discount
  0.95, epsilon 0.2. Robust exposure is a seeded incomplete nine-condition
  cycle over losses 0/0.1/0.2 and delays 0/250/500 ms.
- Evaluation: frozen weights, epsilon zero, matched demand; conditions
  (0,0), (0.1,250 ms), held-out (0.3,1000 ms). Five strategies reuse the full
  robust checkpoint. Ten checkpoint sets, 40 training episodes and 50
  evaluations completed with no execution failures.
- Metrics: tripinfo accumulated per-vehicle waiting to horizon, completion,
  unfinished/uninserted demand, travel, queue, reward and communication cost.
- All training episodes completed 20/20 trips; all frozen evaluations were
  censored. Full ideal/robust waiting means were 47.7575/61.1775 seconds and
  completion fractions 50%/37.5%. These are development observations, not
  comparable to the original waiting proxy or proof of a general ranking.
- Full robust communication attempts averaged 9600 always, 960 periodic,
  206 state-change adaptive, 1797.67 periodic pull, and 564.67 action-sensitive.
  Traffic metrics matched across strategies within each seed-condition;
  the action-sensitive method did not dominate the simpler adaptive control.
- Limitations: two independent master seeds, four training episodes,
  incomplete robust exposure, censored traffic outcomes, three evaluation
  cells and no collected component-ablation campaign. No convergence,
  equivalence, superiority or novelty claim. Parameters were not retuned.
- Validation: 93 tests passed and compilation passed; 90 tripinfo records,
  40 checkpoint hashes, exact evaluation coverage, seed pairing, source
  identity and counter consistency verified. Resume preserved all 421
  campaign manifest/raw/artifact files; original 870 files remain unchanged.
- Full results, paired uncertainty, selected generated artifacts and ranked
  next actions: [development report](docs/FOLLOWUP_DEVELOPMENT_RESULTS.md).
  Raw data remain local in `results/followup_v2/development_001/`.

## Historical development log

Earlier entries below retain the history of individual development phases.
The original Phase 11 campaign is preserved locally; its independent audit is
documented in `docs/PHASE11_AUDIT.md`. Historical statements about unstarted
phases are not the current status.

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

Phase 11 independent audit — 2026-11-12:

- Audit ID: `phase11_audit_v1`; source at inspection:
  `4161f42c13e0a1c89f8ce307579befcbbb530378`.
- Original records all name `9b8b212d482e447583ef6df7daa9467a2b6e478c`, which
  predates the Phase 11 runner. This provenance gap is recorded, not repaired
  by rewriting historical metadata.
- Read-only analysis verified all 755 required records, 15 production
  checkpoint sets, 25 training records per set, 151 summaries, and six stored
  comparisons. Recomputed original waiting-field means: ideal 0.0942471910,
  robust 0.1530476904. This field is not accumulated waiting per vehicle.
- Five original frozen evaluations reproduced all fields except the expected
  current Git hash. Five diagnostic traces checked message influence, policy
  immutability, metric semantics, and channel-counter timing. A separate
  reset diagnostic found channel counters persist across environment resets;
  the original campaign creates fresh environments and is unaffected by that
  lifecycle issue.
- Corrected only the post-step channel telemetry snapshot. Three new tests
  failed before the correction and passed afterward. Full suite: 68 passed.
- Five corrected replays are isolated in
  `results/phase11_audit_v1/corrected_replays/`, each with original run ID,
  source-file SHA-256, timestamp, and modified-working-tree provenance.
  Communication-aware send counts changed from 160 to 168; all traffic
  outputs and scheduler reductions matched. The local-only control was
  unchanged. No checkpoint was retrained.
- Configurations, selected seeds/conditions, detailed trace measurements,
  differences, and all 870 original artifact hashes are recorded in the
  audit directory. SUMO emitted emergency-braking/red-light-stop warnings
  during some replays; those episodes completed, but the warnings reinforce
  the signal-transition limitation documented in the audit.
- This was bounded software validation, not a new final campaign or a
  successful robustness experiment. Original artifacts remain byte-identical.
  Follow-up protocol changes require review; Phase 12 has not started.
