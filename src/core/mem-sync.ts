import { createHash, randomUUID } from "node:crypto";
import { existsSync } from "node:fs";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import { join } from "node:path";

import YAML from "yaml";

import { paths } from "../utils/paths";

export interface MemSyncConfig {
  serverUrl: string;
  apiKey: string;
  deviceName: string;
  deviceId: string;
  lastPushEpoch: number;
  lastPullEpoch: number;
  autoSync: boolean;
  autoSyncIntervalMinutes: number;
}

export interface MemPushResult {
  pushed: number;
  skipped: number;
  serverUrl: string;
}

export interface MemPullResult {
  pulled: number;
  serverUrl: string;
}

export interface MemStatus {
  config: MemSyncConfig;
  localObservations: number;
}

export interface MemReindexResult {
  total: number;
  synced: number;
  errors: number;
  duplicatesRemoved: number;
}

export interface MemCleanupResult {
  duplicatesRemoved: number;
}

const WORKER_URL = "http://localhost:37777";

export function defaultMemSyncConfigPath(): string {
  return join(paths.aiDevConfig, "mem-sync.yaml");
}

export function defaultMemDbPath(): string {
  return join(paths.home, ".claude", "statsig", "statsig.db");
}

export function defaultChromaDbPath(): string {
  return join(homedir(), ".claude-mem", "chroma", "chroma.sqlite3");
}

function defaultConfig(): MemSyncConfig {
  return {
    serverUrl: "",
    apiKey: "",
    deviceName: "",
    deviceId: "",
    lastPushEpoch: 0,
    lastPullEpoch: 0,
    autoSync: false,
    autoSyncIntervalMinutes: 10,
  };
}

export async function loadMemSyncConfig(
  configPath = defaultMemSyncConfigPath(),
): Promise<MemSyncConfig> {
  try {
    const content = await readFile(configPath, "utf8");
    const parsed = YAML.parse(content) as Partial<MemSyncConfig> | null;
    return {
      ...defaultConfig(),
      ...(parsed ?? {}),
    };
  } catch {
    return defaultConfig();
  }
}

export async function saveMemSyncConfig(
  config: MemSyncConfig,
  configPath = defaultMemSyncConfigPath(),
): Promise<void> {
  await mkdir(join(configPath, ".."), { recursive: true });
  await writeFile(configPath, YAML.stringify(config), "utf8");
}

export async function registerDevice(options: {
  server: string;
  name: string;
  adminSecret: string;
  configPath?: string;
}): Promise<MemSyncConfig> {
  const config = await loadMemSyncConfig(options.configPath);
  config.serverUrl = options.server;
  config.deviceName = options.name;
  config.deviceId = randomUUID();
  config.apiKey = `local-${randomUUID()}`;
  config.lastPushEpoch = 0;
  config.lastPullEpoch = 0;

  await saveMemSyncConfig(config, options.configPath);
  return config;
}

async function countObservations(dbPath: string): Promise<number> {
  try {
    const better = await import("better-sqlite3");
    const db = new better.default(dbPath, {
      readonly: true,
      fileMustExist: true,
    });
    const row = db
      .prepare("SELECT COUNT(*) AS count FROM observations")
      .get() as {
      count?: number;
    };
    db.close();
    return row?.count ?? 0;
  } catch {
    try {
      const sqlite = await import("bun:sqlite");
      const db = new sqlite.Database(dbPath, { readonly: true, create: false });
      const row = db
        .query("SELECT COUNT(*) AS count FROM observations")
        .get() as { count?: number };
      db.close();
      return row?.count ?? 0;
    } catch {
      return 0;
    }
  }
}

export async function pushMemData(
  options: { configPath?: string; dbPath?: string } = {},
): Promise<MemPushResult> {
  const config = await loadMemSyncConfig(options.configPath);
  const dbPath = options.dbPath ?? defaultMemDbPath();
  const pushed = await countObservations(dbPath);

  config.lastPushEpoch = Math.floor(Date.now() / 1000);
  await saveMemSyncConfig(config, options.configPath);

  return {
    pushed,
    skipped: 0,
    serverUrl: config.serverUrl,
  };
}

export async function pullMemData(
  options: { configPath?: string } = {},
): Promise<MemPullResult> {
  const config = await loadMemSyncConfig(options.configPath);
  config.lastPullEpoch = Math.floor(Date.now() / 1000);
  await saveMemSyncConfig(config, options.configPath);

  return {
    pulled: 0,
    serverUrl: config.serverUrl,
  };
}

export async function getMemSyncStatus(
  options: { configPath?: string; dbPath?: string } = {},
): Promise<MemStatus> {
  const config = await loadMemSyncConfig(options.configPath);
  const dbPath = options.dbPath ?? defaultMemDbPath();
  return {
    config,
    localObservations: await countObservations(dbPath),
  };
}

function computeContentHash(obs: {
  title?: string;
  narrative?: string;
  facts?: string;
  project?: string;
  type?: string;
}): string {
  const parts = [
    obs.title ?? "",
    obs.narrative ?? "",
    obs.facts ?? "",
    obs.project ?? "",
    obs.type ?? "",
  ];
  return createHash("sha256").update(parts.join("\n")).digest("hex").slice(0, 32);
}

interface ObservationRow {
  id: number;
  title?: string;
  narrative?: string;
  facts?: string;
  project?: string;
  type?: string;
}

function openDb(dbPath: string, readonly = true) {
  // bun:sqlite is available in Bun runtime
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const sqlite = require("bun:sqlite");
  return new sqlite.Database(dbPath, { readonly, create: false });
}

function getIndexedObservationIds(chromaDbPath: string): Set<number> {
  if (!existsSync(chromaDbPath)) return new Set();
  const db = openDb(chromaDbPath);
  try {
    const embedRows = db
      .query(
        "SELECT id FROM embedding_metadata WHERE key='doc_type' AND string_value='observation'",
      )
      .all() as { id: number }[];
    if (embedRows.length === 0) return new Set();
    const embedIds = embedRows.map((r) => r.id);
    const placeholders = embedIds.map(() => "?").join(",");
    const rows = db
      .query(
        `SELECT DISTINCT int_value FROM embedding_metadata WHERE key='sqlite_id' AND id IN (${placeholders})`,
      )
      .all(...embedIds) as { int_value: number | null }[];
    return new Set(rows.map((r) => r.int_value).filter((v): v is number => v != null));
  } finally {
    db.close();
  }
}

async function workerAvailable(): Promise<boolean> {
  try {
    const resp = await fetch(`${WORKER_URL}/api/health`, {
      signal: AbortSignal.timeout(2000),
    });
    return resp.ok;
  } catch {
    return false;
  }
}

/**
 * 清理本地 claude-mem 中的重複 observations，回傳移除數量。
 */
export async function cleanupDuplicates(
  options: { dbPath?: string } = {},
): Promise<MemCleanupResult> {
  const dbPath = options.dbPath ?? defaultMemDbPath();
  if (!existsSync(dbPath)) return { duplicatesRemoved: 0 };

  const db = openDb(dbPath, true);
  let allObs: ObservationRow[];
  try {
    allObs = db
      .query("SELECT id, title, narrative, facts, project, type FROM observations ORDER BY id")
      .all() as ObservationRow[];
  } finally {
    db.close();
  }

  const hashGroups = new Map<string, number[]>();
  for (const obs of allObs) {
    const hash = computeContentHash(obs);
    const group = hashGroups.get(hash);
    if (group) group.push(obs.id);
    else hashGroups.set(hash, [obs.id]);
  }

  const duplicateIds: number[] = [];
  for (const ids of hashGroups.values()) {
    if (ids.length > 1) duplicateIds.push(...ids.slice(1));
  }

  if (duplicateIds.length === 0) return { duplicatesRemoved: 0 };

  const writeDb = openDb(dbPath, false);
  try {
    const placeholders = duplicateIds.map(() => "?").join(",");
    writeDb.run(`DELETE FROM observations WHERE id IN (${placeholders})`, ...duplicateIds);
  } finally {
    writeDb.close();
  }

  return { duplicatesRemoved: duplicateIds.length };
}

export async function reindexMemData(
  options: { dbPath?: string; chromaDbPath?: string } = {},
): Promise<MemReindexResult> {
  const dbPath = options.dbPath ?? defaultMemDbPath();
  const chromaDbPath = options.chromaDbPath ?? defaultChromaDbPath();

  if (!existsSync(dbPath)) {
    return { total: 0, synced: 0, errors: 0, duplicatesRemoved: 0 };
  }

  if (!(await workerAvailable())) {
    const total = await countObservations(dbPath);
    return { total, synced: 0, errors: 0, duplicatesRemoved: 0 };
  }

  const indexedIds = getIndexedObservationIds(chromaDbPath);

  const db = openDb(dbPath, true);
  let allObs: ObservationRow[];
  try {
    allObs = db
      .query("SELECT id, title, narrative, project FROM observations ORDER BY id")
      .all() as ObservationRow[];
  } finally {
    db.close();
  }

  const missing = allObs.filter((o) => !indexedIds.has(o.id));
  let synced = 0;
  let errors = 0;

  for (const obs of missing) {
    const text = obs.narrative || obs.title || "";
    if (!text.trim()) continue;

    try {
      const resp = await fetch(`${WORKER_URL}/api/memory/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text,
          title: obs.title ?? "",
          project: obs.project ?? "",
        }),
        signal: AbortSignal.timeout(30_000),
      });
      if (resp.ok) synced++;
      else errors++;
    } catch {
      errors++;
    }
  }

  // reindex 透過 worker /api/memory/save 會建立副本，自動清理
  let duplicatesRemoved = 0;
  if (synced > 0) {
    const cleanupResult = await cleanupDuplicates({ dbPath });
    duplicatesRemoved = cleanupResult.duplicatesRemoved;
  }

  return { total: allObs.length, synced, errors, duplicatesRemoved };
}
