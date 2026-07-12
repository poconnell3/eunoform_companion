import type { AnimationTarget } from "./animation.ts";
import type { CompanionEvent, CompanionStatus, Explanation, InteractionState, SimulatorPreferences, VisualBehavior } from "./types.ts";

export const appMarkup = `
  <main class="shell">
    <header class="masthead">
      <div><p class="eyebrow">LOCAL BODY SIMULATOR</p><h1>Eunoform <span>Companion</span></h1></div>
      <div class="connection"><span id="connection-dot" aria-hidden="true"></span><span id="connection-text">Connecting…</span></div>
    </header>
    <section class="stage" aria-labelledby="stage-title">
      <div class="ambient ambient-one"></div><div class="ambient ambient-two"></div>
      <div class="companion-wrap">
        <p id="stage-title" class="state-kicker">CURRENT PRESENCE</p>
        <div id="companion" class="companion" data-expression="resting" data-gesture="still" aria-label="Eunoform companion, resting">
          <div class="shadow"></div>
          <svg class="body" viewBox="0 0 420 430" role="img" aria-labelledby="body-title body-description">
            <title id="body-title">Eunoform companion</title><desc id="body-description">A soft abstract companion with an animated face and one small arm.</desc>
            <defs><linearGradient id="shell-gradient" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f0dcc0"/><stop offset="1" stop-color="#c69f79"/></linearGradient></defs>
            <path class="arm" d="M315 249 C372 245 386 201 365 171" fill="none" stroke="url(#shell-gradient)" stroke-width="30" stroke-linecap="round"/>
            <path class="shell-shape" d="M110 359 C70 318 65 219 91 132 C110 68 165 38 225 48 C300 59 343 123 340 215 C337 310 302 368 221 382 C172 390 133 381 110 359Z" fill="url(#shell-gradient)"/>
            <ellipse class="face-panel" cx="215" cy="185" rx="105" ry="92"/>
            <path class="eye eye-left" d="M160 177 Q177 162 194 177"/><path class="eye eye-right" d="M236 177 Q253 162 270 177"/>
            <path class="mouth" d="M187 222 Q215 242 243 222"/>
            <circle class="cheek cheek-left" cx="157" cy="211" r="11"/><circle class="cheek cheek-right" cx="273" cy="211" r="11"/>
            <circle class="status-light" cx="217" cy="328" r="8"/>
          </svg>
        </div>
        <div class="presence-copy"><h2 id="behavior-label">Resting</h2><p id="elapsed-label">Ready when you are.</p></div>
      </div>
      <aside class="status-card" aria-label="Live companion status">
        <div><span>STATE</span><strong id="state-value">idle</strong></div>
        <div><span>EXPRESSION</span><strong id="expression-value">resting</strong></div>
        <div><span>GESTURE</span><strong id="gesture-value">still</strong></div>
        <div><span>MODE</span><strong id="mode-value">live API</strong></div>
        <div><span>SOUND</span><strong id="sound-value">available</strong></div>
      </aside>
    </section>
    <section id="controls" class="control-deck" aria-labelledby="controls-title">
      <div class="control-heading"><div><p class="eyebrow">DEVELOPER DECK</p><h2 id="controls-title">Guide the current loop</h2></div><button id="refresh" class="icon-button" type="button" aria-label="Refresh status">↻</button></div>
      <div class="control-grid">
        <div class="control-group"><h3>Session</h3><div class="button-row"><button data-action="start">Start focus</button><button data-action="evaluate">Trigger check-in</button><button data-action="stop" class="quiet-button">Stop</button></div></div>
        <div class="control-group"><h3>Response</h3><div class="button-row"><button data-action="accept">Take a break</button><button data-action="defer">Later</button><button data-action="dismiss" class="quiet-button">Dismiss</button><button data-action="explain" class="quiet-button">Why?</button><button data-action="reduce-frequency" class="quiet-button">Fewer check-ins</button></div></div>
        <div class="control-group"><h3>Presence</h3><div class="button-row"><button data-action="quiet">Quiet mode</button><button data-action="end-quiet">End quiet</button><button data-action="resume" class="quiet-button">Resume</button></div></div>
      </div>
      <details class="settings-panel"><summary>Simulator settings</summary><div class="settings-grid">
        <label><span>Data source</span><select id="data-mode"><option value="live">Live local API</option><option value="mock">Mock data</option></select></label>
        <label><span>Mock state</span><select id="mock-state"></select></label>
        <label class="check"><input id="reduced-motion" type="checkbox"/><span>Reduce motion</span></label>
        <label class="check"><input id="low-sensory" type="checkbox"/><span>Low sensory mode</span></label>
        <label class="check"><input id="high-contrast" type="checkbox"/><span>High contrast</span></label>
        <label><span>Refresh rate</span><select id="poll-rate"><option value="2000">2 seconds</option><option value="5000">5 seconds</option></select></label>
      </div></details>
      <div class="inspector-grid"><section aria-labelledby="explanation-title"><h3 id="explanation-title">Explanation</h3><p id="explanation-value">Ask why after a check-in to see the policy facts.</p></section><section aria-labelledby="events-title"><h3 id="events-title">Recent events</h3><ol id="event-history"><li>No events yet.</li></ol></section></div>
      <p id="error-message" class="error-message" role="alert" hidden></p><div id="announcer" class="sr-only" aria-live="polite"></div>
    </section>
  </main>`;

const required = <T extends Element>(selector: string): T => {
  const element = document.querySelector<T>(selector);
  if (!element) throw new Error(`Missing required element: ${selector}`);
  return element;
};

export class CompanionView implements AnimationTarget {
  private readonly companion = required<HTMLElement>("#companion");

  apply(behavior: VisualBehavior): void {
    this.companion.dataset.expression = behavior.expression;
    this.companion.dataset.gesture = behavior.gesture;
    this.companion.setAttribute("aria-label", `Eunoform companion, ${behavior.label.toLowerCase()}`);
    required("#behavior-label").textContent = behavior.label;
    required("#expression-value").textContent = behavior.expression.replaceAll("_", " ");
    required("#gesture-value").textContent = behavior.gesture.replaceAll("_", " ");
  }

  settle(): void { this.companion.dataset.gesture = "still"; }

  renderStatus(status: CompanionStatus, behavior: VisualBehavior, isMock: boolean): void {
    required("#state-value").textContent = status.interaction_state.replaceAll("_", " ");
    required("#mode-value").textContent = isMock ? "mock data" : "live API";
    required("#sound-value").textContent = status.settings.muted ? "muted" : status.interaction_state === "quiet" ? "quiet" : "available";
    required("#elapsed-label").textContent = status.focus_session ? `${status.elapsed_minutes} minutes in this focus session.` : "Ready when you are.";
    required("#announcer").textContent = behavior.announcement;
    document.body.dataset.state = status.interaction_state;
  }

  renderExplanation(explanation: Explanation): void {
    required("#explanation-value").textContent = explanation.message;
    required("#announcer").textContent = explanation.message;
  }

  renderEvents(events: CompanionEvent[]): void {
    const list = required<HTMLOListElement>("#event-history");
    list.replaceChildren();
    if (events.length === 0) {
      const item = document.createElement("li"); item.textContent = "No events yet."; list.append(item); return;
    }
    for (const event of events) {
      const item = document.createElement("li");
      const label = String(event.event_type ?? event.type ?? event.policy_reason ?? "check-in").replaceAll("_", " ");
      const timestamp = event.occurred_at ?? event.created_at;
      item.textContent = timestamp ? `${label} · ${new Date(timestamp).toLocaleTimeString()}` : label;
      list.append(item);
    }
  }

  renderConnection(connected: boolean, isMock: boolean): void {
    required("#connection-text").textContent = isMock ? "Mock mode" : connected ? "Local API connected" : "API unavailable";
    required("#connection-dot").classList.toggle("offline", !connected && !isMock);
  }

  renderPreferences(preferences: SimulatorPreferences): void {
    document.documentElement.classList.toggle("reduce-motion", preferences.reducedMotion);
    document.documentElement.classList.toggle("low-sensory", preferences.sensoryLevel === "low");
    document.documentElement.classList.toggle("high-contrast", preferences.highContrast);
    required<HTMLInputElement>("#reduced-motion").checked = preferences.reducedMotion;
    required<HTMLInputElement>("#low-sensory").checked = preferences.sensoryLevel === "low";
    required<HTMLInputElement>("#high-contrast").checked = preferences.highContrast;
    required<HTMLSelectElement>("#poll-rate").value = String(preferences.pollIntervalMs);
  }

  showError(message?: string): void {
    const element = required<HTMLElement>("#error-message");
    element.hidden = !message;
    element.textContent = message ?? "";
  }

  setMockControls(isMock: boolean): void {
    required<HTMLSelectElement>("#mock-state").disabled = !isMock;
  }
}

export const interactionStateLabel = (state: InteractionState): string => state.replaceAll("_", " ");
