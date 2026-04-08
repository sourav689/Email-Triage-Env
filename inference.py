import os
import sys
import json
import time
import random
import re
import requests
from openai import OpenAI

from grader import compute_final_score
from tasks.easy import GROUND_TRUTH as EASY_GT
from tasks.medium import GROUND_TRUTH as MEDIUM_GT
from tasks.hard import GROUND_TRUTH as HARD_GT

GROUND_TRUTHS = {"easy": EASY_GT, "medium": MEDIUM_GT, "hard": HARD_GT}

# ── env ─────────────────────────────────────────────────────────────
BASE_URL   = os.environ.get("API_BASE_URL", "https://api.groq.com/openai/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "llama-3.3-70b-versatile")
API_KEY    = os.environ.get("OPENAI_API_KEY") or os.environ.get("API_KEY", "")
ENV_URL    = os.environ.get("ENV_URL", "http://localhost:7860")

# ── client ──────────────────────────────────────────────────────────
client = None
if API_KEY:
    try:
        client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    except Exception as e:
        print(f"[WARN] Client init failed: {e}", file=sys.stderr)
else:
    print("[INFO] Heuristic-only mode", file=sys.stderr)

# ── analyzer ────────────────────────────────────────────────────────
def analyze_email(obs, history):
    subject = (obs.get("subject") or "").lower()
    body    = (obs.get("body") or "").lower()
    sender  = (obs.get("sender") or "").lower()

    content = subject + " " + body

    signals = {
        "newsletter": False,
        "phishing": False,
        "urgency": "none",
        "false_alarm": False,
        "duplicate": False,
        "buried": False,
        "internal": "@yourcompany.com" in sender,
        "subject_body_mismatch": False,
    }

    # newsletter
    if any(x in body for x in ["unsubscribe","opt out","preferences","marketing"]):
        signals["newsletter"] = True

    # phishing (strong but not over-aggressive)
    if not signals["internal"]:
        if any(x in content for x in [
            "wire transfer","bank","urgent payment","verify account",
            "password reset","click link","login now"
        ]):
            signals["phishing"] = True

    # urgency
    if any(x in content for x in ["outage","down","incident","breach","critical"]):
        signals["urgency"] = "real"
    elif any(x in content for x in ["act now","offer","reward","prize"]):
        signals["urgency"] = "fake"

    # false alarm
    if "no action required" in body or "resolved" in body:
        signals["false_alarm"] = True

    # buried request
    if len(body) > 250 and any(x in body for x in ["please","could you","approve","review"]):
        signals["buried"] = True

    # duplicate (improved)
    for prev in history[-5:]:
        ps = (prev.get("subject") or "").lower()
        if sender == prev.get("sender"):
            if subject[:30] in ps or ps[:30] in subject:
                signals["duplicate"] = True

    # subject-body mismatch (HARD task killer feature)
    if "urgent" in subject and "newsletter" in body:
        signals["subject_body_mismatch"] = True

    return signals

# ── confidence-based rule ───────────────────────────────────────────
def rule_policy(obs, s):
    eid = obs["email_id"]

    # HIGH CONFIDENCE RULES
    if s["false_alarm"]:
        return {"action_type": "ignore", "priority": "low", "email_id": eid}, 0.95

    if s["phishing"]:
        return {"action_type": "escalate", "priority": "high", "email_id": eid}, 0.9

    if s["newsletter"] and not s["buried"]:
        return {"action_type": "ignore", "priority": "low", "email_id": eid}, 0.9

    if s["urgency"] == "real":
        if s["internal"]:
            return {"action_type": "escalate", "priority": "high", "email_id": eid}, 0.85
        return {"action_type": "reply", "priority": "high", "email_id": eid}, 0.8

    # MEDIUM CONFIDENCE
    if s["buried"]:
        return {"action_type": "reply", "priority": "high", "email_id": eid}, 0.7

    if s["duplicate"]:
        return {"action_type": "classify", "priority": "low", "email_id": eid}, 0.7

    if s["urgency"] == "fake":
        return {"action_type": "classify", "priority": "low", "email_id": eid}, 0.75

    # LOW confidence → let LLM decide
    return None, 0.0

# ── LLM ─────────────────────────────────────────────────────────────
def call_model(obs, signals):
    if client is None:
        return None

    prompt = f"""
You are an expert email triage agent.

Email:
From: {obs.get("sender")}
Subject: {obs.get("subject")}
Body: {obs.get("body")}

Decide:
- classify / reply / escalate / ignore
- priority: high / medium / low

Rules:
- phishing → escalate high
- real outage → escalate high
- newsletters → ignore low
- fake urgency → classify low
- buried request → reply high

Return ONLY JSON:
{{"action_type":"...","priority":"..."}}
"""

    try:
        res = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=80,
        )

        raw = res.choices[0].message.content
        match = re.search(r"\{.*?\}", raw, re.DOTALL)
        if not match:
            return None

        parsed = json.loads(match.group())

        if parsed.get("action_type") not in {"classify","reply","escalate","ignore"}:
            return None
        if parsed.get("priority") not in {"high","medium","low"}:
            return None

        return parsed

    except Exception:
        return None

# ── decision engine (CORE IMPROVEMENT) ──────────────────────────────
def decide(obs, history):
    signals = analyze_email(obs, history)

    rule, confidence = rule_policy(obs, signals)

    # HIGH confidence → trust rules
    if rule and confidence >= 0.85:
        return rule

    # MEDIUM confidence → try LLM override
    if confidence >= 0.6:
        model_out = call_model(obs, signals)
        if model_out:
            return {
                "action_type": model_out["action_type"],
                "priority": model_out["priority"],
                "email_id": obs["email_id"],
            }
        return rule

    # LOW confidence → LLM first
    model_out = call_model(obs, signals)
    if model_out:
        return {
            "action_type": model_out["action_type"],
            "priority": model_out["priority"],
            "email_id": obs["email_id"],
        }

    # FINAL fallback (deterministic)
    return {"action_type": "reply", "priority": "medium", "email_id": obs["email_id"]}

# ── safe request ────────────────────────────────────────────────────
def safe_post(url, **kwargs):
    for i in range(2):
        try:
            return requests.post(url, timeout=20, **kwargs).json()
        except Exception:
            time.sleep(1 + i)
    raise RuntimeError(f"Request failed: {url}")

# ── runner with REQUIRED LOGS ───────────────────────────────────────
def run_task(task):
    print(f"[START] task={task}", flush=True)

    reset = safe_post(f"{ENV_URL}/reset", params={"task": task})
    eid = reset["episode_id"]
    obs = reset["observation"]

    history = []
    actions = []
    step = 0

    while not obs.get("done"):
        action = decide(obs, history)

        resp = safe_post(f"{ENV_URL}/step", json={
            "episode_id": eid,
            **action
        })

        reward = resp.get("reward", 0.0)

        print(f"[STEP] step={step} action={action} reward={reward}", flush=True)

        history.append(obs)
        actions.append(action)
        obs = resp["observation"]
        step += 1

    score = compute_final_score(actions, GROUND_TRUTHS[task])

    print(f"[END] task={task} score={score:.4f} steps={step}", flush=True)

    return score

# ── entry ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    for t in ["easy","medium","hard"]:
        try:
            run_task(t)
        except Exception as e:
            print(f"[END] task={t} ERROR {e}", flush=True)