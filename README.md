# Robust Multi-Agent Traffic Signal Control under Packet Loss and Delay

Research project for evaluating multi-agent traffic signal control under
communication packet loss and delay. The implementation is being developed
incrementally according to [PROJECT_SPEC.md](./PROJECT_SPEC.md).

## Current status

The repository is currently in **Phase 0: Project Setup**. This phase provides
the Python package scaffold, configuration templates, test setup, and
reproducibility documentation. The SUMO environment and MARL implementation
are intentionally not included yet.

## Requirements

- Python 3.11 or newer (Python 3.14 was detected during the initial setup check)
- Git
- SUMO and `sumo-gui` for Phase 1 and later

SUMO was not discoverable on the development machine during Phase 0 setup.
Install SUMO separately and ensure both executables are available on `PATH`
before beginning Phase 1.

## Setup

Create and activate a virtual environment, then install the project and
development dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -e ".[dev]"
```

The optional machine-learning dependencies can be installed when Phase 2
begins:

```powershell
py -m pip install -e ".[ml]"
```

## Tests

Run the Phase 0 setup checks with:

```powershell
py -m pytest
```

## Repository layout

```text
configs/       YAML configuration templates
src/           Python package
tests/         Automated tests
```

Experiment outputs are intentionally excluded from version control by default.
See [PROJECT_STATUS.md](./PROJECT_STATUS.md) for the current milestone and
[AGENTS.md](./AGENTS.md) for the development workflow.