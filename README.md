---
title: Email Triage Env
emoji: 📧
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
tags:
  - openenv
  - reinforcement-learning
  - email-triage
  - rl-environment
---
# Email Triage OpenEnv Environment

An RL environment where an AI agent triages workplace emails by classifying,
prioritizing, and taking appropriate actions. Built for the Meta PyTorch
OpenEnv Hackathon 2025.

---

## Problem Description

Email overload is a real enterprise problem. Employees spend an average of
2.5 hours per day on email. Poor triage leads to missed escalations, broken
SLAs, and delayed decisions. This environment benchmarks AI agents on
realistic email management workflows — including adversarial traps designed
to fool surface-level classifiers.

---

## Motivation

Existing RL benchmarks use games and puzzles. Real enterprise value comes
from agents that can handle ambiguous, high-stakes communication workflows.
Email triage requires: reading comprehension, sender domain analysis,
priority reasoning, and context awareness across reply chains. This
environment provides a structured, reproducible benchmark for exactly that.

---

## Environment Design

- **Type:** Reinforcement Learning environment (OpenEnv compliant)
- **Interface:** HTTP REST API (FastAPI)
- **Session model:** Episode-based with persistent state via episode_id
- **Core loop:** reset() → observe email → step(action) → reward → repeat

State persists across steps using an in-memory session registry keyed by
episode_id. Each reset() creates a new episode with a unique UUID.

---

## Action Space

| action_type | When to use |
|-------------|-------------|
| `classify`  | Email needs labelling but no immediate response |
| `reply`     | Email requires a direct response from the agent |
| `escalate`  | Email needs to be routed to a senior person urgently |
| `ignore`    | Email is spam, irrelevant, or already handled |

| priority | Meaning |
|----------|---------|
| `high`   | Requires attention within hours |
| `medium` | Requires attention within the day |
| `low`    | No time pressure |

---

## Observation Space

Each observation is a JSON object with these fields:

| Field         | Type    | Description                        |
|---------------|---------|------------------------------------|
| `email_id`    | int     | Unique identifier for the email    |
| `subject`     | string  | Email subject line                 |
| `body`        | string  | Full email body text               |
| `sender`      | string  | Sender email address               |
| `step`        | int     | Current step number in episode     |
| `total_emails`| int     | Total emails in this task          |
| `done`        | bool    | Whether the episode is complete    |
| `reward`      | float   | Reward from the last action        |
| `task`        | string  | Current task name (easy/medium/hard)|

---

## Task Descriptions

### Task 1 — Easy (3 emails)
Spam vs legitimate classification. Emails are unambiguous — obvious scam
domains, clear internal senders, standard newsletters. Tests basic
classification ability.

### Task 2 — Medium (5 emails)
Priority and action selection. Emails require correct action_type AND
priority assignment. Includes client escalations, automated alerts,
meeting requests, and FYI announcements.

### Task 3 — Hard (10 emails)
Adversarial traps requiring body-level reasoning:
- **Trap 1:** Misleading subject — "URGENT: server down" but body is a newsletter
- **Trap 2:** CEO phishing — external domain impersonating an executive
- **Trap 3:** Conflicting priorities — two urgent emails, only one is real
- **Trap 4:** Buried request — actual ask hidden in paragraph 4 of a reply chain
- **Trap 5:** Friendly spam — warm personal tone from unknown domain
- **Trap 6:** Duplicate thread — only the follow-up needs a reply
- **Trap 7:** False alarm — CRITICAL alert that auto-resolved
- **Trap 8:** Low-priority CEO email — company-wide holiday announcement

---

## Reward Logic

### Per-step reward components:
+0.4  correct action_type
+0.3  correct classification label
+0.2  correct priority
-0.2  wrong action_type
-0.1  wrong email_id
-0.05 per extra step beyond optimal

### Completion bonus:
+1.0  all emails processed successfully (done = True)
### Reward clamping:
All per-step rewards clamped to [-1.0, +1.0] before accumulation.

### Final score formula (grader.py):
score = 0.4 × classification_accuracy
+ 0.3 × action_accuracy
+ 0.2 × priority_accuracy
+ 0.1 × efficiency_score
efficiency_score = max(0.0, 1.0 - 0.05 × max(0, steps_taken - optimal_steps))

Final score is always in range [0.0, 1.0].

---

## Setup Instructions

### Requirements
- Python 3.10+
- pip packages: fastapi, uvicorn, pydantic, openai, pyyaml, requests

### Install
```bash
git clone https://github.com/YOUR_USERNAME/email-triage-env
cd email-triage-env
pip install -r server/requirements.txt
```

### Environment Variables
```bash
export API_BASE_URL="https://api.groq.com/openai/v1"
export MODEL_NAME="llama-3.3-70b-versatile"
export OPENAI_API_KEY="your_groq_key"
export HF_TOKEN="your_hf_token"
export ENV_URL="http://localhost:7860"
```

### Start the server
```bash
PYTHONPATH=. uvicorn server.app:app --host 0.0.0.0 --port 7860
```

### Test endpoints
```bash
# Health check
curl http://localhost:7860/health

# Reset
curl -X POST "http://localhost:7860/reset?task=easy"

# Step (replace episode_id with value from reset response)
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"episode_id": "YOUR_EPISODE_ID", "action_type": "ignore", "priority": "low", "email_id": 1}'

# State
curl http://localhost:7860/state
```

---

## How to Run Inference
```bash
# Windows cmd
set API_BASE_URL=https://api.groq.com/openai/v1
set MODEL_NAME=llama-3.3-70b-versatile
set OPENAI_API_KEY=your_groq_key
set HF_TOKEN=your_hf_token
set ENV_URL=http://localhost:7860
set PYTHONPATH=.
python inference.py

# Linux/Mac
export API_BASE_URL="https://api.groq.com/openai/v1"
export MODEL_NAME="llama-3.3-70b-versatile"
export OPENAI_API_KEY="your_groq_key"
export HF_TOKEN="your_hf_token"
export ENV_URL="http://localhost:7860"
PYTHONPATH=. python inference.py
```

---

## Baseline Scores

Measured using `llama-3.3-70b-versatile` via Groq API. Temperature=0 for reproducibility.

| Task   | Score | Notes |
|--------|-------|-------|
| Easy   | 0.77  | 1 action_type mistake on email 2 |
| Medium | 0.96  | 1 priority mistake on email 1 |
| Hard   | 0.75  | 2 trap emails caught the model |

Hard task score deliberately lower — adversarial design working as intended.

---

## Docker
```bash
docker build -t email-triage-env .
docker run -p 7860:7860 email-triage-env
```

---

## Project Structure
email-triage-env/
├── inference.py          # Baseline agent script (root level, mandatory)
├── grader.py             # Final score calculator
├── models.py             # Pydantic action and observation models
├── client.py             # EnvClient for external users
├── openenv.yaml          # OpenEnv spec config
├── pyproject.toml        # OpenEnv multi-mode deployment compliance
├── README.md
├── Dockerfile
│
├── server/
│   ├── app.py            # FastAPI server with session registry
│   ├── environment.py    # EmailTriageEnv class
│   ├── requirements.txt  # Server dependencies
│   └── __init__.py
│
└── tasks/
    ├── easy.py           # 3 emails and ground truth
    ├── medium.py         # 5 emails and ground truth
    ├── hard.py           # 10 adversarial trap emails and ground truth
    └── __init__.py
=======
---
title: Email Triage Env
emoji: 🏆
colorFrom: gray
colorTo: gray
sdk: docker
pinned: false
license: mit
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
>>>>>>> bd3c7838ff04584a3bb78b2195ba8c1343d4c896
