# Phase 2 — Local API Implementation Notes

> **Status:** Implemented and tested  
> **Date:** July 11, 2026  
> **Milestone:** Local FastAPI interface around the deterministic Phase 1 core

## Purpose

Phase 2 exposes the focus-session, policy, interaction, settings, explanation, and event-history capabilities through a local HTTP API. The API does not make policy decisions itself; it delegates to the deterministic Humane Policy Engine and explicit interaction state machine.

## Added Components

- `app/main.py` — application factory and local FastAPI entry point
- `app/api/router.py` — HTTP routes and error mapping
- `app/api/schemas.py` — validated request and response contracts
- `app/services/companion_application_service.py` — orchestration across domain services and repositories
- API tests covering normal flows, invalid transitions, settings validation, persistence, and event history

## Public MVP Routes

```text
GET    /status
POST   /focus-sessions
GET    /focus-sessions/current
POST   /focus-sessions/current/stop
POST   /focus-sessions/current/resume

POST   /interactions/current/accept
POST   /interactions/current/defer
POST   /interactions/current/dismiss
POST   /interactions/current/quiet
POST   /interactions/current/quiet/end
POST   /interactions/current/reduce-frequency
GET    /interactions/current/explanation

GET    /settings
PATCH  /settings
GET    /events
```

## Internal Bridge Routes

These routes support the future scheduler and body simulator. They are intentionally explicit rather than hidden background behavior.

```text
POST   /interactions/evaluate
POST   /interactions/current/attention-complete
```

`/interactions/evaluate` asks the policy engine whether a nudge is currently allowed. If allowed, it creates a structured nudge event and moves the interaction into `attracting_attention`. The simulator will later call `attention-complete` after the visual lead-in and small gesture have finished.

## Error Behavior

- Invalid state transitions return HTTP `409 Conflict`.
- Invalid request values return HTTP `422 Unprocessable Entity`.
- A rejected transition is checked before creating a deferral or quiet interval.
- Write endpoints return the confirmed resulting application state.

## Persistence and Restart Recovery

The API uses the existing SQLite repositories. On restart it restores a safe interaction state from persisted facts:

- no active session → `idle`
- active session with active quiet interval → `quiet`
- active session with active deferral → `deferred`
- otherwise → `focusing`

A previously persisted nudge is retained in event history but is not silently restored as a live interaction. This avoids accepting, deferring, or dismissing a stale prompt after a process restart.

## Run Locally

From the repository’s `code` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

uvicorn app.main:app \
  --app-dir apps/companion-service \
  --host 127.0.0.1 \
  --port 8000 \
  --reload
```

Open the generated API documentation at:

```text
http://127.0.0.1:8000/docs
```

The host should remain `127.0.0.1` during personal prototype development so the service is not exposed to the local network by default.

## Test

```bash
python -m pytest
```

Phase 2 adds 13 API tests. They cover:

- initial status;
- starting and stopping sessions;
- duplicate-session rejection;
- policy blocking before the threshold;
- allowed nudge creation;
- attention handoff;
- accept and resume;
- ten-minute deferral;
- cooldown after dismissal;
- quiet mode;
- factual explanations;
- settings updates and validation;
- event history;
- invalid-action conflicts;
- restart recovery;
- stopping a session while quiet.

## Deliberately Deferred

- background scheduler loop;
- graphical body simulator;
- WebSocket body connection;
- speech input and output;
- LLM integration;
- authentication for network exposure;
- multi-user support.

The next milestone is Phase 3: a visual body simulator consuming semantic expression and gesture commands.
