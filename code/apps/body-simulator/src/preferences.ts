import type { SimulatorPreferences } from "./types.ts";

const storageKey = "eunoform.simulator.preferences.v1";

export const defaultPreferences = (): SimulatorPreferences => ({
  reducedMotion: window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  sensoryLevel: "standard",
  highContrast: window.matchMedia("(prefers-contrast: more)").matches,
  pollIntervalMs: 2000,
});

export function loadPreferences(): SimulatorPreferences {
  const defaults = defaultPreferences();
  try {
    const stored = JSON.parse(localStorage.getItem(storageKey) ?? "{}") as Partial<SimulatorPreferences>;
    return {
      reducedMotion: typeof stored.reducedMotion === "boolean" ? stored.reducedMotion : defaults.reducedMotion,
      sensoryLevel: stored.sensoryLevel === "low" ? "low" : "standard",
      highContrast: typeof stored.highContrast === "boolean" ? stored.highContrast : defaults.highContrast,
      pollIntervalMs: stored.pollIntervalMs === 5000 ? 5000 : 2000,
    };
  } catch {
    return defaults;
  }
}

export function savePreferences(preferences: SimulatorPreferences): void {
  localStorage.setItem(storageKey, JSON.stringify(preferences));
}
