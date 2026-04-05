import os
import sys
from uuid import uuid4
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Literal

from tasks.easy import EMAILS as EASY_EMAILS, GROUND_TRUTH as EASY_GT
from tasks.medium import EMAILS as MEDIUM_EMAILS, GROUND_TRUTH as MEDIUM_GT
from tasks.hard import EMAILS as HARD_EMAILS, GROUND_TRUTH as HARD_GT

# ── in-memory session registry ────────────────────────────────────────────────
# Maps episode_id → full environment state dict
# One session per task — hackathon single-agent pattern
_SESSIONS: dict = {}
_ACTIVE_EPISODE_ID: str = ""   # last reset's episode_id

TASK_DATA = {
    "easy":   {"emails": EASY_EMAILS,   "ground_truth": EASY_GT},
    "medium": {"emails": MEDIUM_EMAILS, "ground_truth": MEDIUM_GT},
    "hard":   {"emails": HARD_EMAILS,   "ground_truth": HARD_GT},
}

# ── request/response models ───────────────────────────────────────────────────

class ActionRequest(BaseModel):
    episode_id: Optional[str] = None          # optional — falls back to last reset
    action: Optional[dict] = None             # nested form  {"action": {...}}
    action_type: Optional[Literal["classify", "reply", "escalate", "ignore"]] = None
    priority: Optional[Literal["high", "medium", "low"]] = None
    email_id: Optional[int] = None


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_obs(session: dict) -> dict:
    idx = session["current_index"]
    emails = session["emails"]
    done = session["done"]

    if done or idx >= len(emails):
        return {
            "email_id": -1,
            "subject": "[Episode Complete]",
            "body": "All emails have been processed.",
            "sender": "system",
            "step": session["step_count"],
            "total_emails": len(emails),
            "done": True,
            "reward": 0.0,
            "task": session["task"],
        }

    email = emails[idx]
    return {
        "email_id": email["email_id"],
        "subject": email["subject"],
        "body": email["body"],
        "sender": email["sender"],
        "step": session["step_count"],
        "total_emails": len(emails),
        "done": False,
        "reward": session.get("last_reward", 0.0),
        "task": session["task"],
    }


def _compute_reward(action_type: str, priority: str, email_id: int, session: dict) -> float:
    idx = session["current_index"]
    gt = session["ground_truth"][idx]
    reward = 0.0

    if email_id != gt["email_id"]:
        reward -= 0.1
    else:
        if action_type == gt["action_type"]:
            reward += 0.4
        else:
            reward -= 0.2

        if action_type == gt.get("classification", gt["action_type"]):
            reward += 0.3

        if priority == gt["priority"]:
            reward += 0.2

    optimal = len(session["emails"])
    extra_steps = max(0, session["step_count"] - optimal)
    reward -= 0.05 * extra_steps

    return round(max(-1.0, min(1.0, reward)), 4)


def _new_session(task: str) -> dict:
    data = TASK_DATA[task]
    return {
        "task": task,
        "emails": data["emails"],
        "ground_truth": data["ground_truth"],
        "current_index": 0,
        "step_count": 0,
        "actions_taken": [],
        "total_reward": 0.0,
        "last_reward": 0.0,
        "done": False,
        "episode_id": str(uuid4()),
    }


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Email Triage OpenEnv",
    description="RL environment for AI email triage — Meta PyTorch Hackathon 2025",
    version="1.0.0",
)


@app.get("/")
@app.get("/health")
def health():
    return {"status": "ok", "env": "email_triage_env", "version": "1.0.0"}


@app.post("/reset")
def reset(task: str = Query(default="easy", enum=["easy", "medium", "hard"])):
    global _ACTIVE_EPISODE_ID

    if task not in TASK_DATA:
        raise HTTPException(status_code=400, detail=f"Unknown task '{task}'. Use: easy, medium, hard")

    session = _new_session(task)
    _SESSIONS[session["episode_id"]] = session
    _ACTIVE_EPISODE_ID = session["episode_id"]

    obs = _make_obs(session)
    return {
        "episode_id": session["episode_id"],
        "observation": obs,
        "task": task,
        "total_emails": len(session["emails"]),
    }


@app.post("/step")
def step(body: ActionRequest):
    global _SESSIONS, _ACTIVE_EPISODE_ID

    # resolve episode_id — accept from body or fall back to last reset
    episode_id = body.episode_id or _ACTIVE_EPISODE_ID

    if not episode_id or episode_id not in _SESSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"episode_id '{episode_id}' not found. Call /reset first."
        )

    session = _SESSIONS[episode_id]

    if session["done"]:
        return {
            "observation": _make_obs(session),
            "reward": 0.0,
            "done": True,
            "info": {"message": "Episode already complete. Call /reset to start a new episode."},
        }

    # extract action fields — support both flat and nested {"action": {...}}
    if body.action:
        action_type = body.action.get("action_type")
        priority = body.action.get("priority")
        email_id = body.action.get("email_id")
    else:
        action_type = body.action_type
        priority = body.priority
        email_id = body.email_id

    # validate
    valid_actions = {"classify", "reply", "escalate", "ignore"}
    valid_priorities = {"high", "medium", "low"}

    if action_type not in valid_actions:
        raise HTTPException(status_code=422, detail=f"action_type must be one of {valid_actions}")
    if priority not in valid_priorities:
        raise HTTPException(status_code=422, detail=f"priority must be one of {valid_priorities}")
    if email_id is None:
        email_id = session["emails"][session["current_index"]]["email_id"]

    # compute reward
    reward = _compute_reward(action_type, priority, email_id, session)

    # record action
    session["actions_taken"].append({
        "email_id": email_id,
        "action_type": action_type,
        "priority": priority,
        "reward": reward,
    })
    session["total_reward"] = round(session["total_reward"] + reward, 4)
    session["last_reward"] = reward
    session["step_count"] += 1
    session["current_index"] += 1

    # check termination
    max_steps = len(session["emails"]) * 2
    if session["current_index"] >= len(session["emails"]) or session["step_count"] >= max_steps:
        session["done"] = True
        reward += 1.0   # completion bonus

    obs = _make_obs(session)

    return {
        "observation": obs,
        "reward": round(reward, 4),
        "done": session["done"],
        "info": {
            "episode_id": episode_id,
            "step": session["step_count"],
            "total_reward": session["total_reward"],
            "emails_remaining": max(0, len(session["emails"]) - session["current_index"]),
        },
    }


@app.get("/state")
def state():
    if not _ACTIVE_EPISODE_ID or _ACTIVE_EPISODE_ID not in _SESSIONS:
        return {"message": "No active episode. Call /reset first.", "sessions": len(_SESSIONS)}

    session = _SESSIONS[_ACTIVE_EPISODE_ID]
    return {
        "episode_id": _ACTIVE_EPISODE_ID,
        "task": session["task"],
        "current_index": session["current_index"],
        "total_emails": len(session["emails"]),
        "step_count": session["step_count"],
        "actions_taken": session["actions_taken"],
        "total_reward": session["total_reward"],
        "done": session["done"],
    }