---
title: Email Triage Env
emoji: 📧
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
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
Email triage requires reading comprehension, sender domain analysis,
priority reasoning, and context awareness across reply chains. This
environment provides a structured, reproducible benchmark for exactly that.

Email triage is absent from the current OpenEnv environment catalog, which
skews toward code execution, games, and web browsing. This environment fills
a gap in enterprise communication workflows where agent reliability has
immediate business value.

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

| Field          | Type   | Description                          |
|----------------|--------|--------------------------------------|
| `email_id`     | int    | Unique identifier for the email      |
| `subject`      | string | Email subject line                   |
| `body`         | string | Full email body text                 |
| `sender`       | string | Sender email address                 |
| `step`         | int    | Current step number in episode       |
| `total_emails` | int    | Total emails in this task            |
| `done`         | bool   | Whether the episode is complete      |
| `reward`       | float  | Reward from the last action          |
| `task`         | string | Current task name easy/medium/hard   |

---

## Task Descriptions

### Task 1 — Easy (3 emails)

Spam vs legitimate classification. Emails are unambiguous — obvious scam
domains, clear internal senders, standard newsletters. Tests basic
classification ability. Agent should score near-perfect here.

### Task 2 — Medium (5 emails)

Priority and action selection. Emails require correct action_type AND
priority assignment. Includes client escalations, automated alerts,
meeting requests, and FYI announcements.

### Task 3 — Hard (10 emails)

Adversarial traps requiring body-level reasoning. Agent cannot rely on
subject line alone.

- **Trap 1:** Misleading subject — URGENT server down subject but body is a newsletter
- **Trap 2:** CEO phishing — external domain impersonating an executive requesting wire transfer
- **Trap 3:** Conflicting priorities — two urgent emails, only one is from a real internal VIP
- **Trap 4:** Buried request — actual ask hidden in paragraph 4 of a long reply chain
- **Trap 5:** Friendly spam — warm personal tone from unknown external domain with suspicious link
- **Trap 6:** Duplicate thread — only the follow-up email needs a reply, not the original
- **Trap 7:** False alarm — CRITICAL alert in subject but body says auto-resolved, no action needed
- **Trap 8:** Low priority CEO email — CEO sender but content is a company-wide holiday announcement

---

## Reward Logic

### Per-step reward components
+0.4   correct action_type match
+0.3   correct classification label match
+0.2   correct priority match
-0.2   wrong action_type
-0.1   wrong email_id
-0.05  per extra step beyond optimal step count

### Completion bonus
+1.0   all emails processed successfully (done = True)

### Reward clamping

All per-step rewards are clamped to the range [-1.0, +1.0] before accumulation.

### Final score formula
score = 0.4 x classification_accuracy
+ 0.3 x action_accuracy
+ 0.2 x priority_accuracy
+ 0.1 x efficiency_score
efficiency_score = max(0.0, 1.0 - 0.05 x max(0, steps_taken - optimal_steps))

Final score is always in range [0.0, 1.0]. Deterministic — same inputs always produce same output.

---

## Reward Design Philosophy

The reward function is designed to provide a rich training signal at every
step rather than a sparse end-of-episode outcome. This allows agents to learn
from partial correctness — for example, choosing the right action_type but
wrong priority still earns +0.7 instead of 0.0.

The efficiency penalty (-0.05 per extra step) discourages agents from taking
redundant actions. The completion bonus (+1.0) creates a strong signal for
finishing episodes cleanly. Together these shape an agent toward fast,
accurate, and decisive triage behavior.

The hard task traps are specifically designed so that surface-level keyword
matching fails. An agent must model sender domain legitimacy, body-subject
mismatch, and conversational context to score above 0.8.

---

## Setup Instructions

### Requirements

- Python 3.10 or higher
- pip packages: fastapi, uvicorn, pydantic, openai, pyyaml, requests, openenv-core

### Install
```bash
git clone https://github.com/hugdevp/email-triage-env
cd email-triage-env
pip install -r server/requirements.txt
```

### Environment Variables
```bash
export API_BASE_URL="https://api.groq.com/openai/v1"
export MODEL_NAME="llama-3.3-70b-versatile"
export OPENAI_API_KEY="your_groq_api_key"
export HF_TOKEN="your_hf_token"
export ENV_URL="http://localhost:7860"
```

### Start the server
```bash
PYTHONPATH=. uvicorn server.app:app --host 0.0.0.0 --port 7860
```

### Test endpoints
```bash
curl http://localhost:7860/health

curl -X POST "http://localhost:7860/reset?task=easy"

curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"episode_id": "YOUR_EPISODE_ID", "action_type": "ignore", "priority": "low", "email_id": 1}'

curl http://localhost:7860/state
```

---

## How to Run Inference

### Windows
```cmd
set API_BASE_URL=https://api.groq.com/openai/v1
set MODEL_NAME=llama-3.3-70b-versatile
set OPENAI_API_KEY=your_groq_api_key
set HF_TOKEN=your_hf_token
set ENV_URL=http://localhost:7860
set PYTHONPATH=.
python inference.py
```

### Linux and Mac
```bash
export API_BASE_URL="https://api.groq.com/openai/v1"
export MODEL_NAME="llama-3.3-70b-versatile"
export OPENAI_API_KEY="your_groq_api_key"
export HF_TOKEN="your_hf_token"
export ENV_URL="http://localhost:7860"
PYTHONPATH=. python inference.py
```

---

## Baseline Scores

Measured using llama-3.3-70b-versatile via Groq API with temperature=0 for full reproducibility.

| Task   | Score | Notes                                        |
|--------|-------|----------------------------------------------|
| Easy   | 0.77  | 1 action_type mistake on email 2             |
| Medium | 0.96  | 1 priority mistake on email 1                |
| Hard   | 0.75  | 2 adversarial trap emails caught the model   |

Hard task score is deliberately lower. The adversarial trap design is working as intended.

---

## Docker
```bash
docker build -t email-triage-env .
docker run -p 7860:7860 email-triage-env
```

Open browser to http://localhost:7860/health to verify.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | /health  | Health check — returns status ok |
| GET    | /        | Same as /health |
| POST   | /reset   | Start new episode, returns episode_id and first observation |
| POST   | /step    | Take action, returns observation reward done info |
| GET    | /state   | Get full current session state |

### Reset query parameter
POST /reset?task=easy
POST /reset?task=medium
POST /reset?task=hard

### Step request body
```json
{
  "episode_id": "uuid-from-reset",
  "action_type": "classify",
  "priority": "high",
  "email_id": 1
}
```

---

## Project Structure:
email-triage-env/
├── inference.py          ← Baseline agent script (root level, mandatory)
├── grader.py             ← Final score calculator
├── models.py             ← Pydantic action and observation models
├── client.py             ← EnvClient for external users
├── openenv.yaml          ← OpenEnv spec config
├── pyproject.toml        ← OpenEnv multi-mode deployment compliance
├── README.md
├── Dockerfile
│
├── server/
│   ├── app.py            ← FastAPI server with session registry
│   ├── environment.py    ← EmailTriageEnv class
│   ├── requirements.txt  ← Server dependencies
│   └── init.py
│
└── tasks/
├── easy.py           ← 3 emails and ground truth
├── medium.py         ← 5 emails and ground truth
├── hard.py           ← 10 adversarial trap emails and ground truth
└── init.py

---

## Disqualification Checklist

- Environment deploys and responds on HF Space
- Not plagiarized — original email triage domain not present in existing OpenEnv catalog
- Grader returns different scores per task — Easy 0.77, Medium 0.96, Hard 0.75
- Baseline inference script at root level producing valid logs

