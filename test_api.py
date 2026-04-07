import requests
import json

BASE = "https://hugdevp-email-triage-env.hf.space"

def main():
    print("Testing live HF Space...")

    # 1. Reset environment
    r = requests.post(f"{BASE}/reset", params={"task": "easy"})
    r.raise_for_status()
    data = r.json()

    episode_id = data["episode_id"]
    obs = data["observation"]

    print(
        "Reset OK — episode_id:",
        episode_id[:8],
        "... total_emails:",
        obs["total_emails"],
    )

    # 2. Take a step
    r2 = requests.post(
        f"{BASE}/step",
        json={
            "episode_id": episode_id,
            "action_type": "ignore",
            "priority": "low",
            "email_id": obs["email_id"],
        },
    )
    r2.raise_for_status()
    step_data = r2.json()

    print(
        "Step OK — reward:",
        step_data["reward"],
        "done:",
        step_data["done"],
    )

    # 3. Get state
    r3 = requests.get(f"{BASE}/state")
    r3.raise_for_status()
    state = r3.json()

    print(
        "State OK — current_index:",
        state["current_index"],
    )

    # 4. Get metrics
    r4 = requests.get(f"{BASE}/metrics")
    r4.raise_for_status()
    metrics = r4.json()

    print(
        "Metrics OK — final_score:",
        metrics.get("final_score"),
    )

    print("\nALL LIVE CHECKS PASSED")


if __name__ == "__main__":
    main()