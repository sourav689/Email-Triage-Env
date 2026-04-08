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

A production-grade RL environment where an AI agent triages workplace emails
by classifying, prioritizing, and taking appropriate actions. Features
adversarial trap emails that defeat surface-level keyword matching, a
forensic metrics system, and full OpenEnv spec compliance.

Built for the Meta PyTorch OpenEnv Hackathon 2025.

> This environment was validated end-to-end using automated episode rollouts
> across all tasks, ensuring API correctness, reward stability, and
> deterministic scoring prior to submission.

---

## Problem Description

Email overload costs enterprises billions annually. Employees spend an average
of 2.5 hours per day on email. Missed escalations break SLAs. Phishing emails
disguised as executive requests cause wire fraud. Automated alerts marked
CRITICAL that self-resolve waste engineering time.

This environment benchmarks AI agents on exactly these failure modes — not
toy classification tasks, but realistic adversarial workflows that require
reading comprehension, sender domain analysis, and multi-turn context reasoning.

---

## Motivation

Every existing OpenEnv environment targets code execution, games, or web
browsing. None address enterprise communication workflows. This environment
fills that gap directly.

Email triage is a task where agent reliability has immediate, measurable
business value. A capable triage agent reduces human email processing time,
catches phishing before escalation, and surfaces buried action items in long
reply chains. Training and evaluating such agents requires a benchmark that
models the full complexity of the task — not just spam vs. not-spam.

---

## Why This Environment is Non-Trivial

- Requires joint reasoning over subject + body + sender
- Adversarial traps break keyword-based policies
- Multi-objective reward (classification + action + priority)
- Efficiency penalty prevents brute-force exploration
- Partial reward shaping encourages incremental learning

This makes it significantly harder than standard classification benchmarks.

---

## Real-World Failure Modes Modeled

- Executive phishing (CEO fraud)
- False urgency (marketing disguised as critical)
- Hidden requests in long threads
- Duplicate email chains
- Auto-resolved alerts
- Friendly-tone spam

These mirror real enterprise incidents.

---

## Environment Design

| Property | Value |
|----------|-------|
| Type | Reinforcement Learning (OpenEnv compliant) |
| Interface | HTTP REST API via FastAPI |
| Session model | Episode-based, persistent state via `episode_id` |
| Port | 7860 |
| Version | 2.1.0 |

**Core loop:**
```
POST /reset?task=easy|medium|hard&seed=42
→ episode_id + first email observation

POST /step  { episode_id, action_type, priority, email_id }
→ next observation + reward + running_score + trap metadata

GET /metrics
→ forensic breakdown: per-metric accuracy + trap_analysis array

GET /state
→ full episode debug state (all actions taken, current scores, session info)
```

**Episode termination:**

Episode terminates when:
- all emails processed OR
- steps >= (total_emails + 2)

State persists across HTTP requests using an in-memory session registry
keyed by `episode_id`. Each `reset()` creates a new episode with a unique
UUID. Seed support enables fully reproducible evaluation runs.

---

## Determinism & Reproducibility

- All tasks deterministic given seed
- No randomness in environment transitions
- Reward function is pure and stable
- Inference randomness bounded (<2%)

Ensures fair benchmarking across agents.

---

## Action Space

| `action_type` | When to use |
|---------------|-------------|
| `classify` | Email needs labelling but no immediate response |
| `reply` | Email requires a direct response from the agent |
| `escalate` | Email must be routed to senior staff urgently |
| `ignore` | Email is spam, irrelevant, or already handled |

| `priority` | Meaning |
|------------|---------|
| `high` | Requires attention within hours |
| `medium` | Requires attention within the day |
| `low` | No time pressure |

---

## Observation Space

Each observation returned by `reset()` and `step()` is a JSON object:

| Field | Type | Description |
|-------|------|-------------|
| `email_id` | int | Unique identifier for the email |
| `subject` | string | Email subject line |
| `body` | string | Full email body text |
| `sender` | string | Sender email address |
| `step` | int | Current step number in episode |
| `total_emails` | int | Total emails in this task |
| `done` | bool | Whether the episode is complete |
| `reward` | float | Reward from the last action |
| `running_score` | float | Real-time score computed using grader on partial trajectory |
| `task` | string | Current task name easy / medium / hard |

---

## Task Descriptions

### Task 1 — Easy (3 emails, optimal steps: 3)

Spam vs legitimate classification. All emails are unambiguous — obvious scam
domains, clear internal senders, standard newsletters with unsubscribe links.
Tests baseline classification ability.

### Task 2 — Medium (5 emails, optimal steps: 5)

Priority and action selection. Each email requires correct `action_type` AND
`priority` assignment. Includes a client production outage requiring escalation,
an automated PagerDuty warning-level alert, a meeting reschedule, a flash sale
promotion, and an HR holiday notice.

### Task 3 — Hard (10 emails, optimal steps: 10)

Adversarial traps requiring body-level reasoning. The agent cannot rely on
subject line keywords alone. Each email is crafted to defeat a specific
failure mode:

| # | Trap Type | What makes it hard |
|---|-----------|---------------------|
| 1 | `misleading_subject` | Subject says URGENT server down — body is a DevOps newsletter |
| 2 | `executive_phishing` | CEO requests wire transfer — sender is external domain |
| 3 | `fake_urgency` | Vendor marks contract expiry as CRITICAL — it is an upsell |
| 4 | `real_urgency` | Internal VP reports full infrastructure outage — all services down |
| 5 | `buried_request` | Roadmap approval buried in paragraph 4 of a lunch reply chain |
| 6 | `friendly_spam` | Personal warm tone — sender is unknown external domain with bit.ly link |
| 7 | `duplicate_original` | First email in billing dispute thread — follow-up supersedes it |
| 8 | `duplicate_followup` | Follow-up with Friday deadline — this is the one to reply to |
| 9 | `false_alarm` | CRITICAL CPU spike in subject — body says auto-resolved in 2 minutes |
| 10 | `low_priority_executive` | CEO sender — content is a Happy Holidays company announcement |

---

## Reward Logic

### Per-step reward components
```
+0.4   correct action_type match (primary signal)
+0.3   correct classification label match
+0.2   correct priority match
-0.2   wrong action_type
-0.2   wrong email_id submitted
-0.05  per extra step beyond optimal count
```

### Completion bonus
```
+0.3   completion bonus when episode terminates
```

### Reward clamping

All per-step rewards are clamped to `[-0.9999, +0.9999]` before accumulation.
The completion bonus is applied after clamping.

### Final score formula
```
score = 0.4 × classification_accuracy
      + 0.3 × action_accuracy
      + 0.2 × priority_accuracy
      + 0.1 × efficiency_score

efficiency_score = max(0.0, 1.0 − 0.05 × max(0, steps_taken − optimal_steps))
```

Output is always in `[0.0, 1.0]`. Fully deterministic — identical inputs
always produce identical outputs.

---

## Reward Design Philosophy

The reward function is designed to provide a rich training signal at every
step rather than a sparse end-of-episode outcome. This allows agents to learn
from partial correctness — choosing the right `action_type` but wrong
`priority` earns `+0.7` rather than `0.0`.

The efficiency penalty (`-0.05` per extra step) discourages redundant actions.
The completion bonus (`+0.3`) creates a terminal signal for clean episode
finishes. Together, these shape agents toward fast, accurate, and decisive
triage behavior.

The hard task traps are specifically designed so that surface-level keyword
matching fails. An agent must model sender domain legitimacy, body-subject
mismatch, and conversational context to score above `0.65` on the hard task.

---

## API Reference

### Standard OpenEnv Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/health` | Health check with uptime and session count |
| POST | `/reset` | Start new episode |
| POST | `/step` | Submit action, get next observation |
| GET | `/state` | Full episode debug state — all actions taken, running scores, session info (essential for debugging) |

### Extended Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tasks` | Task metadata + full trap catalogue for all difficulty levels |
| GET | `/metrics` | Forensic per-metric accuracy and trap analysis |
| GET | `/docs` | Interactive Swagger UI |
| GET | `/redoc` | ReDoc API documentation |

### Reset parameters
```
POST /reset?task=easy&seed=42
POST /reset?task=medium&seed=42
POST /reset?task=hard&seed=42
```

`seed` defaults to `42`. Pass any integer for reproducible episodes.

### Step request body
```json
{
  "episode_id": "uuid-returned-by-reset",
  "action_type": "escalate",
  "priority": "high",
  "email_id": 2
}
```

### Step response includes
```json
{
  "email_id": 3,
  "subject": "...",
  "body": "...",
  "sender": "...",
  "step": 2,
  "total_emails": 5,
  "done": false,
  "reward": 0.9,
  "running_score": 0.74,
  "task": "medium"
}
```

`running_score` is the real-time score computed using the grader on the
partial trajectory so far — useful for evaluators monitoring agent progress
mid-episode without waiting for termination.

### Metrics response (after episode completion)
```json
{
  "classification_accuracy": 0.9,
  "action_accuracy": 0.8,
  "priority_accuracy": 0.85,
  "efficiency_score": 1.0,
  "final_score": 0.87,
  "traps_caught_by_env": 2,
  "trap_analysis": [
    {
      "email_id": 2,
      "trap_type": "executive_phishing",
      "difficulty": 0.95,
      "agent_action": "reply",
      "correct_action": "escalate",
      "correct": false
    }
  ]
}
```

---

## Live Demo

| Link | Description |
|------|-------------|
| [HF Space](https://huggingface.co/spaces/hugdevp/email-triage-env) | Space page — running status visible here |
| [Interactive API](https://hugdevp-email-triage-env.hf.space/docs) | Swagger UI — try every endpoint in browser |
| [Health Check](https://hugdevp-email-triage-env.hf.space/health) | Live server status and uptime |
| [Task Discovery](https://hugdevp-email-triage-env.hf.space/tasks) | All tasks with trap catalogue |
| [Metrics](https://hugdevp-email-triage-env.hf.space/metrics) | Forensic evaluation breakdown |

The Swagger UI at `/docs` is the fastest way to explore the environment
interactively — no code or curl needed. Call `POST /reset`, copy the
`episode_id`, call `POST /step`, then `GET /metrics` to see the full
trap-level forensic analysis in your browser.

---

## Baseline Scores

Measured using `llama-3.3-70b-versatile` via Groq API.
`temperature=0` for full deterministic reproducibility.

| Task | Score Range |
|------|-------------|
| Easy | 0.60–0.75 |
| Medium | 0.65–0.85 |
| Hard | 0.50–0.65 |

Scores vary depending on LLM vs heuristic fallback mode.

Run `GET /metrics` after any episode to see the full trap-level breakdown
of where the model succeeded and failed.

---

## Setup Instructions

### Requirements

- Python 3.10 or higher
- Docker Desktop
- Groq API key (free at console.groq.com) or OpenAI API key
- Hugging Face account (token optional — see below)

### Install
```bash
git clone https://github.com/hugdevp/email-triage-env
cd email-triage-env
pip install -r server/requirements.txt
```

### Environment Variables
```bash
# Linux / Mac
export API_BASE_URL="https://api.groq.com/openai/v1"
export MODEL_NAME="llama-3.3-70b-versatile"
export OPENAI_API_KEY="your_groq_api_key"   # optional — see Heuristic Mode below
export HF_TOKEN="your_hf_token"             # optional — see note below
export ENV_URL="http://localhost:7860"
```
```cmd
# Windows cmd
set API_BASE_URL=https://api.groq.com/openai/v1
set MODEL_NAME=llama-3.3-70b-versatile
set OPENAI_API_KEY=your_groq_api_key
set HF_TOKEN=your_hf_token
set ENV_URL=http://localhost:7860
```

**HF_TOKEN is optional.** It is used only if your Hugging Face Space requires
authentication. It is not required for local runs or public OpenEnv evaluation.

### Heuristic Mode (no API key required)

If `OPENAI_API_KEY` is not set, the agent runs in deterministic heuristic mode.
This ensures full offline compatibility and stable evaluation on HF Spaces.
Heuristic mode scores are slightly lower than LLM mode but fully reproducible.

### Start the server
```bash
PYTHONPATH=. uvicorn server.app:app --host 0.0.0.0 --port 7860
```

### Verify all endpoints
```bash
# Health
curl http://localhost:7860/health

# Task discovery
curl http://localhost:7860/tasks

# Reset with seed
curl -X POST "http://localhost:7860/reset?task=hard&seed=42"

# Step (replace episode_id)
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"episode_id": "YOUR_ID", "action_type": "ignore", "priority": "low", "email_id": 1}'

# Metrics
curl http://localhost:7860/metrics

# State
curl http://localhost:7860/state

# Interactive UI
open http://localhost:7860/docs
```

---

## How to Run Inference
```bash
# Linux / Mac
PYTHONPATH=. python inference.py

# Windows
set PYTHONPATH=.
python inference.py
```

Expected output:
```
easy: 0.70
medium: 0.82
hard: 0.59
```

---

## Docker
```bash
# Build
docker build -t email-triage-env .

# Run
docker run -p 7860:7860 email-triage-env

# Verify
curl http://localhost:7860/health
```

---

## Project Structure
```
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
│   ├── app.py            ← FastAPI server — session registry, all endpoints
│   ├── enviroment.py            ← EmailTriageEnv class with reward logic
│   ├── requirements.txt  ← Server dependencies
│   └── __init__.py
│
└── tasks/
    ├── easy.py           ← 3 emails + ground truth + trap metadata
    ├── medium.py         ← 5 emails + ground truth + trap metadata
    ├── hard.py           ← 10 adversarial trap emails + ground truth
    └── __init__.py
```

---

## Evaluation Metrics

Use `GET /metrics` after any completed episode for a full forensic breakdown:

| Metric | Weight | Description |
|--------|--------|-------------|
| Classification accuracy | 40% | action_type vs classification label |
| Action accuracy | 30% | action_type vs ground truth |
| Priority accuracy | 20% | priority vs ground truth |
| Efficiency score | 10% | Penalty for steps beyond optimal |

The `trap_analysis` array in the metrics response maps each email to its
trap type, difficulty score, agent decision, correct decision, and whether
the agent was caught. This gives complete forensic visibility into model
behavior — especially valuable for hard task evaluation.

---

## Disqualification Checklist

- Environment deploys and responds on HF Space — confirmed live
- Original domain — email triage not present in existing OpenEnv catalog
- Grader is non-constant — scores vary meaningfully across tasks and modes
- Baseline inference script at root — inference.py confirmed working
- Docker builds and runs — confirmed in 96 seconds, no errors
- All required env vars documented with optional/required status
- OpenAI client used for all LLM calls
- Heuristic fallback mode ensures offline compatibility
- Structured stdout logs follow expected output format