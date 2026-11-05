"""Run short functional verification for Phase 10 communication scheduling."""

import json
from pathlib import Path

import numpy as np

from traffic_control.communication import CommunicationScheduler, FreshnessConfig
from traffic_control.rl import (
    AGENT_IDS,
    CommunicationAwareEnvironmentConfig,
    CommunicationAwareLinearQAgent,
    CommunicationAwareMultiAgentEnvironment,
)


ROOT = Path(__file__).parents[1]


def scheduler_checks() -> dict[str, object]:
    state = np.zeros(5, dtype=np.float32)
    changed = np.full(5, 0.2, dtype=np.float32)
    always = CommunicationScheduler(("A0",), strategy="always")
    periodic = CommunicationScheduler(("A0",), strategy="periodic", periodic_interval_ms=1000)
    adaptive = CommunicationScheduler(
        ("A0",), strategy="adaptive", change_threshold=0.1, max_silence_ms=1000
    )
    always_decisions = [always.should_transmit("A0", state, time) for time in (0.0, 1.0)]
    periodic_decisions = [periodic.should_transmit("A0", state, time) for time in (0.0, 0.5, 1.0)]
    adaptive_decisions = [
        adaptive.should_transmit("A0", state, 0.0),
        adaptive.should_transmit("A0", state, 0.1),
        adaptive.should_transmit("A0", changed, 0.2),
        adaptive.should_transmit("A0", changed, 1.2),
    ]
    return {
        "always_transmits": all(decision.transmit for decision in always_decisions),
        "periodic_transmits_at_boundary": periodic_decisions[-1].trigger_reason == "periodic",
        "adaptive_suppresses_stable": not adaptive_decisions[1].transmit,
        "adaptive_triggers_change": adaptive_decisions[2].trigger_reason == "change",
        "adaptive_triggers_heartbeat": adaptive_decisions[3].trigger_reason == "heartbeat",
        "adaptive_telemetry": adaptive.telemetry().__dict__,
    }


def main() -> None:
    checks = scheduler_checks()
    environment = CommunicationAwareMultiAgentEnvironment(
        CommunicationAwareEnvironmentConfig(
            sumo_config_file=ROOT / "sumo/simulation/grid.sumocfg",
            max_steps=2,
            communication_strategy="adaptive",
            adaptive_change_threshold=0.1,
            adaptive_max_silence_ms=1000,
            communication_delay_ms=250,
            communication_packet_loss_probability=0.0,
            communication_seed=42,
            freshness=FreshnessConfig(500.0, 2000.0, 1000.0),
        )
    )
    try:
        observations = environment.reset()
        actions = {agent_id: 0 for agent_id in AGENT_IDS}
        _, _, _, info = environment.step(actions)
        scheduler = info["communication_scheduler"]
        telemetry = info["communication"]
        learner = CommunicationAwareLinearQAgent(
            neighbor_ids=("A1", "B0"), seed=42
        )
        action = learner.select_action(observations["A0"])
        output = {
            "functional_verification": True,
            "topology_A0": list(environment.communication.topology.for_agent("A0")),
            "scheduler_checks": checks,
            "observation_shape": list(observations["A0"].shape),
            "policy_action": action,
            "scheduler_opportunities": scheduler.scheduling_opportunities,
            "scheduled_agent_transmissions": scheduler.scheduled_transmissions,
            "suppressed_agent_transmissions": scheduler.suppressed_transmissions,
            "communication_send_attempts": telemetry.send_attempts,
            "pending_messages": telemetry.pending_messages,
            "simulation_time_after_one_step": info["simulation_time"],
            "note": "Functional verification only; not a research conclusion.",
        }
    finally:
        environment.close()
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
