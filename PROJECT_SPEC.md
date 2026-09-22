# Robust Multi-Agent Traffic Signal Control under Packet Loss and Delay

## Project Specification

**Project Type:** BTech / Research Project  
**Primary Domain:** Multi-Agent Reinforcement Learning, Intelligent Transportation Systems, Traffic Signal Control, Robust AI, Networked Multi-Agent Systems  
**Simulator:** SUMO (Simulation of Urban Mobility)  
**Repository:** `Robust-Multi-Agent-Traffic-Signal-Control-under-Packet-Loss-and-Delay`

---

# 1. Project Identity

## 1.1 Project Title

**Robust Multi-Agent Traffic Signal Control under Packet Loss and Delay**

## 1.2 Core Problem

Urban traffic signal control is increasingly being studied using Multi-Agent Reinforcement Learning (MARL), where individual intersections are controlled by autonomous agents that can exchange information with neighboring intersections.

In a real deployment, however, communication between traffic-signal agents may not be perfect.

Messages can:

- be lost,
- arrive late,
- become stale,
- arrive irregularly,
- or be unavailable temporarily.

A MARL controller that performs well under perfect communication may therefore degrade when communication becomes unreliable.

This project investigates how traffic-signal control performance changes under **communication packet loss and communication delay**, and develops a communication-aware robust MARL approach capable of operating under such conditions.

---

# 2. Research Objective

The primary objective is:

> To design, implement, and experimentally evaluate a multi-agent traffic signal control system that remains effective when inter-agent communication is affected by packet loss and delay.

The project must not assume perfect communication.

The communication layer should explicitly model impairments and expose their effects to the traffic-signal agents.

The project should compare:

1. normal MARL with reliable communication,
2. MARL operating under impaired communication,
3. a communication-aware robust approach,
4. optionally, an adaptive communication strategy.

---

# 3. Research Questions

The project should investigate the following questions.

### RQ1

How does packet loss affect the performance of cooperative multi-agent traffic signal control?

### RQ2

How does communication delay affect cooperative traffic signal control?

### RQ3

How does the combination of packet loss and delay affect traffic-control performance compared with either impairment independently?

### RQ4

Can a communication-aware robustness mechanism reduce performance degradation under unreliable communication?

### RQ5

Can adaptive communication reduce unnecessary communication while maintaining traffic-control performance?

### RQ6

How well does a controller trained under selected communication conditions generalize to previously unseen packet-loss and delay conditions?

---

# 4. Research Hypotheses

The following hypotheses should be tested experimentally rather than assumed to be true.

### H1 — Packet Loss

Increasing packet-loss probability will generally degrade cooperative MARL performance because agents receive less information from neighboring intersections.

### H2 — Communication Delay

Increasing communication delay will generally degrade performance because agents increasingly operate using stale information.

### H3 — Combined Impairments

Combined packet loss and delay will produce larger degradation than reliable communication and may expose failure modes not visible when either impairment is studied independently.

### H4 — Robustness

A communication-aware robustness mechanism will reduce performance degradation under impaired communication compared with a standard controller that assumes reliable communication.

### H5 — Adaptive Communication

Adaptive communication can reduce communication volume while maintaining acceptable traffic-control performance compared with continuously transmitting agents.

### H6 — Generalization

Training across a range of communication conditions should improve robustness to communication conditions that were not explicitly used during training.

These hypotheses are research hypotheses and must be validated using experimental evidence.

---

# 5. Expected Contributions

The project should aim for the following contributions.

## Contribution 1 — Communication Robustness Benchmark

Develop a reproducible benchmark for evaluating MARL traffic signal control under:

- packet loss,
- communication delay,
- combined packet loss and delay.

The benchmark should systematically vary communication conditions.

---

## Contribution 2 — Communication-Aware Robust MARL

Develop a controller that does not blindly assume that received information is current and reliable.

The controller should account for factors such as:

- message availability,
- message age,
- missing messages,
- delayed messages,
- communication reliability.

---

## Contribution 3 — Adaptive Communication

If computationally feasible, investigate whether agents can adapt their communication behavior based on the usefulness or freshness of information.

This component is optional until the core robust system is working.

---

# 6. Project Scope

## 6.1 Required Components

The minimum successful research system must contain:

- SUMO traffic simulation,
- multiple traffic intersections,
- multiple RL agents,
- decentralized signal control,
- inter-agent communication,
- packet-loss simulation,
- communication-delay simulation,
- combined packet-loss + delay simulation,
- baseline MARL controller,
- robust MARL controller,
- reproducible experiments,
- multiple random seeds,
- quantitative evaluation,
- plots/tables,
- statistical analysis,
- documentation.

---

## 6.2 Optional Components

These should only be implemented after the required system is stable:

- adaptive communication,
- message-priority mechanisms,
- learned message filtering,
- uncertainty estimation,
- attention-based message aggregation,
- larger road networks,
- heterogeneous traffic demand,
- transfer/generalization experiments.

Optional features must never destabilize the core research pipeline.

---

# 7. Technology Stack

## 7.1 Programming Language

Python 3.11+ preferred.

---

## 7.2 Traffic Simulator

SUMO — Simulation of Urban Mobility.

Use:

- `sumo`
- `sumo-gui`
- TraCI
- optionally `libsumo`

The implementation should abstract simulator interaction so that the RL environment is not tightly coupled to one execution mode.

---

## 7.3 Machine Learning

Primary framework:

- PyTorch

Potential RL/MARL support:

- PettingZoo where appropriate,
- custom MARL training code where necessary.

Do not introduce a large RL framework unless it provides a clear benefit.

---

## 7.4 Scientific Python

Use:

- NumPy
- Pandas
- SciPy
- Matplotlib

Optional:

- Seaborn only if explicitly justified.

---

## 7.5 Experiment Tracking

Use lightweight reproducible experiment tracking.

Possible tools:

- TensorBoard,
- CSV/JSON result files,
- YAML configuration files.

The project must remain runnable without depending on a paid external service.

---

## 7.6 Testing

Use:

- `pytest`

Tests should cover critical non-SUMO logic independently from the simulator.

---

## 7.7 Version Control

Use:

- Git
- GitHub

Every meaningful implementation stage should produce a genuine commit.

Do not create artificial commits merely to increase GitHub contribution activity.

---

# 8. High-Level System Architecture

The intended architecture is:

```text
                 ┌──────────────────────────┐
                 │       SUMO Simulator     │
                 │                          │
                 │  Traffic Network         │
                 │  Vehicles                │
                 │  Intersections           │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │      MARL Environment    │
                 └────────────┬─────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │ Agent 1  │    │ Agent 2  │    │ Agent N  │
        │Signal Ctrl│   │Signal Ctrl│   │Signal Ctrl│
        └─────┬────┘    └─────┬────┘    └─────┬────┘
              │               │               │
              └───────────────┼───────────────┘
                              ▼
                 ┌──────────────────────────┐
                 │   Communication Layer    │
                 │                          │
                 │ Message Generation       │
                 │ Packet Loss              │
                 │ Delay                    │
                 │ Message Age              │
                 │ Delivery Status          │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │ Robustness Mechanism     │
                 │                          │
                 │ Stale-data handling      │
                 │ Missing-data handling    │
                 │ Freshness information    │
                 │ Optional uncertainty     │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │ Signal Action            │
                 │                          │
                 │ Phase selection/change   │
                 └──────────────────────────┘
```

---

# 9. Initial Traffic Network

Begin with a small controlled network.

Recommended initial topology:

```text
        Intersection 1
              │
              │
Intersection 2 ───── Intersection 3
              │
              │
        Intersection 4
```

A simpler 2×2 grid may be used initially:

```text
I1 ───── I2
│        │
│        │
I3 ───── I4
```

The exact SUMO network should be generated or configured programmatically where practical.

Do not begin with a large city-scale network.

The research system must first work reliably on a small network.

---

# 10. Traffic Environment

Each intersection is controlled by one RL agent.

The environment should expose:

- local traffic observations,
- neighboring-agent information,
- communication state,
- current signal state,
- reward,
- episode termination.

---

# 11. Agent Observation

A baseline observation may include:

### Local Traffic State

- queue length,
- vehicle count,
- waiting vehicles,
- approaching vehicle count,
- lane occupancy,
- current signal phase,
- time since phase change.

### Neighbor Information

When available:

- neighboring queue information,
- neighboring traffic density,
- neighboring signal state,
- neighboring estimated demand.

### Communication Metadata

The robust controller may additionally receive:

- whether a message was received,
- message age,
- time since last successful message,
- packet-delivery indicator,
- communication confidence/freshness indicator.

The observation representation should remain fixed when comparing methods unless the experiment explicitly studies observation differences.

---

# 12. Action Space

The baseline action space should remain simple.

Possible actions:

```text
0 = maintain current phase
1 = change phase
```

or a small discrete phase-selection action space.

The exact signal-control formulation must be documented and held consistent across comparable experiments.

Avoid unnecessarily complex action spaces during the first implementation.

---

# 13. Reward Function

The reward should encourage traffic efficiency.

A candidate reward is based on changes in:

- queue length,
- waiting time,
- delay,
- throughput.

For example:

```text
reward =
    - α * queue_length
    - β * waiting_time
    + γ * throughput
```

The exact coefficients must be defined in configuration files rather than hard-coded throughout the implementation.

Reward design must remain identical between baseline and proposed methods unless reward sensitivity is itself an experiment.

---

# 14. Multi-Agent Learning

The baseline should use decentralized agents.

Each agent:

1. observes its local state,
2. receives available neighboring information,
3. selects a signal-control action,
4. receives a reward,
5. updates its policy.

A centralized-training/decentralized-execution approach may be investigated if computationally practical.

The project should initially prioritize a stable baseline over algorithmic complexity.

---

# 15. Communication Layer

Communication must be implemented as a separate abstraction.

The traffic-control agent should not directly simulate packet loss using ad-hoc conditionals throughout the RL code.

Use a dedicated communication component.

Conceptually:

```text
Agent A
   │
   │ message
   ▼
Communication Layer
   │
   ├── packet-loss model
   ├── delay model
   ├── timestamp
   ├── delivery status
   └── message queue
   │
   ▼
Agent B
```

A message should contain enough metadata to determine whether the information is fresh or stale.

---

# 16. Message Structure

A conceptual message may contain:

```text
sender_id
receiver_id
timestamp
payload
sequence_number
send_time
delivery_time
```

Optional fields:

```text
message_type
priority
confidence
```

The implementation should use a typed structure such as a dataclass or equivalent.

---

# 17. Packet Loss Model

Packet loss should be explicitly parameterized.

The initial benchmark should include:

```text
0%
5%
10%
20%
30%
```

The implementation should allow arbitrary packet-loss probabilities through configuration.

For each transmitted message:

```text
random_value < packet_loss_probability
```

may determine whether the message is dropped.

The random process must be reproducible through controlled random seeds.

---

# 18. Communication Delay Model

The initial delay benchmark should include:

```text
0 ms
100 ms
250 ms
500 ms
1000 ms
```

The communication layer should support delayed delivery.

Messages should not simply be delivered immediately with a "delay" flag.

The simulation should preserve causal ordering:

```text
send time
      ↓
delay process
      ↓
delivery time
      ↓
agent receives message
```

A message sent at time `t` with delay `d` should become available no earlier than:

```text
t + d
```

---

# 19. Packet Loss + Delay

The combined impairment experiment is essential.

For example:

| Packet Loss | Delay |
|---:|---:|
| 0% | 0 ms |
| 0% | 250 ms |
| 0% | 500 ms |
| 10% | 250 ms |
| 10% | 500 ms |
| 20% | 250 ms |
| 20% | 500 ms |
| 30% | 500 ms |
| 30% | 1000 ms |

The final experiment matrix should be defined through configuration files rather than hard-coded experiment scripts.

---

# 20. Stale Information

A major research consideration is that delayed information may still arrive.

Therefore:

```text
received ≠ fresh
```

The controller should be able to determine message age.

Example:

```text
message_age = current_time - message_timestamp
```

The system should distinguish:

1. fresh message,
2. delayed but usable message,
3. stale message,
4. missing message.

---

# 21. Missing-Information Handling

When no current message is available, the agent should have a defined fallback.

Possible strategies:

### Strategy A

Use the most recent available message.

### Strategy B

Use a locally predicted estimate.

### Strategy C

Use a default/zero neighbor state.

### Strategy D

Use a learned uncertainty-aware representation.

The initial implementation should use the simplest defensible approach.

More advanced approaches can be investigated later.

---

# 22. Robustness Mechanism

The proposed robust controller should explicitly account for communication reliability.

A basic robust representation may augment neighbor information with:

```text
neighbor_state
message_age
message_available
time_since_last_update
```

Conceptually:

```text
robust_neighbor_observation =
[
    neighbor_traffic_state,
    message_available,
    message_age
]
```

This allows the policy to distinguish between:

```text
"neighbor queue = 10, fresh"
```

and:

```text
"neighbor queue = 10, but information is 1 second old"
```

The precise robustness mechanism should be selected after the baseline and communication simulator are functioning.

---

# 23. Adaptive Communication

Adaptive communication is an optional research extension.

Instead of transmitting continuously, an agent may communicate when information is likely to be useful.

Potential triggers include:

- significant traffic-state change,
- significant queue change,
- message age threshold,
- predicted information value,
- uncertainty threshold.

A simple initial mechanism may be:

```text
if traffic_state_change > threshold:
    send_message()
```

The threshold must be configurable.

Evaluation should include:

- traffic performance,
- number of messages,
- communication reduction,
- packet delivery,
- average message age.

Adaptive communication should not be implemented before the core robust communication pipeline is validated.

---

# 24. Robust Training

The project should investigate training strategies that expose the policy to unreliable communication.

Possible training conditions:

### Training A

Perfect communication only.

### Training B

Fixed packet-loss/delay condition.

### Training C

Randomly sampled packet-loss and delay conditions.

### Training D

Curriculum/randomized impairment training.

The final strategy should be selected based on experimental design and computational feasibility.

---

# 25. Experimental Conditions

The main communication dimensions are:

## Packet Loss

```text
0%
5%
10%
20%
30%
```

## Delay

```text
0 ms
100 ms
250 ms
500 ms
1000 ms
```

The project should include:

### Experiment Group A

Perfect communication.

### Experiment Group B

Packet loss only.

### Experiment Group C

Delay only.

### Experiment Group D

Packet loss + delay.

### Experiment Group E

Robust controller.

### Experiment Group F

Optional adaptive communication.

### Experiment Group G

Generalization to unseen communication conditions.

---

# 26. Baselines

At minimum, implement:

## Baseline 1 — Conventional MARL

Normal multi-agent controller under reliable communication.

---

## Baseline 2 — MARL under Impaired Communication

The same basic controller operating under packet loss and delay without a specialized robustness mechanism.

This isolates the effect of communication impairment.

---

## Proposed Method — Robust MARL

Controller explicitly incorporating communication reliability/freshness information.

---

## Optional Proposed Extension — Robust + Adaptive Communication

The robust controller additionally controls when communication occurs.

---

# 27. Fair Comparison Requirements

Comparisons should keep constant where possible:

- traffic demand,
- network topology,
- simulation duration,
- action space,
- reward function,
- training budget,
- evaluation scenarios,
- random seeds,
- simulator configuration.

The primary independent variables should be the communication condition and controller/method.

---

# 28. Evaluation Metrics

## Traffic Performance

### Average Waiting Time

Measure average vehicle waiting time.

### Average Travel Time

Measure time required for vehicles to complete their trips.

### Queue Length

Measure mean and/or maximum queue length.

### Throughput

Number of vehicles completing their trips within the evaluation period.

### Number of Stops

Measure unnecessary stopping where feasible.

---

# 29. Communication Metrics

Measure:

- packets transmitted,
- packets delivered,
- packet-loss rate,
- average message delay,
- average message age,
- maximum message age,
- communication frequency,
- communication overhead.

---

# 30. Robustness Metrics

A key metric should be degradation relative to ideal communication.

For a metric where lower is better:

```text
degradation (%) =
    ((impaired_performance - ideal_performance)
     / ideal_performance) × 100
```

For metrics where higher is better, the formulation must be adjusted appropriately.

The exact metric direction must always be documented.

The project should report both:

1. absolute performance,
2. relative degradation.

This prevents robustness claims from being based only on raw values.

---

# 31. Statistical Evaluation

Experiments must use multiple random seeds.

Initial target:

```text
5 seeds minimum
```

Preferred final evaluation:

```text
5–10 seeds
```

depending on computational resources.

Report:

- mean,
- standard deviation,
- confidence intervals where appropriate.

Where statistically appropriate, use methods such as:

- t-tests,
- bootstrap confidence intervals,
- ANOVA,
- non-parametric tests.

The statistical method must match the experimental design.

Do not perform statistical tests merely for appearance.

---

# 32. Ablation Studies

The robustness mechanism should be decomposed where practical.

Potential ablations:

```text
Full robust model
       │
       ├── remove message age
       ├── remove availability indicator
       ├── remove stale-data handling
       ├── remove adaptive communication
       └── remove robust training
```

The goal is to determine which components actually contribute to observed behavior.

---

# 33. Generalization Experiments

Training and evaluation conditions should not necessarily be identical.

Example:

```text
Training:
0–20% packet loss
0–500 ms delay
```

Evaluation:

```text
30% packet loss
1000 ms delay
```

The exact held-out conditions must be documented before running the final experiment.

This experiment should determine whether robustness extends beyond the communication conditions encountered during training.

---

# 34. Reproducibility

Every experiment must record:

- experiment ID,
- timestamp,
- Git commit hash,
- configuration file,
- random seed,
- network configuration,
- traffic-demand configuration,
- model configuration,
- training steps/episodes,
- evaluation episodes,
- communication parameters,
- software versions where practical.

A result without reproducibility metadata should not be treated as a final research result.

---

# 35. Configuration System

Avoid hard-coded experiment parameters.

Use configuration files such as:

```text
configs/
├── base.yaml
├── training.yaml
├── communication.yaml
├── network.yaml
├── experiments.yaml
└── evaluation.yaml
```

Example conceptual configuration:

```yaml
communication:
  packet_loss_probability: 0.10
  delay_ms: 250
  enabled: true

experiment:
  seed: 42

training:
  episodes: 1000
```

Actual configuration structure may evolve during implementation.

---

# 36. Proposed Repository Structure

The project should evolve toward:

```text
Robust-Multi-Agent-Traffic-Signal-Control-under-Packet-Loss-and-Delay/
│
├── AGENTS.md
├── PROJECT_SPEC.md
├── README.md
├── LICENSE
├── requirements.txt
├── pyproject.toml
│
├── .gitignore
│
├── configs/
│   ├── base.yaml
│   ├── network.yaml
│   ├── communication.yaml
│   ├── training.yaml
│   └── experiments.yaml
│
├── src/
│   └── traffic_control/
│       ├── __init__.py
│       │
│       ├── environment/
│       │   ├── __init__.py
│       │   ├── sumo_env.py
│       │   ├── traffic_state.py
│       │   └── signal_controller.py
│       │
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── agent.py
│       │   ├── policy.py
│       │   └── marl.py
│       │
│       ├── communication/
│       │   ├── __init__.py
│       │   ├── message.py
│       │   ├── channel.py
│       │   ├── packet_loss.py
│       │   ├── delay.py
│       │   └── reliability.py
│       │
│       ├── robustness/
│       │   ├── __init__.py
│       │   ├── stale_information.py
│       │   ├── robust_observation.py
│       │   └── adaptive_communication.py
│       │
│       ├── training/
│       │   ├── __init__.py
│       │   ├── trainer.py
│       │   └── replay_buffer.py
│       │
│       ├── evaluation/
│       │   ├── __init__.py
│       │   ├── metrics.py
│       │   ├── evaluate.py
│       │   └── statistics.py
│       │
│       └── utils/
│           ├── __init__.py
│           ├── config.py
│           ├── seeds.py
│           └── logging.py
│
├── tests/
│   ├── test_communication.py
│   ├── test_packet_loss.py
│   ├── test_delay.py
│   ├── test_message_age.py
│   ├── test_environment.py
│   └── test_metrics.py
│
├── sumo/
│   ├── network/
│   ├── routes/
│   ├── additional/
│   └── simulation/
│
├── experiments/
│   ├── scripts/
│   ├── configs/
│   └── logs/
│
├── results/
│   ├── raw/
│   ├── processed/
│   ├── figures/
│   └── tables/
│
├── docs/
│   ├── methodology/
│   ├── experiments/
│   └── paper/
│
└── notebooks/
```

The exact structure may evolve, but architecture should remain modular.

---

# 37. Development Phases

The project must be developed incrementally.

---

## Phase 0 — Project Setup

Tasks:

- initialize repository structure,
- verify Python,
- verify Git,
- verify SUMO installation,
- create dependency configuration,
- create configuration system skeleton,
- create test structure,
- create documentation,
- create `.gitignore`,
- verify GitHub remote.

Deliverable:

> A clean, reproducible development environment.

Do not implement MARL yet.

---

## Phase 1 — SUMO Environment

Implement:

- SUMO network,
- traffic routes,
- simulation wrapper,
- reset,
- step,
- traffic-state extraction,
- signal control,
- basic metrics.

Deliverable:

> A working programmatic SUMO traffic-control environment.

---

## Phase 2 — Single-Agent RL

Before full MARL, validate RL logic on a simplified setting.

Implement:

- observation,
- action,
- reward,
- policy,
- training loop,
- evaluation.

Deliverable:

> A functioning RL signal-control baseline.

---

## Phase 3 — Multi-Agent RL

Expand to multiple intersections.

Implement:

- multiple agents,
- local observations,
- independent policies or shared policy,
- coordinated execution,
- multi-agent training.

Deliverable:

> A functioning multi-intersection MARL baseline.

---

## Phase 4 — Communication Simulator

Implement:

- message abstraction,
- sender/receiver,
- timestamps,
- delivery scheduling,
- message queues,
- message age.

Deliverable:

> Reliable communication simulation with no packet loss and zero delay.

---

## Phase 5 — Packet Loss

Add configurable packet loss.

Evaluate:

```text
0%
5%
10%
20%
30%
```

Deliverable:

> Reproducible packet-loss experiments.

---

## Phase 6 — Communication Delay

Add configurable delay.

Evaluate:

```text
0
100
250
500
1000 ms
```

Deliverable:

> Reproducible delay experiments.

---

## Phase 7 — Combined Impairments

Combine:

- packet loss,
- delay.

Deliverable:

> Communication robustness benchmark.

---

## Phase 8 — Robustness Mechanism

Implement:

- message freshness,
- message availability,
- stale-information handling,
- robust observation representation.

Deliverable:

> Robust MARL controller.

---

## Phase 9 — Robust Training

Investigate training across variable communication conditions.

Deliverable:

> Robust-training experimental comparison.

---

## Phase 10 — Adaptive Communication

Optional.

Implement adaptive communication policy.

Evaluate:

- performance,
- messages sent,
- communication reduction,
- robustness.

Deliverable:

> Robust + adaptive communication extension.

---

## Phase 11 — Final Experiments

Run:

- baselines,
- packet-loss experiments,
- delay experiments,
- combined experiments,
- robustness experiments,
- ablations,
- generalization experiments.

Use multiple seeds.

Freeze the final experimental configuration before collecting final results.

---

## Phase 12 — Documentation and Paper

Prepare:

- final README,
- methodology documentation,
- experiment documentation,
- results,
- figures,
- tables,
- limitations,
- reproducibility instructions,
- research paper draft.

Potential paper structure:

```text
1. Abstract
2. Introduction
3. Related Work
4. Problem Formulation
5. Methodology
6. Communication Impairment Model
7. Experimental Setup
8. Results
9. Ablation Study
10. Generalization
11. Limitations
12. Conclusion
13. References
```

---

# 38. Testing Strategy

Every major module should have tests.

Examples:

### Packet Loss

Given a fixed seed and loss probability, behavior should be reproducible.

### Delay

A message scheduled with delay `d` must not be delivered before its delivery time.

### Message Age

Message age must be calculated correctly.

### Missing Messages

Agents must handle unavailable messages without crashing.

### Configuration

Invalid communication parameters should be rejected.

### Environment

Environment reset and step behavior should be deterministic when seeded appropriately.

---

# 39. Research Integrity

This project is intended as a genuine research project.

The following are prohibited:

- fabricated experimental results,
- fabricated citations,
- fabricated benchmarks,
- invented statistical significance,
- invented training success,
- invented GitHub activity,
- fake commits,
- empty commits solely for contribution graphs,
- backdated commits,
- cherry-picking only favorable random seeds,
- deleting unfavorable experimental results without documentation.

If an experiment fails, the failure should be documented.

If a hypothesis is unsupported, the final paper must report that honestly.

---

# 40. Git and GitHub Workflow

Meaningful development should be reflected in Git.

Recommended workflow:

```text
Inspect
   ↓
Plan
   ↓
Implement
   ↓
Test
   ↓
Fix
   ↓
Document
   ↓
Review diff
   ↓
Commit
   ↓
Push
```

Recommended commit prefixes:

```text
feat:
fix:
test:
refactor:
docs:
experiment:
analysis:
config:
```

Examples:

```text
feat: add SUMO environment wrapper
test: add communication delay tests
feat: implement packet loss channel
experiment: add packet loss benchmark configuration
feat: add stale message handling
docs: document communication model
analysis: add robustness degradation metrics
```

Never create a commit solely to make the GitHub contribution graph appear active.

---

# 41. Git Safety

The coding agent must:

- inspect `git status`,
- inspect relevant diffs,
- avoid committing secrets,
- avoid committing huge generated files,
- avoid force-pushing,
- avoid rewriting history,
- avoid deleting work without justification.

The default branch should remain stable.

---

# 42. Generated Data

Large generated data should not automatically be committed.

Generally:

```text
results/raw/
results/processed/
experiments/logs/
```

should be controlled through `.gitignore` where appropriate.

However, lightweight:

- configuration files,
- summary tables,
- selected figures,
- reproducibility metadata

may be committed when useful.

The final repository should contain enough information for another researcher to reproduce the experiments without unnecessarily storing massive simulator outputs.

---

# 43. Experiment Naming

Use deterministic experiment IDs.

Example:

```text
exp_pl00_d000_seed42
exp_pl10_d250_seed42
exp_pl20_d500_seed17
```

Where:

```text
pl = packet loss percentage
d  = delay in milliseconds
seed = random seed
```

For example:

```text
exp_pl20_d500_seed42
```

means:

```text
20% packet loss
500 ms delay
seed 42
```

---

# 44. Result Organization

Results should be structured approximately as:

```text
results/
├── raw/
│   ├── exp_pl00_d000_seed42/
│   ├── exp_pl10_d250_seed42/
│   └── ...
│
├── processed/
│   ├── summary.csv
│   └── statistics.csv
│
├── figures/
│   ├── packet_loss_curve.png
│   ├── delay_curve.png
│   ├── heatmap_packet_loss_delay.png
│   └── robustness_comparison.png
│
└── tables/
    ├── main_results.csv
    └── ablation_results.csv
```

---

# 45. Expected Visualizations

The final project should aim to produce figures such as:

### Packet Loss Curve

```text
Performance
    │
    │\
    │ \
    │  \
    │   \
    │    \
    └──────────────
       Packet Loss
```

### Delay Curve

```text
Performance
    │\
    │ \
    │  \
    │   \
    │    \
    └──────────────
          Delay
```

### Packet Loss × Delay Heatmap

```text
             Delay
        0   100  250  500  1000
      ┌─────────────────────────
  0%  │
  5%  │
 10%  │
 20%  │
 30%  │
      └─────────────────────────
       Packet Loss
```

### Robustness Comparison

Compare absolute performance and relative degradation for:

- baseline MARL,
- impaired MARL,
- robust MARL,
- optional adaptive MARL.

Do not select visualization styles based on which one makes a method appear better.

---

# 46. Limitations to Track

The final research should explicitly discuss limitations such as:

- simulation-to-reality gap,
- simplified communication model,
- limited network size,
- limited traffic-demand scenarios,
- assumptions about packet-loss independence,
- assumptions about delay distributions,
- computational constraints,
- RL training instability,
- sensitivity to random seeds.

These limitations are part of the research rather than something to hide.

---

# 47. Novelty Positioning

The project should **not** claim that packet loss, communication delay, or MARL traffic signal control are individually unexplored.

The novelty claim should be based on the exact implemented methodology and evidence.

Potential novelty dimensions include:

- systematic packet-loss × delay evaluation,
- explicit message freshness modeling,
- communication-aware robustness,
- adaptive communication,
- robustness degradation metrics,
- training across communication conditions,
- generalization to unseen communication conditions.

Any final novelty statement must be supported by a literature review.

---

# 48. Literature Review Requirements

The literature review should investigate at least these categories:

### Traffic Signal Control

- traditional traffic signal control,
- RL-based traffic signal control,
- MARL traffic signal control.

### Communication in MARL

- cooperative MARL,
- decentralized coordination,
- communication learning,
- communication-efficient MARL.

### Communication Impairments

- packet loss,
- communication delay,
- stale information,
- unreliable communication.

### Robust MARL

- robust reinforcement learning,
- robustness to observation uncertainty,
- robustness to communication failures.

### Intelligent Transportation Systems

- connected vehicles,
- cooperative traffic management,
- networked traffic control.

The literature review must distinguish:

```text
what is already established
```

from:

```text
what this project specifically investigates
```

---

# 49. Final Research Comparison

The central final comparison should conceptually answer:

```text
                Reliable
                   │
                   ▼
             Baseline MARL
                   │
                   ▼
        Communication Impairment
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
 Packet Loss               Delay
        │                     │
        └──────────┬──────────┘
                   ▼
          Combined Impairment
                   │
                   ▼
          Robust MARL
                   │
                   ▼
     Optional Adaptive Communication
```

The experiment should determine whether the robustness mechanism changes performance degradation under communication impairment.

The result must be determined by the data, not assumed in advance.

---

# 50. Completion Criteria

The project should be considered technically complete when:

- SUMO environment works,
- multiple intersections are controlled,
- MARL baseline trains,
- communication layer works,
- packet loss works,
- delay works,
- combined impairment works,
- robust mechanism works,
- experiments are reproducible,
- multiple seeds are evaluated,
- metrics are collected,
- statistical analysis is completed,
- ablations are completed where feasible,
- generalization is evaluated where feasible,
- documentation is complete,
- code is tested,
- Git history reflects genuine development,
- final results are traceable to configurations and commits.

---

# 51. Start Here

Do **not** immediately implement the entire project.

Start with **Phase 0 only**.

The first implementation task is:

1. Inspect the repository.
2. Inspect the existing Git state.
3. Verify Python.
4. Verify SUMO and `sumo-gui`.
5. Verify Git remote.
6. Create the initial project structure.
7. Create the Python project configuration.
8. Create the test structure.
9. Create the configuration structure.
10. Create/update `.gitignore`.
11. Create the initial documentation.
12. Run basic environment checks.
13. Run tests.
14. Review the Git diff.
15. Commit the completed Phase 0 work.
16. Push the genuine commit to GitHub.
17. Report exactly what was completed.

Do **not** begin Phase 1 until Phase 0 is verified.

---

# 52. Agent Operating Principle

The coding agent should develop the project incrementally.

The intended progression is:

```text
Phase 0
Project Setup
    ↓
Phase 1
SUMO Environment
    ↓
Phase 2
Single-Agent RL
    ↓
Phase 3
Multi-Agent RL
    ↓
Phase 4
Communication
    ↓
Phase 5
Packet Loss
    ↓
Phase 6
Delay
    ↓
Phase 7
Combined Impairments
    ↓
Phase 8
Robustness
    ↓
Phase 9
Robust Training
    ↓
Phase 10
Adaptive Communication
    ↓
Phase 11
Final Experiments
    ↓
Phase 12
Research Analysis + Paper
```

At every stage:

```text
Implement
→ Test
→ Verify
→ Document
→ Commit
→ Push
→ Continue
```

The project should prioritize **correctness, reproducibility, research integrity, and meaningful progression** over speed or superficial repository activity.

---

# 53. Authoritative Specification Rule

This file defines the intended research scope and methodology.

`AGENTS.md` defines coding-agent behavior and execution rules.

If implementation details need to change during development, the change should be documented.

Major changes to:

- research questions,
- hypotheses,
- title,
- experimental methodology,
- evaluation metrics,
- major contributions,
- baseline definitions

should be explicitly reviewed before implementation.

---

## End of PROJECT_SPEC.md