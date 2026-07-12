# Phase 4 — Automatic Scheduler Implementation Notes

> **Status:** Implemented and tested  
> **Date:** July 12, 2026  
> **Milestone:** Automatic humane interaction loop

## Purpose

Phase 4 removes the need to press **Trigger check-in** during ordinary use. A small lifecycle-managed scheduler asks the existing application service to evaluate policy. The deterministic Humane Policy Engine remains the sole authority for whether a nudge is allowed.

## Behavior

- The scheduler starts and stops with the FastAPI lifespan.
- One policy tick runs in a worker thread at a configurable interval.
- API actions and scheduler actions share a reentrant service lock.
- Focus thresholds are evaluated automatically.
- Active quiet intervals and deferrals remain authoritative.
- An expired deferral becomes an explicit reminder, including after restart.
- Interaction-locked states are never advanced by the scheduler.
- Scheduler exceptions are logged and retried without terminating the API.
- `/status` exposes `next_evaluation_at` for the simulator.

The scheduler can be disabled through `create_app(scheduler_enabled=False)` for deterministic hosts and tests. Its default production interval is one second.

## Simulator

The live status card displays the next scheduled check time. The manual trigger remains available as a developer control, but it is no longer required for the ordinary focus loop.

## Verification

The test suite covers automatic threshold evaluation, deferral reminders, scheduler disablement, persisted restart recovery, and all earlier policy and API behavior.

```bash
cd code
.venv/bin/python -m pytest
.venv/bin/ruff check .

cd ..
npm test
npm run lint
npm run build
```

## Deliberately Deferred

- WebSocket body protocol;
- speech recognition and synthesis;
- LLM or model-gateway integration;
- physical ESP32-S3 body;
- network exposure and authentication.
