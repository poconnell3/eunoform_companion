// @vitest-environment jsdom
import { describe, expect, it, vi } from "vitest";
import { BehaviorAnimator, type AnimationTarget } from "./animation.ts";
import type { VisualBehavior } from "./types.ts";

const behavior: VisualBehavior = { expression: "warm", gesture: "wave_small", label: "Test", announcement: "Test", durationMs: 1000 };

describe("BehaviorAnimator", () => {
  it("cancels an in-flight sequence safely when a new one begins", async () => {
    vi.useFakeTimers();
    const target: AnimationTarget = { apply: vi.fn(), settle: vi.fn() };
    const animator = new BehaviorAnimator(target);
    const first = animator.play(behavior);
    const second = animator.play({ ...behavior, durationMs: 10 });
    await vi.advanceTimersByTimeAsync(10);
    await expect(first).resolves.toBe(false);
    await expect(second).resolves.toBe(true);
    expect(target.apply).toHaveBeenCalledTimes(2);
    expect(target.settle).toHaveBeenCalled();
    vi.useRealTimers();
  });
});
