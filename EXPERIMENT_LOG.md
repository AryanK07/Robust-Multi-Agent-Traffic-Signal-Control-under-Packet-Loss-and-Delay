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
