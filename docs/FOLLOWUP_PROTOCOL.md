# Phase 11 follow-up v2 — development protocol

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
