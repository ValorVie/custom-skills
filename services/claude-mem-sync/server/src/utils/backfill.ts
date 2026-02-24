import { computeContentHash, type ObservationLike } from "./hash.js";

type SyncTimeInput = string | Date | null | undefined;

export type PendingObservationRow = ObservationLike & {
  id: number;
  synced_at: SyncTimeInput;
};

export type ExistingHashRow = {
  id: number;
  sync_content_hash: string;
  synced_at: SyncTimeInput;
};

type HashOwner = {
  id: number;
  syncedAtMs: number;
};

export type BackfillPlan = {
  updates: Array<{ id: number; hash: string }>;
  deleteIds: number[];
};

function toMillis(value: SyncTimeInput): number {
  if (value instanceof Date) {
    return value.getTime();
  }
  if (typeof value === "string") {
    const parsed = Date.parse(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }
  return Number.POSITIVE_INFINITY;
}

function shouldReplaceOwner(current: HashOwner, candidate: HashOwner): boolean {
  if (candidate.syncedAtMs < current.syncedAtMs) {
    return true;
  }
  if (candidate.syncedAtMs > current.syncedAtMs) {
    return false;
  }
  return candidate.id < current.id;
}

export function planHashBackfill(
  pendingRows: PendingObservationRow[],
  existingRows: ExistingHashRow[]
): BackfillPlan {
  const owners = new Map<string, HashOwner>();
  for (const row of existingRows) {
    if (!row.sync_content_hash) {
      continue;
    }
    owners.set(row.sync_content_hash, {
      id: row.id,
      syncedAtMs: toMillis(row.synced_at),
    });
  }

  const updates = new Map<number, string>();
  const deleteIds = new Set<number>();

  for (const row of pendingRows) {
    const hash = computeContentHash(row);
    const candidate: HashOwner = {
      id: row.id,
      syncedAtMs: toMillis(row.synced_at),
    };

    const currentOwner = owners.get(hash);
    if (!currentOwner) {
      owners.set(hash, candidate);
      updates.set(row.id, hash);
      continue;
    }

    if (shouldReplaceOwner(currentOwner, candidate)) {
      deleteIds.add(currentOwner.id);
      updates.delete(currentOwner.id);
      owners.set(hash, candidate);
      updates.set(row.id, hash);
      continue;
    }

    deleteIds.add(row.id);
  }

  return {
    updates: [...updates.entries()].map(([id, hash]) => ({ id, hash })),
    deleteIds: [...deleteIds],
  };
}
