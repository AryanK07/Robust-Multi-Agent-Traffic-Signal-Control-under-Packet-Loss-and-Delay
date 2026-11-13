"""Versioned, time-resolved small-network environment for follow-up research."""

from collections import Counter
from dataclasses import dataclass, field
import json
from math import isfinite
from pathlib import Path
from typing import Mapping

import numpy as np
import traci.constants as tc

from traffic_control.communication import CommunicationChannel, CommunicationScheduler, FreshnessConfig
from traffic_control.communication.action_margin import action_margin_certificate
from traffic_control.communication.freshness import NeighborInformationCache, TrafficSnapshot
from traffic_control.environment import SumoEnvironment, SumoEnvironmentConfig
from traffic_control.environment.safe_signals import SafeSignalTransitions
from traffic_control.environment.traffic_state import IntersectionTrafficState
from .multi_agent_env import AGENT_IDS
from .q_learning import LinearQAgent
from .phase_features import phase_features
from traffic_control.communication.freshness import FEATURE_SCHEMA_VERSION, PHASE_FEATURE_SCHEMA


FEATURE_MODES = ("local", "plain", "full", "no_age", "no_availability", "no_decay", "no_stale")
STRATEGIES = ("always", "periodic", "adaptive", "periodic_pull", "action_sensitive")


@dataclass(frozen=True)
class FollowupEnvironmentConfig:
    sumo_config_file: Path
    tripinfo_output: Path
    backend: str = "traci"
    observation_schema: str = FEATURE_SCHEMA_VERSION
    metadata_scale: float = 1.0
    horizon_seconds: float = 120.0
    simulation_step: float = 0.05
    communication_interval: float = 0.1
    decision_interval: float = 1.0
    minimum_green: float = 5.0
    yellow_seconds: float = 3.0
    seed: int = 42
    packet_loss_seed: int = 43
    packet_loss: float = 0.0
    delay_ms: float = 0.0
    feature_mode: str = "full"
    strategy: str = "always"
    periodic_interval_ms: float = 1000.0
    change_threshold: float = 0.1
    heartbeat_ms: float = 5000.0
    request_cooldown_ms: float = 1000.0
    freshness: FreshnessConfig = field(default_factory=FreshnessConfig)

    def __post_init__(self):
        if not isfinite(self.metadata_scale) or not 0 < self.metadata_scale <= 1:
            raise ValueError('metadata_scale must lie in (0,1]')
        if self.observation_schema not in (FEATURE_SCHEMA_VERSION, PHASE_FEATURE_SCHEMA):
            raise ValueError('unsupported observation schema')
        durations = (self.simulation_step, self.communication_interval,
                     self.decision_interval, self.horizon_seconds,
                     self.minimum_green, self.yellow_seconds, self.request_cooldown_ms)
        if any(not isfinite(value) or value <= 0 for value in durations):
            raise ValueError("time intervals must be positive and finite")
        for value in durations[1:6]:
            if not np.isclose(value / self.simulation_step, round(value / self.simulation_step)):
                raise ValueError("intervals must be multiples of simulation_step")
        if not np.isclose(self.horizon_seconds / self.decision_interval,
                          round(self.horizon_seconds / self.decision_interval)):
            raise ValueError("horizon must contain whole decisions")
        if self.feature_mode not in FEATURE_MODES or self.strategy not in STRATEGIES:
            raise ValueError("unsupported feature mode or strategy")
        if self.feature_mode == "local" and self.strategy != "always":
            raise ValueError("local-only mode has no communication strategy")


class FollowupEnvironment:
    """Receive between action decisions; count request and response costs.

    Gate inputs belong solely to each receiver: its own policy, local state
    and delivered cache. The sender samples its own state only after a request
    is delivered. Nonzero delay therefore applies to both legs.
    """

    def __init__(self, config: FollowupEnvironmentConfig, policies: Mapping[str, LinearQAgent]):
        self.config = config
        self.policies = policies
        if set(policies) != set(AGENT_IDS):
            raise ValueError("one policy per intersection is required")
        size = 5 if config.feature_mode == "local" else 23
        if any(p.observation_size != size or p.action_size != 2 for p in policies.values()):
            raise ValueError("incompatible follow-up policy dimensions")
        self.simulator = SumoEnvironment(SumoEnvironmentConfig(
            config_file=config.sumo_config_file, seed=config.seed,
            step_length=config.simulation_step, tripinfo_output=config.tripinfo_output,
            collect_legacy_metrics=False, backend=config.backend))
        self.channel = CommunicationChannel(packet_loss_probability=config.packet_loss,
                                            delay_ms=config.delay_ms, seed=config.packet_loss_seed)
        self.cache = NeighborInformationCache(self.channel.topology, config.observation_schema)
        self.scheduler = CommunicationScheduler(AGENT_IDS,
            strategy=config.strategy if config.strategy in ("always", "periodic", "adaptive") else "always",
            periodic_interval_ms=config.periodic_interval_ms,
            change_threshold=config.change_threshold, max_silence_ms=config.heartbeat_ms)
        self._last_request = {}
        self.counts = Counter()
        self.payload_bytes = 0
        self.age_samples = []
        self.missing_samples = []
        self._ticks = 0
        self._local = {}
        self._states = {}
        self._queue_total = self._queue_samples = self._max_queue = 0
        self._delivery_delay_sum = self._delivery_count = 0

    def reset(self):
        self.simulator.reset()
        self.channel.reset_episode()
        self.cache.clear()
        self.scheduler.reset()
        self._last_request.clear()
        self.counts.clear()
        self.payload_bytes = 0
        self.age_samples.clear()
        self.missing_samples.clear()
        self._ticks = 0
        self._queue_total = self._queue_samples = self._max_queue = 0
        self._delivery_delay_sum = self._delivery_count = 0
        connection = self.simulator._require_started()
        self._lanes = {agent: tuple(dict.fromkeys(connection.trafficlight.getControlledLanes(agent)))
                       for agent in AGENT_IDS}
        self._all_lanes = tuple(connection.lane.getIDList())
        self._served_lanes = {}
        if self.config.observation_schema == PHASE_FEATURE_SCHEMA:
            for agent in AGENT_IDS:
                links = connection.trafficlight.getControlledLinks(agent)
                phases = connection.trafficlight.getAllProgramLogics(agent)[0].phases
                for green in (0, 2):
                    self._served_lanes[(agent, green)] = {
                        link[0] for index, group in enumerate(links)
                        for link in group if phases[green].state[index] in 'Gg'}
                first, second = (self._served_lanes[(agent, green)] for green in (0, 2))
                if first & second or first | second != set(self._lanes[agent]):
                    raise ValueError('phase-relative encoder requires two disjoint served lane groups')
        for lane in self._all_lanes:
            connection.lane.subscribe(lane, (tc.LAST_STEP_VEHICLE_NUMBER, tc.VAR_WAITING_TIME,
                                             tc.LAST_STEP_VEHICLE_HALTING_NUMBER, tc.LAST_STEP_OCCUPANCY))
        self.signals = SafeSignalTransitions(connection, AGENT_IDS,
                                            self.config.minimum_green, self.config.yellow_seconds)
        self._read_local()
        self._communicate(True)
        return self.observations()

    @property
    def time(self):
        return self.simulator.simulation_time

    def _read_local(self):
        connection = self.simulator._require_started()
        self._lane_states = {lane: connection.lane.getSubscriptionResults(lane) for lane in self._all_lanes}
        self._states = {}
        for agent in AGENT_IDS:
            lanes = [self._lane_states[lane] for lane in self._lanes[agent]]
            green, _, deadline = self.signals.state[agent]
            self._states[agent] = IntersectionTrafficState(
                agent, sum(v[tc.LAST_STEP_VEHICLE_NUMBER] for v in lanes),
                sum(v[tc.VAR_WAITING_TIME] for v in lanes),
                sum(v[tc.LAST_STEP_VEHICLE_HALTING_NUMBER] for v in lanes),
                float(np.mean([v[tc.LAST_STEP_OCCUPANCY] for v in lanes])),
                green if deadline is None else green + 1)
        self._local = {agent: np.clip(np.asarray([
            state.queue_length / 10, state.waiting_time / 100,
            state.vehicle_count / 20, state.lane_occupancy / 100, state.phase / 3,
        ], dtype=np.float32), 0, 1) for agent, state in self._states.items()}
        if self.config.observation_schema == PHASE_FEATURE_SCHEMA:
            for agent in AGENT_IDS:
                green, since, deadline = self.signals.state[agent]
                served = self._served_lanes[(agent, green)]
                opposed = set(self._lanes[agent]) - served
                def total(lanes, variable):
                    return sum(self._lane_states[lane][variable] for lane in lanes)
                self._local[agent] = phase_features(
                    total(served, tc.LAST_STEP_VEHICLE_HALTING_NUMBER),
                    total(opposed, tc.LAST_STEP_VEHICLE_HALTING_NUMBER),
                    total(served, tc.LAST_STEP_VEHICLE_NUMBER),
                    total(opposed, tc.LAST_STEP_VEHICLE_NUMBER), self.time, since,
                    deadline, self.config.minimum_green, self.config.yellow_seconds)

    def observation(self, agent):
        if self.config.feature_mode == "local":
            return self._local[agent].copy()
        blocks = np.asarray(self.cache.observation(agent, self.time, self.config.freshness), dtype=float)
        for index, neighbor in enumerate(self.channel.topology.for_agent(agent)):
            start = index * 9
            mode = self.config.feature_mode
            if mode in ("plain", "no_decay"):
                state = self.cache.get(agent, neighbor)
                blocks[start+4:start+9] = state.features if state else np.zeros(5)
            if mode == "plain":
                blocks[start:start+4] = 0
            elif mode == "no_age":
                blocks[start+1] = 0
            elif mode == "no_availability":
                blocks[start] = 0
            elif mode == "no_decay":
                blocks[start+2] = 0
            elif mode == "no_stale":
                blocks[start+3] = 0
            blocks[start:start+4] *= self.config.metadata_scale
        return np.asarray([*self._local[agent], *blocks], dtype=np.float32)

    def observations(self):
        return {agent: self.observation(agent) for agent in AGENT_IDS}

    def _bounds(self, obs):
        lower, upper = obs.astype(float).copy(), obs.astype(float).copy()
        lower[5:], upper[5:] = 0, 1
        for start in (5, 14):
            upper[start:start+4] = float(np.float32(self.config.metadata_scale))
        fixed = {"plain": (0, 1, 2, 3), "no_age": (1,), "no_availability": (0,),
                 "no_decay": (2,), "no_stale": (3,)}.get(self.config.feature_mode, ())
        for start in (5, 14):
            for offset in fixed:
                lower[start+offset] = upper[start+offset] = 0
        return lower, upper

    def _send(self, sender, receiver, payload, kind):
        self.channel.send(sender, receiver, payload, self.time)
        self.counts[f"{kind}_attempts"] += 1
        self.payload_bytes += len(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())

    def _snapshot(self, sender, receiver, kind="snapshot"):
        payload = dict(TrafficSnapshot(sender, tuple(map(float, self._local[sender])), self.time,
                                      self.config.observation_schema).to_payload())
        payload["kind"] = "snapshot"
        self._send(sender, receiver, payload, kind)

    def _drain(self):
        # A request can generate one response, never another request. Two
        # passes remove topology-order bias for zero-delay round trips.
        for _ in range(2):
            for receiver in AGENT_IDS:
                for message in self.channel.receive(receiver, self.time):
                    self._delivery_delay_sum += (self.time-message.generation_timestamp)*1000
                    self._delivery_count += 1
                    if message.payload.get("kind") == "request":
                        self._snapshot(receiver, message.sender_id, "response")
                    else:
                        self.cache.update(receiver, message)

    def _communicate(self, opportunity):
        if self.config.feature_mode == "local":
            return
        self._drain()
        if opportunity:
            if self.config.strategy in ("action_sensitive", "periodic_pull"):
                self._request_round()
            else:
                for sender in AGENT_IDS:
                    decision = self.scheduler.should_transmit(sender, self._local[sender], self.time)
                    self.counts[f"push_{decision.trigger_reason}"] += 1
                    if decision.transmit:
                        for receiver in self.channel.topology.for_agent(sender):
                            self._snapshot(sender, receiver)
            self._drain()

    def _request_round(self):
        for receiver in AGENT_IDS:
            obs = self.observation(receiver)
            policy = self.policies[receiver]
            decision = action_margin_certificate(obs, policy.weights, policy.bias, *self._bounds(obs))
            self.counts["invariant_checks" if decision.invariant else "uncertain_checks"] += 1
            for index, sender in enumerate(self.channel.topology.for_agent(receiver)):
                key = (receiver, sender)
                last = self._last_request.get(key)
                elapsed = (self.time - last) * 1000 if last is not None else float("inf")
                if elapsed + 1e-6 < self.config.request_cooldown_ms:
                    self.counts["request_cooldown"] += 1
                    continue
                reason = None
                if last is None:
                    reason = "first"
                elif elapsed + 1e-6 >= self.config.heartbeat_ms:
                    reason = "heartbeat"
                elif self.config.strategy == "periodic_pull":
                    reason = "periodic"
                elif not decision.invariant and decision.neighbor_risks[index] > 0:
                    reason = "margin"
                if reason:
                    self._send(receiver, sender, {"kind": "request"}, "request")
                    self.counts[f"request_{reason}"] += 1
                    self._last_request[key] = self.time
                else:
                    self.counts["request_suppressed"] += 1

    def step(self, actions):
        if set(actions) != set(AGENT_IDS) or any(action not in (0, 1) for action in actions.values()):
            raise ValueError("one binary action per intersection is required")
        if self.time + 1e-9 >= self.config.horizon_seconds:
            raise RuntimeError("episode has ended")
        for agent, action in actions.items():
            self.signals.request(agent, action, self.time)
        reward = dict.fromkeys(AGENT_IDS, 0.0)
        ticks = round(self.config.decision_interval / self.config.simulation_step)
        period = round(self.config.communication_interval / self.config.simulation_step)
        for _ in range(ticks):
            self.simulator.step()
            self._ticks += 1
            self.signals.advance(self.time)
            self._read_local()
            queue = sum(values[tc.LAST_STEP_VEHICLE_HALTING_NUMBER] for values in self._lane_states.values())
            self._queue_total += queue
            self._queue_samples += 1
            self._max_queue = max(self._max_queue, queue)
            for agent in AGENT_IDS:
                reward[agent] -= self._states[agent].queue_length * self.config.simulation_step
            terminal = self.time + 1e-9 >= self.config.horizon_seconds
            self._communicate(self._ticks % period == 0 and not terminal)
        for receiver in AGENT_IDS:
            for sender in self.channel.topology.for_agent(receiver):
                state = self.cache.get(receiver, sender)
                self.missing_samples.append(state is None)
                if state:
                    self.age_samples.append(self.config.freshness.age_ms(state.generation_timestamp, self.time))
        return self.observations(), reward, terminal, self.telemetry()

    def telemetry(self):
        channel = self.channel.telemetry()
        return {
            "simulation_time": self.time,
            "communication": dict(channel.__dict__),
            "trigger_counts": dict(self.counts),
            "payload_bytes": self.payload_bytes,
            "mean_message_age_ms": float(np.mean(self.age_samples)) if self.age_samples else None,
            "max_message_age_ms": float(max(self.age_samples)) if self.age_samples else None,
            "mean_delivered_delay_ms": self._delivery_delay_sum/self._delivery_count if self._delivery_count else None,
            "missing_message_fraction": float(np.mean(self.missing_samples)) if self.missing_samples else None,
            "stale_message_fraction": float(np.mean(np.asarray(self.age_samples) >= self.config.freshness.stale_message_threshold_ms)) if self.age_samples else None,
            "mean_queue_length": self._queue_total / self._queue_samples if self._queue_samples else 0.,
            "max_queue_length": self._max_queue,
            "signal_switches": self.signals.switches,
        }

    def close(self):
        self.simulator.close()
