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

  test("matches Python implementation", () => {
    const value = computeContentHash({
      title: "Test observation",
      narrative: "This is a test",
      facts: '["fact1"]',
      project: "test-project",
      type: "discovery",
    });

    expect(value).toBe("14e05009b56669e285c9338331d18dc7");
  });
});
