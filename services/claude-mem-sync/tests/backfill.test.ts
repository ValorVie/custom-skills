import { describe, test, expect } from "bun:test";
import { computeContentHash } from "../server/src/utils/hash.js";
import {
  planHashBackfill,
  type ExistingHashRow,
  type PendingObservationRow,
} from "../server/src/utils/backfill.js";

function makePending(
  id: number,
  syncedAt: string,
  overrides: Partial<PendingObservationRow> = {}
): PendingObservationRow {
  return {
    id,
    synced_at: syncedAt,
    title: "T",
    narrative: "N",
    facts: "[]",
    project: "P",
    type: "discovery",
    ...overrides,
  };
}

describe("planHashBackfill", () => {
  test("plans updates for unique pending rows", () => {
    const pending = [
      makePending(1, "2026-02-24T00:00:00Z", { title: "A" }),
      makePending(2, "2026-02-24T00:01:00Z", { title: "B" }),
    ];

    const plan = planHashBackfill(pending, []);

    expect(plan.deleteIds).toEqual([]);
    expect(plan.updates).toHaveLength(2);
  });

  test("keeps earliest row when pending rows share same hash", () => {
    const pending = [
      makePending(10, "2026-02-24T00:00:00Z", { title: "Same" }),
      makePending(20, "2026-02-24T00:05:00Z", { title: "Same" }),
    ];

    const plan = planHashBackfill(pending, []);

    expect(plan.deleteIds).toEqual([20]);
    expect(plan.updates).toHaveLength(1);
    expect(plan.updates[0]?.id).toBe(10);
  });

  test("replaces existing newer hash owner with earlier pending row", () => {
    const pendingRow = makePending(5, "2026-02-24T00:00:00Z", { title: "Shared" });
    const hash = computeContentHash(pendingRow);
    const existing: ExistingHashRow[] = [
      {
        id: 50,
        sync_content_hash: hash,
        synced_at: "2026-02-24T02:00:00Z",
      },
    ];

    const plan = planHashBackfill([pendingRow], existing);

    expect(plan.deleteIds).toEqual([50]);
    expect(plan.updates).toEqual([{ id: 5, hash }]);
  });

  test("deletes pending row when existing owner is earlier", () => {
    const pendingRow = makePending(9, "2026-02-24T03:00:00Z", { title: "Shared" });
    const hash = computeContentHash(pendingRow);
    const existing: ExistingHashRow[] = [
      {
        id: 2,
        sync_content_hash: hash,
        synced_at: "2026-02-24T01:00:00Z",
      },
    ];

    const plan = planHashBackfill([pendingRow], existing);

    expect(plan.deleteIds).toEqual([9]);
    expect(plan.updates).toEqual([]);
  });
});
