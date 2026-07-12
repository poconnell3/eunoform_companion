# Technical Architecture Plan

> **Status:** Early architecture draft  
> **Last researched:** July 11, 2026  
> **Project:** Eunoform Companion

## Purpose

The Eunoform Companion is a small, desktop-oriented AI presence designed to support time awareness, healthy transitions, and self-care without behaving like a taskmaster. It should feel caring, gentle, friendly, and humane. Its physical form may include a small expressive face, a simple moving arm, voice interaction, and subtle attention cues.

The architecture must support a modest first prototype while preserving a credible path toward a self-contained companion with local AI capabilities.

## Architectural Principles

- **Humane before clever:** Predictable, respectful behavior is more important than maximum automation.
- **Human in the loop:** The companion suggests, asks, and adapts; it does not dictate.
- **Local-first and cloud-optional:** Core functions should remain useful without sending personal activity data to a remote service.
- **Small body, modular brain:** Physical expression and AI computation should be separable so the device can stay compact and evolve over time.
- **Graceful degradation:** The face, controls, basic gestures, timers, and privacy controls should continue working even when the language model or network is unavailable.
- **Explicit behavior rules:** Healthful nudges, cooldowns, quiet hours, and deferrals should be governed by testable policies rather than improvised entirely by a language model.
- **No dead-end prototypes:** Early software, interaction policies, hardware protocols, and expression assets should transfer into later versions.
- **No covert observation:** The companion should not infer emotion, attention, diagnosis, or intent from ambiguous signals without clear consent and strong evidence.

## Core Components

- **AI Model:** A replaceable local or remote language-model backend, rather than a model embedded directly into application logic.
- **Companion Service:** The central application responsible for conversation, time awareness, preferences, memory, policy evaluation, and device coordination.
- **Body Controller:** A small microcontroller responsible for the face, arm, buttons, lights, and local safety behavior.
- **Display:** A small animated screen used primarily for expressions and state communication rather than dense text.
- **Minimal Actuation:** One carefully limited arm or appendage for waving, celebrating, and attracting attention.
- **Voice Pipeline:** Wake-word or push-to-talk activation, voice-activity detection, speech recognition, response generation, and text-to-speech.
- **Local Data Store:** A transparent store for preferences, interaction history, reminders, and user-approved memory.

## AI Capabilities

- **Conversation:** Short, natural, context-aware exchanges with a warm and non-authoritarian personality.
- **Time Awareness:** Explain elapsed time, provide gentle temporal landmarks, and support transitions without treating every interval as a deadline.
- **Humane Nudging:** Offer a break, stretch, drink, posture change, or refocus suggestion according to configurable policies.
- **Deferral and Consent:** Understand responses such as “not now,” “give me ten minutes,” “fewer reminders today,” and “please be quiet.”
- **Adaptive Preferences:** Learn explicit preferences and observed response patterns cautiously, with inspection and reset controls.
- **Expression Coordination:** Convert companion states into facial expressions, small gestures, sounds, and light cues.
- **Cloud Escalation:** Optionally route unusually complex requests to a cloud model only when enabled and clearly indicated.

## Expansion and Scalability

- **Modular Hardware:** The body controller, compute module, display, audio hardware, sensors, and actuator should be independently replaceable.
- **Provider-Agnostic Models:** Local and cloud models should expose a common interface so the companion logic does not depend on a single vendor.
- **Versioned Device Protocol:** Commands and events exchanged with the body should use a documented, versioned message schema.
- **Simulation First:** The physical body should have a software simulator so personality and behavior can be developed before every hardware component exists.
- **Capability Discovery:** The companion service should ask the body which display, gestures, sensors, and indicators are present rather than assuming one fixed build.

---

# Recommendations

## 1. Recommended System Shape: Separate the Brain from the Body

The best first architecture is a **two-part system**:

1. A small **ESP32-S3 body controller** inside the companion.
2. A **local companion service** running initially on an existing desktop or laptop.

This is not a temporary shortcut. It is a durable architectural boundary.

The body controller should own:

- facial animation;
- arm motion and motion limits;
- buttons and touch input;
- listening and privacy indicators;
- optional proximity sensing;
- local idle behavior;
- safe startup, shutdown, and disconnected states.

The companion service should own:

- conversation orchestration;
- time-awareness logic;
- intervention policies;
- reminders and scheduling;
- speech recognition and synthesis;
- local model inference;
- preferences and memory;
- integrations with desktop activity, calendars, or other tools.

### Why this is the preferred starting point

- The physical companion can remain small, cool, quiet, and inexpensive.
- Local AI can still be fully private because it runs on the user’s own computer rather than necessarily in the cloud.
- Hardware development is reduced to approachable display, servo, audio, and sensor work.
- AI models can be changed without rebuilding the physical device.
- A later Compute Module or Jetson base can replace the desktop as the brain while preserving the body firmware and protocol.
- The body remains responsive even while a language model is generating a response.

## 2. Hardware Recommendations

### 2.1 Body Controller: ESP32-S3 with PSRAM

Use an **ESP32-S3 development board with at least 8 MB of PSRAM and 8–16 MB of flash** for the first body controller.

The ESP32-S3 is well matched to this role because it provides:

- dual-core processing up to 240 MHz;
- Wi-Fi and Bluetooth Low Energy;
- plentiful GPIO, PWM, I2S, I2C, SPI, and USB capabilities;
- vector instructions intended for signal-processing and lightweight neural-network workloads;
- a mature development ecosystem;
- enough capability to animate a face, drive a servo, manage controls, and maintain a reliable connection to the companion service.

It should **not** be expected to run the primary conversational language model. Its job is embodiment, responsiveness, and safety.

**Recommended development form:** an ESP32-S3 board with native USB, PSRAM, and an exposed display connector or sufficient SPI pins. A compact module can replace the development board after the enclosure and electronics stabilize.

### 2.2 Display: Small IPS LCD, Not E-Paper

Use a **2.0–2.8 inch IPS LCD**, ideally 320×320 or 480×480, for the expressive face.

A round display can make the companion visually distinctive, while a square display is easier to source, prototype, and mount. The software should treat the face as a resizable canvas so this choice remains reversible.

Prefer an IPS LCD because it supports:

- smooth eye and mouth animation;
- immediate state changes;
- high contrast at normal desk distance;
- flexible color and motion;
- fewer animation constraints than e-paper.

E-paper is excellent for static, low-power information but poorly suited to a lively face. OLED can look beautiful, but persistent eyes and expressions create a burn-in risk; it is better reserved for experiments or designs with aggressive pixel movement and blanking.

The display should communicate only a few clear states: idle, listening, thinking, speaking, nudging, celebrating, unavailable, muted, and needing attention.

### 2.3 Arm and Actuation

For the earliest mechanical prototype, use an inexpensive **metal-geared micro servo** with conservative speed and travel limits. This keeps the first arm inexpensive and easy to replace.

For a refined version, prefer a **ROBOTIS DYNAMIXEL XL330-class smart servo** or equivalent. Compared with a basic hobby servo, a smart serial servo provides position feedback, controlled velocity, current information, and better fault handling. Those features make gestures quieter, safer, and more expressive, but the added cost is not necessary for the first proof of concept.

Recommended safeguards:

- mechanically limit the arm’s range;
- enforce software travel and speed limits in the body controller;
- use compliant or lightweight arm materials;
- stop motion on overcurrent, stall, or repeated positioning error where supported;
- never let a language model send raw motor positions;
- map high-level commands such as `wave_gentle` or `celebrate_small` to pre-approved motion sequences in firmware.

### 2.4 Audio Input

For the first prototype, use a **USB microphone or a two-to-four microphone USB array with acoustic echo cancellation** connected to the host computer. This avoids making embedded audio the first major engineering challenge.

As the companion becomes self-contained, evaluate a compact microphone array based on an XMOS-class audio processor or another board with hardware acoustic echo cancellation, beamforming, and noise suppression.

Audio quality matters more than microphone count. A single well-positioned microphone with a good enclosure and push-to-talk can outperform a poorly integrated array.

The device should include:

- a **physical microphone mute control**;
- an unmistakable listening indicator;
- a push-to-talk option even when wake-word mode exists;
- no raw-audio retention by default.

A hardware mute that electrically disconnects or powers down the microphone is preferable to a software-only mute.

### 2.5 Audio Output

Use a compact **3 W full-range speaker** in a small, vented acoustic chamber. For an embedded build, an I2S Class-D amplifier such as a MAX98357A-class module is an approachable choice. During initial development, USB audio or the host computer’s speaker is acceptable.

Prioritize intelligibility and a pleasant midrange over loudness or bass. The companion should sound close and calm, not like a smart speaker addressing an entire room.

### 2.6 Controls and Indicators

The first body should include:

- one large multifunction button or capacitive touch surface;
- a physical microphone mute switch;
- a visible listening/privacy light that cannot be disabled by the conversational model;
- an optional small rotary encoder for volume or interaction intensity;
- a recessed reset or recovery control.

A single button can support:

- tap: gain attention or push to talk;
- double tap: acknowledge a nudge;
- long press: quiet mode;
- very long press: local safe/recovery mode.

These mappings must remain configurable and discoverable.

### 2.7 Optional Sensors

Start with few or no passive sensors. Add them only when each has a clear, consented purpose.

Useful later additions include:

- a short-range time-of-flight distance sensor to tell whether someone is near the desk;
- an ambient-light sensor for face brightness;
- an inertial sensor to detect whether the companion was picked up or knocked over;
- a temperature sensor for internal thermal monitoring.

Do not begin with a camera. A camera raises privacy, inference, enclosure, bandwidth, and trust concerns before it provides essential value. If a later use case genuinely requires vision, add a physical shutter and an independent activity indicator.

### 2.8 Power and Electrical Design

Use separate regulated power paths for compute/audio and actuator loads, with a shared ground and appropriate filtering. Servo current spikes can otherwise reset the microcontroller, introduce audio noise, or corrupt display behavior.

Recommended practices:

- power the prototype from a certified USB-C supply;
- add bulk capacitance near the servo rail;
- use a dedicated servo regulator when practical;
- provide overcurrent and thermal protection;
- keep motor wiring away from microphone and audio paths;
- prefer locking or keyed internal connectors during enclosure iterations.

Battery power is not recommended for the first desktop version. It adds charging, protection, thermal, certification, and battery-aging complexity without helping the core interaction concept.

### 2.9 Local Compute Options

#### Option A — Recommended MVP: Existing Computer

Run the companion service and AI models on the user’s existing desktop or laptop. Connect the body by USB serial initially, with WebSocket/Wi-Fi as a later option.

This gives the project its fastest route to a useful, embodied prototype and allows larger local models than a small single-board computer can comfortably support.

#### Option B — Self-Contained General-Purpose Version: Raspberry Pi Compute Module 5

Use a **Raspberry Pi Compute Module 5 with 8 GB or 16 GB RAM** and NVMe or eMMC storage when the companion is ready to become self-contained.

The Compute Module 5 is preferable to a full-size Raspberry Pi board for a polished enclosure because it is much smaller, exposes PCIe, supports eMMC options, and allows a custom carrier board. Prototype the self-contained version first on a Raspberry Pi 5, then move to the Compute Module only after ports, thermals, and power requirements are known.

Use active or carefully designed passive cooling. Avoid relying on microSD as the only long-term writable storage; NVMe or eMMC is more appropriate for logs, databases, model files, and frequent updates.

Expected role:

- wake word, VAD, speech recognition, TTS, policy engine, and small quantized language models;
- best suited to compact models and short conversations;
- not a guarantee of instant responses when several AI services run concurrently.

#### Option C — AI-Heavy Version: NVIDIA Jetson Orin Nano Super

Use a **Jetson Orin Nano Super Developer Kit** when low-latency local AI, camera experiments, larger speech workloads, or richer multimodal models become central.

Its GPU and CUDA/TensorRT ecosystem make it substantially more capable for local generative AI than a conventional Raspberry Pi. The tradeoffs are heat, active cooling, power use, enclosure volume, software complexity, and 8 GB of unified memory.

For the small companion, the Jetson is best treated as a **weighted base or separate compute puck**, not necessarily placed behind the face. The body protocol should make this substitution transparent.

#### Option D — Specialized Accelerator: Raspberry Pi AI HAT+ 2

The Raspberry Pi AI HAT+ 2 is technically interesting because it includes a Hailo-10H accelerator and dedicated memory for local language and vision models. It should be treated as a later evaluation path rather than the default MVP.

Reasons to defer it:

- additional hardware cost;
- a more specialized model toolchain;
- model compatibility and conversion constraints;
- less direct benefit to the first one-arm, voice-first companion than a simple host-computer architecture.

Re-evaluate it when the project has a benchmark suite and a specific model known to run well on the Hailo stack.

### 2.10 Recommended First Physical Bill of Materials

The exact brands can remain flexible, but the first useful body should contain approximately:

- ESP32-S3 development board with native USB and PSRAM;
- 2.0–2.8 inch IPS display;
- one micro servo;
- lightweight 3D-printed or hand-built arm;
- one large button or touch input;
- physical microphone-mute switch;
- listening/status LED;
- USB microphone connected to the host computer;
- host-computer audio initially, followed by a small speaker/amplifier;
- powered USB connection;
- simple weighted enclosure with removable panels.

This build is enough to validate the project’s most important questions: Does the companion feel kind? Are its interruptions welcome? Does the arm add emotional clarity? Does a face improve continuity and attention? Those answers matter before expensive embedded AI hardware is selected.

## 3. Software Language and Library Recommendations

### Runtime Boundary

Eunoform Companion uses a polyglot local architecture with explicit runtime responsibilities:

- **Authoritative backend:** Python 3.11+ and FastAPI provide the deterministic companion service, including the policy engine, persistence, domain model, and application services.
- **Interactive simulator and frontend:** Node.js 24 and TypeScript are required for the future visual body simulator and JavaScript-based interface tooling. Each JavaScript or TypeScript package must declare Node `>=24 <25` in its `engines` field.
- **Communication boundary:** Interactive applications communicate with the Python companion service through its local HTTP API. They do not replace or bypass the authoritative Python domain and policy layers.

Future Node-based containers should use `node:24-bookworm-slim` by default. Python service containers should continue to use an appropriate Python base image.

### 3.1 Primary Application Language: Python

Use **Python** for the companion service.

This is the best fit because it aligns with the creator’s existing strengths and provides mature libraries for AI inference, audio, scheduling, APIs, data storage, testing, and hardware communication.

Recommended stack:

- **FastAPI** for the local service API, WebSocket endpoints, configuration interface, and automatically generated API documentation;
- **Pydantic** for typed settings, events, commands, and model-provider contracts;
- **asyncio** for concurrent audio, model, scheduler, and device tasks;
- **SQLite in WAL mode** for preferences, reminders, interaction events, and user-approved memory;
- **SQLModel or SQLAlchemy** only if the database layer grows beyond straightforward SQLite access;
- **APScheduler** for reminders, deferred nudges, quiet-hour boundaries, and recurring temporal landmarks;
- **pyserial** for the first USB body connection;
- **pytest** for policy, protocol, and behavioral acceptance tests.

Avoid starting with a large agent framework. The first companion needs transparent, inspectable orchestration more than generalized autonomous-agent behavior.

### 3.2 Body Firmware: C++ with PlatformIO

Use **C++ with PlatformIO and the Arduino framework for ESP32** for the first body firmware.

This combination provides a gentle entry into physical computing, strong library availability, reproducible builds, serial monitoring, and manageable dependency configuration.

Move selected components to native **ESP-IDF** only when the project requires tighter real-time control, advanced audio, custom USB behavior, secure boot, production OTA updates, or more explicit FreeRTOS task management.

Do not use MicroPython as the long-term body firmware. It is excellent for quick experiments, but predictable display timing, servo safety, memory control, and production recovery behavior favor compiled firmware.

### 3.3 Face Rendering: LVGL

Use **LVGL** for the face and local controls. It is designed for embedded graphical interfaces and can run on the ESP32-S3.

Represent expressions as parameterized components rather than fixed videos:

- eye position and openness;
- brow shape;
- mouth curvature;
- blink timing;
- breathing or idle motion;
- small icon overlays for muted, listening, thinking, or unavailable states.

The companion service should send semantic states such as `gentle_attention` or `quiet_celebration`. The body firmware should decide how those states look on the installed display.

### 3.4 Configuration Interface: TypeScript, React, and Vite

Use **TypeScript with React and Vite** for an optional browser-based configuration and observability interface. This aligns with the creator’s existing front-end experience.

The interface should allow the user to:

- adjust nudge frequency and intensity;
- define quiet hours;
- inspect and delete stored memory;
- test expressions and gestures;
- review why a nudge occurred;
- choose local or cloud model providers;
- inspect privacy and device status;
- export diagnostic logs intentionally.

The browser interface is an administrative surface, not the companion’s personality. Everyday interaction should remain voice-, face-, and gesture-oriented.

## 4. Local AI and Voice Stack

### 4.1 Language-Model Runtime: llama.cpp

Use **llama.cpp** as the primary local language-model runtime, exposed through its OpenAI-compatible server interface.

Reasons:

- efficient C/C++ implementation;
- broad CPU and GPU support;
- ARM support;
- GGUF quantized-model ecosystem;
- CPU/GPU hybrid execution;
- a stable HTTP boundary between the companion application and the model.

The application should not depend on one model name. Define a provider interface supporting:

- local llama.cpp;
- an optional desktop model service;
- an optional cloud API;
- test/fake providers for deterministic development.

On Raspberry Pi-class hardware, begin by benchmarking instruction-tuned models in the **1–3 billion parameter range at four-bit quantization**. On a desktop or Jetson, benchmark larger models only after measuring complete voice-to-voice latency and memory use. Model size should be selected by interaction quality and response time, not by leaderboard position.

The language model should generate language and bounded high-level intentions. It should not directly control timers, privacy state, database writes, or motors without validation by deterministic application code.

### 4.2 Speech Recognition

Recommended order of evaluation:

1. **whisper.cpp** for a simple, portable local speech-to-text baseline, particularly on ARM and CPU-only systems;
2. **sherpa-onnx** when streaming recognition, keyword spotting, unified ONNX deployment, or Jetson/ARM portability becomes more important.

Use small or base-class speech-recognition models first and measure accuracy in the actual room, with the actual microphone, speaker, and fan noise. Embedded voice performance depends heavily on acoustics and echo control, not only model choice.

### 4.3 Voice Activity Detection

Use **Silero VAD through ONNX Runtime**, or the equivalent VAD integrated through sherpa-onnx. Silero VAD is small, fast, portable, and suitable for edge voice interfaces.

VAD should control when audio is sent to speech recognition, but it should not be treated as proof that the user is addressing the companion.

### 4.4 Wake Word

Use **openWakeWord** for an optional local wake word. It is lightweight enough for Raspberry Pi-class devices and supports custom model work.

Wake-word mode should always coexist with:

- push to talk;
- physical mute;
- visible listening state;
- a setting to disable continuous listening entirely.

Do not make the project’s personality dependent on a wake phrase. A button, touch, name, or simple conversational turn should all be valid ways to begin interaction.

### 4.5 Text-to-Speech

Use **Piper** as the first local text-to-speech engine because it is fast, local, available through command-line and programming interfaces, and practical on modest hardware.

Important: the current Piper project is GPL-3.0 licensed. Before distributing a packaged product, review how its use and integration affect the project’s licensing obligations. Keep the TTS provider behind an interface so another engine can be substituted without redesigning the companion.

Voice selection should prioritize warmth, clarity, and low listener fatigue. The companion should speak in short phrases and allow interruption rather than delivering long monologues.

### 4.6 Turn-Taking and Interruption

The speech pipeline should be a state machine rather than one monolithic function:

`idle → attention_detected → listening → transcribing → thinking → speaking → idle`

It should also support:

- barge-in while speaking;
- cancellation;
- mute at any time;
- visible failure states;
- retry without pretending it understood;
- short acknowledgement sounds when full speech would be intrusive.

## 5. Companion Application Architecture

### 5.1 Recommended Modules

Use a modular monolith before considering microservices.

Suggested modules:

- **Conversation Manager:** Builds prompts, maintains short-term context, and coordinates model calls.
- **Humane Policy Engine:** Determines whether, when, and how the companion may nudge.
- **Time-Awareness Service:** Tracks elapsed sessions, temporal landmarks, deferrals, and transitions.
- **Scheduler:** Executes explicit reminders, quiet hours, and deferred actions.
- **Preference Service:** Stores user-controlled behavior and accessibility settings.
- **Memory Service:** Stores only approved summaries and provides inspect/delete/reset controls.
- **Speech Service:** Coordinates wake word, VAD, transcription, synthesis, and audio state.
- **Expression Service:** Maps conversational and policy states to high-level face and gesture requests.
- **Device Bridge:** Maintains body connection, capability discovery, telemetry, and command validation.
- **Model Gateway:** Provides one interface for local and optional cloud models.
- **Audit/Explanation Service:** Records why significant nudges or actions occurred without retaining raw audio.

### 5.2 Humane Policy Engine

This is the most important software component after the basic conversation loop.

Nudging should be governed by explicit conditions such as:

- minimum time since the last nudge;
- whether the user deferred or declined recently;
- quiet hours;
- current conversation state;
- whether the device can attract attention silently first;
- user-selected intensity;
- confidence that the user is present;
- urgency of an explicit reminder versus a general wellness suggestion.

A language model may help phrase a nudge, but it should not decide independently that a nudge is required.

Every nudge should support:

- acknowledge;
- defer;
- dismiss;
- reduce frequency;
- quiet mode;
- explanation: “Why did you remind me?”

### 5.3 State and Memory

Separate these concepts:

- **Ephemeral conversation context:** recent turns needed for coherent dialogue;
- **Session state:** current focus period, last movement, active reminder, and interaction mode;
- **Preferences:** explicit user choices;
- **Long-term memory:** sparse, user-approved summaries only;
- **Audit events:** structured records explaining actions and failures.

Do not store raw microphone audio by default. Do not silently convert casual conversation into permanent memory. Long-term memory should be visible, editable, exportable, and erasable.

### 5.4 Body Communication Protocol

Begin with **USB CDC serial** because it is simple, reliable, low-latency, and easy to debug. Add Wi-Fi/WebSocket only after the USB version is stable.

Use newline-delimited JSON during development for readability. If bandwidth or parsing becomes a problem, preserve the same message schema and move to CBOR later.

Example high-level messages:

```json
{"v":1,"type":"set_expression","name":"gentle_attention","intensity":0.35}
{"v":1,"type":"play_gesture","name":"wave_small","request_id":"abc123"}
{"v":1,"type":"button","gesture":"long_press","timestamp":1783785600}
{"v":1,"type":"capabilities","display":"round_480","gestures":["wave_small","celebrate_small"]}
```

The protocol should include:

- schema version;
- request identifiers;
- acknowledgements;
- timeouts;
- capability discovery;
- safe maximum values;
- heartbeat and disconnected state;
- firmware version and diagnostic status.

## 6. Deployment and Development Practices

### 6.1 Development

Use a single repository with clear boundaries:

```text
/apps/companion-service
/apps/control-ui
/firmware/body-controller
/packages/protocol
/packages/behavior-specs
/simulators/body-simulator
/docs
/tests/behavior
```

Recommended tools:

- `uv` or another modern Python environment/package manager;
- `ruff` for Python linting and formatting;
- `mypy` or Pyright for static type checking;
- `pytest` for unit and behavioral tests;
- PlatformIO for firmware builds and device upload;
- pre-commit hooks for consistent checks;
- GitHub Actions for tests and documentation validation.

### 6.2 Runtime

During development, Docker Compose can help run optional model and support services, but the body firmware and local audio devices should not be forced through containers when that adds friction.

For an appliance-like Raspberry Pi or Jetson deployment, prefer **systemd services** with explicit dependencies, health checks, restart limits, and local logs. Containers may remain useful for the model runtime on Jetson, but they are not an architectural requirement.

### 6.3 Testing

Create behavioral acceptance tests before adding sophisticated adaptation.

Examples:

- After “not now,” the companion does not repeat the same suggestion during the configured cooldown.
- During quiet hours, a non-urgent wellness nudge remains visual and silent.
- A disconnected language model cannot prevent physical mute or button input.
- An invalid gesture command cannot exceed firmware motion limits.
- The companion admits when speech was unclear rather than fabricating an answer.
- Memory is not persisted unless the relevant policy permits it.
- The user can ask why a nudge occurred and receive a plain-language explanation.

The body simulator should display expression and gesture events on screen so most application behavior can be developed without the physical prototype connected.

## 7. Privacy, Security, and Trust Recommendations

- Bind local APIs to loopback by default.
- Require deliberate pairing before accepting a network-connected body.
- Store secrets outside the repository and encrypt them at rest where practical.
- Provide a hardware microphone mute and visible listening indicator.
- Do not retain raw audio by default.
- Make cloud escalation opt-in and visibly distinguish it from local processing.
- Provide one-click memory review, export, and deletion.
- Use signed firmware updates before distributing devices beyond personal prototypes.
- Keep the body’s safety limits in firmware, independent of AI or network state.
- Avoid presenting the companion as a clinician, therapist, or medical device.
- Never use emotional attachment to pressure the user into compliance, continued use, or data sharing.

## 8. What Not to Add Yet

### ROS 2

ROS 2 is powerful but unnecessary for one screen, one arm, and a few sensors. It would add conceptual and deployment overhead before the project needs distributed robotics, mapping, camera pipelines, or coordinated multi-joint motion. Revisit it only if the physical system becomes substantially more robotic.

### Camera and Emotion Recognition

A camera is not required for the core purpose. Emotion or attention inference would create significant privacy and trust risks while producing uncertain conclusions. Begin with explicit interaction, time-based context, and simple presence sensing.

### Autonomous Agent Frameworks

Do not begin with LangChain-style autonomous agents or unrestricted tool execution. Use explicit application services and a small set of validated tools. Add orchestration frameworks only when a concrete requirement exceeds the simpler design.

### Large On-Device Models as a Milestone

The project should not define success as fitting the largest possible model into the smallest enclosure. A fast, bounded, emotionally coherent interaction using a small model or a separate local computer is more aligned with the humane design goal.

### Battery, Mobility, and Multiple Joints

A stationary USB-powered device with one gesture is enough to test embodiment. Batteries, wheels, legs, necks, and multiple arms multiply mechanical and safety work without proving the central relationship.

## 9. Recommended Build Sequence

### Stage 0 — Software Companion and Body Simulator

- Build the Python companion service.
- Implement the humane policy engine and time-awareness model.
- Add text conversation with a model-provider abstraction.
- Simulate facial states and arm gestures in a small desktop window.
- Test nudge language, cooldowns, deferral, quiet modes, and explanations.

### Stage 1 — Expressive Body, Computer Brain

- Add ESP32-S3, display, button, privacy light, and one servo.
- Connect by USB serial.
- Keep microphone, speech recognition, model inference, and TTS on the computer.
- Validate that face and gesture add value rather than distraction.

### Stage 2 — Embedded Audio and Refined Enclosure

- Add dedicated microphone, speaker, amplifier, physical mute, and improved acoustic design.
- Refine expression system and arm mechanics.
- Add optional presence and ambient-light sensors.
- Replace hobby servo with a smart servo if feedback and quieter motion justify it.

### Stage 3 — Self-Contained Compute

- Prototype on Raspberry Pi 5 with NVMe and cooling.
- Benchmark complete wake-to-response and voice-to-voice latency.
- Move to Compute Module 5 and a custom or compact carrier only after requirements stabilize.

### Stage 4 — AI-Accelerated Variant

- Evaluate Jetson Orin Nano Super or Raspberry Pi AI HAT+ 2 against a written benchmark suite.
- Test larger models, streaming speech, and optional multimodal capabilities.
- Keep the same companion service contracts and body protocol.

## 10. Current Preferred Stack

| Layer | Preferred Starting Choice | Upgrade Path |
|---|---|---|
| Physical body | ESP32-S3 with PSRAM | Custom ESP32-S3 carrier/module |
| Face | 2.0–2.8 inch IPS LCD + LVGL | Higher-resolution round display |
| Arm | Metal-geared micro servo | DYNAMIXEL XL330-class smart servo |
| Initial compute | Existing desktop/laptop | Compute Module 5 or Jetson base |
| Application | Python, FastAPI, Pydantic, asyncio | Preserve modular monolith unless scale requires more |
| Firmware | C++, PlatformIO, Arduino-ESP32 | ESP-IDF for production needs |
| Configuration UI | TypeScript, React, Vite | Local PWA or packaged desktop shell |
| LLM runtime | llama.cpp server | Jetson/TensorRT or optional cloud provider |
| Speech recognition | whisper.cpp | sherpa-onnx streaming pipeline |
| Wake word | openWakeWord | Custom wake model or sherpa-onnx KWS |
| VAD | Silero VAD/ONNX | Integrated sherpa-onnx VAD |
| TTS | Piper behind an interface | Alternative local TTS after quality/license review |
| Storage | SQLite WAL | SQLite vector extension only if retrieval is justified |
| Scheduling | APScheduler | Dedicated event scheduler only if needed |
| Body transport | USB serial + JSON | WebSocket and/or CBOR |
| Production runtime | systemd | Selective containers on Jetson |

## 11. Decision Summary

The recommended first embodiment is **not** a Raspberry Pi trying to do everything inside the head. It is a small ESP32-S3 companion body paired with a local Python service running on an existing computer. This is the lowest-risk way to create something charming and useful while preserving all important expansion paths.

The first major technical milestone should be a complete humane interaction loop:

1. The companion notices an explicit timer or focus condition.
2. The policy engine determines that a nudge is appropriate.
3. The face changes subtly and the arm gives a small wave.
4. The companion offers a short, caring prompt.
5. The user can accept, defer, dismiss, or quiet the companion.
6. The companion responds gracefully and updates its cooldown state.

Once that loop feels genuinely supportive, more compute, sensors, and autonomy can be added with confidence.

## Research Basis

The recommendations above were informed by current official documentation and project repositories, including:

- [Raspberry Pi 5](https://www.raspberrypi.com/products/raspberry-pi-5/)
- [Raspberry Pi Compute Module 5](https://www.raspberrypi.com/products/compute-module-5/)
- [Raspberry Pi AI HAT+ 2](https://www.raspberrypi.com/products/ai-hat-plus-2/)
- [NVIDIA Jetson Orin Nano Super Developer Kit](https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/nano-super-developer-kit/)
- [Espressif ESP32-S3](https://www.espressif.com/en/products/socs/esp32-s3)
- [ROBOTIS DYNAMIXEL XL330-M288](https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/)
- [llama.cpp](https://github.com/ggml-org/llama.cpp)
- [whisper.cpp](https://github.com/ggml-org/whisper.cpp)
- [openWakeWord](https://github.com/dscripka/openWakeWord)
- [sherpa-onnx](https://k2-fsa.github.io/sherpa/onnx/)
- [Silero VAD](https://github.com/snakers4/silero-vad)
- [Piper](https://github.com/OHF-Voice/piper1-gpl)
- [FastAPI](https://fastapi.tiangolo.com/)
- [PlatformIO Arduino Framework](https://docs.platformio.org/en/latest/frameworks/arduino.html)
- [LVGL](https://lvgl.io/)

Hardware prices, availability, model support, and software licensing should be rechecked immediately before purchasing components or distributing a packaged product.
