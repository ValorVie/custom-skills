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

function normalizeFacts(value: unknown): string {
  if (value === null || value === undefined) {
    return "[]";
  }
  if (typeof value === "string") {
    return value;
  }
  return JSON.stringify(value);
}

export function computeContentHash(obs: ObservationLike): string {
  const payload = JSON.stringify({
    facts: normalizeFacts(obs.facts),
    narrative: normalizeText(obs.narrative),
    project: normalizeText(obs.project),
    title: normalizeText(obs.title),
    type: normalizeText(obs.type),
  });

  return createHash("sha256").update(payload, "utf-8").digest("hex").slice(0, 32);
}
