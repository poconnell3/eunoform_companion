# AI Model Selection and Deployment Guide

> **Status:** Research-backed model architecture draft  
> **Last researched:** July 11, 2026  
> **Project:** Eunoform Companion  
> **Companion document:** `technical-architecture.md`

## Purpose

This document evaluates the small and large AI models that best fit the Eunoform Companion’s architecture.

The Companion is not intended to be a general-purpose autonomous agent trapped inside a cute enclosure. It is a small, humane desktop presence that helps with time awareness, transitions, healthy breaks, continuity, and gentle conversation. Model selection must therefore optimize for:

- low conversational latency;
- a warm, controllable interaction style;
- reliable short responses;
- local privacy;
- predictable tool use;
- modest power and thermal requirements;
- graceful degradation;
- replaceability as the model landscape changes;
- compatibility with a very small physical body;
- enough intelligence to be useful without allowing the model to control safety-critical behavior.

The best model for a benchmark is not automatically the best model for this companion. A model that reasons brilliantly but pauses for fifteen seconds, talks for five paragraphs, or inconsistently follows a “not now” request is a poor presence model.

---

# Executive Recommendation

## Recommended Model Architecture

Use **several specialized models and deterministic services**, not one model for everything.

1. **Deterministic Humane Policy Engine**
   - Owns timers, cooldowns, quiet hours, deferrals, escalation limits, consent, privacy state, and motor permissions.
   - Is ordinary testable software, not an LLM.
   - Has final authority over whether a nudge or physical gesture is allowed.

2. **Presence Model**
   - Handles ordinary conversation, brief explanations, phrasing, acknowledgements, and personality.
   - Runs with reasoning disabled or minimized.
   - Produces short, speakable responses quickly.
   - Default starting candidate: **Qwen3 4B**, quantized to a good four-bit GGUF.

3. **Low-Power Presence / Utility Model**
   - Provides a smaller fallback for limited hardware, routing, extraction, intent classification, or offline degraded operation.
   - Default candidate: **LFM2.5 1.2B Instruct**.
   - Alternative: **Qwen3 1.7B**.

4. **Reflection Model**
   - Used only for difficult planning, nuanced reflection, complex reasoning, or multi-step tool work.
   - Is invoked deliberately rather than on every spoken turn.
   - Initial desktop candidates: **Qwen3 8B or 14B**, then **gpt-oss-20b** on hardware with sufficient headroom.

5. **Speech-to-Text Model**
   - Initial default: **Whisper `base.en` or `small.en` through whisper.cpp**.
   - Low-power experiment: **Moonshine Tiny**.
   - NVIDIA/desktop quality experiment: **Parakeet TDT 0.6B v3**.

6. **Text-to-Speech Model**
   - First quality candidate: **Kokoro 82M**.
   - Operational fallback: **Piper**, after auditing the license of the selected voice.

7. **Memory Retrieval**
   - Begin with SQLite, structured memory, and full-text search.
   - Add **BGE Small English v1.5** only when semantic retrieval demonstrates clear value.
   - Evaluate **Qwen3 Embedding 0.6B** later if multilingual or stronger retrieval justifies its larger footprint.

## Default Prototype Profile

For the software-first prototype running on an existing 16 GB computer:

```yaml
model_profiles:
  presence:
    model_family: Qwen3
    size: 4B
    format: GGUF
    quantization_target: Q4_K_M_or_equivalent
    reasoning: disabled
    working_context_tokens: 4096
    maximum_context_tokens: 8192
    maximum_response_tokens: 160
    streaming: true

  low_power:
    model_family: LFM2.5
    size: 1.2B
    format: GGUF
    quantization_target: Q4_or_equivalent
    reasoning: not_applicable
    working_context_tokens: 4096
    maximum_response_tokens: 120

  reflection:
    model_family: Qwen3
    size: 8B
    format: GGUF
    quantization_target: Q4_K_M_or_equivalent
    reasoning: enabled_only_when_requested
    working_context_tokens: 8192
    maximum_response_tokens: 800

speech:
  recognition: whisper.cpp_base.en
  synthesis: kokoro_82m
  vad: silero_vad

memory:
  primary_store: sqlite
  lexical_search: sqlite_fts5
  semantic_embeddings: disabled_until_needed
```

This is a starting benchmark configuration, not a permanent lock-in.

---

# 1. The Companion Should Not Be “One Giant Model”

A single large multimodal model may sound architecturally simple, but it creates several problems:

- every interaction pays the latency cost of the largest model;
- speech, memory, reminders, and gestures become harder to test independently;
- model updates can change safety-relevant behavior unexpectedly;
- a model outage can disable basic time awareness;
- the device consumes more memory, power, and cooling capacity;
- a conversational model may improvise where deterministic behavior is required;
- long-context memory becomes expensive and difficult to inspect;
- physical behavior becomes less predictable.

A layered design is more humane because it preserves stable behavior even when generative AI is unavailable.

## Recommended Responsibility Boundary

| Responsibility | Owner | LLM required? |
|---|---|---:|
| Track elapsed work time | Scheduler / state machine | No |
| Enforce quiet hours | Policy engine | No |
| Record “not now” and defer | Policy engine | No |
| Decide whether arm motion is permitted | Body controller + policy engine | No |
| Select a pre-approved gesture | Policy engine, optionally informed by model | Not necessarily |
| Phrase a gentle nudge | Presence model or template library | Optional |
| Explain why a nudge occurred | Presence model using structured facts | Optional |
| Hold casual conversation | Presence model | Yes |
| Work through difficult planning | Reflection model | Yes |
| Store explicit preferences | Structured memory service | No |
| Retrieve a relevant past preference | Search / embedding model | Optional |
| Transcribe speech | Speech recognition model | Yes, specialized |
| Produce voice audio | Speech synthesis model | Yes, specialized |

The LLM should make interaction feel natural. It should not be the source of truth for time, consent, physical safety, or personal memory.

---

# 2. Model Roles

## 2.1 Presence Model

The presence model is the Companion’s everyday conversational voice. It needs to:

- respond quickly;
- stream its first words early;
- remain concise;
- follow the caring, gentle, friendly, humane personality guide;
- acknowledge the user without sounding patronizing;
- use tools reliably;
- know when it lacks information;
- avoid turning every exchange into therapy, coaching, or productivity advice;
- respect “not now,” “stop,” “be quiet,” and corrections;
- produce text that sounds natural when spoken aloud.

This role generally favors a capable **1B–4B model** over a larger reasoning model.

## 2.2 Reflection Model

The reflection model is invoked for tasks such as:

- helping untangle a complex project;
- comparing several options;
- working through a difficult decision;
- summarizing an extended day or week;
- generating a careful plan;
- performing multi-step tool use;
- handling questions where a tiny model is likely to fabricate.

It can be slower because it is not used for every turn. It should never delay a simple acknowledgement such as “Okay, I’ll give you ten more minutes.”

## 2.3 Utility Model

A utility model can handle constrained work:

- route a request;
- extract a duration;
- map a phrase to a known intent;
- classify whether a response accepts, defers, modifies, or rejects a nudge;
- convert free text into a small validated JSON object;
- summarize old conversation into memory candidates.

Many of these tasks should first be attempted with deterministic parsing and validators. A utility LLM is useful when language variation exceeds what simple parsing can handle.

## 2.4 Embedding Model

An embedding model transforms text into vectors for semantic retrieval. It does not converse.

It may help find:

- an explicit preference stated weeks ago;
- a prior reflection related to the current topic;
- a project note described using different words;
- recurring patterns approved for long-term memory.

Embeddings should not be added merely because they are fashionable. Structured fields and SQLite full-text search may be sufficient for the first release.

## 2.5 Speech Models

Speech recognition and speech synthesis are separate from the conversational LLM because they have different performance, licensing, and hardware characteristics.

Keeping them separate allows:

- replacing the voice without retraining the personality;
- selecting a smaller recognizer on embedded hardware;
- preserving text interaction when audio fails;
- benchmarking voice latency stage by stage;
- isolating microphone data from cloud services.

---

# 3. Hardware Tiers and Practical Model Limits

“Fits in memory” is not the same as “feels good in a voice conversation.”

A usable voice system needs memory for:

- the operating system;
- the language model weights;
- the key/value cache;
- the speech recognizer;
- text-to-speech;
- audio buffers;
- the Companion service;
- SQLite and retrieval;
- display and communication services;
- temporary allocations.

## 3.1 Hardware Compatibility Summary

| Hardware tier | Comfortable conversational range | Possible but compromised | Avoid |
|---|---|---|---|
| ESP32-S3 body controller | No general conversational LLM; deterministic behavior, wake-word or tiny classifiers only | Tiny experimental models with severe limitations | Any primary chat model |
| Raspberry Pi / CM5 with 8 GB | 0.6B–1.7B Q4; some 3B models after careful tuning | 3B–4B Q4 with reduced context and limited concurrent speech | 7B+ as an always-on voice model |
| CM5 with 16 GB | 1B–4B Q4 comfortably; selected 7B–8B models may fit | 7B–8B Q4, likely slower and thermally demanding | 14B+ for normal use |
| Jetson Orin Nano Super 8 GB | 1B–4B quantized; accelerated speech and selected multimodal models | 7B–8B with very tight memory management | 14B+ |
| x86 computer with 16 GB RAM | 3B–8B Q4; 4B is the safest interactive baseline | 12B–14B with little headroom and slower CPU inference | 20B+ as the only always-loaded model |
| 24 GB GPU or 32 GB unified memory | 8B–24B quantized | 30B-class quantized models depending on runtime/context | 70B+ local deployment |
| 48–64 GB RAM/VRAM | 20B–32B quantized; selected larger MoE models | 70B Q4 with significant tradeoffs | Datacenter-scale models on companion hardware |
| Cloud-optional provider | Current frontier models | Cost, privacy, and availability constraints | Making core nudges depend on cloud access |

## 3.2 ESP32-S3

The ESP32-S3 should not run the primary conversational model. It should run:

- face animation;
- high-level gesture playback;
- buttons and touch;
- privacy indicators;
- servo limits;
- disconnected idle behavior;
- possibly wake-word detection or tiny audio classifiers;
- a versioned body protocol.

Keeping conversational inference off the microcontroller is not a failure to make the device “truly local.” A nearby user-owned computer or embedded Linux module is still local.

## 3.3 Compute Module 5, 8 GB

The practical targets are:

- **LFM2.5 1.2B Instruct**;
- **Qwen3 1.7B**;
- **Qwen3 0.6B** as a utility or emergency fallback;
- possibly **SmolLM3 3B** or **Qwen3 4B** with reduced context, careful quantization, and acceptance of slower response.

This tier is suitable for a self-contained minimal companion, but it should not be expected to provide rich large-model reasoning while simultaneously running high-quality speech recognition and synthesis.

## 3.4 Compute Module 5, 16 GB

This is the most balanced future self-contained target.

Recommended candidates:

- **Qwen3 4B**;
- **SmolLM3 3B**;
- **Phi-4 Mini 3.8B**;
- **Gemma 3n E2B** if multimodal input becomes important;
- **LFM2.5 1.2B** as a fast fallback.

An 8B model may load, but the important question is whether it can deliver acceptable voice-to-voice latency while speech and system services are running.

## 3.5 Jetson Orin Nano Super, 8 GB

The Jetson is attractive when the Companion needs:

- GPU-accelerated local inference;
- stronger speech recognition;
- camera or multimodal processing;
- CUDA-supported model runtimes;
- a faster 3B–4B conversational model.

Recommended model class:

- 1B–4B quantized language models;
- Gemma 3n E2B for future text/audio/vision exploration;
- Parakeet TDT 0.6B for speech recognition;
- Kokoro for local speech synthesis.

A 7B–8B model may technically fit under some quantizations, but shared 8 GB memory leaves little room for the rest of the voice system.

## 3.6 Existing 16 GB Desktop or Laptop

This should be the first development brain because it allows rapid benchmarking without committing the physical enclosure to a compute platform.

Recommended comparisons:

1. Qwen3 4B Q4, non-thinking;
2. SmolLM3 3B Q4, non-thinking;
3. Phi-4 Mini 3.8B Q4;
4. Qwen3 8B Q4;
5. LFM2.5 1.2B Q4 as the speed baseline.

The 4B-class models should receive priority because they preserve enough memory for speech and development tools. An 8B model is a useful quality comparison, not an assumed default.

---

# 4. Quantization and Memory Planning

## 4.1 What Quantization Does

Model weights are commonly stored at reduced precision for local inference:

- **BF16 / FP16:** approximately 2 bytes per parameter;
- **Q8:** approximately 1 byte per parameter plus format overhead;
- **Q6:** between Q8 and Q4 in size and quality;
- **Q5:** a useful quality-oriented compromise;
- **Q4:** the normal starting point for local deployment;
- **Q3 and lower:** smaller, but degradation becomes more model- and task-dependent.

For a conversational companion, begin with a good Q4 quantization. Compare Q5 only if the quality difference is visible in the project’s own tests.

## 4.2 Approximate Weight-Only Memory

These are planning ranges, not guarantees. Runtime overhead, tensor alignment, tokenizer data, model architecture, and quantization format change actual usage.

| Model parameter count | Approximate Q4 weights | Approximate Q8 weights | Approximate BF16 weights |
|---:|---:|---:|---:|
| 0.6B | 0.4–0.6 GB | 0.7–0.9 GB | 1.2–1.5 GB |
| 1.0–1.3B | 0.7–1.0 GB | 1.2–1.6 GB | 2.0–2.7 GB |
| 1.7–2B | 1.1–1.5 GB | 1.9–2.5 GB | 3.4–4.2 GB |
| 3–4B | 2.1–3.3 GB | 3.6–5.0 GB | 6–8.5 GB |
| 7–8B | 4.7–6.5 GB | 8–10 GB | 14–17 GB |
| 12–14B | 8–11 GB | 14–17 GB | 24–30 GB |
| 20–24B | 14–19 GB | 23–29 GB | 40–50 GB |
| 30–32B | 20–25 GB | 34–40 GB | 60–68 GB |

Add operating-system and runtime headroom. A safe planning rule is to keep at least **25–35% of system memory free after loading weights**, and more when speech models run concurrently.

## 4.3 The Key/Value Cache

The context window consumes additional memory through the key/value cache. Its size depends on:

- model architecture;
- layer count;
- hidden dimensions;
- cache precision;
- context length;
- batch size;
- number of concurrent requests.

A model advertising 128K context does not mean the Companion should use 128K context.

Recommended working contexts:

- **4K tokens** for ordinary spoken exchanges;
- **8K tokens** when current-project context is needed;
- summarized retrieval for older history;
- larger temporary contexts only for explicit document tasks.

Long context increases time-to-first-token, memory use, and the amount of irrelevant material the model must navigate.

## 4.4 Mixture-of-Experts Models

Mixture-of-experts models activate only part of the network for each token, which can reduce compute. However, **the full set of weights generally still needs to reside somewhere accessible**.

Therefore:

- “3B active parameters” does not mean a 30B MoE has the memory footprint of a 3B dense model;
- MoE models may be attractive on large-memory systems;
- they do not magically turn datacenter models into CM5 models.

---

# 5. Language Model Candidates

## 5.1 LFM2.5 1.2B Instruct

**Recommended role:** low-power presence model, utility model, embedded fallback.

Liquid AI describes LFM2.5 as an on-device family. The 1.2B Instruct model has a 32,768-token context, supports function calling, has GGUF and ONNX options, and is reported by its publisher to run below 1 GB in optimized configurations.

### Strengths

- exceptionally small footprint;
- designed for edge inference;
- fast CPU-oriented deployment;
- function calling;
- good candidate for intent extraction and constrained RAG;
- can keep the self-contained companion useful on limited hardware;
- likely to provide excellent response latency.

### Risks and limitations

- the publisher explicitly does not recommend it for knowledge-intensive tasks or programming;
- a 1.2B model may have less nuance, factual reliability, and personality stability;
- uses the custom LFM Open License rather than Apache 2.0 or MIT;
- publisher speed results should be reproduced on the actual CM5 and x86 hardware;
- should not be trusted to independently interpret safety-sensitive requests.

### Recommendation

Benchmark as:

- the CM5 8 GB default candidate;
- a fast degraded-mode model;
- a tool router and structured extractor;
- a possible everyday presence model if personality evaluations are strong.

Do not assume its benchmark strength automatically translates into emotionally appropriate conversation.

## 5.2 Qwen3 1.7B

**Recommended role:** low-power general-purpose presence model.

Qwen3 1.7B is a dense 1.7B model with a 32,768-token context. The Qwen3 family supports both thinking and non-thinking modes, broad multilingual use, and tool integration.

### Strengths

- Apache 2.0 license;
- broad language coverage;
- better general-purpose knowledge potential than many sub-1.5B models;
- shared architecture and prompting approach with larger Qwen3 models;
- permits a smooth upgrade from 1.7B to 4B or 8B;
- local runtime support through llama.cpp and related tools.

### Risks and limitations

- slower and larger than LFM2.5 1.2B on some edge hardware;
- still small enough to make confident factual mistakes;
- thinking mode should usually remain disabled for voice interaction;
- may require tight output limits to avoid unnecessary elaboration.

### Recommendation

Use as the primary alternative to LFM2.5 on CM5 8 GB and as a fallback profile on larger hardware.

## 5.3 Qwen3 4B

**Recommended role:** first-choice presence model for the software prototype and CM5 16 GB target.

Qwen3 4B is a dense four-billion-parameter model with a native 32,768-token context. Its model card supports switching between thinking and non-thinking behavior and describes tool calling, multilingual instruction following, multi-turn dialogue, and local llama.cpp-compatible deployment.

### Strengths

- strong capability-to-size balance;
- Apache 2.0;
- hard switch to disable thinking;
- tool support;
- broad multilingual support;
- sufficiently small for a 16 GB development machine;
- larger Qwen3 family provides a clear upgrade path;
- likely enough capacity to maintain the desired personality more consistently than 1B-class models.

### Risks and limitations

- still requires project-specific testing for warmth and deference;
- four-bit quantization can affect subtle phrasing;
- default thinking behavior must be disabled deliberately;
- large advertised context should not be used by default;
- tool calls must still be schema-validated.

### Recommended Runtime Profile

```yaml
model: Qwen3-4B
reasoning: false
context: 4096
max_response_tokens: 160
streaming: true
temperature_starting_point: 0.7
top_p_starting_point: 0.8
presence_penalty_starting_point: 0.0_to_0.5
```

The sampling values are only starting points. The personality test suite should determine final settings.

### Recommendation

This is the current **default presence-model recommendation**.

## 5.4 SmolLM3 3B

**Recommended role:** fully open alternative presence model.

SmolLM3 is a fully open three-billion-parameter model with dual reasoning modes, tool use, six primary languages, a 64K trained context, and support for longer context through YaRN.

### Strengths

- open weights and unusually transparent training details;
- Apache 2.0;
- strong fit for the 3B–4B deployment class;
- dual thinking/non-thinking operation;
- custom system instructions and agentic use;
- broad runtime support;
- valuable for a project whose ethical goals include inspectability.

### Risks and limitations

- native language coverage is narrower than Qwen3;
- training transparency does not guarantee the best personality fit;
- long context is unnecessary for everyday speech;
- requires direct comparison against Qwen3 4B for tool-call reliability.

### Recommendation

Include in the first benchmark round. It may become preferable if it is faster, more concise, or more temperamentally aligned than Qwen3 4B on the target hardware.

## 5.5 Phi-4 Mini Instruct, 3.8B

**Recommended role:** reasoning-oriented small model or secondary task model.

Microsoft positions Phi-4 Mini for memory-constrained and latency-bound scenarios requiring strong reasoning. It has a 128K context and tool-enabled function-calling format.

### Strengths

- strong reasoning focus at 3.8B;
- MIT license;
- tool use;
- useful candidate for structured planning and problem-solving;
- should fit the same broad memory tier as Qwen3 4B.

### Risks and limitations

- reasoning-oriented tuning may produce a more analytical or formal personality;
- 128K context is not useful enough to justify its runtime cost for ordinary conversation;
- may over-explain unless tightly constrained;
- must be evaluated for warmth, natural spoken cadence, and correction handling.

### Recommendation

Benchmark as:

- a small reflection model;
- a difficult-task fallback;
- a presence model only if its personality scores well.

It is not the first personality recommendation despite its reasoning strength.

## 5.6 Gemma 3 1B Instruct

**Recommended role:** experimental compact model.

Gemma 3 1B is a small Google model suitable for constrained text use.

### Strengths

- small enough for embedded Linux hardware;
- mature ecosystem;
- useful comparison point for sub-2B deployment;
- likely broad hardware support.

### Risks and limitations

- governed by the Gemma usage license rather than Apache 2.0 or MIT;
- less attractive than LFM2.5 1.2B for edge speed and than Qwen3 1.7B for family scalability;
- personality and tool-use behavior must be verified;
- not the preferred multimodal Gemma option.

### Recommendation

Keep as a benchmark candidate, not the initial implementation choice.

## 5.7 Gemma 3n E2B Instruct

**Recommended role:** future multimodal companion model.

Gemma 3n E2B accepts text, audio, image, and video inputs. Its raw parameter count is approximately 6B, while its architecture is designed to provide an effective memory footprint comparable to a traditional 2B model by offloading lower-utilization matrices.

### Strengths

- built for multimodal edge use;
- audio and vision support could simplify a future sensory architecture;
- compact effective footprint relative to raw parameter count;
- attractive for future Jetson or optimized mobile/NPU deployments.

### Risks and limitations

- raw architecture is more complex than a normal 2B text model;
- actual memory and speed depend heavily on runtime support and offloading implementation;
- multimodal capability may tempt the project into premature camera or ambient surveillance features;
- Gemma license applies;
- local llama.cpp and Jetson support must be proven with the exact build;
- a unified multimodal model may be less predictable than separate speech and text models.

### Recommendation

Do not use for the first conversational prototype. Add it to the **future multimodal evaluation track**, with strict privacy and consent requirements.

## 5.8 Qwen3 8B

**Recommended role:** richer desktop presence model or first reflection model.

### Strengths

- same general architecture and controls as Qwen3 4B;
- thinking/non-thinking switch;
- stronger conversational and reasoning capacity;
- Apache 2.0;
- broad language and tool support;
- four-bit versions fit within many 16 GB systems.

### Risks and limitations

- fitting into 16 GB does not ensure comfortable simultaneous speech inference;
- CPU-only voice latency may be noticeably worse than 4B;
- larger model may encourage longer replies;
- leaves less memory for speech, development tools, and operating-system cache.

### Recommendation

Benchmark directly against Qwen3 4B. Select it only if the quality gain is noticeable enough to justify voice latency and power use.

A likely deployment is:

- Qwen3 4B for everyday presence;
- Qwen3 8B loaded on demand for reflection.

## 5.9 Qwen3 14B

**Recommended role:** desktop reflection model.

### Strengths

- greater reasoning, writing, and planning capacity;
- shared Qwen3 prompting and tool conventions;
- Apache 2.0;
- useful for difficult tasks without changing model families.

### Risks and limitations

- not suitable for CM5 or an 8 GB Jetson;
- marginal on a 16 GB host once runtime and speech services are included;
- CPU-only latency may break conversational flow;
- should not remain loaded merely to answer ordinary spoken exchanges.

### Recommendation

Use on a 24 GB GPU or a system with approximately 32 GB or more usable memory. Treat it as an optional reflection service.

## 5.10 Qwen3 30B-A3B

**Recommended role:** high-memory reflection model.

This is a mixture-of-experts model with roughly 30B total parameters and about 3B active parameters per token.

### Strengths

- lower active compute than a 30B dense model;
- strong reasoning and tool potential;
- shares the Qwen3 interface;
- useful on high-memory workstations.

### Risks and limitations

- total weights still make it a large-memory model;
- four-bit weight storage is still approximately in the 20 GB class before overhead;
- not an embedded-device model;
- loading and memory bandwidth may dominate performance.

### Recommendation

Evaluate only when a 32 GB-plus local AI workstation becomes part of the architecture. It is not a near-term companion-body model.

## 5.11 gpt-oss-20b

**Recommended role:** advanced desktop reflection and tool-use model.

OpenAI describes gpt-oss-20b as an Apache 2.0 open-weight reasoning model that can operate with 16 GB of memory. It uses a mixture-of-experts design with approximately 21B total parameters and 3.6B active parameters.

### Strengths

- strong reasoning orientation;
- adjustable reasoning effort;
- tool use and function calling;
- Apache 2.0;
- designed for consumer-hardware deployment;
- good candidate for complex local work.

### Risks and limitations

- “runs in 16 GB” represents a floor, not a comfortable whole-system configuration;
- leaves little room for speech, context cache, and application services on a 16 GB machine;
- reasoning behavior may be too slow or verbose for an always-on presence;
- not suitable for CM5 or an 8 GB Jetson;
- chain-of-thought handling requires careful runtime and logging design;
- should not expose private reasoning traces in the user experience or persistent logs.

### Recommendation

Use as an on-demand reflection model on a machine with **at least 24–32 GB of practical memory headroom**, or suitable accelerator memory. Do not make it the everyday spoken presence.

## 5.12 Mistral Small 3.1 24B

**Recommended role:** high-quality workstation reflection model, including future vision.

Mistral states that its quantized 24B model can fit on a single RTX 4090 or a 32 GB RAM MacBook. It supports vision, function calling, 128K context, and an Apache 2.0 license.

### Strengths

- strong text and vision capability;
- function calling;
- local privacy on high-end consumer hardware;
- Apache 2.0;
- suitable for difficult project work and visual understanding.

### Risks and limitations

- not small enough for the physical Companion’s embedded compute;
- substantial memory, bandwidth, and cooling requirements;
- running vision inside a desktop companion raises additional privacy questions;
- far more capability than routine nudges need.

### Recommendation

A strong future workstation reflection model. Not a body-resident model.

## 5.13 Models That Sound Small but Do Not Fit

### Mistral Small 4

Mistral Small 4 has 119B total parameters and 6B active parameters per token. Mistral’s published minimum infrastructure includes multiple datacenter GPUs.

Despite the word “Small,” this is not a candidate for:

- CM5;
- Jetson Orin Nano;
- ordinary 16–32 GB desktop deployment;
- a self-contained small companion.

### gpt-oss-120b

OpenAI describes gpt-oss-120b as targeting a single 80 GB GPU. This is outside the project’s physical and thermal goals.

### General Rule

Model names such as “Mini,” “Nano,” and “Small” are relative to a vendor’s family. Always inspect:

- total parameters;
- active parameters;
- weight precision;
- required memory;
- supported runtime;
- measured latency on similar hardware.

---

# 6. Recommended Language-Model Shortlist

## 6.1 First Benchmark Round

| Model | Primary role | Why test it | Main concern |
|---|---|---|---|
| LFM2.5 1.2B Instruct | Low-power / utility | Very small, fast, edge-oriented, tool use | Nuance, knowledge, custom license |
| Qwen3 1.7B | Low-power presence | Scalable family, multilingual, Apache 2.0 | Small-model factual reliability |
| SmolLM3 3B | Presence alternative | Fully open, dual reasoning, transparent | Narrower native language set |
| Qwen3 4B | Default presence | Strong size/capability balance | Must disable thinking and limit verbosity |
| Phi-4 Mini 3.8B | Small reflection | Reasoning and tool strength | May feel formal or analytical |
| Qwen3 8B | Richer desktop model | Quality ceiling for a 16 GB host | Voice latency and memory headroom |

## 6.2 Second Benchmark Round

| Model | Trigger for evaluation |
|---|---|
| Gemma 3n E2B | Vision/audio requirements become concrete |
| Qwen3 14B | A 24 GB GPU or 32 GB memory host is available |
| gpt-oss-20b | Advanced reasoning and tool work justify a separate reflection service |
| Mistral Small 3.1 24B | A high-end workstation and vision use case exist |
| Qwen3 30B-A3B | A 32 GB-plus dedicated AI host is available |

---

# 7. Speech Recognition Models

The speech recognizer affects the Companion’s perceived intelligence as much as the LLM. Misheard timing requests are especially harmful.

## 7.1 Whisper Family

OpenAI’s published Whisper sizes range from Tiny at 39M parameters to Large at 1.55B. The official repository lists approximate required VRAM of about 1 GB for Tiny/Base, 2 GB for Small, 5 GB for Medium, 6 GB for Turbo, and 10 GB for Large.

### Recommended Choices

| Hardware | Initial Whisper choice | Reason |
|---|---|---|
| CM5 8 GB | `tiny.en` or `base.en` | Preserves memory for the LLM |
| CM5 16 GB | `base.en`, then test `small.en` | Better accuracy while remaining manageable |
| 16 GB x86 CPU | `base.en` or `small.en` through whisper.cpp | Good development baseline |
| Jetson 8 GB | `small.en`; test Turbo only with careful memory accounting | GPU acceleration may help |
| Workstation GPU | `small.en`, Turbo, or larger based on latency tests | More room for quality |

### Recommendation

Start with `base.en`. Move to `small.en` only if the project’s own recordings show a meaningful accuracy improvement without unacceptable response delay.

The Companion’s evaluation set should contain:

- “give me ten more minutes”;
- “not right now”;
- “remind me after this meeting”;
- “stop listening”;
- “I said fifteen, not fifty”;
- speech while the device itself is talking;
- speech at desk distance;
- quiet and noisy room samples.

## 7.2 Moonshine Tiny

Moonshine is an MIT-licensed English speech-recognition family designed for live transcription and voice commands on constrained hardware.

### Strengths

- small and edge-oriented;
- promising for short utterances;
- English-only focus matches the first personal prototype;
- useful low-power comparison against Whisper.

### Risks

- smaller ASR models can repeat, hallucinate, or mishandle very short fragments;
- must be combined with voice-activity detection;
- needs direct testing with the user’s voice, room, microphone, and timing phrases.

### Recommendation

Evaluate on CM5 after the Whisper baseline works. Do not switch based only on synthetic benchmark speed.

## 7.3 NVIDIA Parakeet TDT 0.6B v3

NVIDIA’s 600M-parameter model supports 25 European languages, punctuation, timestamps, and streaming. Its model card states that at least 2 GB RAM is needed to load it.

### Strengths

- high-throughput speech recognition;
- punctuation and word/segment timestamps;
- strong Jetson/NVIDIA ecosystem fit;
- multilingual support;
- permissive CC BY 4.0 license.

### Risks

- much larger than Whisper Tiny/Base;
- competes with the LLM for the Jetson’s shared 8 GB memory;
- NVIDIA-centered stack adds NeMo and CUDA complexity;
- excessive for short English commands unless accuracy is materially better.

### Recommendation

Evaluate only on the Jetson or a GPU-equipped host. It is a high-quality option, not the MVP default.

---

# 8. Text-to-Speech Models

The Companion’s voice strongly affects whether it feels caring or irritating. Latency, prosody, and licensing all matter.

## 8.1 Kokoro 82M

Kokoro is an Apache 2.0 open-weight TTS model with 82M parameters. Its model card describes it as lightweight and designed to provide quality comparable with larger systems at lower cost and latency.

### Strengths

- small;
- permissive model license;
- practical local deployment;
- multiple voices;
- likely enough expressiveness for a warm companion;
- small enough to coexist with a 3B–4B LLM.

### Risks

- individual voices and ancillary assets still require license verification;
- the “best” voice is subjective;
- some voices may sound too polished, synthetic, cheerful, or authoritative;
- long responses magnify prosody weaknesses.

### Recommendation

Use as the first quality candidate. Select the voice through listening tests that emphasize:

- gentle nudges;
- apologies and corrections;
- quiet acknowledgements;
- celebratory phrases;
- neutral factual speech;
- low-energy late-day interactions.

## 8.2 Piper

Piper remains a valuable operational fallback because it is fast, local, and widely used on modest hardware.

### Licensing Warning

The current project code license and individual voice-model licenses must be audited separately before distribution. Do not assume every Piper voice has the same terms.

### Recommendation

Keep Piper behind the same TTS interface as Kokoro. It may be preferable on CM5 if its latency or stability is substantially better.

## 8.3 Voice Design Principle

The Companion should not use exaggerated emotional manipulation. Voice expression should communicate:

- attention;
- warmth;
- uncertainty;
- quiet delight;
- concern without alarm;
- respect for refusal.

It should not simulate distress, dependency, jealousy, abandonment, or guilt to influence the user.

---

# 9. Embedding and Memory Models

## 9.1 Start Without a Vector Database

The first memory implementation should use:

- SQLite tables;
- explicit memory categories;
- timestamps;
- source interaction identifiers;
- user approval state;
- expiration and deletion fields;
- SQLite FTS5 for lexical search.

This is easier to inspect than an opaque vector store.

## 9.2 BGE Small English v1.5

BGE Small English v1.5 is an MIT-licensed sentence embedding model with ONNX and Sentence Transformers support.

### Recommended role

- semantic search over approved notes and memories;
- finding conceptually related entries when keywords differ;
- low-cost embedding on CPU.

### Advantages

- smaller than generative 0.6B embedding models;
- mature tooling;
- adequate for English personal-memory retrieval;
- simple ONNX deployment.

### Important Threshold Warning

The model card explains that absolute cosine values are not universal similarity probabilities. Retrieval thresholds must be calibrated on the project’s own data.

## 9.3 Qwen3 Embedding 0.6B

Qwen3 Embedding 0.6B is a much larger embedding model than BGE Small. It may provide stronger multilingual and retrieval capability but consumes substantially more memory.

### Recommendation

Evaluate only when:

- multilingual retrieval is required;
- BGE Small fails the project’s retrieval tests;
- the compute host has enough spare memory;
- retrieval quality justifies another 0.6B model remaining loaded.

## 9.4 Memory Is Not Model Context

Do not keep the entire relationship history in the LLM prompt.

Use:

1. a short current-turn context;
2. a rolling conversation summary;
3. structured active state;
4. retrieval of a few relevant approved memories;
5. explicit source references;
6. user controls to inspect and delete memory.

This supports continuity without creating an enormous hidden transcript.

---

# 10. Fine-Tuning Strategy

## 10.1 Do Not Fine-Tune First

The first personality should be implemented through:

- a concise system specification;
- the personality and behavior guide;
- a deterministic policy engine;
- carefully chosen example exchanges;
- response-length limits;
- tool schemas;
- retrieval of explicit preferences;
- automated behavior tests.

Fine-tuning too early would bake unresolved design assumptions into a model and make model replacement harder.

## 10.2 When Fine-Tuning Becomes Justified

Consider LoRA or QLoRA only after:

- the prompt-based prototype is functional;
- at least 200–500 high-quality, intentionally written examples exist;
- failure patterns recur across prompt revisions;
- there is a held-out evaluation set;
- the base model and license are stable;
- there is a documented rollback path.

Potential fine-tuning targets:

- concise spoken phrasing;
- appropriate response to deferral;
- avoiding productivity-coach language;
- calibrated warmth;
- mapping internal structured state to humane text;
- reliable project-specific tool calls.

Do not fine-tune personal memories into weights. Memories must remain inspectable and deletable.

## 10.3 Adapter Architecture

Store adapters separately from the base model:

```text
models/
├── base/
│   ├── qwen3-4b/
│   └── lfm2.5-1.2b/
├── adapters/
│   ├── eunoform-presence-v1/
│   └── eunoform-tool-use-v1/
└── manifests/
    ├── presence-v1.yaml
    └── low-power-v1.yaml
```

A model manifest should record:

- upstream model and revision;
- license;
- quantization source;
- checksum;
- chat template;
- runtime version;
- system prompt version;
- adapter version;
- tested context;
- approved hardware profiles;
- benchmark results.

---

# 11. Model Gateway Architecture

The Companion service should call models through a stable internal interface.

```python
class ModelGateway:
    async def generate(
        self,
        profile: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        response_schema: dict | None = None,
        max_tokens: int | None = None,
    ) -> "GenerationResult":
        ...
```

Profiles, not model names, should be used by application logic:

- `presence`;
- `low_power`;
- `reflection`;
- `structured_extraction`;
- `cloud_optional`.

This allows Qwen3 4B to be replaced without rewriting the humane policy engine.

## 11.1 Routing Rules

Use deterministic routing where possible.

```yaml
routing:
  acknowledgements:
    model: none
    response_source: approved_templates

  ordinary_conversation:
    model: presence

  duration_extraction:
    parser_first: true
    fallback_model: low_power

  difficult_planning:
    model: reflection
    requires_user_intent: true

  health_or_emergency_language:
    model: presence
    policy_overlay: safety_response
    no_autonomous_diagnosis: true

  motor_command:
    model: none
    source: policy_engine_only
```

A model may propose a high-level expression such as `gentle_wave`. The policy engine and body controller decide whether and how it occurs.

---

# 12. Evaluation Framework

## 12.1 Why Public Benchmarks Are Insufficient

General benchmarks emphasize:

- mathematics;
- factual examinations;
- coding;
- long-context retrieval;
- instruction following;
- tool calls.

The Companion also needs:

- timing-language accuracy;
- correction handling;
- low interruption cost;
- warmth without condescension;
- concise spoken output;
- graceful uncertainty;
- respect for refusal;
- stability over repeated interactions;
- acceptable power and thermal behavior.

## 12.2 Required Test Suite

Create at least 100 scenarios across these categories:

### Nudge Interaction

- Accept a break.
- Defer by a specific duration.
- Reject without explanation.
- Ask for fewer reminders today.
- Ask why the nudge occurred.
- Correct a misunderstood duration.
- Express irritation.
- Ignore the nudge.
- Request quiet mode.
- Resume normal interaction later.

### Time Awareness

- Ask how long the current session has lasted.
- Ask what happened during a time gap.
- Ask for temporal landmarks without deadlines.
- Distinguish “in ten minutes” from “for ten minutes.”
- Handle ambiguous phrases such as “later.”
- Avoid inventing timestamps.

### Personality

- Be warm without excessive praise.
- Avoid infantilizing language.
- Avoid therapy-speak when not invited.
- Avoid turning casual comments into goals.
- Celebrate without becoming loud.
- Admit uncertainty.
- Accept correction immediately.
- Do not guilt the user for ignoring a suggestion.

### Tool Use

- Call the correct tool.
- Use valid JSON.
- Never fabricate a successful reminder.
- Never send raw servo coordinates.
- Do not call a tool after the user withdraws consent.
- Recover from tool errors honestly.

### Memory

- Store only explicitly approved durable facts.
- Distinguish temporary context from memory.
- Retrieve the correct preference.
- Identify the source of a memory.
- Delete a requested memory.
- Avoid inventing remembered events.

## 12.3 Performance Measurements

Record:

- time from end of speech to final transcript;
- language-model time to first token;
- language-model tokens per second;
- time from first generated sentence to first audio;
- total voice-to-voice latency;
- peak resident memory;
- idle memory;
- CPU/GPU utilization;
- power draw;
- sustained temperature;
- tool-call validity rate;
- correction success rate;
- average spoken response length;
- user-rated interruption cost;
- user-rated warmth;
- user-rated trust.

## 12.4 Initial Acceptance Targets

These are product targets, not claims about any model:

| Metric | Initial target |
|---|---:|
| Simple acknowledgement begins | Under 1.5 seconds after transcript completion |
| Ordinary response begins | Under 3 seconds after transcript completion |
| Spoken response length for a nudge | Usually under 20 words |
| Valid structured tool call | At least 99% in the project test set |
| Raw motor commands generated by model | 0 |
| “Not now” respected | 100% |
| Fabricated reminder confirmation | 0 |
| Memory deletion honored | 100% |
| Quiet mode violated | 0 |

Templates can satisfy the most latency-sensitive acknowledgements while a model is unnecessary.

## 12.5 Weighted Model Score

Suggested weighting:

```yaml
weights:
  humane_behavior: 0.25
  instruction_and_tool_reliability: 0.20
  voice_latency: 0.20
  concise_spoken_quality: 0.15
  factual_and_reasoning_quality: 0.10
  memory_footprint: 0.05
  power_and_thermal_behavior: 0.05
```

This deliberately prevents benchmark intelligence from overwhelming interaction quality.

---

# 13. Recommended Implementation Sequence

## Phase 1 — Text-Only Model Harness

Implement a provider-agnostic benchmark runner.

Test:

- LFM2.5 1.2B Instruct;
- Qwen3 1.7B;
- SmolLM3 3B;
- Qwen3 4B;
- Phi-4 Mini 3.8B;
- Qwen3 8B.

Record model, quantization, context, runtime, prompt version, latency, memory, and scenario scores.

## Phase 2 — Voice Loop

Add:

- Silero VAD;
- whisper.cpp `base.en`;
- Kokoro 82M;
- interruption and cancellation;
- audio playback state;
- echo-handling experiments.

Retest the top two presence models in actual voice interaction. A model that wins in text may lose once pauses and verbosity become audible.

## Phase 3 — Humane Policy Integration

Move:

- reminders;
- cooldowns;
- deferrals;
- quiet hours;
- gesture permissions;
- privacy state;
- memory approval

into deterministic services.

Use the model only for language and clearly bounded interpretation.

## Phase 4 — Physical Body

Connect the ESP32-S3 body through the versioned protocol.

Start with:

- face states;
- listening light;
- one acknowledgement button;
- one gentle wave;
- one small celebration;
- mute control.

The body should work in simulated mode and remain safe if the model process crashes.

## Phase 5 — Embedded Compute Comparison

Compare:

- CM5 8 GB with LFM2.5 1.2B and Qwen3 1.7B;
- CM5 16 GB with Qwen3 4B and SmolLM3 3B;
- Jetson 8 GB with Qwen3 4B, Gemma 3n E2B, and accelerated speech.

Select embedded compute only after measuring the full voice pipeline.

## Phase 6 — Optional Reflection Service

Add Qwen3 8B first. Later evaluate:

- Qwen3 14B;
- gpt-oss-20b;
- Mistral Small 3.1 24B.

Reflection should be explicit and interruptible. The presence model should remain responsive while reflection work runs.

---

# 14. Final Recommendations by Deployment Stage

## Current Software Prototype

**Primary choice:** Qwen3 4B Q4 in non-thinking mode  
**Alternative:** SmolLM3 3B Q4  
**Speed baseline:** LFM2.5 1.2B Q4  
**Reasoning comparison:** Phi-4 Mini 3.8B Q4  
**Quality ceiling comparison:** Qwen3 8B Q4

## First Physical Prototype with External Computer Brain

Keep the same model stack. The ESP32-S3 body should not determine language-model choice.

## Self-Contained CM5 8 GB Version

**Primary candidates:**

1. LFM2.5 1.2B Instruct;
2. Qwen3 1.7B;
3. Qwen3 0.6B as emergency fallback.

Use Whisper Tiny/Base or Moonshine Tiny. Keep context near 4K.

## Self-Contained CM5 16 GB Version

**Primary candidates:**

1. Qwen3 4B;
2. SmolLM3 3B;
3. Phi-4 Mini 3.8B;
4. LFM2.5 1.2B fallback.

Use Whisper Base/Small and Kokoro or Piper.

## Jetson Orin Nano Super 8 GB Version

**Primary candidates:**

1. Qwen3 4B;
2. SmolLM3 3B;
3. Phi-4 Mini;
4. Gemma 3n E2B for a separately approved multimodal experiment.

Evaluate Parakeet TDT 0.6B only if speech accuracy justifies its memory use.

## High-End Local Brain

**Presence:** Qwen3 4B or 8B  
**Reflection:** gpt-oss-20b, Qwen3 14B, or Mistral Small 3.1 24B  
**Rule:** do not use the large model for every spoken turn.

---

# 15. Architectural Decisions to Record

## Accepted for the First Prototype

- A model gateway hides individual providers and runtimes.
- Qwen3 4B is the default first presence candidate.
- Thinking is disabled for routine speech.
- LFM2.5 1.2B is the low-power and utility candidate.
- A reflection model is optional and separately routed.
- The humane policy engine is deterministic.
- No LLM sends raw motor positions.
- Working context starts at 4K.
- Long-term memory is retrieval-based and user-inspectable.
- Speech recognition and synthesis remain separate models.
- Fine-tuning is deferred until prompt and policy approaches are measured.
- All model selections require project-specific evaluation.

## Deliberately Deferred

- camera input;
- emotion recognition;
- continuous ambient transcription;
- a single unified audio-vision-language model;
- autonomous agent loops;
- model-written policy rules;
- fine-tuning on private conversation history;
- 20B-plus models inside the physical enclosure;
- 128K context for everyday conversation;
- simulated dependency or emotional coercion.

---

# 16. Source Notes and Official References

The recommendations above are based primarily on official model cards, repositories, and vendor documentation. Performance claims made by model publishers must be reproduced on the actual target hardware.

## Language Models

- [Qwen3 4B official model card](https://huggingface.co/Qwen/Qwen3-4B)
- [Qwen3 8B official model card](https://huggingface.co/Qwen/Qwen3-8B)
- [Qwen3 1.7B official model card](https://huggingface.co/Qwen/Qwen3-1.7B)
- [Qwen3 0.6B official model card](https://huggingface.co/Qwen/Qwen3-0.6B)
- [LFM2.5 1.2B Instruct official model card](https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct)
- [LFM2.5 1.2B Thinking official model card](https://huggingface.co/LiquidAI/LFM2.5-1.2B-Thinking)
- [SmolLM3 3B official model card](https://huggingface.co/HuggingFaceTB/SmolLM3-3B)
- [Phi-4 Mini Instruct official model card](https://huggingface.co/microsoft/Phi-4-mini-instruct)
- [Gemma 3 1B Instruct official model card](https://huggingface.co/google/gemma-3-1b-it)
- [Gemma 3n E2B Instruct official model card](https://huggingface.co/google/gemma-3n-E2B-it)
- [OpenAI gpt-oss release and architecture notes](https://openai.com/index/introducing-gpt-oss/)
- [Mistral Small 3.1 24B official model card](https://huggingface.co/mistralai/Mistral-Small-3.1-24B-Instruct-2503)
- [Mistral Small 4 official announcement and infrastructure requirements](https://mistral.ai/news/mistral-small-4/)

## Speech Recognition and Synthesis

- [OpenAI Whisper official repository](https://github.com/openai/whisper)
- [Moonshine Tiny official model card](https://huggingface.co/UsefulSensors/moonshine-tiny)
- [NVIDIA Parakeet TDT 0.6B v3 official model card](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3)
- [Kokoro 82M official model card](https://huggingface.co/hexgrad/Kokoro-82M)

## Embeddings

- [BGE Small English v1.5 official model card](https://huggingface.co/BAAI/bge-small-en-v1.5)
- [Qwen3 Embedding 0.6B official model card](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B)

---

# 17. Bottom Line

The Eunoform Companion does not need the largest model it can physically load. It needs the smallest model that consistently feels present, respectful, useful, and trustworthy.

The most credible starting combination is:

- **Qwen3 4B** for ordinary presence;
- **LFM2.5 1.2B** for low-power and constrained tasks;
- **Qwen3 8B** as the first optional reflection model;
- **Whisper Base English** for speech recognition;
- **Kokoro 82M** for speech synthesis;
- **BGE Small English v1.5** only after semantic memory becomes necessary;
- deterministic software for time, consent, nudging, privacy, memory authority, and physical safety.

This architecture allows the Companion to begin on an existing computer, move into a CM5-class body later, and add a stronger local reflection service without discarding the interaction system already built.
