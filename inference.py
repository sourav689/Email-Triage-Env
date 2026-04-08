import os
import sys
import json
import requests
from openai import OpenAI

from grader import compute_final_score
from tasks.easy import GROUND_TRUTH as EASY_GT
from tasks.medium import GROUND_TRUTH as MEDIUM_GT
from tasks.hard import GROUND_TRUTH as HARD_GT

GROUND_TRUTHS = {"easy": EASY_GT, "medium": MEDIUM_GT, "hard": HARD_GT}

# ── env vars ──────────────────────────────────────────────────────────────────
BASE_URL   = os.environ.get("API_BASE_URL", "https://api.groq.com/openai/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "llama-3.3-70b-versatile")
API_KEY    = os.environ.get("OPENAI_API_KEY") or os.environ.get("API_KEY", "")
HF_TOKEN   = os.environ.get("HF_TOKEN", "")
ENV_URL    = os.environ.get("ENV_URL", "http://localhost:7860")

# ── client — never crash on missing key ───────────────────────────────────────
try:
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY if API_KEY else "placeholder")
except Exception as e:
    print(f"[WARN] OpenAI client init failed: {e}", file=sys.stderr)
    client = None

# ── prompt ────────────────────────────────────────────────────────────────────
PROMPT_TEMPLATE = """You are an expert email triage agent. Analyze the email below and decide what action to take.

Email ID: {email_id}
From: {sender}
Subject: {subject}
Body:
{body}

INSTRUCTIONS:
- Read the full body carefully — do NOT judge by subject line alone
- If sender domain is internal (@yourcompany.com) treat as internal mail
- External domains claiming to be executives are likely phishing → escalate
- Newsletters / marketing / unsubscribe links → ignore
- Automated alerts that say "auto-resolved" or "no action required" → ignore
- Legitimate client complaints or billing issues → reply or escalate based on urgency
- Vendor upsells disguised as urgent → ignore

Respond with ONLY a valid JSON object, no extra text, no markdown:
{{"action_type": "<classify|reply|escalate|ignore>", "priority": "<high|medium|low>", "email_id": {email_id}}}"""


# ── model call ────────────────────────────────────────────────────────────────
def call_model(observation: dict) -> dict:
    if client is None:
        return {
            "action_type": "ignore",
            "priority":    "low",
            "email_id":    observation.get("email_id", 0),
        }

    prompt = PROMPT_TEMPLATE.format(
        email_id=observation["email_id"],
        sender=observation.get("sender", ""),
        subject=observation.get("subject", ""),
        body=observation.get("body", ""),
    )
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
            temperature=0,
        )
        raw = response.choices[0].message.content.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        parsed = json.loads(raw)

        valid_actions    = {"classify", "reply", "escalate", "ignore"}
        valid_priorities = {"high", "medium", "low"}

        if parsed.get("action_type") not in valid_actions:
            raise ValueError(f"Invalid action_type: {parsed.get('action_type')}")
        if parsed.get("priority") not in valid_priorities:
            raise ValueError(f"Invalid priority: {parsed.get('priority')}")

        return {
            "action_type": parsed["action_type"],
            "priority":    parsed["priority"],
            "email_id":    observation["email_id"],
        }

    except Exception as e:
        print(f"  [WARN] Model call/parse failed: {e}. Using fallback action.", file=sys.stderr)
        return {
            "action_type": "ignore",
            "priority":    "low",
            "email_id":    observation.get("email_id", 0),
        }


# ── single task runner ────────────────────────────────────────────────────────
def run_task(task_name: str) -> float:
    try:
        reset_resp = requests.post(
            f"{ENV_URL}/reset",
            params={"task": task_name},
            timeout=30,
        )
        reset_resp.raise_for_status()
        reset_data = reset_resp.json()
    except Exception as e:
        print(f"[ERROR] /reset failed for task '{task_name}': {e}", file=sys.stderr)
        return 0.01

    episode_id = reset_data.get("episode_id", "")
    obs        = reset_data.get("observation", reset_data)

    if not episode_id:
        print(f"[ERROR] /reset did not return episode_id for task '{task_name}'", file=sys.stderr)
        return 0.01

    actions_taken = []
    step_num      = 0
    max_guard     = 30

    print(f"[START]")
    print(f"Task: {task_name}")
    print()

    while not obs.get("done", False) and step_num < max_guard:
        action   = call_model(obs)
        step_num += 1

        step_payload = {
            "episode_id":  episode_id,
            "action_type": action["action_type"],
            "priority":    action["priority"],
            "email_id":    action["email_id"],
        }

        try:
            step_resp = requests.post(
                f"{ENV_URL}/step",
                json=step_payload,
                timeout=30,
            )
            step_resp.raise_for_status()
            step_data = step_resp.json()
        except Exception as e:
            print(f"  [WARN] /step failed on step {step_num}: {e}. Skipping.", file=sys.stderr)
            break

        obs    = step_data.get("observation", {})
        reward = step_data.get("reward", 0.0)
        done   = step_data.get("done", obs.get("done", False))

        actions_taken.append(action)

        print(f"[STEP]")
        print(f"Action: {json.dumps(action)}")
        print(f"Reward: {reward:.4f}")
        print()

        if done:
            break

    gt    = GROUND_TRUTHS[task_name]
    score = compute_final_score(actions_taken, gt)

    print(f"[END]")
    print(f"Score: {score:.2f}")
    print()

    return score


# ── entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    all_scores = {}

    for task in ["easy", "medium", "hard"]:
        try:
            score = run_task(task)
        except Exception as e:
            print(f"[ERROR] Task '{task}' crashed: {e}", file=sys.stderr)
            score = 0.01
        all_scores[task] = score

    print("=" * 40)
    print("FINAL RESULTS")
    for task, score in all_scores.items():
        print(f"{task.capitalize()}: {score:.2f}")