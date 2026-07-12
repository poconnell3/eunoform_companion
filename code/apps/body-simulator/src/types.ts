export const interactionStates = [
  "idle",
  "focusing",
  "policy_evaluation",
  "attracting_attention",
  "awaiting_response",
  "explaining",
  "deferred",
  "on_break",
  "quiet",
] as const;

export type InteractionState = (typeof interactionStates)[number];
export type ExpressionName = "resting" | "focused" | "gentle_attention" | "curious" | "warm";
export type GestureName = "still" | "breathe" | "lean_in" | "wave_small" | "settle";
export type SensoryLevel = "low" | "standard";

export interface Settings {
  interaction_intensity?: "low" | "medium" | "high";
  visual_lead_in_seconds?: number;
  quiet_default_minutes?: number;
  muted?: boolean;
  wellness_nudges_enabled?: boolean;
  [key: string]: unknown;
}

export interface CompanionStatus {
  interaction_state: InteractionState;
  elapsed_minutes: number;
  focus_session: Record<string, unknown> | null;
  active_deferral: Record<string, unknown> | null;
  active_quiet_interval: Record<string, unknown> | null;
  current_nudge: Record<string, unknown> | null;
  settings: Settings;
}

export interface Explanation {
  message: string;
  facts: Record<string, unknown>;
}

export interface CompanionEvent {
  id?: string;
  event_type?: string;
  occurred_at?: string;
  created_at?: string;
  policy_reason?: string;
  outcome?: string;
  [key: string]: unknown;
}

export interface SimulatorPreferences {
  reducedMotion: boolean;
  sensoryLevel: SensoryLevel;
  highContrast: boolean;
  pollIntervalMs: number;
}

export interface VisualBehavior {
  expression: ExpressionName;
  gesture: GestureName;
  label: string;
  announcement: string;
  durationMs: number;
  attentionComplete?: boolean;
}

export interface Transport {
  getStatus(signal?: AbortSignal): Promise<CompanionStatus>;
  act(path: string, body?: object, signal?: AbortSignal): Promise<CompanionStatus>;
  evaluate(signal?: AbortSignal): Promise<void>;
  getExplanation(signal?: AbortSignal): Promise<Explanation>;
  getEvents(signal?: AbortSignal): Promise<CompanionEvent[]>;
}
