import type { VisualBehavior } from "./types.ts";

export interface AnimationTarget {
  apply(behavior: VisualBehavior): void;
  settle(): void;
}

export class BehaviorAnimator {
  private controller: AbortController | null = null;
  private sequence = 0;

  constructor(private readonly target: AnimationTarget) {}

  async play(behavior: VisualBehavior): Promise<boolean> {
    this.cancel();
    const controller = new AbortController();
    const sequence = ++this.sequence;
    this.controller = controller;
    this.target.apply(behavior);

    if (behavior.durationMs === 0) return true;
    try {
      await abortableDelay(behavior.durationMs, controller.signal);
      return sequence === this.sequence;
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return false;
      throw error;
    }
  }

  cancel(): void {
    this.controller?.abort();
    this.controller = null;
    this.target.settle();
  }
}

export function abortableDelay(durationMs: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) {
      reject(new DOMException("Animation cancelled", "AbortError"));
      return;
    }
    const timer = window.setTimeout(resolve, durationMs);
    signal.addEventListener("abort", () => {
      window.clearTimeout(timer);
      reject(new DOMException("Animation cancelled", "AbortError"));
    }, { once: true });
  });
}
