# Finite metadata calibration before reserved-seed evaluation

Declared 2026-11-13 before collecting these two settings. The completed
termination study (`ac0cf6f`) again failed the full-model usability criterion.
Local/plain variants reached at least 95% in every 81-episode validation
cell; full ideal/robust still failed. Earlier studies remain preserved.

Full observations add availability, age, freshness and stale coordinates
with unit range, whereas typical normalized queues/counts are small. Multiple
nearly constant metadata coordinates can affect conditioning of a linear
TD learner. This is a hypothesis, not an established defect or sole cause.

Evaluate exactly two scales, **0.1 and 0.01**, multiplying only those four
metadata coordinates in each neighbor block. Payload decay and all traffic
features remain unchanged. Use the same phase-relative encoder, completion
termination, seeds 31001/31002, 81 episodes, 9/27/81 validation, reward,
learning rate, discount, epsilon and conditions as the termination study.
Run both full ideal and full robust variants at both settings; do not stop
after a favorable result. Plain metadata coordinates are identically zero
and local-only has no neighbor coordinates, so those controls are unaffected
by this scale. Their matched termination-study results remain references.

Update action-certificate bounds to the actual scaled coordinate range;
otherwise the certificate would be unnecessarily conservative. Store the
scale in configuration and checkpoint metadata and reject incompatible
evaluation loads. The previous default remains 1.0.

Selection rule, fixed before collection: prefer the **largest** scale that
achieves at least 95% completion in every episode-81 validation cell for both
full variants and both development seeds. If neither meets this criterion,
record that failure explicitly; select for characterization by highest worst
cell completion, then highest mean completion, then lowest mean waiting,
then largest scale. This fallback does not satisfy the usability criterion
and cannot be presented as a successful robustness method. Do not expand
this grid or hide failed settings after observing the outcomes.

The selected setting and 81-episode budget will then be frozen for all nine
variants on reserved master seeds 41001–41005, with all 25 impairment cells
and the five communication strategies. Final observations will not trigger
retuning. A negative result is eligible for complete reporting, but not a
claim of traffic improvement, practical usability or publication readiness.
The [analysis plan](FINAL_ANALYSIS_PLAN.md) applies without outcome-dependent
test selection.

Commands (after source/configuration commit):

```powershell
python scripts/run_followup.py --mode run --config configs/metadata_calibration_01.yaml --output results/followup_v2/metadata_calibration_01
python scripts/run_followup.py --mode run --config configs/metadata_calibration_001.yaml --output results/followup_v2/metadata_calibration_001
```
