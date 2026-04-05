from typing import List, Dict


def compute_final_score(
    actions_taken: List[Dict],
    ground_truth: List[Dict],
) -> float:
    n = len(ground_truth)
    if n == 0:
        return 0.0

    taken = actions_taken[:n]

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

    classification_accuracy = classification_hits / n
    action_accuracy = action_hits / n
    priority_accuracy = priority_hits / n

    steps_taken = len(actions_taken)
    optimal_steps = n
    efficiency_score = max(
        0.0,
        1.0 - 0.05 * max(0, steps_taken - optimal_steps)
    )

    score = (
        0.4 * classification_accuracy +
        0.3 * action_accuracy +
        0.2 * priority_accuracy +
        0.1 * efficiency_score
    )

    return round(min(1.0, max(0.0, score)), 4)