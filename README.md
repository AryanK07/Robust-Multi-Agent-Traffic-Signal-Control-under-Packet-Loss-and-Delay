# Robust Multi-Agent Traffic Signal Control under Packet Loss and Delay

Research project for evaluating multi-agent traffic signal control under
communication packet loss and delay. The implementation is being developed
incrementally according to [PROJECT_SPEC.md](./PROJECT_SPEC.md).

## Current status

The repository is currently in **Phase 8: Stale-Information-Aware Robustness**. Phase 1
provides the deterministic SUMO scenario, Phase 2 provides a single-agent
baseline, Phase 3 adds four independent NumPy-only Q-learning agents, and
Phase 4 adds an ideal inter-agent communication abstraction, and Phase 5 adds
seeded packet-loss simulation, and Phase 6 adds fixed simulation-time
communication delay. Robustness processing remains deferred to later phases.

## Requirements

- Python 3.11 or newer (Python 3.14 was detected during the initial setup check)
- Git
- SUMO 1.27.1 and `sumo-gui` for the Phase 1 scenario
- TraCI and sumolib (provided by the SUMO Python tools)

The Phase 1 development machine was verified with SUMO 1.27.1, Python 3.14.0,
TraCI, `sumo`, `sumo-gui`, `netgenerate`, and `netconvert` available.

## Setup

Create and activate a virtual environment, then install the project and
development dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -e ".[dev]"
```

No additional ML framework is required for Phase 2. PyTorch is not installed
because it is not required by the NumPy-only baseline and its Python 3.14
compatibility is not assumed.

## Tests

Run all tests with:

```powershell
py -m pytest
```

The SUMO integration test is marked `sumo` and is skipped with an explicit
reason when SUMO or TraCI is unavailable.

## Phase 1 scenario

The scenario is a deterministic 2x2 grid with four signalized junctions:

```text
A0 ---- B0
|        |
|        |
A1 ---- B1
```

Each edge has one lane and is 100 m long. Six deterministic passenger
vehicles use four short routes. Network generation is reproducible:

```powershell
py scripts\generate_network.py
```

Run the headless TraCI smoke test:

```powershell
py scripts\run_sumo_smoke.py
```

The smoke test starts SUMO, changes one traffic-light phase, advances 12
steps, prints functional metrics, and closes SUMO. Its output is a functional
check, not a traffic-performance result.

To launch the same scenario in SUMO-GUI:

```powershell
sumo-gui -c sumo\simulation\grid.sumocfg --start --quit-on-end
```

## Phase 2 single-agent baseline

Only intersection `A0` is controlled by the learning agent. The observation
is a five-element `float32` vector containing normalized local queue length,
waiting time, vehicle count, lane occupancy, and signal phase. Action `0`
maintains the current phase; action `1` selects the next green phase. The
reward is:

```text
reward = queue_reward_weight * (previous_queue - current_queue)
       + waiting_reward_weight * (previous_waiting - current_waiting)
```

The default weights are `1.0` and `0.1`, configured in
`configs/phase2.yaml`. The implementation is an online linear Q-learning
agent using NumPy, selected to keep Phase 2 reproducible on Python 3.14
without adding an unverified ML framework. Checkpoints use portable `.npz`
files.

Run the small train-save-load-evaluate smoke pipeline:

```powershell
py scripts\run_phase2_smoke_training.py
```

It writes ignored functional-verification outputs under `results/phase2/`.
The smoke run is not a research experiment and does not establish performance
or superiority.

## Phase 3 multi-agent baseline

The four learning agents are `A0`, `A1`, `B0`, and `B1`, one per signalized
intersection. The custom API is:

```python
observations = environment.reset()
next_observations, rewards, terminated, info = environment.step({
    "A0": 0,
    "A1": 0,
    "B0": 1,
    "B1": 0,
})
```

Each agent receives its own local normalized `float32[5]` observation:
queue/halting count, waiting time, vehicle count, lane occupancy, and signal
phase. Actions retain the Phase 2 semantics: `0` maintains the current phase
and `1` selects the next green phase. The local reward for agent `i` is:

```text
r_i = queue_reward_weight * (previous_queue_i - current_queue_i)
    + waiting_reward_weight * (previous_waiting_i - current_waiting_i)
```

Phase 3 uses Independent Q-Learning: four separate learners with independent
parameters and local rewards. A joint action is applied to all four signals,
then SUMO advances exactly once. The baseline has ideal communication
conditions only: packet loss is 0%, delay is 0 ms, delivery is reliable and
instantaneous, and no observations or learned information are exchanged.

Run the functional multi-agent smoke pipeline:

```powershell
py scripts\run_phase3_smoke_training.py
```

It saves one ignored `.npz` checkpoint per agent, reloads all four checkpoints,
evaluates with exploration disabled, and writes CSV/JSON functional-verification
outputs under `results/phase3/`. These outputs are not research results.

## Phase 4 ideal communication layer

Phase 4 provides a SUMO-independent `CommunicationChannel` for the four agents.
Messages are typed records containing a message ID, sender, receiver,
simulation-time generation timestamp, structured mapping payload, and delivery
timestamp once received. The channel uses the 2x2 grid's cardinal neighbors:

```text
A0 <-> B0
|       |
A1 <-> B1
```

Each send/receive operation is deterministic and does not advance SUMO time.
Messages generated at simulation time `t` are available at `t`; messages to
non-neighbors and unknown agents are rejected. The Phase 4 configuration is
explicitly ideal (`enabled: true`, `packet_loss_probability: 0.0`, and
`delay_ms: 0`). Nonzero loss or delay is rejected until its dedicated phase;
packet loss, delay queues, and stale-information handling are not implemented
here. Message age can be derived internally from simulation timestamps, but
age/availability metadata is not added to the Phase 3 RL observation.

Run the short communication smoke test:

```powershell
py scripts\run_phase4_communication_smoke.py
```

The output is functional verification only, not a communication or traffic
performance result.

## Phase 5 packet loss

The communication channel now supports configurable packet-loss probabilities
from 0.0 through 1.0, with an isolated seeded pseudorandom generator. Valid
messages are either delivered immediately or dropped; dropped messages never
enter a receiver queue and are not retried. A successful message preserves its
generation timestamp as its delivery timestamp. Delay remains exactly zero and
nonzero `delay_ms` is rejected until Phase 6.

Each channel exposes bounded telemetry for send attempts, successful
transmissions, pending messages, deliveries, drops, configured probability and
delay, seed, and observed loss rate
(`dropped_messages / send_attempts`, or `0.0` when there are no attempts).
`reset_telemetry()` clears counters without resetting the RNG sequence. The
Phase 3 RL observation, action, reward, and IQL update remain unchanged.

Run the packet-loss functional smoke test:

```powershell
py scripts\run_phase5_packet_loss_smoke.py
```

The smoke output is a functional check, not a traffic-performance or research
result. Combined packet loss and delay, stale-information robustness, adaptive
communication, and robust training are not implemented.

## Phase 6 communication delay

The channel supports a deterministic `fixed` delay configured in milliseconds.
Messages are scheduled at `generation_timestamp + delay_ms / 1000.0` and are
released only when the receiving operation supplies a simulation timestamp at
or after that delivery time. Pending messages remain in per-receiver priority
queues, are ordered by delivery timestamp and send sequence, and never advance
SUMO time. Packet loss is evaluated before scheduling, so dropped messages
never enter a pending queue and are not retried.

```yaml
communication:
  enabled: true
  packet_loss_probability: 0.0
  seed: 42
  delay_model: fixed
  delay_ms: 250
```

Run the Phase 6 functional smoke test:

```powershell
py scripts\run_phase6_communication_delay_smoke.py
```

This phase implements delay simulation only. Combined-condition research
evaluation, stale-information handling, robustness mechanisms, and
message-age-aware observations remain future work.

## Phase 9 robust training

Phase 9 adds condition-randomized training for the Phase 8
freshness-aware policy. The ideal-trained communication-aware baseline uses
only 0% loss and 0 ms delay. The robust-trained variant uses the full Phase 7
5x5 matrix (25 conditions) through a reproducibly shuffled balanced-cycle
schedule: every condition appears once per complete cycle, with the selected
condition fixed for an entire episode.

The training configuration is in `configs/phase9.yaml`. Run the short
functional verification smoke test:

```powershell
py scripts\run_phase9_robust_training_smoke.py
```

The trainer uses separate deterministic seed streams for learner
initialization/exploration, condition scheduling, packet loss, and SUMO.
Each episode creates a fresh environment, clears pending messages and
receiver caches through the Phase 8 reset lifecycle, and preserves learned
weights. Episode records include the selected condition, derived seeds,
traffic metrics, communication telemetry, and status. Ideal and robust
checkpoints use separate directories and metadata containing the policy
variant, Phase 9 marker, 23-feature schema, topology order, freshness
settings, training distribution, schedule, and exposure counts.

Smoke training is software verification only, not evidence of convergence or
traffic-control superiority. Final robust training and statistical evaluation
remain pending. Adaptive communication is implemented in Phase 10, while
communication-budget experiments remain pending.

## Phase 10 adaptive communication

Phase 10 adds deterministic, rule-based transmission scheduling without
changing any policy observation schema, reward, action space, Q-learning
update, or checkpoint. The backward-compatible `always` strategy transmits
every snapshot. `periodic` transmits on the first snapshot and after a
simulation-time interval. `adaptive` transmits on the first snapshot, when

```text
mean(abs(current_normalized_observation - last_transmitted_observation))
    >= change_threshold
```

or when the maximum silence heartbeat interval elapses. The comparison is
always against the last transmission attempt, not the previous observation.
Intervals are simulation-time based and take effect at the next environment
decision step; no real-time waiting or independent SUMO stepping is used.

Configuration is in `configs/phase10.yaml`. Scheduler telemetry reports
opportunities, scheduled and suppressed agent transmissions, trigger reasons,
and communication reduction. Channel telemetry remains responsible for actual
send attempts, drops, delivery, and pending messages. Because the channel has
no acknowledgements, a dropped attempt still updates the scheduler reference
state; a later heartbeat can refresh the receiver cache. Suppressed sends
leave the last-known cache entry intact, so its Phase 8 age increases and
freshness weight decreases.

Run the short functional verification:

```powershell
py scripts\run_phase10_adaptive_communication_smoke.py
```

This is software verification only, not evidence that adaptive communication
improves traffic performance. Full paired comparisons remain pending; Phase 11
and Phase 12 have not started.

## Phase 7 combined impairment experiments

Phase 7 provides a configurable 5x5 matrix from
`configs/phase7.yaml`: packet loss `[0, .05, .10, .20, .30]` crossed with
fixed delay `[0, 100, 250, 500, 1000]` milliseconds. Five replicate seeds are
configured, with RL, communication, and SUMO seeds recorded separately in each
run. The runner reuses frozen Phase 3 checkpoints rather than retraining under
each impairment condition:

```powershell
py scripts\run_phase7_combined_impairment_experiments.py
```

Run-level JSON files are stored under `results/phase7/raw/` and summaries under
`results/phase7/summary.json`; existing raw files are never overwritten. Use
`--condition loss_0p10__delay_250ms` or repeated `--seed` options to select a
bounded subset. A frozen checkpoint set must exist under the configured Phase 3
checkpoint directory.

The current Phase 3 policy uses only local traffic observations and does not
generate or consume communication messages during action selection. Therefore
Phase 7 records communication telemetry and traffic metrics without claiming a
causal traffic-performance effect from impairment. Message-age-aware inputs and
robustness mechanisms are addressed by the separate Phase 8 policy variant.

## Phase 8 freshness-aware communication policy

Phase 7 established that the original Phase 3 IQL policy has no causal
dependency on communication. Phase 8 therefore adds a separate
`freshness_aware_iql` variant without changing the five-feature local-only
baseline, its action/reward interface, or its checkpoints.

Each agent sends its normalized five-feature local traffic observation to the
configured cardinal neighbors in deterministic topology order. A receiver
keeps only the latest valid message for each neighbor. Dropped or pending
messages do not update the cache, and out-of-order messages cannot replace
newer information. Message age is simulation-time based:

```text
message_age_ms = (current_simulation_time - generation_timestamp) * 1000
freshness_weight = exp(-message_age_ms / freshness_decay_tau_ms)
```

The communication-aware observation has 23 `float32` features: five local
features followed by one nine-feature block per neighbor in topology order:
availability, normalized age, freshness weight, stale indicator, and the five
neighbor features weighted by freshness. An unavailable neighbor uses finite
sentinel values and contributes no traffic payload.

The Phase 8 configuration is in `configs/phase8.yaml`. Communication-aware
checkpoints use separate files and store policy variant, schema version,
neighbor ordering, observation size, and freshness parameters. They are
rejected when metadata is incompatible; Phase 3 checkpoints are never loaded
as communication-aware checkpoints.

Run the short functional verification:

```powershell
py scripts\run_phase8_freshness_aware_smoke.py
```

This verifies the delayed message boundary, packet-loss retention behavior,
age decay, the 23-dimensional observation, and both policy variants. It is
software verification only, not a performance result. Phase 9 robust training
and final comparative experiments remain pending.

## Repository layout

```text
configs/       YAML configuration templates
src/           Python package, including communication primitives
tests/         Automated tests
scripts/       Network generation and smoke-test scripts
sumo/         Network, routes, and SUMO configuration
results/       Ignored smoke-training outputs
```

Experiment outputs are intentionally excluded from version control by default.
See [PROJECT_STATUS.md](./PROJECT_STATUS.md) for the current milestone and
[AGENTS.md](./AGENTS.md) for the development workflow.