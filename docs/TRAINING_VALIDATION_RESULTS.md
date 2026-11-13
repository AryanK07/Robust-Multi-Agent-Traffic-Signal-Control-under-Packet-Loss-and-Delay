# Aggregate-observation training validation results

Frozen source: `b3a2766aa84ac9c4e15281cae8b6eda40307808c`; 2026-11-13.

All 10 training jobs, 810 training episodes, 60 frozen validation episodes and
26 final exploratory evaluation episodes completed; zero recorded execution
failures. This is development data, not a confirmatory campaign.

| Variant | Seed | Episodes | Ideal completion | 10% / 250 ms completion |
|---|---:|---:|---:|---:|
| full_ideal | 31001 | 9 | 25% | 25% |
| full_ideal | 31001 | 27 | 50% | 25% |
| full_ideal | 31001 | 81 | 100% | 100% |
| full_ideal | 31002 | 9 | 25% | 25% |
| full_ideal | 31002 | 27 | 25% | 25% |
| full_ideal | 31002 | 81 | 25% | 45% |
| full_robust | 31001 | 9 | 25% | 25% |
| full_robust | 31001 | 27 | 50% | 50% |
| full_robust | 31001 | 81 | 70% | 90% |
| full_robust | 31002 | 9 | 25% | 25% |
| full_robust | 31002 | 27 | 50% | 50% |
| full_robust | 31002 | 81 | 65% | 65% |
| local | 31001 | 9 | 50% | 50% |
| local | 31001 | 27 | 25% | 25% |
| local | 31001 | 81 | 60% | 60% |
| local | 31002 | 9 | 25% | 25% |
| local | 31002 | 27 | 100% | 100% |
| local | 31002 | 81 | 100% | 100% |
| plain_ideal | 31001 | 9 | 75% | 75% |
| plain_ideal | 31001 | 27 | 50% | 50% |
| plain_ideal | 31001 | 81 | 95% | 90% |
| plain_ideal | 31002 | 9 | 75% | 75% |
| plain_ideal | 31002 | 27 | 65% | 65% |
| plain_ideal | 31002 | 81 | 100% | 100% |
| plain_robust | 31001 | 9 | 25% | 25% |
| plain_robust | 31001 | 27 | 50% | 50% |
| plain_robust | 31001 | 81 | 95% | 95% |
| plain_robust | 31002 | 9 | 50% | 50% |
| plain_robust | 31002 | 27 | 95% | 90% |
| plain_robust | 31002 | 81 | 90% | 100% |

The predeclared requirement (95% in every cell at 81 episodes) failed.
Increasing training alone did not reliably resolve greedy-policy starvation.
Some variants/seeds improved, while others remained poor or deteriorated.
These observations justify the separately predeclared phase-relative encoder
comparison; they do not establish a unique causal explanation or convergence.

Raw data remain under `results/followup_v2/training_validation_001/`.
The original Phase 11 campaign and earlier v2 pilot remain unchanged.
