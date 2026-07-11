# Eunoform Companion MVP Specification

> **Status:** Initial implementation specification  
> **Date:** July 11, 2026  
> **Project:** Eunoform Companion  
> **Milestone:** Software-first humane interaction loop

## 1. Purpose

The first Eunoform Companion MVP exists to test one central proposition:

> Can a small companion gently help a person remain connected to time and physical well-being without feeling controlling, scolding, intrusive, or productivity-obsessed?

The MVP is not intended to prove the final hardware platform, select a permanent AI model, implement long-term memory, or create a general-purpose assistant. It should validate the emotional and behavioral quality of one complete interaction before the project adds technical complexity.

## 2. MVP Outcome

The MVP is successful when a user can:

1. begin a focus session;
2. receive a gentle break suggestion after a configurable interval;
3. see the companion express attention through a software face and simulated arm gesture;
4. accept, defer, dismiss, or silence the suggestion;
5. ask why the suggestion occurred;
6. trust that the system respects the response;
7. continue using the companion without an AI model or physical body connected.

The core milestone is a complete, testable, humane interaction loop.

## 3. Design Principles

The MVP must preserve the following principles from the project vision and Humane AI Manifesto:

- **Agency over automation:** The user always controls whether and when a suggestion is followed.
- **Presence over interruption:** The companion should first attract attention subtly and should speak only when appropriate.
- **Continuity over productivity:** The goal is helping the user stay connected with time and self-care, not maximizing output.
- **Relationship over transaction:** The interaction should feel warm and considerate without simulating dependency.
- **Humane before clever:** Predictable and respectful behavior is more important than generative novelty.
- **Explicit consent:** Deferral, dismissal, quiet mode, and correction must be immediate and reliable.
- **Graceful degradation:** Core behavior must work without an LLM, network connection, voice stack, or physical body.
- **Inspectable behavior:** The system must be able to explain why a nudge occurred.

## 4. Target User and Context

The initial user is a neurodivergent adult working at a desktop who may:

- lose awareness of elapsed time while hyperfocusing;
- remain seated or physically still longer than intended;
- experience blunt reminders as disruptive or shaming;
- need help transitioning without being commanded;
- prefer a warm, expressive presence over a productivity dashboard;
- want clear control over reminders, quiet periods, and stored information.

The MVP is a personal prototype, not a medical device, diagnostic tool, therapist, or workplace-monitoring system.

## 5. Primary User Story

> As a person who can become deeply absorbed in work, I want a gentle companion to make me aware that time has passed and offer a brief physical pause, so I can reconnect with my body and choose what to do without feeling reprimanded.

## 6. Core Vertical Slice

The MVP implements one end-to-end scenario:

1. The user starts a focus session manually.
2. The Time-Awareness Service records the start time.
3. The configured focus interval expires.
4. The Humane Policy Engine evaluates whether a nudge is currently permitted.
5. The Body Simulator changes from `idle` to `gentle_attention`.
6. The simulator performs a small, non-urgent wave.
7. The companion offers a short break suggestion using an approved template.
8. The user accepts, defers, dismisses, requests quiet mode, or asks why.
9. The system updates session and cooldown state.
10. The companion returns to an appropriate idle or quiet state.

## 7. In Scope

### 7.1 Focus Session Control

- Start a focus session manually.
- Stop or cancel a focus session manually.
- Display elapsed focus time.
- Configure the initial nudge interval.
- Preserve session state across ordinary UI refreshes.

### 7.2 Humane Nudging

- Evaluate nudges through deterministic policy rules.
- Attract attention visually before presenting text.
- Use short, approved language templates.
- Support multiple levels of interaction intensity.
- Record the structured reason for each nudge.

### 7.3 User Responses

The MVP must support:

- **Accept:** Acknowledge the suggestion and begin a short break state.
- **Defer:** Postpone the suggestion by a specific duration.
- **Dismiss:** End the current suggestion without scheduling an immediate repeat.
- **Quiet:** Suppress non-urgent suggestions for a defined period.
- **Reduce frequency:** Increase the minimum interval between nudges for the current day or session.
- **Ask why:** Explain the policy facts that caused the suggestion.
- **Correct:** Replace a misunderstood duration or response.

### 7.4 Body Simulator

The software simulator must represent:

- face state;
- arm or gesture state;
- current interaction state;
- mute or quiet status;
- connection status;
- basic event history for debugging.

The initial simulator may be visually simple. Emotional clarity and timing matter more than visual polish.

### 7.5 Explainability

For every nudge, the system must be able to answer with facts such as:

- when the focus session began;
- how much time elapsed;
- which configured threshold was reached;
- when the previous nudge occurred;
- whether the suggestion was a general wellness prompt or an explicit reminder.

The explanation must not invent observations such as posture, mood, fatigue, or attention unless a future consented sensor provides reliable evidence.

### 7.6 Local Persistence

Store only the structured information required for the MVP:

- user settings;
- focus-session state;
- nudge events;
- deferrals;
- quiet-mode intervals;
- response outcomes;
- explanation facts.

Use SQLite. Do not store raw audio, inferred emotion, or unrestricted conversation history.

## 8. Explicitly Out of Scope

The following are deferred until the core interaction has been evaluated:

- physical ESP32-S3 hardware;
- servo control;
- production facial animation;
- wake-word detection;
- speech recognition;
- text-to-speech;
- long-term conversational memory;
- vector databases or embeddings;
- calendar integration;
- desktop-activity monitoring;
- cameras;
- emotion or attention recognition;
- autonomous agents;
- cloud-model dependency;
- fine-tuning;
- multi-user support;
- mobile applications;
- batteries or portable operation;
- clinical or therapeutic claims.

An optional local LLM may be added only after the deterministic template-driven loop is complete and tested.

## 9. Interaction States

The application should use an explicit state machine.

```text
idle
  └── start_focus → focusing

focusing
  ├── threshold_reached_and_policy_allows → attracting_attention
  ├── stop_focus → idle
  └── enter_quiet → quiet

attracting_attention
  ├── visual_cue_complete → awaiting_response
  ├── cancel → focusing
  └── enter_quiet → quiet

awaiting_response
  ├── accept → on_break
  ├── defer → deferred
  ├── dismiss → focusing
  ├── ask_why → explaining
  ├── reduce_frequency → focusing
  └── enter_quiet → quiet

explaining
  └── explanation_complete → awaiting_response

deferred
  ├── deferral_expires → policy_evaluation
  ├── stop_focus → idle
  └── enter_quiet → quiet

on_break
  ├── resume_focus → focusing
  └── stop_focus → idle

quiet
  ├── quiet_expires → previous_safe_state
  └── user_disables_quiet → previous_safe_state
```

State transitions must be deterministic and testable. The UI must not imply that a transition occurred until the application confirms it.

## 10. Humane Policy Engine

The Humane Policy Engine has final authority over whether a nudge is allowed.

### 10.1 Required Inputs

- current time;
- focus-session start time;
- elapsed focus duration;
- configured initial threshold;
- minimum cooldown since the last nudge;
- active deferral;
- active quiet mode;
- current interaction state;
- most recent response to a nudge;
- user-selected interaction intensity;
- whether an explicit reminder is due.

### 10.2 Initial Policy Rules

A general wellness nudge is permitted only when all of the following are true:

- a focus session is active;
- the initial focus threshold has elapsed;
- no quiet interval is active;
- no deferral is active;
- the minimum cooldown has elapsed;
- the companion is not already awaiting a response;
- the companion is not speaking, explaining, or handling another action;
- the user has not disabled wellness suggestions for the current session.

### 10.3 Initial Defaults

Defaults are starting values for testing, not permanent behavioral assumptions:

```yaml
focus:
  initial_nudge_minutes: 45
  repeat_nudge_minutes: 30

cooldowns:
  after_dismiss_minutes: 30
  after_accept_minutes: 30
  after_irritation_minutes: 120

quiet_mode:
  default_minutes: 60

interaction:
  intensity: gentle
  visual_lead_in_seconds: 3
  maximum_nudge_words: 20
```

All defaults must be user-configurable.

### 10.4 Policy Precedence

Use the following precedence, highest first:

1. physical or application-level mute;
2. quiet mode;
3. explicit user cancellation;
4. active deferral;
5. current interaction lock;
6. cooldown;
7. explicit scheduled reminder;
8. general wellness threshold.

A lower-priority rule must never bypass a higher-priority user preference.

## 11. Approved Initial Language

The first MVP should use a small template library rather than generative text.

### Gentle Attention

- “You’ve been here for a while. Would a quick stretch feel good?”
- “A little time has passed. Is this a good moment to move for a minute?”
- “Just a gentle check-in—would you like a brief pause?”

### Acceptance

- “Okay. I’ll be here when you’re ready.”
- “Sounds good. Let’s take a small pause.”

### Deferral

- “Of course. I’ll check back in {duration}.”
- “Got it. I’ll give you {duration} more.”

### Dismissal

- “Okay. I’ll leave you with it.”
- “No problem. I won’t repeat that right away.”

### Quiet Mode

- “Quiet mode is on for {duration}.”
- “Understood. I’ll stay quiet until {time}.”

### Explanation

- “You started this focus session {elapsed} ago, and your break-check interval is {threshold}.”

### Correction or Failure

- “I may have misunderstood. What duration should I use?”
- “I couldn’t apply that change, so I left your current setting alone.”

Templates should be evaluated for warmth, clarity, brevity, and freedom from infantilizing or coaching language.

## 12. Initial Simulator Behavior

### 12.1 Face States

- `idle`
- `focusing`
- `gentle_attention`
- `awaiting_response`
- `acknowledging`
- `quiet`
- `celebrating_small`
- `unavailable`
- `error_honest`

### 12.2 Gesture States

- `none`
- `wave_small`
- `acknowledge_small`
- `celebrate_small`

The simulator must accept semantic commands. It must not expose raw servo angles or future hardware-specific coordinates to application logic.

Example:

```json
{
  "v": 1,
  "type": "play_gesture",
  "name": "wave_small",
  "intensity": 0.3,
  "request_id": "nudge-123"
}
```

### 12.3 Attention Sequence

The initial sequence should be:

1. face changes to `gentle_attention`;
2. simulator performs `wave_small`;
3. application waits for the visual lead-in interval;
4. text prompt appears;
5. simulator changes to `awaiting_response`;
6. no additional animation repeats while waiting.

The system should avoid flashing, bouncing, repeated waving, loud alerts, or urgency cues for general wellness nudges.

## 13. Application Components

The MVP should remain a modular monolith.

```text
/apps/companion-service/
  app/
    api/
    domain/
      interaction_state.py
      events.py
      commands.py
    policy/
      humane_policy_engine.py
      policy_models.py
    services/
      focus_session_service.py
      time_awareness_service.py
      scheduler_service.py
      explanation_service.py
      template_service.py
    persistence/
      database.py
      repositories.py
    device/
      body_protocol.py
      simulator_bridge.py
    settings.py
    main.py

/simulators/body-simulator/
  simulator/
    app.py
    face.py
    gestures.py
    state.py

/tests/behavior/
/tests/unit/
/docs/
```

The exact filenames may evolve, but the responsibility boundaries should remain clear.

## 14. Suggested API Surface

A small local API should be enough for the MVP.

```text
POST   /focus-sessions
GET    /focus-sessions/current
POST   /focus-sessions/current/stop

POST   /interactions/current/accept
POST   /interactions/current/defer
POST   /interactions/current/dismiss
POST   /interactions/current/quiet
POST   /interactions/current/reduce-frequency
GET    /interactions/current/explanation

GET    /settings
PATCH  /settings

GET    /status
GET    /events

WS     /body
```

All write endpoints must return the confirmed resulting state. Invalid transitions must return a clear error without changing state.

## 15. Minimum Data Model

### Focus Session

```text
id
started_at
ended_at
status
initial_nudge_at
last_nudge_at
next_eligible_nudge_at
```

### Nudge Event

```text
id
focus_session_id
created_at
policy_reason
threshold_minutes
elapsed_minutes
interaction_intensity
expression_name
gesture_name
outcome
```

### Deferral

```text
id
nudge_event_id
created_at
duration_minutes
expires_at
status
```

### Quiet Interval

```text
id
started_at
ends_at
source
status
```

### Settings

```text
initial_nudge_minutes
repeat_nudge_minutes
after_dismiss_cooldown_minutes
quiet_default_minutes
interaction_intensity
visual_lead_in_seconds
wellness_nudges_enabled
```

Timestamps should be stored in UTC and displayed in the user’s local time zone.

## 16. Behavioral Acceptance Tests

The following behaviors are required before the MVP is considered complete.

### Session and Timing

- Starting a focus session records the correct start time.
- A nudge cannot occur before the configured threshold.
- Stopping a focus session prevents future nudges from that session.
- Elapsed time is calculated from authoritative timestamps rather than LLM output.

### Deferral

- “Give me ten minutes” creates a ten-minute deferral.
- No equivalent wellness nudge occurs during the deferral.
- A corrected duration replaces the unconfirmed or mistaken duration.
- The system never claims a deferral was saved unless persistence succeeds.

### Dismissal and Cooldown

- Dismissal ends the current interaction.
- The same suggestion is not repeated during the configured cooldown.
- Repeated dismissal increases no setting unless the user explicitly requests it.

### Quiet Mode

- Quiet mode suppresses all non-urgent prompts.
- Visual animation does not bypass quiet mode unless explicitly configured.
- The user can end quiet mode manually.
- Quiet-mode expiration returns the system to a safe previous state.

### Explainability

- “Why did you remind me?” returns the actual elapsed time and configured threshold.
- The explanation does not claim to have observed posture, emotion, fatigue, or concentration.
- Explanation remains available after accept, defer, or dismiss through the event history.

### Personality

- A nudge is normally no longer than 20 spoken-equivalent words.
- The companion does not shame, threaten, moralize, or express disappointment.
- The companion does not frame compliance as pleasing the companion.
- The companion accepts correction without argument.
- The companion does not turn a dismissal into a coaching conversation.

### Failure and Degradation

- The template-driven loop works with no LLM configured.
- The simulator can disconnect without corrupting focus-session state.
- A failed simulator command does not cause repeated prompts.
- A persistence failure is reported honestly.
- Invalid state transitions do not modify application state.

## 17. Definition of Done

The MVP milestone is complete when:

- one focus session can run through the complete humane interaction loop;
- accept, defer, dismiss, quiet, reduce-frequency, and ask-why actions work;
- the Body Simulator visibly represents the interaction state;
- the Humane Policy Engine passes all behavioral tests;
- the system runs without an LLM or network connection;
- SQLite persistence survives an application restart;
- event history explains every nudge;
- the user can configure the primary timing and quiet-mode settings;
- no model or simulator component can bypass policy decisions;
- the user judges the interaction as supportive enough to continue testing.

## 18. Evaluation Questions

After using the MVP, record qualitative answers to:

- Did the companion help make elapsed time feel more visible?
- Did the visual cue feel gentler than an ordinary notification?
- Did the simulated wave add emotional clarity or merely distraction?
- Did the wording feel caring without sounding infantilizing?
- Did deferral and dismissal feel immediately respected?
- Was the companion too chatty, too quiet, or appropriately present?
- Did asking “why” increase trust?
- Did the companion reduce or increase transition friction?
- Which interaction felt most artificial?
- Would the user voluntarily keep the companion running during real work?

These answers should guide the next iteration more strongly than adding features for their own sake.

## 19. Implementation Sequence

### Phase 1 — Domain and Policy Core

- Define states, commands, and events.
- Implement the focus-session clock.
- Implement the Humane Policy Engine.
- Implement settings and SQLite persistence.
- Write unit and behavioral tests.

### Phase 2 — Local API

- Add FastAPI endpoints.
- Validate state transitions with Pydantic models.
- Add event and explanation endpoints.
- Provide generated API documentation.

### Phase 3 — Body Simulator

- Render the minimum face states.
- Render semantic gestures.
- Connect through the versioned body protocol.
- Implement safe disconnected behavior.

### Phase 4 — End-to-End Interaction

- Connect policy decisions to simulator expressions and templates.
- Add accept, defer, dismiss, quiet, and ask-why controls.
- Test complete sessions manually.
- Record subjective interaction notes.

### Phase 5 — Optional Presence Model

Only after the deterministic MVP is stable:

- add the provider-agnostic Model Gateway;
- test Qwen3 4B in non-thinking mode;
- permit the model to rephrase approved semantic intentions;
- validate all generated output against length and behavior constraints;
- preserve templates as the fallback path;
- keep policy, time, persistence, and device permissions outside the model.

## 20. Post-MVP Decision Gate

Do not move directly from a working software demo to purchasing every planned hardware component.

Proceed to the first ESP32-S3 physical prototype only when:

- the humane interaction loop feels useful during real work;
- the simulator’s face and gesture demonstrably improve the experience;
- the interaction timing is stable enough to encode physically;
- the semantic body protocol has remained usable through at least one revision;
- the user wants the companion present beyond the novelty period.

If those conditions are not met, revise the behavior and interaction model before adding hardware.

## 21. Bottom Line

The first Eunoform Companion should not try to be an impressive robot. It should prove that a machine can gently enter a person’s attention, make time more visible, offer care without control, and gracefully accept “not now.”

Everything else—voice, local models, memory, sensors, and physical embodiment—should grow from that successful relationship.
