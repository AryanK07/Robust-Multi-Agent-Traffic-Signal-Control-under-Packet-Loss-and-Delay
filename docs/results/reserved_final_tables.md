# Reserved-seed Phase 11 measured tables

Frozen source: `c9547d6176e4d15520ea9492e6a5088879dfa6fd`.

Values are means ± sample SD across five master-seed means. Each
communicating seed mean averages all 25 conditions; local is evaluated
once per seed. Waiting includes unfinished trips only until the horizon.

| Variant | Strategy | Waiting (s/vehicle) | Completed fraction | Packet attempts |
|---|---|---:|---:|---:|
| full_ideal | always | 9.8427 ± 6.4604 | 0.9660 ± 0.0760 | 9600.0000 ± 0.0000 |
| full_robust | always | 6.9195 ± 0.9238 | 1.0000 ± 0.0000 | 9600.0000 ± 0.0000 |
| full_robust | periodic | 6.9195 ± 0.9238 | 1.0000 ± 0.0000 | 960.0000 ± 0.0000 |
| full_robust | adaptive | 6.9195 ± 0.9238 | 1.0000 ± 0.0000 | 339.6000 ± 8.6487 |
| full_robust | periodic_pull | 6.9195 ± 0.9238 | 1.0000 ± 0.0000 | 1793.9200 ± 5.3900 |
| full_robust | action_sensitive | 6.9195 ± 0.9238 | 1.0000 ± 0.0000 | 1793.9200 ± 5.3900 |
| local | always | 6.9195 ± 0.9238 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| no_age_robust | always | 6.9195 ± 0.9238 | 1.0000 ± 0.0000 | 9600.0000 ± 0.0000 |
| no_availability_robust | always | 6.9195 ± 0.9238 | 1.0000 ± 0.0000 | 9600.0000 ± 0.0000 |
| no_decay_robust | always | 6.9195 ± 0.9238 | 1.0000 ± 0.0000 | 9600.0000 ± 0.0000 |
| no_stale_robust | always | 6.9195 ± 0.9238 | 1.0000 ± 0.0000 | 9600.0000 ± 0.0000 |
| plain_ideal | always | 6.9195 ± 0.9238 | 1.0000 ± 0.0000 | 9600.0000 ± 0.0000 |
| plain_robust | always | 7.0072 ± 0.9765 | 1.0000 ± 0.0000 | 9600.0000 ± 0.0000 |

## Prespecified paired comparisons

One difference per master seed. Intervals are descriptive, not simultaneous
or equivalence bounds. Sign-flip inference assumes exchangeability/symmetry.

| Comparison | Mean difference | Descriptive 95% interval | Exact p | Holm p |
|---|---:|---:|---:|---:|
| loss_only | 0.0000 | [0.0000, 0.0000] | 1.0000 | 1.0000 |
| delay_only | 0.0000 | [0.0000, 0.0000] | 1.0000 | 1.0000 |
| combined | 0.0000 | [0.0000, 0.0000] | 1.0000 | 1.0000 |
| loss_delay_interaction | 0.0000 | [0.0000, 0.0000] | 1.0000 | 1.0000 |
| freshness_same_robust_training | -0.0877 | [-0.2486, 0.0732] | 0.5000 | 1.0000 |
| robust_training_held_out | -2.3343 | [-8.5167, 3.8482] | 0.2500 | 1.0000 |
| action_gate_vs_periodic_pull_average_waiting_time | 0.0000 | [0.0000, 0.0000] | 1.0000 | 1.0000 |
| action_gate_vs_periodic_pull_send_attempts | 0.0000 | [0.0000, 0.0000] | 1.0000 | 1.0000 |
| action_gate_vs_periodic_pull_completion_fraction | 0.0000 | [0.0000, 0.0000] | 1.0000 | 1.0000 |
| no_age_robust_minus_full | 0.0000 | [0.0000, 0.0000] | 1.0000 | 1.0000 |
| no_availability_robust_minus_full | 0.0000 | [0.0000, 0.0000] | 1.0000 | 1.0000 |
| no_decay_robust_minus_full | 0.0000 | [0.0000, 0.0000] | 1.0000 | 1.0000 |
| no_stale_robust_minus_full | 0.0000 | [0.0000, 0.0000] | 1.0000 | 1.0000 |

Independent units are master seeds. Five-seed exact two-sided tests cannot attain p<0.05. Holm adjusts all 13 planned tests. Descriptive intervals do not prove equivalence.

## Verified coverage

```json
{
  "campaign_identity": "99301db0a93c6d44f15cb7170c22447af1a70ff5fcf09d7d1969ed5ae028cb31",
  "source_commit": "c9547d6176e4d15520ea9492e6a5088879dfa6fd",
  "expected_evaluations": 1505,
  "successful_evaluations": 1505,
  "training_sets": 45,
  "failed_attempts": 0,
  "source_files_verified": 73,
  "paired_demand_verified": true,
  "seed_domains_disjoint": true,
  "checkpoint_files": 180,
  "training_episodes": 3645,
  "training_censored": 0,
  "evaluation_episodes": 1505,
  "evaluation_censored": 19
}
```
