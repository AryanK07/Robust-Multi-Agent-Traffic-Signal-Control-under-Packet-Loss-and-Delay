# Phase 11 independent audit and follow-up disposition

This report completes the audit requested before Phase 12. It distinguishes
the original campaign, subsequent development studies and the separately
frozen reserved-seed evaluation. Phase 12 and paper drafting remain unstarted.
The [initial audit](PHASE11_AUDIT.md) remains a dated record; its then-pending
actions are assessed here rather than silently rewritten.

## 1. Verified project state

The starting repository was the existing project at `4161f42`, not a new
implementation. Original phases 0–11, source, tests and local research data
were accessible. The accepted extension retains linear Independent Q-Learning,
the four-junction SUMO network, project title, research questions and H1–H6.
It adds an interpretable action-sensitive communication candidate and the
controls needed to evaluate it. No neural model or stochastic delay model was
introduced. The reserved campaign source/configuration is frozen at `c9547d6`.

## 2. Repository and experimental-data accessibility

The original 870 files include 755 evaluation records and 15 checkpoint sets.
Their hashes were independently checked against the initial audit inventory;
none changed. The 421-file development-pilot snapshot also matches its saved
hashes. Ignored local data were not inferred from the user's summary.
All follow-up studies have separate versioned directories. The complete
research archive includes original, corrected, unsuccessful development and
reserved-seed records with a per-file SHA-256 inventory and source history.
See [archive and restoration instructions](RESEARCH_ARCHIVE.md).

## 3. Architecture

SUMO provides lane state and tripinfo; a phase-relative encoder distinguishes
served/opposed demand and exposes signal-transition timing. Four independent
linear Q policies choose keep/switch actions, constrained by minimum green and
yellow transitions. A separate channel applies Bernoulli packet loss and fixed
delay. Timestamped neighbor caches provide optional availability, age,
freshness decay and stale features. Training, frozen evaluation, immutable
artifact storage, independent audits and derived analysis are separate layers.

The action-sensitive receiver holds local features fixed and computes the
minimum chosen-minus-alternative linear Q margin over the joint neighbor
feature box. A positive bound certifies only invariance of this fitted model's
current action over that box. Otherwise it can request influential neighbor
information subject to cooldown/heartbeat. Requests and responses both incur
loss, delay and packet cost. Periodic pull controls for the request protocol;
always, periodic push and state-change adaptive are additional controls.
The bound is conservative and gives no optimality, safety or return guarantee.

## 4. Reproducibility assessment

Original reported counts and waiting-proxy means were reproduced. Historical
source hashes predate the original evaluation runner; that provenance gap is
preserved, not repaired by editing metadata. The corrected follow-up records
source/configuration/package identities, separate training/evaluation seed
domains, generated demand, per-episode tripinfo, checkpoint hashes and every
attempt. Resume checks use full experiment identity and do not overwrite
completed results. Evaluation is greedy with no weight updates; the runner
asserts that parameters stay unchanged.

The final design uses 81 training episodes (nine complete cycles of the nine
robust training conditions), 20 vehicles, 120-second evaluation, 50 ms
simulation, 100 ms message opportunities and one-second policy decisions.
All 25 loss/delay conditions are tested. Loss 0.3 or delay 1000 ms defines nine
extreme held-out cells. The local baseline uses matched training settings and
one evaluation per seed; it is not duplicated into 25 fictitious replicates.

## 5. Why the original adaptive reduction was zero

This was predominantly the configured timing, plus a reporting defect.
Periodic and maximum-silence intervals were both one second, equal to the
communication opportunity/decision interval. Each opportunity therefore
satisfied periodic or heartbeat transmission, independently of the change
threshold. Zero suppression was expected under those settings; it did not
prove that the scheduler or policy integration was broken.

The returned channel snapshot was captured before the final communication
round: 160 reported attempts versus 168 actually executed. A minimal fix and
three regression tests corrected the snapshot. Five separate frozen replays
changed that counter while preserving traffic outputs and suppression.
The original results were not overwritten. Follow-up communication timing and
measurement windows were explicitly redesigned and both pull legs are counted.

## 6. Robust-trained versus ideal-trained performance

The original mean waiting proxies were 0.0942471910 and 0.1530476904 seconds,
respectively. These are consecutive-wait snapshots, not accumulated waiting
per vehicle; all 20-second original evaluations completed zero trips. Five
paired seeds, 25 training episodes and one balanced impairment cycle do not
establish convergence or a reliable training-regime advantage. The audited
paired uncertainty crossed zero. Robust training is not guaranteed to help.

Development evidence did not support simply assuming that more episodes would
solve the problem. A predeclared 9/27/81-episode study failed its all-cell 95%
completion criterion. Phase-relative observations improved the local control
but full models remained poor. Removing empty-network training updates still
did not make every full model usable. A finite calibration scaled only the
four freshness metadata coordinates per neighbor by 0.1 or 0.01; both passed
all eight episode-81 development validation cells. The predeclared rule chose
the largest passing scale, 0.1, without choosing by final waiting results.

These are measured development comparisons. Feature conditioning and empty
state updates are plausible contributors, not a proven complete causal account
of learning behavior. Two development seeds and a passed finite criterion do
not prove generalization or convergence. Final seeds were reserved separately;
their outcomes cannot trigger checkpoint replacement or parameter retuning.

All development records passed independent integrity checks; counts below are
actual executed episodes, not planned budgets. "Censored" means unfinished
traffic at the horizon and is separate from an execution failure.

| Development campaign | Training | Validation | Exploratory evaluation | Censored validation/evaluation | Execution failures |
|---|---:|---:|---:|---:|---:|
| `development_001` | 40 | 0 | 50 | 0 / 50 | 0 |
| `training_validation_001` | 810 | 60 | 26 | 51 / 20 | 0 |
| `training_validation_003` | 810 | 60 | 26 | 43 / 15 | 0 |
| `training_validation_004` | 810 | 60 | 26 | 40 / 10 | 0 |
| `metadata_calibration_01` | 324 | 24 | 12 | 8 / 1 | 0 |
| `metadata_calibration_001` | 324 | 24 | 12 | 8 / 0 | 0 |

The calibration validation counts include the unsuccessful 9/27-episode
checkpoints; all eight selected 81-episode cells passed at both scales.
[Machine-generated integrity records](results/development_integrity_audits.json)
retain exact source identities and checkpoint/source verification counts.

## 7. Software defects and corrections

- Corrected the legacy post-step channel snapshot; affected transmission
  telemetry, not the original traffic trajectories.
- Reset channel counters and RNG for reusable environments; the original
  final runner created fresh environments and was unaffected by that issue.
- Tested fixed-delay delivery boundaries and timestamp ordering, including
  subsecond floating-point boundaries.
- Introduced a separate tripinfo metric schema, time-resolved communication,
  constrained signal transitions and full experiment identity safeguards.
  These address design/measurement limitations without relabeling old numbers.
- Added observation-schema and checkpoint-metadata compatibility checks,
  finite-parameter checks and bounds matching the actual metadata scale.

The larger training horizon, phase-relative encoding, training termination and
metadata calibration are documented methodological changes in development,
not retroactive bug fixes that invalidate or erase unfavorable observations.

## 8. Methodological limitations and contribution scope

The study remains a small, lightly loaded four-junction scenario with fixed
delay and five independent final training seeds. There is one paired traffic
stream per final seed; repeated impairment cells are not independent samples.
Unfinished vehicles contribute waiting only until the horizon, so waiting must
be interpreted jointly with completion. Completed-trip travel time is subject
to survivor selection when trips remain unfinished. Packet counts include
requests/responses; JSON payload bytes are not full wireless wire overhead.
All strategies are measured over the same 120 seconds, including any empty
network tail after the last arrival. Reported savings are whole-episode costs,
not isolated savings during active traffic; the final campaign does not store
an independent active-traffic-only communication total.

The 13 prespecified comparisons use one paired effect per master seed and Holm
correction. With five seeds the minimum exact two-sided sign-flip p is 0.0625;
no rejection at 0.05 is possible. Descriptive t intervals are not simultaneous
or noninferiority bounds. Matched averages do not establish equivalence.
The zero-neighbor diagnostic tests immediate action sensitivity at encountered
states; it is not a separately trained no-communication ablation or a causal
estimate of long-horizon value.
The ablations remove encoder components, not every correlated source of that
information: for example, removing the explicit age coordinate leaves freshness
and stale clues. The no-decay condition removes payload decay and its freshness
coordinate together. Interpret these as the declared component comparisons.

[Verified literature positioning](LITERATURE_POSITIONING.md) identifies close
predecessors, notably VBC's action-gap request gating and CroMAC's certified
communication reasoning. Selective communication and action-value margins are
not new claims here. The contribution under investigation is the transparent
linear joint-box check with explicit impaired request/response accounting and
controlled small-network evaluation. Novelty or superiority remains unclaimed.

## 9. Executed validation

The original 65-test suite passed during the audit; the telemetry correction
expanded it to 68 passing tests. Communication smoke checks for phases 4–10,
compile checks, five original replays and five separate corrected replays were
executed. The completed extension's full suite passed **106 tests**. It includes
real SUMO trajectories, equality between TraCI and libsumo backends, frozen
validation RNG isolation, signal/communication timing, action bounds, terminal
updates, feature schemas, exact statistics and archive restoration/corruption.
Compilation passed. This is executed validation, not a retrospective claim
about checks in the previous development session.

Every complete follow-up is audited against exact design coverage, recomputed
tripinfo metrics, source/checkpoint hashes, paired demand, separated seed
domains, training schedules and channel accounting. Generated figures and
tables come from stored data. The archive is independently hash-checked.

## 10. Actions ranked by scientific importance

1. Preserve and report every final seed and censored episode, including weak
   controllers; do not tune on the reserved data.
2. Base conclusions on completion and waiting together, seed-level uncertainty
   and the prespecified comparisons. Avoid claims of equivalence or superiority.
3. Use the exact frozen source and versioned archive for reproducibility;
   distinguish the original proxy from the follow-up trip-level metric.
4. State the candidate's relationship to established action-gap gating and
   certification. Obtain a broader literature/venue assessment before any
   final novelty or publication-readiness claim.
5. If stronger external-validity or efficacy claims are later required,
   predeclare additional demand scenarios and independent seeds as a new study.
   They are not retroactive additions to this final test.

## 11. Additional controlled experiment

The focused follow-up required by the initial audit has been implemented and
run under separate development and reserved-seed protocols. No further tuning
is justified solely to replace an unfavorable final result. A broader study
would be necessary for strong generalization, superiority or practical-use
claims; it is outside the current approved small-network scope.

## 12. Final coverage, findings and Phase 12 decision

The frozen campaign completed **45 checkpoint sets, 3645 training episodes and
1505 evaluations**, with **zero execution failures**. The independent audit
verified all 180 checkpoint files, 73 source/configuration files, exact design
coverage, raw trip metrics, pairing, seed separation and communication counts.
There were **19 censored evaluations**, all full ideal-trained seed 41003.
Every training episode completed its traffic. No failed seed was replaced.

The [generated tables](results/reserved_final_tables.md) and
[machine-readable statistics](results/reserved_final_statistics.json) contain
all method estimates, seed means and 13 planned paired comparisons. Five
figures were generated from raw records and visually checked. Values below
are measured final results, not imported from the original campaign:

- Full ideal-trained mean waiting was **9.84272 s/vehicle**, completion 96.6%;
  full robust-trained was **6.91950 s/vehicle**, completion 100%. The comparison
  does not establish general robust-training superiority. For the prespecified
  nine held-out conditions, robust minus ideal waiting was **-2.3343 seconds**,
  descriptive 95% interval **[-8.5167, 3.8482]**, exact p=0.25, Holm p=1.
- Full robust, local-only, plain ideal and all four full-model ablations had
  the same aggregate waiting, 6.91950 seconds, and 100% completion. Plain robust
  averaged 7.00720 seconds. The full-minus-plain robust contrast was -0.0877
  seconds, interval [-0.2486, 0.0732]. No mechanism advantage is established.
- Full robust packet attempts averaged **9600 always**, **960 periodic push**,
  **339.6 state-change adaptive**, **1793.92 periodic pull**, and **1793.92
  action-sensitive pull**. State-change adaptive reduced whole-episode attempts
  by 96.4625% versus always with identical measured traffic outcomes. This
  observed match is not a formal noninferiority result.
- The action-sensitive candidate provided **zero savings over periodic pull**.
  Its 81.3133% reduction versus always is attributable to the slower pull
  protocol, not an incremental benefit from the gate. All 600,000 receiver
  checks were uncertain; each eligible post-initial request was margin-triggered.
  The full feature box allows large joint neighbor changes, so the conservative
  bound never certified invariance. This is a measured limitation of the
  configured bound/model combination, not evidence of a broken scheduler.
- Communicated inputs did affect some immediate greedy choices: full robust
  always-transmit differed from the same policy with neighbor coordinates
  zeroed in **732 of 60,000 decisions**. That diagnostic is not a trained
  baseline. The matched local policy and communication strategies nonetheless
  produced the same recorded waiting, completion, travel, queue and stop
  metrics. Communication integration is active; useful coordination is not
  demonstrated in this scenario.

| Hypothesis | Evidence-based disposition |
|---|---|
| H1, loss degradation | Not demonstrated by the prespecified plain-ideal contrast; its effect is zero in this scenario. |
| H2, delay degradation | Not demonstrated by the prespecified plain-ideal contrast. Other variants can react differently; no general monotonic claim follows. |
| H3, combined impairment | Neither the plain-ideal combined contrast nor interaction shows degradation. This does not prove impairments harmless elsewhere. |
| H4, freshness robustness | Small descriptive full-versus-plain difference, uncertainty crosses zero; ablations show no observed benefit here. |
| H5, adaptive communication | The simpler state-change rule saves packets with matching recorded traffic; the action gate adds no saving over periodic pull. No general equivalence or superiority claim. |
| H6, unseen-condition robustness | Robust has lower observed waiting than full ideal, but seed-level uncertainty is wide and includes zero. |

All 13 Holm-adjusted p-values equal 1. Learning curves do not demonstrate
convergence. The candidate extension is implemented and evaluated, including
its unfavorable result; it is not an established novel or superior method.

**Disposition:** the implementation, controlled experiments, audits and
analysis are complete. Off-machine archive publication/verification remains
the last technical prerequisite at this report revision. Once that check is
recorded, Phase 12 can begin as documentation of this limited, mixed/negative
small-network study. Strong efficacy, novelty or publication-readiness claims
are unsupported. A separately approved study would be needed for those goals;
no extra tuning or campaign is silently started. **Phase 12 remains unstarted.**
