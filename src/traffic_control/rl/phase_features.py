"""Five normalized, phase-relative features for the existing linear learner."""

import numpy as np


def phase_features(served_queue, opposed_queue, served_count, opposed_count,
                   now, green_since, yellow_deadline, minimum_green, yellow_seconds):
    """Keep conflicting demands distinct and expose transition readiness.

    Clock [0,.5) denotes progress through yellow; [.5,1] denotes progress
    through minimum green. One denotes an eligible green. Relative approach
    ordering follows the held green during yellow and rotates at its end.
    """
    if yellow_deadline is None:
        clock = .5 + .5 * min(max(now-green_since, 0.) / minimum_green, 1.)
    else:
        clock = .5 * (1 - min(max(yellow_deadline-now, 0.) / yellow_seconds, 1.))
    return np.clip(np.asarray([served_queue/10, opposed_queue/10,
                               served_count/20, opposed_count/20, clock], dtype=np.float32), 0, 1)
