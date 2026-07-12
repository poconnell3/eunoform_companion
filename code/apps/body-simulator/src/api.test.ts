import { describe, expect, it } from "vitest";
import { MockTransport, validateStatus } from "./api.ts";

describe("status validation", () => {
  it("rejects unknown backend states", () => {
    expect(() => validateStatus({ interaction_state: "guessing", elapsed_minutes: 0, settings: {} })).toThrow("unknown interaction state");
  });
});

describe("MockTransport", () => {
  it("supports the complete visual interaction loop", async () => {
    const transport = new MockTransport();
    expect((await transport.act("/focus-sessions")).interaction_state).toBe("focusing");
    await transport.evaluate();
    expect((await transport.getStatus()).interaction_state).toBe("attracting_attention");
    expect((await transport.act("/interactions/current/attention-complete")).interaction_state).toBe("awaiting_response");
    expect((await transport.act("/interactions/current/defer")).interaction_state).toBe("deferred");
    expect((await transport.getExplanation()).message).toContain("42 minutes");
    expect(await transport.getEvents()).toHaveLength(1);
    expect((await transport.act("/interactions/current/reduce-frequency")).interaction_state).toBe("focusing");
  });
});
