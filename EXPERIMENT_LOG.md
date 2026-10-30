# Experiment Log

No experiments have been run. This file will record configurations, seeds,
Git commits, measured metrics, observations, and limitations for each
subsequent experiment.

The Phase 3 smoke-training run is functional verification only, not a research
experiment. It uses seed 42, two training episodes, one evaluation episode,
agents A0/A1/B0/B1, and ideal communication conditions (0% packet loss, 0 ms
delay). Its machine-readable outputs are ignored under `results/phase3/`.

The Phase 4 communication smoke test is functional verification only, not a
research experiment. It verifies an A0-to-A1 message at simulation time 10.0,
including payload, generation timestamp, and immediate delivery timestamp.

The Phase 5 packet-loss smoke test is functional verification only, not a
research experiment. It checks deterministic 0% delivery and reproducibility
of an intermediate seeded packet-loss sequence. No traffic-performance or
robustness conclusion is drawn.

The Phase 6 communication-delay smoke test is functional verification only, not
a research experiment. It checks an A0-to-A1 message generated at simulation
time 10.0 with a fixed 250 ms delay, including unavailable-before-boundary,
exact-boundary delivery, timestamp preservation, telemetry, and compatibility
with complete packet loss. No traffic-performance or robustness conclusion is
drawn. Combined packet-loss and delay evaluation remains Phase 7 work.

Phase 7 framework status: no full research matrix has been run. The configured
matrix contains 25 conditions and five replicate seeds. The runner preserves
run-level JSON results and aggregates successful numeric metrics without
replacing failures. The Phase 7 smoke script exercises four representative
conditions as functional verification only. A causal-path audit found that
Phase 3 policies use local observations only; no communicated messages are
currently generated or consumed by action selection, so no traffic-performance
degradation is claimed from packet loss or delay. Robustness and
message-age-aware policy inputs remain Phase 8 work.

A bounded one-condition frozen-checkpoint pilot was executed for 10% loss and
250 ms delay using seed 42. It is functional framework validation, not a final
benchmark or research conclusion; its raw output is kept under the ignored
Phase 7 results directory.
