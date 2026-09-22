# Robust Multi-Agent Traffic Signal Control under Packet Loss and Delay

Research project for evaluating multi-agent traffic signal control under
communication packet loss and delay. The implementation is being developed
incrementally according to [PROJECT_SPEC.md](./PROJECT_SPEC.md).

## Current status

The repository is currently in **Phase 2: Single-Agent RL**. Phase 1 provides
the deterministic SUMO scenario and simulator wrapper; Phase 2 adds one
learning-controlled intersection using a small NumPy-only linear Q-learning
baseline. MARL, communication, and communication-impairment components are
intentionally deferred to later phases.

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