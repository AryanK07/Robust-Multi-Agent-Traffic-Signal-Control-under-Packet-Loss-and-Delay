"""Small NumPy-only linear Q-learning agent for Phase 2."""

from pathlib import Path
from typing import Any

import numpy as np


class LinearQAgent:
    """Approximate action values with a linear model and online TD updates."""

    def __init__(
        self,
        observation_size: int,
        action_size: int,
        learning_rate: float = 0.05,
        discount_factor: float = 0.95,
        seed: int = 42,
    ) -> None:
        if observation_size <= 0 or action_size <= 0:
            raise ValueError("Observation and action sizes must be positive")
        self.observation_size = observation_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self._rng = np.random.default_rng(seed)
        self.weights = np.zeros((action_size, observation_size), dtype=np.float64)
        self.bias = np.zeros(action_size, dtype=np.float64)

    def q_values(self, observation: np.ndarray) -> np.ndarray:
        """Return predicted values for every discrete action."""
        observation = self._validate_observation(observation)
        return self.weights @ observation + self.bias

    def select_action(self, observation: np.ndarray, epsilon: float = 0.0) -> int:
        """Select an epsilon-greedy action with deterministic tie-breaking."""
        if not 0.0 <= epsilon <= 1.0:
            raise ValueError("Epsilon must be in [0, 1]")
        if self._rng.random() < epsilon:
            return int(self._rng.integers(self.action_size))
        return int(np.argmax(self.q_values(observation)))

    def update(
        self,
        observation: np.ndarray,
        action: int,
        reward: float,
        next_observation: np.ndarray,
        terminated: bool,
    ) -> float:
        """Perform one linear Q-learning update and return the TD error."""
        observation = self._validate_observation(observation)
        next_observation = self._validate_observation(next_observation)
        if not 0 <= action < self.action_size:
            raise ValueError(f"Action must be in [0, {self.action_size})")
        prediction = self.q_values(observation)[action]
        target = reward if terminated else reward + self.discount_factor * np.max(
            self.q_values(next_observation)
        )
        td_error = target - prediction
        self.weights[action] += self.learning_rate * td_error * observation
        self.bias[action] += self.learning_rate * td_error
        return float(td_error)

    def save(self, path: str | Path) -> None:
        """Save model parameters and hyperparameters to a portable NPZ file."""
        model_path = Path(path)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(
            model_path,
            weights=self.weights,
            bias=self.bias,
            observation_size=self.observation_size,
            action_size=self.action_size,
            learning_rate=self.learning_rate,
            discount_factor=self.discount_factor,
        )

    @classmethod
    def load(cls, path: str | Path, seed: int = 42) -> "LinearQAgent":
        """Load a saved model and restore its dimensions and hyperparameters."""
        with np.load(path) as data:
            agent = cls(
                int(data["observation_size"]),
                int(data["action_size"]),
                float(data["learning_rate"]),
                float(data["discount_factor"]),
                seed,
            )
            agent.weights = data["weights"].copy()
            agent.bias = data["bias"].copy()
        return agent

    def _validate_observation(self, observation: np.ndarray) -> np.ndarray:
        array = np.asarray(observation, dtype=np.float64)
        if array.shape != (self.observation_size,):
            raise ValueError(
                f"Observation must have shape {(self.observation_size,)}, got {array.shape}"
            )
        return array
