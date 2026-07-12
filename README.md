# Eunoform Companion

A small, humane desktop AI presence that supports neurodivergent focus, healthy time awareness, and gentle self-care — without behaving like a taskmaster.

---

## What It Is

The Eunoform Companion is a physical device with an expressive animated face, a small gesturing arm, and a voice. It sits on your desk, tracks time, offers gentle nudges, and holds brief, warm conversations. It does not surveil, dictate, or optimize. It supports.

Core design values:

- **Gentle, not intrusive** — nudges wait for natural pauses; "not now" is always respected
- **Local-first, cloud-optional** — core behavior works entirely on-device without sending personal data anywhere
- **Humane before clever** — predictable, caring behavior is more important than maximum automation
- **Human in the loop** — the companion suggests and asks; it never dictates

---

## Architecture Overview

The system is split into two distinct parts:

### Body Controller (ESP32-S3)
Handles all physical expression and responsiveness:
- Animated face display (2.0–2.8" IPS LCD, 320×320 or 480×480)
- Arm/gesture servo with strict motion limits
- Buttons, touch input, and privacy controls
- Listening indicator (hardware-level, cannot be overridden by AI)
- Idle and safe-state behavior when disconnected

### Companion Service (runs on desktop/laptop)
Handles intelligence and coordination:
- Conversation, time awareness, and intervention policies
- Speech recognition and synthesis
- Local model inference
- Preferences, memory, and scheduling
- Optional integrations (calendars, desktop activity)

This boundary keeps the physical companion small, cool, and inexpensive while allowing the AI brain to evolve independently.

---

## AI Model Stack

The companion uses **several specialized models**, not one large general-purpose model:

| Role | Model | Notes |
|---|---|---|
| **Presence** (everyday conversation) | Qwen3 4B (Q4_K_M GGUF) | Reasoning disabled; fast, warm, concise |
| **Utility** (routing, extraction, fallback) | LFM2.5 1.2B or Qwen3 1.7B | Lightweight intent classification |
| **Reflection** (planning, complex reasoning) | Qwen3 8B–14B | Invoked deliberately, not on every turn |
| **Speech-to-Text** | Whisper `base.en` via whisper.cpp | Moonshine Tiny for low-power experiments |
| **Text-to-Speech** | Kokoro 82M | Piper as fallback |
| **Embeddings** (optional, later) | BGE Small English v1.5 | Only added when semantic retrieval proves value |

A **deterministic Humane Policy Engine** — ordinary testable software, not an LLM — owns all safety-relevant decisions: timers, cooldowns, quiet hours, deferrals, and motor permissions. The LLM shapes how interaction *feels*; it is never the source of truth for time, consent, or physical safety.

---

## Personality

The companion is **caring, gentle, friendly, and humane**. It:

- waves and says *"How about a quick stretch?"* after long focus sessions
- celebrates completed tasks warmly, not robotically
- waits for a natural pause before interrupting deep focus
- adapts to individual preferences over time — fewer nudges if you prefer, more if you want them
- asks *"How are you feeling?"* rather than issuing commands

---

## Repository Contents

| File | Description |
|---|---|
| [docs/00_Vision_Statement.md](docs/00_Vision_Statement.md) | Purpose and guiding principles |
| [docs/01_Humane_AI_Manifesto.md](docs/01_Humane_AI_Manifesto.md) | Core ethical design commitments |
| [docs/02_Personality_And_Behavior_Guide.md](docs/02_Personality_And_Behavior_Guide.md) | Personality traits and conversational style |
| [docs/03_00_Technical_Architecture_Plan.md](docs/03_00_Technical_Architecture_Plan.md) | High-level architecture summary |
| [docs/03_01_Technical_Architecture_Expanded.md](docs/03_01_Technical_Architecture_Expanded.md) | Full hardware and system design recommendations |
| [docs/03_02_AI_Model_Selection.md](docs/03_02_AI_Model_Selection.md) | Model evaluation and deployment guide |
| [docs/04_MVP_Specification.md](docs/04_MVP_Specification.md) | First testable humane interaction loop, scope, policy rules, and acceptance criteria |
| [docs/05_Phase_1_Implementation_Notes.md](docs/05_Phase_1_Implementation_Notes.md) | Domain models, state machine, persistence, and Humane Policy Engine implementation notes |
| [docs/06_Phase_2_API_Implementation_Notes.md](docs/06_Phase_2_API_Implementation_Notes.md) | Local FastAPI interface, endpoints, and testing notes |

---

## Status

> Phase 2 local API implemented and tested. The visual body simulator is next.
