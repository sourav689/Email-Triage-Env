import os
import sys
import time
from uuid import uuid4
from typing import Optional
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Literal

from tasks.easy import EMAILS as EASY_EMAILS, GROUND_TRUTH as EASY_GT
from tasks.medium import EMAILS as MEDIUM_EMAILS, GROUND_TRUTH as MEDIUM_GT
from tasks.hard import EMAILS as HARD_EMAILS, GROUND_TRUTH as HARD_GT
from grader import compute_final_score

# ── boot time for uptime tracking ─────────────────────────────────────────────
_BOOT_TIME = time.time()

# ── session registry ──────────────────────────────────────────────────────────
_SESSIONS: dict = {}
_ACTIVE_EPISODE_ID: str = ""

TASK_DATA = {
    "easy":   {"emails": EASY_EMAILS,   "ground_truth": EASY_GT},
    "medium": {"emails": MEDIUM_EMAILS, "ground_truth": MEDIUM_GT},
    "hard":   {"emails": HARD_EMAILS,   "ground_truth": HARD_GT},
}

# ── request models ─────────────────────────────────────────────────────────────
class ActionRequest(BaseModel):
    episode_id: Optional[str] = None
    action: Optional[dict] = None
    action_type: Optional[Literal["classify", "reply", "escalate", "ignore"]] = None
    priority: Optional[Literal["high", "medium", "low"]] = None
    email_id: Optional[int] = None

# ── helpers ────────────────────────────────────────────────────────────────────
def _make_obs(session: dict) -> dict:
    idx    = session["current_index"]
    emails = session["emails"]
    done   = session["done"]

    if done or idx >= len(emails):
        return {
            "email_id":     -1,
            "subject":      "[Episode Complete]",
            "body":         "All emails have been processed.",
            "sender":       "system",
            "step":         session["step_count"],
            "total_emails": len(emails),
            "done":         True,
            "reward":       0.0,
            "task":         session["task"],
        }

    email = emails[idx]
    return {
        "email_id":     email["email_id"],
        "subject":      email["subject"],
        "body":         email["body"],
        "sender":       email["sender"],
        "step":         session["step_count"],
        "total_emails": len(emails),
        "done":         False,
        "reward":       session.get("last_reward", 0.0),
        "task":         session["task"],
    }


def _compute_reward(action_type: str, priority: str, email_id: int, session: dict) -> float:
    idx = session["current_index"]
    gt  = session["ground_truth"][idx]
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

    optimal    = len(session["emails"])
    extra      = max(0, session["step_count"] - optimal)
    reward    -= 0.05 * extra

    return round(max(-1.0, min(1.0, reward)), 4)


def _new_session(task: str, seed: int = 42) -> dict:
    data = TASK_DATA[task]
    return {
        "task":           task,
        "seed":           seed,
        "emails":         data["emails"],
        "ground_truth":   data["ground_truth"],
        "current_index":  0,
        "step_count":     0,
        "actions_taken":  [],
        "total_reward":   0.0,
        "last_reward":    0.0,
        "done":           False,
        "episode_id":     str(uuid4()),
        "created_at":     datetime.utcnow().isoformat() + "Z",
    }


# ── FastAPI app ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Email Triage OpenEnv",
    description=(
        "Production-grade RL environment for AI email triage. "
        "Benchmarks agents on realistic workplace emails including adversarial traps. "
        "Built for the Meta PyTorch OpenEnv Hackathon 2025."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── health ─────────────────────────────────────────────────────────────────────
@app.get("/", tags=["System"])
@app.get("/health", tags=["System"])
def health():
    return {
        "status":        "ok",
        "env":           "email_triage_env",
        "version":       "2.0.0",
        "uptime_seconds": round(time.time() - _BOOT_TIME, 2),
        "active_sessions": len(_SESSIONS),
        "tasks_available": list(TASK_DATA.keys()),
    }


# ── task discovery ─────────────────────────────────────────────────────────────
@app.get("/tasks", tags=["Environment"])
def list_tasks():
    """Discover all available tasks, their metadata and trap types."""
    return {
        "tasks": [
            {
                "name":          "easy",
                "emails":        3,
                "optimal_steps": 3,
                "description":   "Spam vs legitimate classification. Unambiguous emails.",
                "evaluation":    "classification accuracy only",
            },
            {
                "name":          "medium",
                "emails":        5,
                "optimal_steps": 5,
                "description":   "Priority and action selection on real workplace emails.",
                "evaluation":    "classification + priority + action accuracy",
            },
            {
                "name":          "hard",
                "emails":        10,
                "optimal_steps": 10,
                "description":   "Adversarial traps requiring body-level reasoning.",
                "evaluation":    "full pipeline scoring + efficiency penalty",
                "traps": [
                    "misleading_subject",
                    "executive_phishing",
                    "fake_urgency",
                    "real_urgency",
                    "buried_request",
                    "friendly_spam",
                    "duplicate_original",
                    "duplicate_followup",
                    "false_alarm",
                    "low_priority_executive",
                ],
            },
        ]
    }


# ── reset ──────────────────────────────────────────────────────────────────────
@app.post("/reset", tags=["Environment"])
def reset(
    task: str = Query(default="easy", enum=["easy", "medium", "hard"]),
    seed: int = Query(default=42, description="Seed for reproducibility"),
):
    """Start a new episode. Returns episode_id and first email observation."""
    global _ACTIVE_EPISODE_ID

    if task not in TASK_DATA:
        raise HTTPException(status_code=400, detail=f"Unknown task '{task}'. Use: easy, medium, hard")

    session = _new_session(task, seed)
    _SESSIONS[session["episode_id"]] = session
    _ACTIVE_EPISODE_ID = session["episode_id"]

    obs = _make_obs(session)
    return {
        "episode_id":   session["episode_id"],
        "seed":         seed,
        "observation":  obs,
        "task":         task,
        "total_emails": len(session["emails"]),
        "optimal_steps": len(session["emails"]),
    }


# ── step ───────────────────────────────────────────────────────────────────────
@app.post("/step", tags=["Environment"])
def step(body: ActionRequest):
    """Take one action. Returns next observation, reward, done flag, and live metrics."""
    global _SESSIONS, _ACTIVE_EPISODE_ID

    episode_id = body.episode_id or _ACTIVE_EPISODE_ID

    if not episode_id or episode_id not in _SESSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"episode_id '{episode_id}' not found. Call /reset first.",
        )

    session = _SESSIONS[episode_id]

    if session["done"]:
        return {
            "observation": _make_obs(session),
            "reward":      0.0,
            "done":        True,
            "info":        {"message": "Episode complete. Call /reset to start a new episode."},
        }

    # extract action — support flat and nested formats
    if body.action:
        action_type = body.action.get("action_type")
        priority    = body.action.get("priority")
        email_id    = body.action.get("email_id")
    else:
        action_type = body.action_type
        priority    = body.priority
        email_id    = body.email_id

    # validate
    valid_actions    = {"classify", "reply", "escalate", "ignore"}
    valid_priorities = {"high", "medium", "low"}

    if action_type not in valid_actions:
        raise HTTPException(status_code=422, detail=f"action_type must be one of {valid_actions}")
    if priority not in valid_priorities:
        raise HTTPException(status_code=422, detail=f"priority must be one of {valid_priorities}")
    if email_id is None:
        email_id = session["emails"][session["current_index"]]["email_id"]

    # compute reward
    reward = _compute_reward(action_type, priority, email_id, session)

    # get ground truth for this step before advancing
    gt = session["ground_truth"][session["current_index"]]

    # record action with trap metadata
    session["actions_taken"].append({
        "email_id":    email_id,
        "action_type": action_type,
        "priority":    priority,
        "reward":      reward,
        "correct":     action_type == gt["action_type"],
        "trap_type":   gt.get("trap_type", "none"),
    })

    session["total_reward"] = round(session["total_reward"] + reward, 4)
    session["last_reward"]  = reward
    session["step_count"]  += 1
    session["current_index"] += 1

    # check termination
    max_steps = len(session["emails"]) * 2
    if session["current_index"] >= len(session["emails"]) or session["step_count"] >= max_steps:
        session["done"] = True
        reward = round(reward + 1.0, 4)  # completion bonus

    obs = _make_obs(session)

    # live running score
    running_score = compute_final_score(
        session["actions_taken"],
        session["ground_truth"],
    )

    return {
        "observation":   obs,
        "reward":        reward,
        "done":          session["done"],
        "info": {
            "episode_id":       episode_id,
            "step":             session["step_count"],
            "total_reward":     session["total_reward"],
            "running_score":    running_score,
            "emails_remaining": max(0, len(session["emails"]) - session["current_index"]),
        },
    }


# ── state ──────────────────────────────────────────────────────────────────────
@app.get("/state", tags=["Environment"])
def state():
    """Full current session state including all actions taken."""
    if not _ACTIVE_EPISODE_ID or _ACTIVE_EPISODE_ID not in _SESSIONS:
        return {"message": "No active episode. Call /reset first.", "sessions": len(_SESSIONS)}

    session = _SESSIONS[_ACTIVE_EPISODE_ID]
    return {
        "episode_id":    _ACTIVE_EPISODE_ID,
        "task":          session["task"],
        "seed":          session["seed"],
        "current_index": session["current_index"],
        "total_emails":  len(session["emails"]),
        "step_count":    session["step_count"],
        "actions_taken": session["actions_taken"],
        "total_reward":  session["total_reward"],
        "done":          session["done"],
        "created_at":    session["created_at"],
    }


# ── metrics ────────────────────────────────────────────────────────────────────
@app.get("/metrics", tags=["Evaluation"])
def metrics():
    """
    Per-metric accuracy breakdown for the current episode.
    Includes trap-level forensic analysis for the hard task.
    """
    if not _ACTIVE_EPISODE_ID or _ACTIVE_EPISODE_ID not in _SESSIONS:
        return {"message": "No active episode. Call /reset first."}

    session = _SESSIONS[_ACTIVE_EPISODE_ID]
    gt      = session["ground_truth"]
    actions = session["actions_taken"]
    n       = len(gt)
    taken   = actions[:n]

    if not taken:
        return {
            "episode_id": _ACTIVE_EPISODE_ID,
            "task":       session["task"],
            "message":    "No actions taken yet.",
        }

    classification_accuracy = round(sum(
        1 for a, g in zip(taken, gt)
        if a.get("action_type") == g.get("classification", g["action_type"])
    ) / n, 4)

    action_accuracy = round(sum(
        1 for a, g in zip(taken, gt)
        if a.get("action_type") == g["action_type"]
    ) / n, 4)

    priority_accuracy = round(sum(
        1 for a, g in zip(taken, gt)
        if a.get("priority") == g["priority"]
    ) / n, 4)

    optimal       = len(session["emails"])
    steps_taken   = session["step_count"]
    efficiency    = round(max(0.0, 1.0 - 0.05 * max(0, steps_taken - optimal)), 4)

    final_score = compute_final_score(taken, gt)

    trap_analysis = [
        {
            "email_id":   a.get("email_id"),
            "trap_type":  g.get("trap_type", "none"),
            "difficulty": g.get("difficulty", 0.5),
            "agent_action":    a.get("action_type"),
            "correct_action":  g["action_type"],
            "agent_priority":  a.get("priority"),
            "correct_priority": g["priority"],
            "correct":    a.get("action_type") == g["action_type"],
            "reward":     a.get("reward", 0.0),
        }
        for a, g in zip(taken, gt)
    ]

    traps_caught = sum(1 for t in trap_analysis if not t["correct"])

    return {
        "episode_id":              _ACTIVE_EPISODE_ID,
        "task":                    session["task"],
        "steps_taken":             steps_taken,
        "optimal_steps":           optimal,
        "emails_processed":        len(taken),
        "classification_accuracy": classification_accuracy,
        "action_accuracy":         action_accuracy,
        "priority_accuracy":       priority_accuracy,
        "efficiency_score":        efficiency,
        "final_score":             final_score,
        "total_reward":            session["total_reward"],
        "done":                    session["done"],
        "traps_caught_by_env":     traps_caught,
        "trap_analysis":           trap_analysis,
    }

def main():
    import uvicorn
    # Replace 'app' with your FastAPI instance name if it's different
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860, reload=False)

if __name__ == "__main__":
    main()