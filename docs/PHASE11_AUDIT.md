# Phase 11 independent audit

Audit date: 2026-11-12 (user timezone: Asia/Calcutta).
Inspection baseline: `4161f42c13e0a1c89f8ce307579befcbbb530378`.

**Recommendation: conduct a focused, explicitly versioned follow-up before
proceeding to Phase 12 as a completed research evaluation.** The original
campaign exists and its reported numerical aggregates are reproducible, but
its metric definition, temporal resolution, short horizon, and missing
method comparisons prevent it from resolving the full research questions.
An unfavorable result is not a reason to reject a campaign; these measurement
and design limitations are the reasons for this recommendation.

This report distinguishes verified observations, earlier reports, hypotheses,
and proposed changes. It does not draft a paper, change research hypotheses,
or claim novelty, superiority, convergence, or publication readiness.

## 1. Verified current state

- The initial working tree was clean on `main`. Local HEAD, `origin/main`,
  and the live remote `refs/heads/main` all matched the inspection baseline.
- The repository implements Phases 0–11, with a NumPy linear IQL approach;
  Phase 12 has not started. Completion of the campaign is verified, but full
  satisfaction of the Phase 11 scientific specification is not.
- Read `AGENTS.md`, `PROJECT_SPEC.md`, README, status, changelog, experiment
  log, runtime modules, relevant configurations, tests, and experiment scripts.
- Python 3.14.0, Git 2.55.0.windows.2, SUMO 1.27.1 and TraCI are usable.
  Current packages: NumPy 2.4.4, SciPy 1.17.1, pandas 3.0.1,
  Matplotlib 3.10.8, pytest 9.1.1, PyYAML 6.0.3. These are audit-environment
  versions; original run records do not establish their historical versions.
- The original README/status/log contained stale or contradictory phase
  statements. Current status and audit notices have been updated while
  retaining the historical experiment entries.

## 2. Repository and experimental-data accessibility

**Verified:** `results/phase11/` contains 870 files (2,659,276 bytes), including
755 raw JSON records, 15 production checkpoint sets (60 agent NPZ files),
15 metadata files, 15 training logs, pilot checkpoints, configuration,
summaries, statistical report, and figures. No required campaign file was
missing from this workspace.

Every production set has 25 training records: 375 recorded training episodes
in total. Every model has finite parameters, the expected dimensions,
learning rate 0.05, and discount 0.95. All raw checkpoint digests match the
present files. Pilot checkpoints were excluded from production verification.

All 755 expected run IDs and their specification fields match the generated
design exactly, with no missing or extra records: 750 communication-aware
episodes plus five local-only reference episodes. All are marked successful;
there are no recorded failures in this directory. This does not establish
that no earlier, unrecorded failed attempt ever occurred.

The data remain ignored by Git. A fresh Git clone does not include these
checkpoints/results. Preserve an independently backed-up research archive;
this audit did not upload private/local artifacts or create an off-machine
backup. SHA-256 manifests detect later changes but are not a backup or an
access-control mechanism.

## 3. Architecture and actual causal path

`SumoEnvironment` owns TraCI lifecycle, signal access, state extraction, and
metrics. `MultiAgentEnvironment` applies four actions and advances SUMO once,
returning five local features and local queue/waiting delta rewards.
`LinearQAgent` implements two-action linear Q-learning. Actions maintain the
phase or select the next green phase.

`CommunicationChannel` implements seeded Bernoulli packet loss and causal
fixed-delay queues over eight directed neighbor links. The scheduler decides
per sender, then fans each scheduled snapshot out to two neighbors.
`NeighborInformationCache` retains the latest message by generation time.
The communication-aware environment forms 23 features: five local values,
then two nine-value neighbor blocks (availability, normalized age,
freshness, stale flag, and five freshness-weighted payload values).

Both ideal-trained and robust-trained communication-aware policies use this
same freshness mechanism. Their training condition exposure differs. The
local-only reference uses five features and does not communicate.

**Verified message influence:** in a frozen ideal-trained seed-42 ideal-link
trace, zeroing only neighbor payload features changed the greedy action in
19 of 80 observed agent decisions, with local inputs held fixed. Replacing
neighbor blocks with missing-message sentinels also changed actions. These
are diagnostic input interventions on recorded states, not trained ablations
or closed-loop performance comparisons. Communication is genuinely connected
to policy decisions; its benefit is not established by that fact.

## 4. Reproducibility assessment

**Verified strengths:** deterministic run specifications; matched evaluation
traffic and packet-loss streams across policies/strategies; separate
checkpoint directories; no evaluation update calls; epsilon zero at
evaluation; consistent checkpoint hashes; immutable-write checks for raw
JSON; exact independent reproduction of 151 summaries and all six stored
comparisons. Five original 20-step replays matched every recorded field
except the expected current Git hash. Evaluation was guarded against any
call to `LinearQAgent.update`, and five diagnostic traces also verified
unchanged in-memory weights/biases.

Training seeds and evaluation streams were regenerated from code and checked:
there was no numerical intersection between the inspected training seed
values and derived evaluation values. Ideal/robust learners start from fresh
zero weights with the same per-agent RNG seed mapping; robust training does
not load an ideal checkpoint. One fresh environment is created per episode.
The ideal logs contain only (0 loss, 0 delay); each robust log contains every
one of the 25 nominal conditions exactly once. The metadata's full-grid
`training_condition_distribution` for ideal training is misleading; actual
exposure counts and episode logs establish ideal-only exposure.

**Important provenance gap:** every original raw record names
`9b8b212d482e447583ef6df7daa9467a2b6e478c`. That commit does not contain the
Phase 11 runner or configuration; they first appear in `bbfe2c2`. The records
therefore do not identify a complete committed source snapshot. Running
uncommitted Phase 11 additions is consistent with the evidence, but the exact
historical working tree and configuration-freeze chronology cannot be proved
from these files. Do not relabel the old records with a later commit.

Original training metadata omits source hash, timestamp, resolved full
configuration, package versions, and actual per-episode seed values. The
values can often be reconstructed from current code, which is weaker than
recording them at execution. Training logs retain reward and condition, but
not production training traffic metrics or TD-error/convergence diagnostics.
Dependencies are minimum-version constraints rather than a locked environment.

Run IDs omit checkpoint digest, horizon, scheduler/freshness settings, and
source/configuration identity. Changing the horizon to 21 and periodic
interval to 2000 ms generated exactly the same run specifications/IDs in a
diagnostic. Resuming into an old directory can silently reuse incompatible
records. Existing-checkpoint reuse validates only episode budget. Also, CLI
`--mode audit` writes `config.yaml`; it was intentionally not run against
the original directory. The audit invoked design validation directly.

## 5. Why communication reduction was zero

**Classification: correct configured scheduling, an uninformative
configuration for suppression, plus a separate telemetry integration bug.**

- SUMO and decisions advance by 1.0 second.
- Periodic interval = 1000 ms. Every subsequent decision is eligible.
- Adaptive threshold = 0.10 on mean absolute change of five normalized local
  features. If change does not trigger, the 1000 ms heartbeat does.
- The change trigger is tested before heartbeat. A changed signal phase can
  itself exceed the threshold. Loss does not prevent a send attempt from
  updating the scheduler reference; acknowledgements are not modeled.
- Thus every sender transmits at reset and after each of 20 steps: 84 sender
  opportunities, two recipients each, or 168 actual channel send attempts.
- Across 250 episodes per strategy, raw trigger totals are: periodic 1,000
  first + 20,000 periodic; adaptive 1,000 first + 9,038 change + 10,962
  heartbeat. There are zero suppressed opportunities. Always has 1,000 first
  + 20,000 always. Traffic and inspected communication fields are identical
  across matched strategies.

**Defect and correction:** the base environment captured channel telemetry
before the communication-aware subclass sent/received at the new timestamp.
The subclass returned that old snapshot alongside the current scheduler and
cache. The reported 160 attempts cover sends through t=19, while scheduler
counts include t=20. Delayed deliveries, drops, pending counts, and observed
loss could similarly lag. A minimal change refreshes `info['communication']`
after the communication round. It changes reporting only.

The 168 total includes eight terminal-observation messages that cannot affect
a subsequent action in this episode. A future protocol should explicitly
define whether it counts those operations; this audit retains existing
execution and counts what actually happened. It does not remove terminal
sends or redefine the experiment. Correcting the snapshot does not turn
zero reduction into an adaptive benefit.

## 6. Robust-trained versus ideal-trained evidence

The independently recomputed original **waiting-field proxy** means are
0.0942471910 (ideal) and 0.1530476904 (robust); difference +0.0588004994.
They are not validated per-vehicle trip waiting times (see section 8).

| Master seed | Ideal mean | Robust mean | Robust minus ideal |
|---:|---:|---:|---:|
| 42 | 0.393333 | 0.035111 | -0.358222 |
| 123 | 0.033333 | 0.032444 | -0.000889 |
| 456 | 0.011111 | 0.048444 | +0.037333 |
| 789 | 0.022222 | 0.017778 | -0.004444 |
| 1011 | 0.011236 | 0.631461 | +0.620225 |

These are within-seed means over the original conditions/strategies. Robust
has a lower mean in three of five pairs, but its seed-1011 result dominates
the aggregate disadvantage. Ideal seed 42 is also highly sensitive. Neither
seed may be dropped because it is inconvenient.

The stored paired normal-approximation interval is [-0.250212, 0.367813],
based on five master-seed differences. A separately calculated t(4)
sensitivity interval is [-0.378932, 0.496533]. This latter calculation is
exploratory, still assumption-dependent, and does not replace the original
analysis. Both cross zero; neither supports a reliable ordering of methods.
The paired median difference is -0.000889.

Per nominal condition, robust has a lower mean in four zero-delay/loss cells
and a higher mean in the other 21 cells. At ideal links the means are
0.017803 ideal versus 0.260025 robust. At positive delays and 0–20% loss they
are 0.113358 versus 0.175081; at 30% loss they are 0.113358 versus 0.179526.
These are descriptive cell comparisons, not 25 independent statistical wins.

**Verified training constraints:** 25 episodes x 20 updates = 500 updates
per agent; only 20 updates under each nominal robust condition. Ideal and
robust both use constant epsilon 0.1, learning rate 0.05, discount 0.95,
the same 23-feature representation, reward weights, and fresh initialization.
Robust has one shuffled exposure cycle, not repeated training to convergence.
Twenty of its 25 episodes use positive delays, which all map to the same
decision-time delay class. Freshness is exp(-age/500 ms), so at the first
one-second delayed observation it is about 0.1353 and already marked stale.

Training reward averages are mixed, not converged evidence: robust seed
1011 changes from -0.90 in its first five episodes to -1.16 in its last five;
robust seed 42 improves from -1.22 to -0.56. Ideal seed 456 also worsens.
The logged undiscounted sum of delta rewards telescopes to initial minus
final queue/waiting potential; it does not directly measure integrated
traffic delay. The learner's discounted objective is different again.

**Hypotheses requiring validation:** inadequate training exposure, sensitivity
to condition order, representational limitations of a linear model, and the
short-horizon reward/scenario may contribute to seed instability. The current
evidence cannot identify their individual causal contributions. Longer
training might help or fail; it must not be promised to improve performance.

## 7. Software defects and their impact

| Finding | Evidence / affected claims | Audit disposition |
|---|---|---|
| Channel telemetry one round behind | Live trace: reported 160 versus actual 168; delayed/dropped fields can lag. Affects communication-aware absolute cost/delivery statistics. | Fixed with three regression cases; original records preserved. Traffic policies, rewards and zero-suppression finding unchanged. |
| Waiting-time definition/label mismatch | Collector sums current consecutive-wait snapshots and divides by vehicle observations. It is not cumulative per-vehicle waiting. | Documented; no silent metric replacement. Corrected traffic-metric experiments need an agreed definition. |
| Unsafe campaign identity/resume | Same IDs after changing horizon/scheduler; checkpoint reuse checks only episode count. | Verified identity collision; hardening required before a new campaign. No missing/duplicate IDs in original data. |
| Retry handling | Source inspection: `--retry-failed` reruns successful records too; retry records get new IDs, while analysis aggregates all successes and retains original failures. | Latent runner defect; no retry records observed in the original 755. Do not use it for a follow-up until corrected. |
| Environment reset telemetry | A reset/step/reset probe gives 8 then 24 channel attempts; scheduler resets but channel counters/RNG do not. | Lifecycle hazard, not evidence invalidating this campaign, which constructs new environments per episode. |

Other provenance/configuration issues are documented in section 4. Nondefault
freshness values are passed to the environment but not to newly constructed
learners' checkpoint metadata; current campaign defaults agree, so that
latent mismatch does not explain its results. No learner-update or broken
adaptive-trigger defect was found in the inspected execution paths.

## 8. Methodological limitations

**Traffic measurement is the highest-priority issue.** The collector computes
`sum_t sum_present_vehicles getWaitingTime(v,t) * step_length`, then divides
by `sum_t number_of_present_vehicles`. SUMO defines `getWaitingTime` as
consecutive stopped time, resetting when movement resumes; it is not a
vehicle's total trip waiting time. See the official
[TraCI vehicle retrieval documentation](https://sumo.dlr.de/docs/TraCI/Vehicle_Value_Retrieval.html).
A three-second continuous wait contributes 1+2+3=6 at one-second snapshots,
not three seconds. Multiplication by timestep without a corresponding
time-weighted denominator also makes the average definition inconsistent
when timestep changes. Existing tests did not check these metric semantics.

In a seed-42, ideal-trained, 100 ms trace, the stored proxy is 44/90 =
0.488889 while only 13 vehicle-seconds have positive consecutive waiting.
The latter is a diagnostic within-horizon measurement, not a new approved
primary metric or complete trip estimate. Full trajectory/tripinfo data are
not retained in the original raw summaries, so a corrected trip metric
cannot be recovered by simply renaming or rescaling every original value.

**Short scenario:** six scheduled vehicles, four junctions with 100 m spacing,
20 seconds of evaluation despite a 40-second SUMO configuration. All 755
records have zero completed trips. There is no warm-up, steady-state demand,
trip-completion evaluation, or measured travel-time comparison. This is a
functional small-network campaign with severe horizon censoring. Tiny proxy
values do not establish that drivers experience negligible waiting.

Routes/departures are fixed and `sigma=0`, but the simulation is not entirely
seed-invariant: default speed-factor variation remains. Live speed factors
ranged, for example, from 0.8694 to 1.0428 in seed 42. SUMO documents this
[default speed distribution](https://sumo.dlr.de/docs/Simulation/Randomness.html).
The evaluation seed controls real simulator variation, but the five seeds do
not represent five different demand patterns.

**Delay resolution:** channel scheduling is causal, but reception and policy
decisions occur only at integer seconds. Every delay in {100,250,500,1000}
ms therefore first becomes usable at the next decision. All matched positive
delay results are exactly identical across the inspected traffic/age/channel
fields, and 100 versus 1000 ms diagnostic traces have identical observations
and actions. The 25 nominal cells contain only ten effective loss x
decision-delay combinations. The aggregate weights delayed behavior four
times as heavily as zero-delay behavior. This is a configuration/integration
resolution limitation, not evidence of an insensitive delay model.

**Baseline fairness:** common network, horizon, evaluation seeds, action,
reward, and number of updates are strengths. But local-only training uses
epsilon `max(0.1,0.95**episode)` (1.0 down to about 0.292), whereas both
communication policies use 0.1 throughout; training SUMO seed schedules also
differ. The local-only average proxy is 0.011111. It is a useful reference,
not an isolated communication-feature ablation. It needs no impairment
matrix because its policy does not consume messages.

**Missing comparisons:** ideal and robust communication policies both already
have freshness/availability/stale features. This isolates training exposure,
not the benefit of the robustness mechanism. There is no communication-aware
non-freshness baseline, age/availability/stale-handling component ablation,
or held-out impairment evaluation. Robust training sees all 25 test condition
labels. Evaluation seeds are separated, but H6/RQ6 unseen-condition
generalization is not tested. These gaps matter under PROJECT_SPEC sections
26, 32, 33, and Phase 11; absence must not be presented as completion.

**Statistics:** the robust-versus-ideal code correctly aggregates within
training seed before pairing. The three strategies are identical repeated
outcomes, not additional independent evidence. Strategy comparisons pool two
policy families as ten policy-seed units, despite five shared master seeds;
future inference should report families separately or account for that
dependence. Five pairs, one evaluation traffic/loss stream per checkpoint,
normal intervals, heterogeneous seed outcomes, and no multiplicity correction
limit inference. There are no reported adjusted p-values or family-wise
tests. Descriptive results are permissible; a significance/superiority claim
across the 25 cells is not. Relative degradation is unstable near a small
ideal proxy and undefined at zero.

**Signal realism:** actions jump directly between green phases, bypassing
the three-second yellow phases; no minimum green/all-red enforcement exists.
Some replay runs emitted emergency-braking/red-light-stop warnings. Collision
handling is configured as `none`. These simplify the controller and limit
traffic realism; changing them would require a documented protocol revision
and affected retraining/evaluation, not a silent audit fix.

## 9. Tests and checks actually executed

| Check | Observed result |
|---|---|
| Original `python -m pytest -q` | 65 passed, 4.32 seconds; no skips |
| `python -m compileall -q src scripts tests` | Passed before and after correction |
| Phase 4–8 communication/freshness smoke scripts | Exit 0; expected delivery/loss/delay/cache checks |
| Phase 9 training smoke | Exit 0; two two-step episodes per variant, temporary checkpoints |
| Phase 10 scheduler smoke | Exit 0; change, heartbeat, and suppression checks true |
| New targeted regression before fix | All three cases failed on stale telemetry |
| Full Phase 8 tests after fix | 11 passed |
| Full suite after fix | 68 passed, 5.92 seconds; no skips |
| Data/checkpoint audit | Exact 755-run coverage; 60 valid model files; 15 training logs |
| Stored analysis recomputation | All 151 summaries and six comparisons matched exactly |
| Original bounded replay | Five 20-step evaluations reproduced recorded results except Git hash |
| Diagnostic policy traces | Five 20-step episodes; frozen weights; real message action influence |
| Corrected bounded replay | Five separate episodes; only channel telemetry fields changed |
| Artifact preservation | All 870 original file hashes matched after validation |

No production training or full matrix rerun was performed. No assertion of
historical successful compilation is needed: compilation was executed during
this audit. Smoke success establishes functional behavior, not research
quality. Warnings during replay were retained in the audit account above.

## 10. Corrective actions ranked by scientific importance

1. Agree the primary waiting metric, denominator, horizon, and handling of
   unfinished trips. Add synthetic metric tests and trip-level validation.
   Preserve the old proxy under its original experiment identity. Do not
   reinterpret its numerical values as corrected measurements.
2. Resolve decision/delay granularity before interpreting the delay sweep.
   Validate distinct observation ages at each intended delay while maintaining
   a consistent control interval; a subsecond communications implementation
   alone cannot make decisions observe distinctions they never sample.
3. Write and commit a versioned follow-up protocol with full configuration,
   source/environment/checkpoint hashes and timestamps before execution.
   Repair resume/retry identity and protect original output paths. Back up
   original artifacts separately. The telemetry snapshot fix is already done.
4. Restore the missing controlled comparison: communication-aware baseline
   versus freshness mechanism with matched training settings; explicit
   component ablations and predeclared held-out impairments. Keep the existing
   IQL model and small network; no new algorithm is necessary.
5. Determine a defensible training budget using separate development seeds
   and learning curves, then freeze it. Match exploration schedules and
   record per-episode rewards, traffic metrics, seed streams, and exposure.
   More episodes alone are not a justified cure for the current limitations.
6. For adaptive communication, choose a small predeclared set of intervals
   longer than the decision step (for example 2 s and 5 s) and justify
   thresholds on development traces. Evaluate both traffic and real message
   cost. These examples are exploratory candidates, not approved final
   settings or parameters selected to obtain a favorable result.
7. Use matched independent training seeds, more than one evaluation stream
   per frozen checkpoint where practical, and seed-level uncertainty.
   Predefine primary contrasts; handle multiplicity for confirmatory cell
   claims. Do not count duplicated strategies/delays as replication.

## 11. Is another controlled experiment necessary?

**Yes, to answer the intended research questions with the specified metrics
and comparisons.** A new campaign is not required merely to report the old
mixed findings honestly, and a repeat of all 755 current settings would not
resolve the defects in design.

A focused sequence is recommended: first validate the metric, timing and
provenance contract using a few frozen diagnostic episodes; then approve a
small-network follow-up protocol that fixes these limitations, matches
baselines, includes essential ablations/held-out conditions, and chooses the
budget on independent development data. Reserve new evaluation seeds and
predeclare analysis before running it. Measure adaptive suppression only
after the base traffic measurement is defensible. Preserve failures and all
seeds. Do not call post-audit tuning an independent confirmation of the
original final test.

Changing the primary metric or experimental protocol after substantial runs
requires human confirmation under AGENTS.md section 13, which explicitly
lists "Changing the primary evaluation metrics" and "Changing the
experimental protocol after substantial experiments have already been run."
No such change or follow-up campaign was authorized/executed by this audit.

## 12. Phase 12 decision and audit artifacts

**Not ready to proceed as though Phase 11's full research acceptance criteria
are satisfied.** The software foundation works, the original records are
real and accessible, and the unfavorable aggregate must remain in the
research record. However, the current evidence cannot support per-vehicle
waiting claims, a resolved multi-level delay effect, mechanism attribution,
adaptive savings, or unseen-condition generalization. Phase 12 remains
unstarted pending the user's decision on the focused follow-up protocol.

Only one runtime behavior was corrected: returned channel telemetry now
matches the completed communication round. Regression tests and current
status documentation were added. No checkpoint, original result, research
question, reward, traffic metric implementation, signal policy, or experiment
configuration was changed.

Local evidence (ignored, separate from original results):

- [Original SHA-256 manifest](../results/phase11_audit_v1/phase11_original_sha256.json)
- [Independent data and per-condition analysis](../results/phase11_audit_v1/phase11_audit_evidence.json)
- [Original replays and observation/action traces](../results/phase11_audit_v1/phase11_replay_evidence.json)
- [Corrected replay differences](../results/phase11_audit_v1/correction_validation.json)
- [Stored analysis verification](../results/phase11_audit_v1/stored_analysis_validation.json)
- Corrected raw episodes: `results/phase11_audit_v1/corrected_replays/`.

Corrected validation records retain the original run ID for association only,
live in a separate directory, and contain audit timestamp, source-file
SHA-256, and a modified-working-tree marker. They are not merged into the
old summaries. The original record's commit identity remains untouched.
