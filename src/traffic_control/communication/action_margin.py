"""Receiver-local action-invariance test for a two-action linear policy.

No simulator, neighbor ground truth, learned gate, or remote policy is used.
The certificate is conditional on input bounds and the fitted linear model.
"""

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class MarginDecision:
    action: int
    margin: float
    worst_case_margin: float
    invariant: bool
    neighbor_risks: tuple[float, float]


def action_margin_certificate(
    observation: np.ndarray, weights: np.ndarray, bias: np.ndarray,
    lower: np.ndarray, upper: np.ndarray,
) -> MarginDecision:
    """Minimize chosen-minus-alternative Q exactly over a feature box.

    Local features must be fixed. Neighbor coordinates may vary jointly;
    checking each neighbor separately would miss combined action flips.
    This conservative test allows even physically infeasible box corners.
    """
    observation, weights, bias, lower, upper = [np.asarray(v, dtype=float)
                                               for v in (observation, weights, bias, lower, upper)]
    if (observation.shape != (23,) or weights.shape != (2, 23)
            or bias.shape != (2,) or lower.shape != (23,) or upper.shape != (23,)):
        raise ValueError("expected a two-action, 23-feature linear policy")
    if not all(np.all(np.isfinite(v)) for v in (observation, weights, bias, lower, upper)):
        raise ValueError("policy and bounds must be finite")
    if np.any(lower > observation) or np.any(upper < observation):
        raise ValueError("observation must lie inside the declared box")
    if not (np.array_equal(lower[:5], observation[:5])
            and np.array_equal(upper[:5], observation[:5])):
        raise ValueError("local features must remain fixed")
    values = weights @ observation + bias
    action = int(np.argmax(values))
    coefficients = weights[action] - weights[1 - action]
    margin = float(values[action] - values[1 - action])
    reductions = -np.minimum(coefficients * (lower - observation),
                             coefficients * (upper - observation))
    risks = (float(sum(reductions[5:14])), float(sum(reductions[14:23])))
    worst = margin - sum(risks)
    return MarginDecision(action, margin, worst,
                          sum(risks) == 0.0 or worst > 1e-12, risks)
