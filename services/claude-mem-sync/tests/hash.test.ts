import { createHash } from "crypto";
import { describe, test, expect } from "bun:test";
import { computeContentHash } from "../server/src/utils/hash.js";

describe("computeContentHash", () => {
  test("returns 32-char hex string", () => {
    const value = computeContentHash({
      title: "Test",
      narrative: "Narrative",
      facts: "[]",
      project: "p",
      type: "t",
    });

    expect(value).toHaveLength(32);
    expect(value).toMatch(/^[0-9a-f]{32}$/);
  });

  test("same content produces same hash", () => {
    const a = { title: "A", narrative: "B", facts: "[]", project: "p", type: "t" };
    const b = {
      title: "A",
      narrative: "B",
      facts: "[]",
      project: "p",
      type: "t",
      created_at_epoch: 123,
    };

    expect(computeContentHash(a)).toBe(computeContentHash(b));
  });

  test("different content produces different hash", () => {
    const a = { title: "A", narrative: "B", facts: "[]", project: "p", type: "t" };
    const b = { title: "A", narrative: "C", facts: "[]", project: "p", type: "t" };

    expect(computeContentHash(a)).not.toBe(computeContentHash(b));
  });

  test("known hash value", () => {
    const value = computeContentHash({
      title: "Test observation",
      narrative: "This is a test",
      facts: '["fact1"]',
      project: "test-project",
      type: "discovery",
    });

    expect(value).toBe("5d08594de1e6bf6e7a7a23e2b44df26e");
  });

  test("null/undefined fields normalize to empty string", () => {
    const a = computeContentHash({});
    const b = computeContentHash({ title: null, narrative: undefined, facts: null, project: null, type: null });

    expect(a).toBe(b);
  });

  test("matches client-side algorithm (parts.join newline)", () => {
    const obs = {
      title: "Test observation",
      narrative: "This is a test",
      facts: '["fact1"]',
      project: "test-project",
      type: "discovery",
    };

    // Client algorithm: parts.join("\n") + SHA256
    const parts = [
      String(obs.title ?? ""),
      String(obs.narrative ?? ""),
      String(obs.facts ?? ""),
      String(obs.project ?? ""),
      String(obs.type ?? ""),
    ];
    const clientHash = createHash("sha256").update(parts.join("\n")).digest("hex").slice(0, 32);

    expect(computeContentHash(obs)).toBe(clientHash);
  });
});
