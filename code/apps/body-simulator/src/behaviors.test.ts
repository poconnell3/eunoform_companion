import { describe, expect, it } from "vitest";
import { behaviorFor } from "./behaviors.ts";
import type { SimulatorPreferences } from "./types.ts";

const standard: SimulatorPreferences = { reducedMotion: false, sensoryLevel: "standard", highContrast: false, pollIntervalMs: 2000 };

describe("behaviorFor", () => {
  it("maps attention to a gentle, completable visual cue", () => {
    expect(behaviorFor("attracting_attention", standard)).toMatchObject({ expression: "gentle_attention", gesture: "wave_small", attentionComplete: true });
  });

  it("keeps quiet mode still", () => {
    expect(behaviorFor("quiet", standard)).toMatchObject({ expression: "resting", gesture: "still", durationMs: 0 });
  });

  it("removes motion in reduced-motion mode", () => {
    expect(behaviorFor("attracting_attention", { ...standard, reducedMotion: true })).toMatchObject({ gesture: "still", durationMs: 500 });
  });
});
