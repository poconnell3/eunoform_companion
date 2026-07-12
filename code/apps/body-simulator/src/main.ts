import "./styles.css";
import { SimulatorController } from "./controller.ts";
import { loadPreferences } from "./preferences.ts";
import { interactionStates, type InteractionState } from "./types.ts";
import { appMarkup, CompanionView, interactionStateLabel } from "./view.ts";

const root = document.querySelector<HTMLDivElement>("#app");
if (!root) throw new Error("Simulator root element is missing.");
root.innerHTML = appMarkup;

const controller = new SimulatorController(new CompanionView(), loadPreferences());
const mockState = document.querySelector<HTMLSelectElement>("#mock-state");
if (!mockState) throw new Error("Mock state selector is missing.");
for (const state of interactionStates) mockState.add(new Option(interactionStateLabel(state), state));

document.querySelector("#refresh")?.addEventListener("click", () => void controller.refresh());
document.querySelectorAll<HTMLButtonElement>("[data-action]").forEach((button) => button.addEventListener("click", () => void controller.perform(button.dataset.action ?? "")));
document.querySelector<HTMLSelectElement>("#data-mode")?.addEventListener("change", (event) => controller.setMode((event.target as HTMLSelectElement).value === "mock"));
mockState.addEventListener("change", () => void controller.selectMockState(mockState.value as InteractionState));
document.querySelector<HTMLInputElement>("#reduced-motion")?.addEventListener("change", (event) => controller.updatePreferences({ reducedMotion: (event.target as HTMLInputElement).checked }));
document.querySelector<HTMLInputElement>("#low-sensory")?.addEventListener("change", (event) => controller.updatePreferences({ sensoryLevel: (event.target as HTMLInputElement).checked ? "low" : "standard" }));
document.querySelector<HTMLInputElement>("#high-contrast")?.addEventListener("change", (event) => controller.updatePreferences({ highContrast: (event.target as HTMLInputElement).checked }));
document.querySelector<HTMLSelectElement>("#poll-rate")?.addEventListener("change", (event) => controller.updatePreferences({ pollIntervalMs: Number((event.target as HTMLSelectElement).value) }));
window.addEventListener("beforeunload", () => controller.stop());
controller.start();
