import { interactionStates, type CompanionEvent, type CompanionStatus, type Explanation, type InteractionState, type Transport } from "./types.ts";

const isInteractionState = (value: unknown): value is InteractionState =>
  typeof value === "string" && interactionStates.includes(value as InteractionState);

export function validateStatus(value: unknown): CompanionStatus {
  if (typeof value !== "object" || value === null) throw new Error("API returned an invalid status payload.");
  const candidate = value as Partial<CompanionStatus>;
  if (!isInteractionState(candidate.interaction_state)) throw new Error("API returned an unknown interaction state.");
  if (typeof candidate.elapsed_minutes !== "number" || typeof candidate.settings !== "object" || candidate.settings === null) {
    throw new Error("API returned an incomplete status payload.");
  }
  return candidate as CompanionStatus;
}

export class ApiTransport implements Transport {
  constructor(private readonly baseUrl = "/api") {}

  async getStatus(signal?: AbortSignal): Promise<CompanionStatus> {
    return validateStatus(await this.request("/status", { signal }));
  }

  async act(path: string, body?: object, signal?: AbortSignal): Promise<CompanionStatus> {
    return validateStatus(await this.request(path, {
      method: "POST",
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal,
    }));
  }

  async evaluate(signal?: AbortSignal): Promise<void> {
    await this.request("/interactions/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ explicit_reminder_due: true }),
      signal,
    });
  }

  async getExplanation(signal?: AbortSignal): Promise<Explanation> {
    const value = await this.request("/interactions/current/explanation", { signal });
    if (typeof value !== "object" || value === null || typeof (value as Partial<Explanation>).message !== "string") {
      throw new Error("API returned an invalid explanation payload.");
    }
    return value as Explanation;
  }

  async getEvents(signal?: AbortSignal): Promise<CompanionEvent[]> {
    const value = await this.request("/events?limit=12", { signal });
    if (!Array.isArray(value)) throw new Error("API returned an invalid event history payload.");
    return value as CompanionEvent[];
  }

  private async request(path: string, init: RequestInit): Promise<unknown> {
    const response = await fetch(`${this.baseUrl}${path}`, init);
    const payload = await response.json().catch(() => null) as { detail?: string } | null;
    if (!response.ok) throw new Error(payload?.detail ?? `Request failed with status ${response.status}.`);
    return payload;
  }
}

const emptyStatus = (state: InteractionState): CompanionStatus => ({
  interaction_state: state,
  elapsed_minutes: state === "idle" ? 0 : 42,
  focus_session: state === "idle" ? null : { id: "mock-session", started_at: new Date().toISOString() },
  active_deferral: state === "deferred" ? { expires_at: new Date(Date.now() + 600_000).toISOString() } : null,
  active_quiet_interval: state === "quiet" ? { ends_at: new Date(Date.now() + 600_000).toISOString() } : null,
  current_nudge: ["attracting_attention", "awaiting_response", "explaining"].includes(state) ? { id: "mock-nudge" } : null,
  next_evaluation_at: state === "focusing" ? new Date(Date.now() + 600_000).toISOString() : null,
  settings: { interaction_intensity: "medium", visual_lead_in_seconds: 1, quiet_default_minutes: 30 },
});

export class MockTransport implements Transport {
  private status = emptyStatus("idle");

  async getStatus(): Promise<CompanionStatus> { return structuredClone(this.status); }
  setState(state: InteractionState): void { this.status = emptyStatus(state); }

  async evaluate(): Promise<void> { this.setState("attracting_attention"); }
  async getExplanation(): Promise<Explanation> {
    return { message: "You have been focusing for 42 minutes, so the configured check-in threshold was reached.", facts: { elapsed_minutes: 42 } };
  }
  async getEvents(): Promise<CompanionEvent[]> {
    return [{ id: "mock-event", event_type: "nudge_created", occurred_at: new Date().toISOString() }];
  }

  async act(path: string): Promise<CompanionStatus> {
    const next: Record<string, InteractionState> = {
      "/focus-sessions": "focusing",
      "/focus-sessions/current/stop": "idle",
      "/focus-sessions/current/resume": "focusing",
      "/interactions/current/attention-complete": "awaiting_response",
      "/interactions/current/accept": "on_break",
      "/interactions/current/defer": "deferred",
      "/interactions/current/dismiss": "focusing",
      "/interactions/current/quiet": "quiet",
      "/interactions/current/quiet/end": "focusing",
      "/interactions/current/reduce-frequency": "focusing",
    };
    this.setState(next[path] ?? this.status.interaction_state);
    return this.getStatus();
  }
}
