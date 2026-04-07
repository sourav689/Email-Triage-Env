from typing import List, Dict

def compute_final_score(
    actions_taken: List[Dict],
    ground_truth: List[Dict],
) -> float:
    """
    Computes a weighted score based on classification, action, priority, and efficiency.
    Strictly returns a value between 0.01 and 0.99 to pass Phase 2 validation.
    """
    n = len(ground_truth)
    
    # Error Fix: Never return 0.0. Return 0.01 if no ground truth exists.
    if n == 0:
        return 0.01

    # Ensure we only evaluate up to the number of emails provided
    taken = actions_taken[:n]

    # 1. Classification Accuracy (0.4 weight)
    classification_hits = sum(
        1 for a, g in zip(taken, ground_truth)
        if a and a.get("action_type") == g.get("classification", g.get("action_type"))
    )
    
    # 2. Action Accuracy (0.3 weight)
    action_hits = sum(
        1 for a, g in zip(taken, ground_truth)
        if a and a.get("action_type") == g.get("action_type")
    )
    
    # 3. Priority Accuracy (0.2 weight)
    priority_hits = sum(
        1 for a, g in zip(taken, ground_truth)
        if a and a.get("priority") == g.get("priority")
    )

    classification_accuracy = classification_hits / n
    action_accuracy = action_hits / n
    priority_accuracy = priority_hits / n

    # 4. Efficiency Score (0.1 weight)
    steps_taken = len(actions_taken)
    optimal_steps = n
    # Penalize extra steps taken beyond the number of emails
    efficiency_score = max(
        0.0,
        1.0 - 0.05 * max(0, steps_taken - optimal_steps)
    )

    # Weighted Calculation
    score = (
        0.4 * classification_accuracy +
        0.3 * action_accuracy +
        0.2 * priority_accuracy +
        0.1 * efficiency_score
    )

    # ── THE CRITICAL VALIDATOR FIX ──────────────────────────────────────────
    # Clamping ensures the score is NEVER 0.0 and NEVER 1.0.
    # This keeps the value strictly within the (0, 1) range as required.
    final_score = max(0.01, min(0.99, score))

    return round(final_score, 4)