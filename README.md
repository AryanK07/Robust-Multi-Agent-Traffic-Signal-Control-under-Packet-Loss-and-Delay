# Robust Multi-Agent Traffic Signal Control under Packet Loss and Delay

Research project for evaluating multi-agent traffic signal control under
communication packet loss and delay. The implementation is being developed
incrementally according to [PROJECT_SPEC.md](./PROJECT_SPEC.md).

## Current status

The repository is currently in **Phase 3: Multi-Agent RL**. Phase 1 provides
the deterministic SUMO scenario, Phase 2 provides a single-agent baseline, and
Phase 3 adds four independent NumPy-only Q-learning agents. Communication
impairments and message exchange are intentionally deferred to later phases.

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

## Repository layout

```text
configs/       YAML configuration templates
src/           Python package
tests/         Automated tests
scripts/       Network generation and smoke-test scripts
sumo/         Network, routes, and SUMO configuration
results/       Ignored smoke-training outputs
```

Experiment outputs are intentionally excluded from version control by default.
See [PROJECT_STATUS.md](./PROJECT_STATUS.md) for the current milestone and
[AGENTS.md](./AGENTS.md) for the development workflow.