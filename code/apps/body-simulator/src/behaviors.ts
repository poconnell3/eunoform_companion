import type { InteractionState, SimulatorPreferences, VisualBehavior } from "./types.ts";

const behaviorMap: Record<InteractionState, VisualBehavior> = {
  idle: { expression: "resting", gesture: "breathe", label: "Resting", announcement: "Companion is resting.", durationMs: 2600 },
  focusing: { expression: "focused", gesture: "breathe", label: "Focus in progress", announcement: "Focus session in progress.", durationMs: 2800 },
  policy_evaluation: { expression: "focused", gesture: "still", label: "Checking timing", announcement: "Checking the humane interaction policy.", durationMs: 900 },
  attracting_attention: { expression: "gentle_attention", gesture: "wave_small", label: "Gentle check-in", announcement: "The companion has a gentle check-in.", durationMs: 1800, attentionComplete: true },
  awaiting_response: { expression: "curious", gesture: "lean_in", label: "Waiting for you", announcement: "The companion is waiting for your response.", durationMs: 2400 },
  explaining: { expression: "curious", gesture: "still", label: "Explaining", announcement: "The companion is explaining this check-in.", durationMs: 2200 },
  deferred: { expression: "resting", gesture: "settle", label: "Deferred", announcement: "The check-in is deferred.", durationMs: 1800 },
  on_break: { expression: "warm", gesture: "breathe", label: "Break time", announcement: "A break is in progress.", durationMs: 2600 },
  quiet: { expression: "resting", gesture: "still", label: "Quiet mode", announcement: "Quiet mode is active.", durationMs: 0 },
};

export function behaviorFor(state: InteractionState, preferences: SimulatorPreferences): VisualBehavior {
  const behavior = behaviorMap[state];
  if (preferences.reducedMotion || preferences.sensoryLevel === "low") {
    return { ...behavior, gesture: "still", durationMs: Math.min(behavior.durationMs, 500) };
  }
  return behavior;
}

export { behaviorMap };
