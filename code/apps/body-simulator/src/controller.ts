import { BehaviorAnimator } from "./animation.ts";
import { ApiTransport, MockTransport } from "./api.ts";
import { behaviorFor } from "./behaviors.ts";
import { savePreferences } from "./preferences.ts";
import type { CompanionStatus, InteractionState, SimulatorPreferences, Transport } from "./types.ts";
import type { CompanionView } from "./view.ts";

const actionMap: Record<string, { path: string; body?: object }> = {
  start: { path: "/focus-sessions" }, stop: { path: "/focus-sessions/current/stop" }, resume: { path: "/focus-sessions/current/resume" },
  accept: { path: "/interactions/current/accept" }, defer: { path: "/interactions/current/defer", body: { minutes: 10 } }, dismiss: { path: "/interactions/current/dismiss" },
  quiet: { path: "/interactions/current/quiet", body: { minutes: 30 } }, "end-quiet": { path: "/interactions/current/quiet/end" },
  "reduce-frequency": { path: "/interactions/current/reduce-frequency", body: { additional_minutes: 15 } },
};

export class SimulatorController {
  private readonly live = new ApiTransport();
  private readonly mock = new MockTransport();
  private transport: Transport = this.live;
  private isMock = false;
  private pollTimer: number | undefined;
  private request: AbortController | null = null;
  private status: CompanionStatus | null = null;
  private attentionCompletionInFlight = false;
  private readonly animator: BehaviorAnimator;

  constructor(private readonly view: CompanionView, private preferences: SimulatorPreferences) {
    this.animator = new BehaviorAnimator(view);
  }

  start(): void { this.view.renderPreferences(this.preferences); void this.refresh(); this.schedulePoll(); }
  stop(): void { window.clearTimeout(this.pollTimer); this.request?.abort(); this.animator.cancel(); }

  async refresh(): Promise<void> {
    this.request?.abort();
    this.request = new AbortController();
    try {
      const status = await this.transport.getStatus(this.request.signal);
      await this.present(status);
      this.view.renderConnection(true, this.isMock);
      this.view.showError();
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      this.view.renderConnection(false, this.isMock);
      this.view.showError(error instanceof Error ? error.message : "Unable to reach the companion service.");
    }
  }

  async perform(action: string): Promise<void> {
    try {
      if (action === "evaluate") {
        await this.transport.evaluate();
        await this.refresh();
        return;
      }
      if (action === "explain") {
        this.view.renderExplanation(await this.transport.getExplanation());
        return;
      }
      const command = actionMap[action];
      if (!command) return;
      await this.present(await this.transport.act(command.path, command.body));
      this.view.showError();
    } catch (error) {
      this.view.showError(error instanceof Error ? error.message : "The action could not be completed.");
      await this.refresh();
    }
  }

  async selectMockState(state: InteractionState): Promise<void> { this.mock.setState(state); await this.refresh(); }

  setMode(mock: boolean): void {
    this.isMock = mock;
    this.transport = mock ? this.mock : this.live;
    this.view.setMockControls(mock);
    this.animator.cancel();
    void this.refresh();
  }

  updatePreferences(next: Partial<SimulatorPreferences>): void {
    this.preferences = { ...this.preferences, ...next };
    savePreferences(this.preferences);
    this.view.renderPreferences(this.preferences);
    if (this.status) void this.present(this.status);
    this.schedulePoll();
  }

  private async present(status: CompanionStatus): Promise<void> {
    this.status = status;
    const behavior = behaviorFor(status.interaction_state, this.preferences);
    this.view.renderStatus(status, behavior, this.isMock);
    this.view.renderEvents(await this.transport.getEvents().catch(() => []));
    const completed = await this.animator.play(behavior);
    if (completed && behavior.attentionComplete && !this.attentionCompletionInFlight) {
      this.attentionCompletionInFlight = true;
      try { await this.transport.act("/interactions/current/attention-complete"); await this.refresh(); }
      catch (error) { this.view.showError(error instanceof Error ? error.message : "Could not complete the visual cue."); }
      finally { this.attentionCompletionInFlight = false; }
    }
  }

  private schedulePoll(): void {
    window.clearTimeout(this.pollTimer);
    this.pollTimer = window.setTimeout(async () => { await this.refresh(); this.schedulePoll(); }, this.preferences.pollIntervalMs);
  }
}
