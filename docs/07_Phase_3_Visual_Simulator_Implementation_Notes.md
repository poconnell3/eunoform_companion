# Phase 3 — Visual Body Simulator Implementation Notes

> **Status:** Implemented and tested  
> **Date:** July 12, 2026  
> **Milestone:** Software body consuming the deterministic local API

## Purpose

Phase 3 adds a browser-based visual body for the companion without moving policy or interaction authority into the user interface. The simulator renders semantic expressions and bounded gestures from the confirmed API state.

## Added Components

- Node.js 24 npm workspace at the repository root;
- TypeScript and Vite application in `code/apps/body-simulator`;
- semantic state-to-expression and state-to-gesture mapping;
- small arm, face, connection, focus-time, mute, and quiet indicators;
- controls for the complete MVP response loop;
- factual explanations and recent event history;
- mock-state mode for isolated visual development;
- reduced-motion, low-sensory, and high-contrast preferences;
- Vitest, ESLint, production build, and CI coverage.

## API Integration

The Vite development and preview servers proxy `/api` to `http://127.0.0.1:8000`. The simulator polls `/status` and treats every returned state as authoritative. After an `attracting_attention` animation completes, it calls `/interactions/current/attention-complete`; it never advances the state locally.

## Run Locally

In one terminal:

```bash
cd code
source .venv/bin/activate
uvicorn app.main:app --app-dir apps/companion-service --host 127.0.0.1 --port 8000
```

In another terminal from the repository root:

```bash
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Verify

```bash
npm test
npm run lint
npm run build

cd code
.venv/bin/python -m pytest
.venv/bin/ruff check .
```

## Deliberately Deferred

- background scheduler loop;
- WebSocket body protocol;
- speech recognition and synthesis;
- LLM or model-gateway integration;
- physical ESP32-S3 body;
- network exposure and authentication.
