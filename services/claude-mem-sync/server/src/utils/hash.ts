import { createHash } from "crypto";

export interface ObservationLike {
  title?: unknown;
  narrative?: unknown;
  facts?: unknown;
  project?: unknown;
  type?: unknown;
}

function normalizeText(value: unknown): string {
  if (value === null || value === undefined) {
    return "";
  }
  if (typeof value === "string") {
    return value;
  }
  return String(value);
}

export function computeContentHash(obs: ObservationLike): string {
  const parts = [
    normalizeText(obs.title),
    normalizeText(obs.narrative),
    normalizeText(obs.facts),
    normalizeText(obs.project),
    normalizeText(obs.type),
  ];

  return createHash("sha256").update(parts.join("\n"), "utf-8").digest("hex").slice(0, 32);
}
