from openenv.core.http_env_client import HTTPEnvClient
from models import EmailAction, EmailObservation


class EmailTriageEnvClient(HTTPEnvClient):
    """Client for interacting with the Email Triage environment."""

    action_cls = EmailAction
    observation_cls = EmailObservation

    def reset(self, task: str = "easy") -> EmailObservation:
        return super().reset(task=task)