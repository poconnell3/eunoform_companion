# Phase 1 Implementation Notes

> **Status:** Initial implementation package  
> **Date:** July 11, 2026  
> **Milestone:** Domain and Policy Core

## What This Package Implements

This package implements the first deterministic foundation described in `04_MVP_Specification.md`:

- explicit interaction states and validated transitions;
- authoritative focus-session timing through an injectable clock;
- the deterministic Humane Policy Engine;
- user settings and policy precedence;
- SQLite schema and repositories;
- structured explanation facts;
- unit and behavioral tests.

It intentionally does **not** include an LLM, FastAPI, voice, the body simulator, or physical hardware.

## Core Design Decisions

### Policy Is Pure Decision Logic

`HumanePolicyEngine.evaluate()` accepts a complete `PolicyContext` and returns a `PolicyDecision`. It does not mutate state, write to the database, phrase language, or command a body. This makes precedence behavior easy to test and prevents hidden side effects.

### User Controls Precede All Automated Behavior

The engine evaluates controls in this order:

1. mute;
2. quiet mode;
3. explicit cancellation;
4. active deferral;
5. interaction lock;
6. cooldown;
7. explicit reminder;
8. general wellness threshold.

An explicit reminder therefore cannot silently bypass mute, quiet mode, a deferral, or cooldown.

### Time Is Authoritative

All timestamps are timezone-aware and normalized to UTC. The `Clock` protocol allows production code to use real time while tests use `FixedClock`. No language model is involved in elapsed-time calculation.

### Invalid Transitions Do Not Change State

The state machine raises `InvalidTransitionError` before changing state. UI and future API layers must wait for a confirmed transition before presenting it as complete.

### Persistence Is Explicit

SQLite writes occur in explicit transactions. A caller should only confirm a user action after the repository call succeeds. The behavioral test suite reopens the database to prove that settings, a session, and a nudge survive application restart.

## Repository Layout Added

```text
/pyproject.toml
/apps/companion-service/app/
  domain/
  policy/
  services/
  persistence/
/tests/unit/
/tests/behavior/
/docs/05_Phase_1_Implementation_Notes.md
```

## Running the Tests

With `uv`:

```bash
uv sync --dev
uv run pytest
```

With a conventional virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\\Scripts\\activate
python -m pip install pytest
pytest
```

## Phase 1 Acceptance Covered

The tests currently verify:

- a nudge cannot occur before the threshold;
- a nudge is allowed when the threshold is reached;
- mute and quiet mode override automated behavior;
- a ten-minute deferral is respected for the full ten minutes;
- cooldown blocks even an otherwise-due explicit reminder;
- duplicate nudges cannot occur while awaiting a response;
- invalid state transitions leave state unchanged;
- elapsed time comes from the clock;
- explanations use only authoritative facts;
- persisted state survives a restart.

## Next Implementation Step

Phase 2 should add a small FastAPI layer around the existing domain core. The API should not duplicate policy logic. Endpoints should call services, return the confirmed resulting state, and translate `InvalidTransitionError` into a clear conflict response without mutating state.
