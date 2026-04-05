from pydantic import Field
from typing import Literal, Optional
from openenv.core.env_server.types import Action, Observation


class EmailAction(Action):
    """Agent action on a single email."""
    action_type: Literal["classify", "reply", "escalate", "ignore"] = Field(
        ..., description="What the agent decides to do with the email"
    )
    priority: Literal["high", "medium", "low"] = Field(
        ..., description="Agent-assigned priority level"
    )
    email_id: int = Field(
        ..., description="ID of the email being acted on"
    )


class EmailObservation(Observation):
    """What the agent sees at each step."""
    email_id: int = Field(..., description="Unique email identifier")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Full email body text")
    sender: str = Field(..., description="Sender email address")
    step: int = Field(default=0, description="Current step number")
    total_emails: int = Field(default=0, description="Total emails in task")
    done: bool = Field(default=False, description="Episode complete flag")
    reward: float = Field(default=0.0, description="Reward from last action")
    task: str = Field(default="easy", description="Current task name")