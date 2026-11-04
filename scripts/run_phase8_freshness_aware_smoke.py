"""Run the Phase 8 freshness-aware functional verification smoke test."""

import json
from pathlib import Path

import numpy as np

from traffic_control.communication import CommunicationChannel, FreshnessConfig
from traffic_control.communication.freshness import NeighborInformationCache, TrafficSnapshot
from traffic_control.rl import (
    AGENT_IDS,
    CommunicationAwareEnvironmentConfig,
    CommunicationAwareLinearQAgent,
    CommunicationAwareMultiAgentEnvironment,
    LinearQAgent,
)


ROOT = Path(__file__).parents[1]


def main() -> None:
    freshness = FreshnessConfig(500.0, 2000.0, 1000.0)
    channel = CommunicationChannel(delay_ms=250.0, seed=42)
    message = channel.send("A0", "A1", {"schema_version": "traffic_observation_v1", "sender_id": "A0", "features": [0.1] * 5}, 10.0)
    unavailable = channel.receive("A1", 10.249)
    available = channel.receive("A1", 10.25)
    dropped = CommunicationChannel(packet_loss_probability=1.0, delay_ms=250.0, seed=42)
    dropped.send("A0", "A1", message.payload, 10.0)
    loss_telemetry = dropped.telemetry()

    cache = NeighborInformationCache(channel.topology)
    cache.update("A1", available[0])
    fresh = cache.observation("A1", 10.25, freshness)
    old = cache.observation("A1", 11.25, freshness)
    if unavailable or not available or fresh[2] <= old[2]:
        raise RuntimeError("Freshness-aware cache behavior failed")
    if loss_telemetry.pending_messages != 0:
        raise RuntimeError("Dropped message entered pending queue")

    config = CommunicationAwareEnvironmentConfig(
        sumo_config_file=ROOT / "sumo/simulation/grid.sumocfg",
        max_steps=1,
        communication_delay_ms=0.0,
        communication_seed=42,
        freshness=freshness,
    )
    environment = CommunicationAwareMultiAgentEnvironment(config)
    try:
        observations = environment.reset()
        learner = CommunicationAwareLinearQAgent(
            neighbor_ids=("A1", "B0"),
            freshness_decay_tau_ms=500.0,
            max_message_age_ms=2000.0,
            stale_message_threshold_ms=1000.0,
        )
        action = learner.select_action(observations["A0"])
        _, _, terminated, info = environment.step({agent_id: 0 for agent_id in AGENT_IDS})
        local_agent = LinearQAgent(5, 2)
        local_action = local_agent.select_action(np.zeros(5, dtype=np.float32))
        if observations["A0"].shape != (23,) or action not in (0, 1) or local_action not in (0, 1):
            raise RuntimeError("Policy observation/action smoke check failed")
        output = {
            "functional_verification": True,
            "agents": list(AGENT_IDS),
            "neighbor_order_A0": list(environment.communication.topology.for_agent("A0")),
            "delayed_message_unavailable_at_10_249": not unavailable,
            "delayed_message_available_at_10_250": bool(available),
            "message_generation_timestamp": message.generation_timestamp,
            "message_delivery_timestamp": available[0].delivery_timestamp,
            "freshness_weight_at_zero_age": fresh[2],
            "freshness_weight_after_1000ms": old[2],
            "observation_shape": list(observations["A0"].shape),
            "communication_aware_action": action,
            "local_only_action": local_action,
            "sumo_step_terminated": terminated,
            "simulation_time": info["simulation_time"],
            "packet_loss_dropped_messages": loss_telemetry.dropped_messages,
        }
    finally:
        environment.close()
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
