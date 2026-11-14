# Phase 11 follow-up v2 — development protocol

This document preserves the first development-pilot design. The later
[reserved-seed protocol](PHASE11_RESERVED_PROTOCOL.md) records the accepted
completion work, including phase-relative observations, training termination,
81 episodes and metadata scale 0.1. In that version, the four active metadata
coordinates are bounded by the actual scaled range, not the pilot's unit
range. Each design retains its own committed source and output directory.

On 2026-11-13 the user authorized correction of the audit findings and selected
action-sensitive communication within existing linear IQL. This is a new,
exploratory protocol. The original Phase 11 record and unfavorable findings
remain unchanged. No novelty/superiority conclusion or Phase 12 paper is
authorized by these changes.

## Measurement and preservation

The primary field in v2 is SUMO tripinfo `waitingTime` summed over all departed
vehicles, divided by that count. Unfinished vehicles contribute waiting up to
the horizon. Always report departed/expected demand, uninserted vehicles,
unfinished trips, completion fraction, completed-trip mean travel time, stops,
departure delay, queue and communication cost. A censored low-wait result is
not evidence of improvement. Source:
[SUMO TripInfo](https://sumo.dlr.de/docs/Simulation/Output/TripInfo.html).

Historical snapshot metrics remain available only for reproducing v1; do not
pool schemas. Original `results/phase11` is read-only to the legacy runner.
New directories have a manifest covering resolved configuration, source,
environment and checkpoint identity. Failed attempts are retained; successful
logical runs are never retried or counted twice. Raw tripinfo and training
records are preserved in the versioned campaign directory.

## Focused research direction

Investigate receiver-local action-margin requests: use the receiving linear
Q function and its cached inputs to determine whether bounded unknown neighbor
features could change its greedy action. If the action is invariant over the
declared feature box, suppress a request; otherwise request the most influential
neighbor(s), subject to a cooldown and heartbeat. Both request and response
packets traverse the real lossy/delayed channel and count toward cost. No gate
may inspect undelivered true neighbor state. A margin certificate concerns
the fitted policy on a declared input set, not optimality or physical safety.

The comparison set will retain local-only, communication without freshness,
full freshness, and component ablations. All use the same linear learner,
training budget, exploration schedule, reward and signal constraints. Always,
periodic, state-change and action-sensitive strategies use the same frozen
checkpoint for communication-cost comparisons.

### Implemented gate and its limits

For greedy action a and the other action b, let c = W[a] - W[b], current
margin m = Q[a](x) - Q[b](x), and fixed-local / uncertain-neighbor box [l,u].
The minimum possible margin is exactly
`m + sum(min(c * (l-x), c * (u-x)))`. Request suppression is certified when
this is strictly positive, or when the margin cannot vary at all. Both
neighbor blocks vary jointly; separate one-neighbor tests would miss combined
flips. Unknown active coordinates span [0,1]; disabled ablation coordinates
remain zero. This is deliberately conservative and makes no unverified
traffic-rate-of-change assumption. It may request unnecessarily.

Every receiver uses only its own policy and delivered cache. Influential
neighbors are requested when the joint certificate fails, with a 1 s
per-link cooldown and 5 s heartbeat. Requests and responses incur the same
configured loss/delay independently. `periodic_pull` uses the same request
protocol/cooldown without the margin gate, isolating gating from push/pull
overhead. Payload-byte counts cover serialized JSON payloads, not physical
wire overhead. Terminal snapshots are suppressed; legitimate responses to
earlier requests may still be sent at the horizon.

Feature modes are `local`, `plain` (neighbor payload without metadata/decay),
`full`, `no_age`, `no_availability`, `no_decay` (raw payload, zero freshness
coordinate), and `no_stale`. Single-coordinate ablations test encoder
components: for example, `no_age` retains freshness/stale clues and must not
be described as removing every source of age information.

The follow-up reward is negative local queue integrated over simulation
ticks, replacing the endpoint-sensitive delta reward only in v2. All v2
baselines share it. Minimum green is 5 s and yellow 3 s. There is no all-red
clearance in the original two-green network; these simulator constraints are
not a real-world safety certification. Time-resolved communication and the
new reward/horizon require new checkpoints, not reuse of the original ones.

Timing will separate 50 ms simulation ticks, 100 ms communication opportunities
and one-second action decisions. This permits fresh-generation timestamps to
distinguish the specified subsecond delays at decision times. Signal changes
must respect minimum green and yellow instead of jumping between greens.
The network remains the existing four junctions; a separate seeded demand
scenario and a longer horizon replace the six-vehicle 20-second smoke scenario.

Training conditions exclude the held-out loss/delay values. Development seeds
and evaluation seeds are disjoint. Only a bounded development pilot is planned
in this task; it cannot establish convergence or a final generalization claim.
Final budgets must be chosen from development learning curves before freezing
a later confirmatory campaign. Analysis pairs by master seed and evaluation
scenario, averages repeated conditions within seed, and reports uncertainty
without treating identical scheduling runs as independent replications.

### Pilot frozen before collection

`configs/followup_v2.yaml` fixes two development seeds (20261, 20262), four
training episodes, five variants (local, plain ideal/robust, full ideal/robust),
20 seeded vehicles departing over 30 s, and a 120 s horizon. The resulting
10 checkpoint sets require 40 training episodes and 50 frozen evaluations.
At most two independent SUMO worker processes run concurrently, each with
isolated TraCI state, seeds, checkpoints and output paths.
Evaluation cells are (0,0), (0.1,250 ms), and held-out (0.3,1000 ms). The full
robust checkpoint is reused for all five communication strategies. The other
variants use always-transmit. All methods use learning rate 0.01, discount
0.95 and constant training epsilon 0.2; evaluation epsilon is zero.

Robust training cycles through the nine combinations of losses {0,0.1,0.2}
and delays {0,250,500} ms. Four pilot episodes are an incomplete first shuffled
cycle, explicitly recorded, not proof of adequate exposure. All component
ablations and the complete 25-cell evaluation are executable in the larger
exploratory design but are not silently included in this bounded pilot.
Its default 25-episode budget remains a development starting point, not a
validated final training budget. One evaluation stream per master seed limits
statistical inference, particularly with only two development seeds.

The same traffic seeds and generated demand are paired across variants. Loss
uses a separate sequential seeded RNG; strategies consume different numbers
of draws, so equal seeds do not imply equal per-packet outcomes. All requests,
responses, drops, pending packets, cache ages and suppression reasons are
recorded. Negative savings and incomplete trips must remain visible.

Lane subscriptions return the same SUMO state variables at each 50 ms tick;
they reduce repeated remote calls without changing reward/queue sampling.
Tripinfo supplies authoritative vehicle waiting/travel metrics after closure.

Run a read-only design audit with `python scripts/run_followup.py --mode audit`.
After committing the source, run the bounded pilot with
`python scripts/run_followup.py --mode pilot --output results/followup_v2/development_001`.
Use `--mode analyze` on the same output to regenerate processed summaries.
`--mode run` executes the larger exploratory configuration and should be
budgeted separately. `--retry-failed` only retries failed logical runs and
preserves their earlier records. Any changed design/source requires a new
output directory. A source manifest is recorded before training.

The frozen pilot was subsequently collected at commit `eada4cd`; see the
[development results](FOLLOWUP_DEVELOPMENT_RESULTS.md). Its unsuccessful traffic
outcomes are preserved. This protocol was not retuned after those outcomes.

## Literature positioning (checked 2026-11-13)

Selective communication itself is established. IC3Net learns communication
gating: Singh, Jain and Sukhbaatar,
[Learning when to Communicate at Scale](https://arxiv.org/abs/1812.09755),
ICLR 2019. Hu et al.,
[Event-Triggered Multi-agent Reinforcement Learning with Communication under
Limited-bandwidth Constraint](https://arxiv.org/abs/2010.04978), 2020,
studies bandwidth-aware event triggering. Zhang et al.,
[VIL2C](https://arxiv.org/abs/2511.19146), 2025 preprint,
studies information value and communication latency. These are related work,
not algorithms reproduced by this repository.

The candidate differentiation is an interpretable linear action-invariance
test coupled to causal request/response accounting, explicit packet loss and
age, and traffic-control ablations. This limited search does not establish
that the combination is new. The contribution must be supported by broader
literature comparison and controlled evidence, including negative results.
