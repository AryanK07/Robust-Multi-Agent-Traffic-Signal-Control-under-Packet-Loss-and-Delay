# Follow-up v2 development pilot

Date: 2026-11-13, Asia/Calcutta. Experiment: `followup_v2/development_001`.
Source frozen before collection: `eada4cdc26ac7ca07791b4e48e1f1d7ab2ad3209`.
Campaign identity: `3af3cf17ffa75c9959afd57e94f65cc40ce6b711159f4e7f4a33eeb550db2087`.

**Outcome:** the corrected pipeline and action-sensitive communication execute
successfully. The four-episode frozen policies do not provide adequate traffic
control. All 50 evaluation episodes have unfinished trips. This pilot does not
establish convergence, traffic benefit, generalization, novelty or superiority.
Phase 12 remains unstarted.

## Scope and reproducibility

The user selected action-sensitive communication within existing linear IQL.
The [protocol](FOLLOWUP_PROTOCOL.md) records the authorized changes and related
work. Original Phase 11 results remain separate; all 870 original files match
the pre-correction SHA-256 manifest. New waiting values use `tripinfo_v2` and
must not be pooled with the original snapshot proxy.

The pilot used master seeds 20261 and 20262, five variants, four training
episodes each, and 50 frozen evaluations: 10 checkpoint sets, 40 training
episodes, 90 SUMO episodes total. No execution failures occurred. All 40
training episodes completed 20/20 trips; all 50 greedy evaluation episodes
were horizon-censored. An execution success means the episode ran and its
artifacts were saved; it does not mean the controller performed well.

Training epsilon was 0.2; evaluation epsilon was zero and weights/biases were
asserted unchanged. Learning rate was 0.01 and discount 0.95 for every variant.
Robust training used the first four entries of a seeded shuffled nine-condition
cycle, not complete coverage. Evaluation conditions were (loss, delay ms)
(0,0), (0.1,250), and held-out (0.3,1000). Traffic and loss streams were
separated from training, with identical demand paired across evaluated methods.
All training starts were fresh; each strategy reused the corresponding full
robust checkpoint. Local-only was run once per master seed because its inputs
and actions have no channel dependence.

The existing four-junction network was retained. Each episode had 20 vehicles,
seeded departures over 30 seconds, a 120-second horizon, 50 ms simulation
ticks, 100 ms communication opportunities, and one-second decisions. Green
holds were at least five seconds and yellow lasted three seconds. This is
simulator validation, not road-safety certification.

## Measured traffic results

The following means use the fixed pilot cells, with equal weighting within
master seed. There are only **two independent master seeds**; six condition
runs are not six independent training replicates. Waiting includes accumulated
waiting of unfinished vehicles up to 120 seconds. These are censored values,
not estimated waiting until eventual completion. Every evaluation inserted all
20 vehicles; completion fractions below therefore represent unfinished trips.

| Policy (always-transmit where applicable) | Evaluations | Waiting to horizon (s/vehicle) | Trips completed |
|---|---:|---:|---:|
| Local only | 2 | 59.8787 | 37.5% |
| Plain communication, ideal training | 6 | 54.6921 | 37.5% |
| Plain communication, robust training | 6 | 55.6221 | 40.0% |
| Freshness, ideal training | 6 | 47.7575 | 50.0% |
| Freshness, robust training | 6 | 61.1775 | 37.5% |

The full robust-minus-full ideal paired waiting difference was +13.4200 seconds
per vehicle. The two seed differences were +21.8550 and +4.9850 seconds.
The descriptive seed-level 95% t interval was [-93.7568, 120.5968] seconds.
With two seeds and censoring this is not persuasive evidence for a population
ranking. The plain robust comparison also does not support a general claim
that impairment training helps. All methods need adequate greedy-policy
validation before a final comparison.

## Measured communication trade-off

Each row below averages the same six seed-condition cells. Both request and
response attempts count, including packets subsequently dropped. Reduction is
relative to always-transmit at the new 100 ms opportunity interval; it is not
comparable to the old 160-message report.

| Strategy (same full robust checkpoint) | Mean packet attempts | Reduction vs always | Waiting to horizon (s/vehicle) | Trips completed |
|---|---:|---:|---:|---:|
| always | 9600.00 | 0.00% | 61.1775 | 37.5% |
| periodic | 960.00 | 90.00% | 61.1775 | 37.5% |
| adaptive | 206.00 | 97.85% | 61.1775 | 37.5% |
| periodic_pull | 1797.67 | 81.27% | 61.1775 | 37.5% |
| action_sensitive | 564.67 | 94.12% | 61.1775 | 37.5% |

Action-sensitive requests used fewer attempts than periodic pull in every
matched pilot cell. Their mean difference was -1233.0 attempts; the two
seed-average differences were -1433.33 and -1032.67. This isolates the margin
gate from the request/response protocol more directly than comparison to push
alone. It does **not** establish an overall improvement: state-change adaptive
push used fewer messages than action-sensitive pull in this pilot, and traffic
outcomes were identical across the five strategies within each seed-condition.
Identical observed traffic results are not an equivalence proof.

For seed 20261 the full robust controller made zero accepted signal switches,
completed only 5/20 trips, and all 4800 gate checks per episode were invariant.
Its requests came only from initialization and heartbeat. For seed 20262 the
same variant made 30 accepted switches and completed 10/20 trips; requests
also included margin triggers. Savings under weak or insensitive controllers
are not evidence that communication is unnecessary for competent control.

## Interpretation: facts, hypotheses and limits

**Verified:** messages traverse the real channel; both pull legs incur loss
and delay; counter identities reconcile; the gate suppresses requests; policies
stay frozen; traffic demand is paired; raw tripinfo reproduces all 90 episode
metric records. Time-resolution tests distinguish 100, 250, 500 and 1000 ms
message ages. These observations establish implementation behavior.

**Hypotheses requiring validation:** insufficient training and the loss of
exploration at evaluation contribute to poor greedy control. Four-episode
training curves fluctuate and do not establish convergence. No inference here
identifies a uniquely responsible learning parameter. Robust exposure divides
an already small budget among conditions. A conservative box certificate can
request when a real action change is impossible; that is a design limitation,
not a promise that every request is useful.

The certificate is exact for the current two-action linear Q model over the
declared box with local features fixed. It is not a guarantee about future
local states, optimal actions, closed-loop traffic performance, or signal
safety. Signal eligibility also depends on an internal minimum-green timer
not included in the five local observations, so the learner has partial
observability. This should be considered explicitly in future design work,
not silently changed in this completed pilot.

Only three impairment cells and five variants were collected. Component
ablations and all 25 conditions are implemented/configured but not empirically
completed in v2. A single evaluation traffic stream per master seed, small
network, fixed delays, low demand, horizon censoring, and correlated conditions
limit inference. Descriptive intervals are not multiplicity-adjusted tests;
zero observed paired variance does not prove equivalence. The larger default
configuration remains exploratory and includes development seeds; it is not
an untouched confirmatory test set.

Selective/event-triggered communication already exists in the literature.
The candidate contribution is an interpretable action-invariance gate with
causal request/response costs under loss and delay. The
[literature positioning](FOLLOWUP_PROTOCOL.md#literature-positioning-checked-2026-11-13)
records primary sources and the limits of the search. No final novelty claim
has been made.

## Validation actually executed

- Full suite: **93 passed**; Python compilation and Git whitespace checks passed.
- All 90 saved tripinfo files independently reproduced their episode metrics.
- All 40 new checkpoint hashes and all 34 recorded source-file hashes matched.
- All 50 expected evaluation identities matched the frozen design exactly.
- Paired demand hashes, separate train/evaluation demand, and communication
  accounting were verified.
- Reissuing the completed pilot resumed without launching new episodes;
  all 421 manifest/raw/artifact files retained identical hashes.
- All 870 original Phase 11 files remained unchanged.

The compact, generated [summary](results/followup_development_001_summary.json),
[resolved manifest](results/followup_development_001_manifest.json), and
[integrity record](results/followup_development_001_integrity.json) are committed
so this outcome is reviewable without the local experiment directory. They
are deliberately selected small research artifacts. Complete raw tripinfo,
training histories and checkpoints remain locally under
`results/followup_v2/development_001/`, ignored by Git. A fresh clone cannot
reanalyse absent raw files; an independently backed-up research archive is
still required. Hash manifests do not constitute an off-machine backup.

## Ranked next actions and Phase 12 decision

1. **Validate greedy control and training budget on development data.** Use a
   separately versioned, predeclared budget study with complete robust-condition
   cycles and frozen validation at checkpoints. Compare matched local/plain/full
   policies, waiting, trip completion, accepted switching, rewards and TD-error
   curves. Choose stopping/budget criteria before running it; do not pick a
   favorable seed or tune against a later confirmatory test. Do not assume
   that simply increasing episodes will resolve function-approximation issues.
2. **Establish the communication trade-off on competent checkpoints.** Retain
   periodic push, state-change push and periodic pull controls, both-leg packet
   accounting, feature ablations, and paired conditions. Investigate negative
   savings or unhelpful requests as results rather than hiding them.
3. **Freeze a confirmatory protocol only after development validation.** Use
   fresh reserved evaluation streams, enough independent training seeds for
   the intended uncertainty, all required cells, explicit held-outs and a
   prespecified multiplicity strategy if formal tests are planned. Archive
   raw outputs and environment requirements independently.
4. **Broaden literature comparison before claiming novelty.** Compare the
   exact linear certificate and loss/delay accounting to established event
   triggering and value-of-information communication.

An additional controlled development experiment is necessary. The software
extension and bounded pilot are complete; the final research evaluation is
not. Do not start Phase 12 as a finalized-results paper yet. No long training
campaign or full v2 matrix was run in this task.
