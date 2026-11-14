# Project Status

## Current Phase

Phase 11 — independent audit and frozen follow-up completed; off-machine
archive publication/verification remains the final technical prerequisite.
Phase 12 has not started. See [the readiness report](docs/PHASE11_READINESS.md).

## Completed

- Existing phases 0–11 inspected and preserved; original 755 evaluations,
  15 checkpoint sets and all 870 artifact hashes independently checked.
- Corrected channel telemetry/reset behavior and tested timing boundaries.
- Separate follow-up tripinfo metrics, immutable campaign storage, matched
  linear-IQL baselines, constrained signals and time-resolved communication.
- Action-sensitive joint-box margin gate with counted impaired requests and
  responses, matched periodic-pull control and component ablations.
- Controlled development studies of training budget, phase-relative state,
  training termination and finite metadata scaling; all unfavorable data kept.
- Reserved-seed final campaign frozen at `c9547d6`: 45 checkpoint sets,
  3645 training episodes and 1505 evaluations, no execution failures.
- Independent full-data audit, paired seed analysis with one 13-test Holm
  family, generated tables and five visually checked figures.
- Verified literature comparison and archive builder with a successful source
  restoration/corruption-detection test. No paper draft was produced.

## In Progress

- Publish and independently verify the complete versioned research archive.

## Upcoming

- After archive verification, Phase 12 may document the measured mixed/negative
  findings and limitations. It remains unstarted under the user's boundary.
- A stronger novelty, efficacy or broad-generalization claim needs a separately
  approved study; no new scenario, model or outcome-driven tuning is scheduled.

## Tests

Full suite: **106 passed in 38.30 seconds**. Compilation passed. This includes
live SUMO tests, complete TraCI/libsumo trajectory equivalence, feature/bounds
compatibility, frozen validation RNG isolation, training termination, exact
seed-level inference and archive restoration. Final analysis was executed on
the complete campaign; tables/figures are generated from saved records.
Earlier audit: 65 original tests, 68 after the counter correction, communication
smokes for phases 4–10 and five original/five corrected frozen replays passed.

## Experiments

- Final source: `c9547d6176e4d15520ea9492e6a5088879dfa6fd`.
- Reserved seeds: 41001–41005, 81 training episodes per model, all 25 cells,
  nine variants, five full-robust communication strategies; 1505/1505 present.
- Audit verified 180 checkpoint files, 73 source/configuration files, all raw
  traffic metrics, training schedules, demand pairing and seed separation.
- Nineteen final evaluations were censored, all full-ideal seed 41003; no
  training episode was censored. Execution success does not imply completion.
- Full robust waiting 6.9195 s/vehicle, full ideal 9.84272; paired uncertainty
  does not establish superiority. Local-only matches full robust traffic.
- Adaptive state-change: 339.6 packet attempts versus always 9600. Action gate
  and periodic pull: both 1793.92. The gate adds no measured suppression.
- Six development studies also passed integrity checks. The original 870 files
  and pilot 421-file snapshot remain unchanged. See the complete experiment
  ledger and generated results linked in the readiness report.

## Known Issues

- Small network/demand, five independent seeds, one evaluation stream per seed,
  fixed delays and censored outcomes limit external validity and inference.
- Exact two-sided five-seed tests cannot attain p<0.05; every Holm-adjusted
  p-value here equals 1. Identical observed outcomes do not prove equivalence.
- The conservative action bound stayed uncertain on every final check. No
  incremental action-gate benefit or useful traffic coordination is shown.
- Original waiting is a snapshot proxy, not tripinfo waiting; original source
  metadata predates the runner. These historical limitations remain recorded.
- Original one-second scheduling explains zero suppression; the 160-send
  snapshot defect is fixed and separate replays measure 168 actual attempts.
- Whole-episode communication costs include empty-network time. Payload bytes
  exclude wireless headers. No real-world safety or publication-readiness claim.
- Off-machine archive publication remains pending at this status revision.

## Latest Commit

Original Phase 11 `4161f42`; audit `959745d`; initial v2 pilot `eada4cd`;
reserved final source `c9547d6`; archive tooling `1937f06`.
This report/results revision is identified by its containing Git commit;
`git log -1` gives the resolved documentation commit. Runtime source remains
explicitly tied to the frozen campaign, not a later documentation commit.
