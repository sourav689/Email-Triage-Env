from uuid import uuid4
from typing import Optional
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from models import EmailAction, EmailObservation


# ✅ Robust task loader
def _load_task(task_name: str):
    try:
        if task_name == "easy":
            from tasks.easy import EMAILS, GROUND_TRUTH
        elif task_name == "medium":
            from tasks.medium import EMAILS, GROUND_TRUTH
        elif task_name == "hard":
            from tasks.hard import EMAILS, GROUND_TRUTH
        else:
            raise ValueError(f"Unknown task: {task_name}")

        # ✅ Debug logs
        print(f"[DEBUG] Loaded task '{task_name}'")
        print(f"[DEBUG] Emails: {len(EMAILS)}, Ground Truth: {len(GROUND_TRUTH)}")

        # ✅ Validation
        if not EMAILS or not GROUND_TRUTH:
            raise ValueError(f"Task '{task_name}' has empty data")

        if len(EMAILS) != len(GROUND_TRUTH):
            raise ValueError("Mismatch between EMAILS and GROUND_TRUTH")

        return EMAILS, GROUND_TRUTH

    except Exception as e:
        print(f"[ERROR] Failed to load task '{task_name}': {e}")
        raise


class EmailTriageEnv(Environment):
    def __init__(self, task: str = "easy"):
        self._task = task
        self._emails = []
        self._ground_truth = []
        self._current_index = 0
        self._actions_taken = []
        self._total_reward = 0.0
        self._done = False
        self._episode_id = str(uuid4())
        self._step_count = 0

    def reset(self, task: Optional[str] = None) -> EmailObservation:
        if task:
            self._task = task

        self._emails, self._ground_truth = _load_task(self._task)

        self._current_index = 0
        self._actions_taken = []
        self._total_reward = 0.0
        self._done = False
        self._episode_id = str(uuid4())
        self._step_count = 0

        return self._make_observation(reward=0.0)

    def step(self, action: EmailAction) -> EmailObservation:
        # ✅ Already finished
        if self._done:
            return self._make_observation(reward=0.0)

        # ✅ Prevent crash
        if self._current_index >= len(self._ground_truth):
            self._done = True
            return self._make_observation(reward=0.0)

        gt = self._ground_truth[self._current_index]

        # ✅ Compute reward
        reward = self._compute_reward(action, gt)

        # ✅ Track action
        self._actions_taken.append({
            "email_id": action.email_id,
            "action_type": action.action_type,
            "priority": action.priority,
            "reward": reward,
        })

        self._total_reward += reward
        self._step_count += 1
        self._current_index += 1

        # ✅ End condition
        if self._current_index >= len(self._emails):
            self._done = True
            reward += 1.0  # completion bonus

        return self._make_observation(reward=round(reward, 4))

    @property
    def state(self) -> State:
        return State(
            episode_id=self._episode_id,
            step_count=self._step_count,
            extra={
                "task": self._task,
                "current_index": self._current_index,
                "total_emails": len(self._emails),
                "actions_taken": self._actions_taken,
                "total_reward": round(self._total_reward, 4),
                "done": self._done,
            }
        )

    def _compute_reward(self, action: EmailAction, gt: dict) -> float:
        reward = 0.0

        # ❌ Wrong email
        if action.email_id != gt["email_id"]:
            return -0.3

        # ✅ Action correctness
        if action.action_type == gt["action_type"]:
            reward += 0.5
        else:
            reward -= 0.3

        # ✅ Classification alignment
        if action.action_type == gt.get("classification", gt["action_type"]):
            reward += 0.2

        # ✅ Priority correctness
        if action.priority == gt["priority"]:
            reward += 0.2

        # ✅ Efficiency penalty
        optimal_steps = len(self._emails)
        if self._step_count >= optimal_steps:
            reward -= 0.05 * (self._step_count - optimal_steps + 1)

        # ✅ Clamp reward
        return round(max(-1.0, min(1.0, reward)), 4)

    def _make_observation(self, reward: float) -> EmailObservation:
        # ✅ Episode complete
        if self._done or self._current_index >= len(self._emails):
            return EmailObservation(
                email_id=-1,
                subject="[Episode Complete]",
                body="All emails processed.",
                sender="system",
                step=self._step_count,
                total_emails=len(self._emails),
                done=True,
                reward=reward,
                task=self._task,
            )

        email = self._emails[self._current_index]

        return EmailObservation(
            email_id=email["email_id"],
            subject=email["subject"],
            body=email["body"],
            sender=email["sender"],
            step=self._step_count,
            total_emails=len(self._emails),
            done=self._done,
            reward=reward,
            task=self._task,
        )