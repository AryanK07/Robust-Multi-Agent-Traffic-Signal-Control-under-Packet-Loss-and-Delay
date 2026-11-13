# Predeclared traffic-completion training comparison

2026-11-13. `training_validation_003` completed its 896 SUMO episodes with
zero execution failures, but the unchanged all-cell 95% criterion failed.
At 81 episodes, phase-relative local policies completed all validation trips;
full ideal/robust policies remained at 25–50% in several cells. Those raw
outputs and their source (`094b1f1`) are retained.

Raw tripinfo from all 810 training episodes shows all 20 vehicles arrived,
with mean last arrival at 86.7115 seconds. The existing training loop still
updates until 120 seconds: on average 33.2885 seconds of empty-network
updates. Constant availability/freshness features remain active during that
tail. Whether this contributes to poor fitted policies is a hypothesis.

## Single changed training rule

In `configs/training_validation_v4.yaml`, enable `training_stop_when_clear`.
Once SUMO reports no active **or future scheduled** vehicles, mark the last
transition terminal and end the training episode. Do not bootstrap its target
from the empty state. The maximum horizon remains 120 seconds. Evaluation
always retains the full 120 seconds, ensuring the same communication-cost
measurement window across methods. Every baseline/proposed variant receives
the same training termination rule. It is a documented development protocol
change, not a repair to stored results.

All other settings match the phase-relative comparison: five variants,
development seeds 31001/31002, 81 episodes, validation at 9/27/81, unchanged
epsilon/learning-rate/discount/reward/demand/signal rules and validation
streams. The original aggregate, phase-relative-only and completion-terminated
studies remain separately identified. No final test seeds are used.

Retain the 95%-completion-in-every-validation-cell criterion at episode 81.
Report every checkpoint and failure. Do not select a different budget or
individual seed after seeing results. This checks training termination, not
formal convergence. A failure remains a limitation requiring explicit
disposition before a final campaign.

```powershell
python scripts/run_followup.py --mode run --config configs/training_validation_v4.yaml --output results/followup_v2/training_validation_004
```
