# Frozen reserved-seed Phase 11 protocol

Declared 2026-11-13, after development calibration and before any data from
master seeds 41001–41005. Phase 12 remains unstarted. This campaign replaces
neither the original Phase 11 record nor any unsuccessful development study.

## Development decision

Both predeclared metadata scales (0.1 and 0.01) completed 100% of trips in
all eight episode-81 validation cells for full ideal/robust policies and
development seeds 31001/31002. The rule prefers the largest passing scale,
therefore **0.1** is selected; it is not selected by the best waiting result.
Local/plain matched controls in the termination study met the 95% threshold.
This validates a limited development criterion, not universal competence or
convergence. All prior failed approaches and calibration settings are retained.

## Frozen design

`configs/phase11_reserved_final.yaml` is authoritative:

- Five fresh master seeds: 41001, 41002, 41003, 41004, 41005. Separate seed
  domains for training and evaluation; no development checkpoints reused.
- Nine variants: local, plain ideal/robust, full ideal/robust, no-age,
  no-availability, no-decay, no-stale (the four removals robust-trained).
- 81 training episodes, epsilon 0.2, learning rate 0.01, discount 0.95,
  zero initialization, negative local queue integral reward. Robust training
  has nine complete balanced cycles of losses 0/0.1/0.2 × delays 0/250/500 ms.
- Common phase-relative observations, metadata scale 0.1, five-second minimum
  green and three-second yellow. Training terminates when no active or future
  vehicles remain, or at 120 seconds. No new algorithm or network topology.
- Existing four-junction network; 20 vehicles with seeded departure jitter
  over 30 seconds; explicit speed deviation 0.1. Evaluate for 120 seconds.
- Frozen evaluation, epsilon zero, no parameter updates, matched demand.
- All 25 cells: losses 0/0.05/0.1/0.2/0.3 × delays 0/100/250/500/1000 ms.
  Nine extreme held-outs have loss 0.3 or delay 1000 ms, absent from training.
- Full robust uses always, periodic, adaptive state-change, periodic pull,
  and action-sensitive pull, all on the same checkpoint. Other communicating
  variants use always. Local-only is evaluated once per seed.
- Simulation 50 ms; message opportunities 100 ms; decisions one second;
  periodic/cooldown one second; heartbeat five seconds; state-change threshold
  0.1; freshness tau 500 ms, age scale 2000 ms, stale threshold 1000 ms.
- Exactly **45 checkpoint sets, 3645 training episodes, 1505 evaluations**.
  Four isolated SUMO worker processes; the equivalent libsumo 1.27.1 backend.

## Analysis and acceptance

Apply [the prespecified analysis](FINAL_ANALYSIS_PLAN.md), including all
conditions, absolute/relative metrics, paired seed effects and one 13-test
Holm family. Report five independent training seeds, not 125 independent
condition samples. Inference is low-powered and results remain specific to
this small scenario. Censoring, negative results and unsupported hypotheses
must remain visible. No outcome-dependent training, threshold, seed,
exclusion, comparison, or statistical-test changes are allowed.

The campaign is technically complete only when all exact run identities are
present, failures are accounted for, raw metrics/checkpoint/source identities
verify, analysis/figures regenerate, original records remain unchanged, and
a reproducibility archive is created and checked. A poor reserved-seed
controller is retained and reported; it cannot be replaced with a favorable
checkpoint. Completion of these steps does not authorize a superiority,
novelty or publication-readiness claim.

```powershell
python scripts/run_followup.py --mode run --config configs/phase11_reserved_final.yaml --output results/followup_v2/reserved_final_001
python scripts/audit_followup.py results/followup_v2/reserved_final_001
python scripts/analyze_final.py results/followup_v2/reserved_final_001
```

Commit the source/configuration before collection; the manifest records that
commit and hashes. `requirements-research-lock.txt` captures the direct and
principal plotting runtime dependencies. Use a clean Python environment and
SUMO 1.27.1. The installed host also contains optional PyArrow 25.0.1, for which
libsumo prints an Arrow compatibility warning; no Arrow APIs are used and
the complete-trajectory equivalence test passed. PyArrow is not required by
this experiment and is not included in the reproduction lock.
