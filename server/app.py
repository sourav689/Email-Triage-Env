import os
import sys
import time
import threading
from uuid import uuid4
from typing import Optional, Literal
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from tasks.easy import EMAILS as EASY_EMAILS, GROUND_TRUTH as EASY_GT
from tasks.medium import EMAILS as MEDIUM_EMAILS, GROUND_TRUTH as MEDIUM_GT
from tasks.hard import EMAILS as HARD_EMAILS, GROUND_TRUTH as HARD_GT
from grader import compute_final_score


# ──────────────────────────────────────────────────────────────────────────────
# GLOBAL STATE
# ──────────────────────────────────────────────────────────────────────────────
_BOOT_TIME = time.time()
_SESSIONS: dict = {}
_ACTIVE_EPISODE_ID: str = ""
_LOCK = threading.Lock()

EPSILON = 1e-6
MAX_SESSIONS = 500

TASK_DATA = {
    "easy":   {"emails": EASY_EMAILS,   "ground_truth": EASY_GT},
    "medium": {"emails": MEDIUM_EMAILS, "ground_truth": MEDIUM_GT},
    "hard":   {"emails": HARD_EMAILS,   "ground_truth": HARD_GT},
}


# ──────────────────────────────────────────────────────────────────────────────
# NUMERIC STABILITY
# ──────────────────────────────────────────────────────────────────────────────
def _strict_clamp(x: float) -> float:
    return max(EPSILON, min(1.0 - EPSILON, x))


def _safe_score(x: float) -> float:
    return _strict_clamp(round(x, 6))


# ──────────────────────────────────────────────────────────────────────────────
# SESSION MGMT
# ──────────────────────────────────────────────────────────────────────────────
def _cleanup_sessions():
    if len(_SESSIONS) <= MAX_SESSIONS:
        return

    oldest = sorted(
        _SESSIONS.items(),
        key=lambda x: datetime.fromisoformat(x[1]["created_at"])
    )[: len(_SESSIONS) - MAX_SESSIONS]

    for k, _ in oldest:
        del _SESSIONS[k]


def _new_session(task: str, seed: int):
    data = TASK_DATA[task]

    return {
        "task": task,
        "seed": seed,
        "emails": data["emails"],
        "ground_truth": data["ground_truth"],
        "current_index": 0,
        "step_count": 0,
        "actions_taken": [],
        "total_reward": 0.0,
        "last_reward": 0.0,
        "done": False,
        "episode_id": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


# ──────────────────────────────────────────────────────────────────────────────
# REQUEST MODEL
# ──────────────────────────────────────────────────────────────────────────────
class ActionRequest(BaseModel):
    episode_id: Optional[str] = None
    action: Optional[dict] = None
    action_type: Optional[Literal["classify", "reply", "escalate", "ignore"]] = None
    priority: Optional[Literal["high", "medium", "low"]] = None
    email_id: Optional[int] = None


# ──────────────────────────────────────────────────────────────────────────────
# OBS
# ──────────────────────────────────────────────────────────────────────────────
def _make_obs(session):
    idx = session["current_index"]
    emails = session["emails"]

    if session["done"] or idx >= len(emails):
        return {
            "email_id": -1,
            "subject": "[Episode Complete]",
            "body": "All emails processed.",
            "sender": "system",
            "step": session["step_count"],
            "total_emails": len(emails),
            "done": True,
            "reward": 0.0,
            "task": session["task"],
        }

    e = emails[idx]

    return {
        "email_id": e["email_id"],
        "subject": e["subject"],
        "body": e["body"],
        "sender": e["sender"],
        "step": session["step_count"],
        "total_emails": len(emails),
        "done": False,
        "reward": session["last_reward"],
        "task": session["task"],
    }


# ──────────────────────────────────────────────────────────────────────────────
# REWARD
# ──────────────────────────────────────────────────────────────────────────────
def _compute_reward(action_type, priority, email_id, session):
    idx = session["current_index"]

    if idx >= len(session["ground_truth"]):
        return 0.0

    gt = session["ground_truth"][idx]

    reward = 0.0

    if email_id != gt["email_id"]:
        reward -= 0.2
    else:
        reward += 0.4 if action_type == gt["action_type"] else -0.2

        if action_type == gt.get("classification", gt["action_type"]):
            reward += 0.3

        if priority == gt["priority"]:
            reward += 0.2

    optimal = len(session["emails"])
    extra = max(0, session["step_count"] - optimal)
    reward -= 0.05 * extra

    return round(max(-0.9999, min(0.9999, reward)), 4)


# ──────────────────────────────────────────────────────────────────────────────
# FASTAPI
# ──────────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Email Triage OpenEnv", version="3.0.0")


@app.get("/")
@app.get("/health")
def health():
    return {
        "status": "ok",
        "uptime": round(time.time() - _BOOT_TIME, 2),
        "sessions": len(_SESSIONS),
    }


@app.post("/reset")
def reset(task: str = Query("easy"), seed: int = 42):
    global _ACTIVE_EPISODE_ID

    if task not in TASK_DATA:
        raise HTTPException(400, "Invalid task")

    with _LOCK:
        _cleanup_sessions()
        session = _new_session(task, seed)
        _SESSIONS[session["episode_id"]] = session
        _ACTIVE_EPISODE_ID = session["episode_id"]

    return {
        "episode_id": session["episode_id"],
        "observation": _make_obs(session),
        "task": task,
        "total_emails": len(session["emails"]),
    }


@app.post("/step")
def step(body: ActionRequest):
    global _ACTIVE_EPISODE_ID

    episode_id = body.episode_id or _ACTIVE_EPISODE_ID

    if not episode_id or episode_id not in _SESSIONS:
        raise HTTPException(400, "Invalid episode_id")

    with _LOCK:
        session = _SESSIONS[episode_id]

        if session["done"]:
            return {"done": True, "reward": 0.0, "observation": _make_obs(session)}

        action_type = body.action_type or (body.action or {}).get("action_type")
        priority    = body.priority or (body.action or {}).get("priority")
        email_id    = body.email_id or session["emails"][session["current_index"]]["email_id"]

        if action_type not in {"classify","reply","escalate","ignore"}:
            raise HTTPException(422, "Invalid action_type")

        if priority not in {"high","medium","low"}:
            raise HTTPException(422, "Invalid priority")

        reward = _compute_reward(action_type, priority, email_id, session)

        session["actions_taken"].append({
            "email_id": email_id,
            "action_type": action_type,
            "priority": priority,
            "reward": reward,
        })

        session["total_reward"] = round(session["total_reward"] + reward, 4)
        session["last_reward"]  = reward
        session["step_count"]  += 1
        session["current_index"] += 1

        max_steps = len(session["emails"]) + 2

        if session["current_index"] >= len(session["emails"]) or session["step_count"] >= max_steps:
            session["done"] = True
            reward = round(min(0.9999, reward + 0.3), 4)

    obs = _make_obs(session)

    taken = session["actions_taken"][:len(session["ground_truth"])]
    running_score = _safe_score(compute_final_score(taken, session["ground_truth"]))

    return {
        "observation": obs,
        "reward": reward,
        "done": session["done"],
        "info": {
            "running_score": running_score,
            "steps": session["step_count"],
            "remaining": max(0, len(session["emails"]) - session["current_index"]),
        },
    }


@app.get("/metrics")
def metrics():
    if not _ACTIVE_EPISODE_ID or _ACTIVE_EPISODE_ID not in _SESSIONS:
        return {"message": "No active episode"}

    s = _SESSIONS[_ACTIVE_EPISODE_ID]
    gt = s["ground_truth"]
    taken = s["actions_taken"][:len(gt)]

    if not taken:
        return {"message": "No actions yet"}

    final_score = _safe_score(compute_final_score(taken, gt))

    return {
        "final_score": final_score,
        "steps": s["step_count"],
        "emails": len(gt),
        "done": s["done"],
        "total_reward": s["total_reward"],
    }


@app.get("/state")
def state():
    if not _ACTIVE_EPISODE_ID or _ACTIVE_EPISODE_ID not in _SESSIONS:
        return {"message": "No active session"}

    return _SESSIONS[_ACTIVE_EPISODE_ID]