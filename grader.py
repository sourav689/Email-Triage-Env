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
    
    # ── FIX 1: VALIDATOR RANGE SAFETY ───────────────────────────────────────
    # If ground truth is missing or task didn't run, return 0.01 (not 0.0)
    if n <= 0:
        return 0.01

    # Ensure we only evaluate up to the number of emails available in ground truth
    # We use a copy to avoid modifying the original list
    taken = actions_taken[:n] if actions_taken else []

    # Initialize hits
    classification_hits = 0
    action_hits = 0
    priority_hits = 0

    # ── FIX 2: ROBUST DICTIONARY CHECKING ───────────────────────────────────
    # We iterate carefully to prevent any 'NoneType' or 'Attribute' errors
    for i in range(len(taken)):
        a = taken[i]
        g = ground_truth[i]
        
        if isinstance(a, dict):
            # 1. Classification (0.4 weight)
            # Checks if action matches the specific 'classification' key OR the general 'action_type'
            target_class = g.get("classification", g.get("action_type"))
            if a.get("action_type") == target_class:
                classification_hits += 1
            
            # 2. Action (0.3 weight)
            if a.get("action_type") == g.get("action_type"):
                action_hits += 1
            
            # 3. Priority (0.2 weight)
            if a.get("priority") == g.get("priority"):
                priority_hits += 1

    # Calculate raw accuracies
    classification_acc = classification_hits / n
    action_acc = action_hits / n
    priority_acc = priority_hits / n

    # 4. Efficiency Score (0.1 weight)
    # Penalize if the agent took more steps than there are emails
    steps_taken = len(actions_taken) if actions_taken else 0
    optimal_steps = n
    efficiency_raw = 1.0 - 0.05 * max(0, steps_taken - optimal_steps)
    efficiency_score = max(0.0, min(1.0, efficiency_raw))

    # Weighted Calculation
    score = (
        0.4 * classification_acc +
        0.3 * action_acc +
        0.2 * priority_acc +
        0.1 * efficiency_score
    )

    # ── THE CRITICAL VALIDATOR FIX ──────────────────────────────────────────
    # Clamping ensures the score is NEVER 0.0 and NEVER 1.0.
    # We use 0.01 and 0.99 to stay safely away from the 'out of range' boundaries.
    final_score = max(0.01, min(0.99, score))

    return round(float(final_score), 4)