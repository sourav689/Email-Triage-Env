import random
from uuid import uuid4
from typing import Optional

EPSILON = 1e-6


# ──────────────────────────────────────────────────────────────────────────────
# NUMERIC STABILITY
# ──────────────────────────────────────────────────────────────────────────────
def _strict_clamp(value: float, lo: float = -0.9999, hi: float = 0.9999) -> float:
    return max(lo, min(hi, value))


# ──────────────────────────────────────────────────────────────────────────────
# TASK LOADER
# ──────────────────────────────────────────────────────────────────────────────
def _load_task(task_name: str):
    if task_name == "easy":
        from tasks.easy import EMAILS, GROUND_TRUTH
    elif task_name == "medium":
        from tasks.medium import EMAILS, GROUND_TRUTH
    elif task_name == "hard":
        from tasks.hard import EMAILS, GROUND_TRUTH
    else:
        raise ValueError(f"Unknown task: {task_name}")
    return EMAILS, GROUND_TRUTH


# ──────────────────────────────────────────────────────────────────────────────
# ENVIRONMENT
# ──────────────────────────────────────────────────────────────────────────────
class EmailTriageEnv:

    def __init__(self, task: str = "easy"):
        self._task          = task
        self._emails        = []
        self._ground_truth  = []
        self._current_index = 0
        self._actions_taken = []
        self._total_reward  = 0.0
        self._done          = False
        self._episode_id    = str(uuid4())
        self._step_count    = 0

    # ──────────────────────────────────────────────────────────────────────────
    # RESET
    # ──────────────────────────────────────────────────────────────────────────
    def reset(self, task: Optional[str] = None):
        if task:
            self._task = task

        self._emails, self._ground_truth = _load_task(self._task)

        self._current_index = 0
        self._actions_taken = []
        self._total_reward  = 0.0
        self._done          = False
        self._episode_id    = str(uuid4())
        self._step_count    = 0

        return self._make_obs(reward=0.0)

    # ──────────────────────────────────────────────────────────────────────────
    # STEP
    # ──────────────────────────────────────────────────────────────────────────
    def step(self, action_type: str, priority: str, email_id: int):
        if self._done:
            return self._make_obs(reward=0.0), 0.0, True, {}

        gt = self._ground_truth[self._current_index]

        reward = self._compute_reward(action_type, priority, email_id, gt)

        self._actions_taken.append({
            "email_id":    email_id,
            "action_type": action_type,
            "priority":    priority,
            "reward":      reward,
        })

        self._total_reward   = round(self._total_reward + reward, 4)
        self._step_count    += 1
        self._current_index += 1

        # ✅ FIX 1 — align with app.py + grader
        max_steps = len(self._emails) + 2

        if (
            self._current_index >= len(self._emails)
            or self._step_count >= max_steps
        ):
            self._done = True

            # ✅ FIX 2 — controlled completion bonus
            reward = round(_strict_clamp(reward + 0.3), 4)

        obs = self._make_obs(reward=reward)

        return obs, reward, self._done, {"step": self._step_count}

    # ──────────────────────────────────────────────────────────────────────────
    # STATE
    # ──────────────────────────────────────────────────────────────────────────
    def state(self):
        return {
            "task":          self._task,
            "episode_id":    self._episode_id,
            "current_index": self._current_index,
            "total_emails":  len(self._emails),
            "step_count":    self._step_count,
            "actions_taken": self._actions_taken,
            "total_reward":  self._total_reward,
            "done":          self._done,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # REWARD FUNCTION
    # ──────────────────────────────────────────────────────────────────────────
    def _compute_reward(self, action_type: str, priority: str, email_id: int, gt: dict) -> float:
        reward = 0.0

        if email_id != gt["email_id"]:
            reward -= 0.2
        else:
            if action_type == gt["action_type"]:
                reward += 0.4
            else:
                reward -= 0.2

            if action_type == gt.get("classification", gt["action_type"]):
                reward += 0.3

            if priority == gt["priority"]:
                reward += 0.2

        # efficiency penalty
        optimal = len(self._emails)
        extra   = max(0, self._step_count - optimal)
        reward -= 0.05 * extra

        # ✅ FIX 3 — REMOVE noise (critical for stable scoring)
        return round(_strict_clamp(reward), 4)

    # ──────────────────────────────────────────────────────────────────────────
    # OBSERVATION
    # ──────────────────────────────────────────────────────────────────────────
    def _make_obs(self, reward: float) -> dict:
        if self._done or self._current_index >= len(self._emails):
            return {
                "email_id":     -1,
                "subject":      "[Episode Complete]",
                "body":         "All emails have been processed.",
                "sender":       "system",
                "step":         self._step_count,
                "total_emails": len(self._emails),
                "done":         True,
                "reward":       reward,
                "task":         self._task,
            }

        email = self._emails[self._current_index]

        return {
            "email_id":     email["email_id"],
            "subject":      email["subject"],
            "body":         email["body"],
            "sender":       email["sender"],
            "step":         self._step_count,
            "total_emails": len(self._emails),
            "done":         False,
            "reward":       reward,
            "task":         self._task,
        }