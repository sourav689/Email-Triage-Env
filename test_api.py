import requests
import json
import time

BASE = "http://localhost:7860"

def assert_true(cond, msg):
    if not cond:
        raise Exception(f"[FAIL] {msg}")

def test_full_pipeline(task="hard"):
    print(f"\n🚀 TESTING TASK: {task.upper()}")

    # ─────────────────────────────────────────────
    # 1. RESET
    # ─────────────────────────────────────────────
    r = requests.post(f"{BASE}/reset", params={"task": task})
    assert_true(r.status_code == 200, "Reset failed")

    data = r.json()
    eid = data["episode_id"]
    obs = data["observation"]

    assert_true("email_id" in obs, "Invalid observation")
    print("✅ Reset OK")

    steps = 0
    max_steps = obs["total_emails"] + 2

    # ─────────────────────────────────────────────
    # 2. RUN FULL EPISODE (agent simulation)
    # ─────────────────────────────────────────────
    while not obs.get("done", False):

        action = {
            "episode_id": eid,
            "action_type": "classify",
            "priority": "low",
            "email_id": obs["email_id"]
        }

        r = requests.post(f"{BASE}/step", json=action)
        assert_true(r.status_code == 200, "Step failed")

        step_data = r.json()

        # Validate structure
        assert_true("reward" in step_data, "Missing reward")
        assert_true("observation" in step_data, "Missing observation")
        assert_true("done" in step_data, "Missing done flag")

        obs = step_data["observation"]
        steps += 1

        # Guard infinite loops
        assert_true(steps <= max_steps, "Exceeded max steps")

    print("✅ Episode completed")

    # ─────────────────────────────────────────────
    # 3. METRICS CHECK
    # ─────────────────────────────────────────────
    r = requests.get(f"{BASE}/metrics")
    assert_true(r.status_code == 200, "Metrics failed")

    metrics = r.json()

    assert_true("final_score" in metrics, "Missing final_score")
    assert_true(0 <= metrics["final_score"] <= 1, "Invalid score range")

    print(f"✅ Final Score: {metrics['final_score']:.4f}")

    # ─────────────────────────────────────────────
    # 4. STATE CHECK
    # ─────────────────────────────────────────────
    r = requests.get(f"{BASE}/state")
    assert_true(r.status_code == 200, "State failed")

    state = r.json()
    assert_true(state["done"] is True, "State mismatch")

    print("✅ State consistent")

    print("🎯 TEST PASSED\n")


if __name__ == "__main__":
    for t in ["easy", "medium", "hard"]:
        test_full_pipeline(t)

    print("🔥 ALL TESTS PASSED — READY FOR SUBMISSION")