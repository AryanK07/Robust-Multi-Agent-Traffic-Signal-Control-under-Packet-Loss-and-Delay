# Phase-relative observation development comparison

Predeclared 2026-11-13 before collecting this treatment. This is a documented
development revision following the user's request to complete Phase 11
prerequisites, not a relabeling of the original or v2 campaigns.

## Evidence and change

At episode 81 of the frozen aggregate-observation study, seed 31001 local
validation completed 60% of trips in both cells and full robust completed
70%/90%. Thus the predeclared all-cell 95% feasibility criterion already
failed; the entire fixed study is still retained, including remaining seeds.
Inspection finds a structural ambiguity: summing both approach queues hides
whether stopped traffic has green or red. Minimum-green/yellow timing is
also hidden. This does not establish the unique cause of poor learning.

Add an independently selectable `phase_relative_observation_v3` encoder:

1. Served-approach queue / 10.
2. Opposing-approach queue / 10.
3. Served-approach vehicle count / 20.
4. Opposing-approach vehicle count / 20.
5. Transition clock: [0,0.5) through yellow; [0.5,1] through minimum green;
   1 means switching is eligible.

All coordinates are clipped to [0,1]. Served/opposing sets are derived from
the actual SUMO controlled links and green-phase states, not hardcoded lane
names. Their ordering rotates only when yellow completes. The encoder rejects
networks whose two green lane groups overlap or fail to cover controlled lanes.
The same five values are communicated, with a distinct message schema. Caches
and evaluation metadata reject mismatched feature semantics. The old encoder
and old checkpoints remain available unchanged.

This changes the state representation and therefore requires fresh training.
It is not a new MARL algorithm. All baseline/proposed variants share this
change within the new comparison, preserving attribution of freshness and
communication effects. It remains a partial traffic observation, not a claim
of full Markov state reconstruction.

## Fixed comparison

`configs/training_validation_v3.yaml` matches Stage 1: five variants, seeds
31001/31002, 81 training episodes, validation at 9/27/81, same demand, reward,
exploration, learning rate, discount, constraints and validation streams.
Only feature semantics change. Four isolated worker processes are allowed
on the 18-logical-CPU host; concurrency does not alter per-job randomness.
The complete-trajectory backend equivalence test also covers the new schema.

Report all checkpoints and compare paired completion/waiting against the
aggregate-observation development study. Retain the same 95%-in-every-cell
criterion at 81 episodes; do not silently relax it. No parameters will be
tuned during this collection. If feasibility is not met, record the failure
and diagnose it before final protocol selection.

Frozen evaluations also count greedy-action changes when neighbor features
are zeroed at the same observed local state. This diagnostic is an input
intervention, not a trained ablation or proof of communication benefit.

Source is prepared in an isolated worktree while Stage 1 finishes. After
tests, review and commit, run the new study in its own directory:

```powershell
python scripts/run_followup.py --mode run --config configs/training_validation_v3.yaml --output results/followup_v2/training_validation_003
```
