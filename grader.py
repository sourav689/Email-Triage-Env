from typing import List, Dict

EPSILON = 1e-6
SMOOTH  = 0.01   # additive smoothing constant


def _smooth(hits: int, total: int) -> float:
    """Laplace-smoothed accuracy — never returns exact 0.0 or 1.0."""
    return (hits + SMOOTH) / (total + 2 * SMOOTH)


def _clamp(value: float) -> float:
    """Strictly open interval (0, 1) — never touches either boundary."""
    return max(EPSILON, min(1.0 - EPSILON, value))


def compute_final_score(
    actions_taken: List[Dict],
    ground_truth: List[Dict],
) -> float:

    n = len(ground_truth)
    if n == 0:
        return _clamp(0.5)

    taken = actions_taken[:n]

    if not taken:
        return _clamp(SMOOTH / (1 + 2 * SMOOTH))

    classification_hits = sum(
        1 for a, g in zip(taken, ground_truth)
        if a.get("action_type") == g.get("classification", g["action_type"])
    )
    action_hits = sum(
        1 for a, g in zip(taken, ground_truth)
        if a.get("action_type") == g["action_type"]
    )
    priority_hits = sum(
        1 for a, g in zip(taken, ground_truth)
        if a.get("priority") == g["priority"]
    )

    # ✅ FIX 1: use effective_n instead of n
    effective_n = len(taken)

    classification_accuracy = _smooth(classification_hits, effective_n)
    action_accuracy         = _smooth(action_hits, effective_n)
    priority_accuracy       = _smooth(priority_hits, effective_n)

    steps_taken   = len(actions_taken)
    optimal_steps = n

    # ✅ FIX 2: remove redundant EPSILON max
    raw_efficiency = 1.0 - 0.05 * max(0, steps_taken - optimal_steps)
    efficiency_score = _clamp(raw_efficiency)

    raw_score = (
        0.4 * classification_accuracy +
        0.3 * action_accuracy +
        0.2 * priority_accuracy +
        0.1 * efficiency_score
    )

    # ✅ FIX 3: double clamp (before + after rounding)
    score = _clamp(raw_score)
    score = round(score, 6)
    return _clamp(score)