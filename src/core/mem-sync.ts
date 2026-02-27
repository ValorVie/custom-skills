import { execSync } from "node:child_process";
import { createHash, randomUUID } from "node:crypto";
import { existsSync } from "node:fs";
import { mkdir, readFile, unlink, writeFile } from "node:fs/promises";
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

export interface MemCategoryStats {
  sessions: number;
  observations: number;
  summaries: number;
  prompts: number;
}

export interface MemPushResult {
  pushed: number;
  skipped: number;
  errors: number;
  serverUrl: string;
  /** Per-category counts sent to server */
  sent: MemCategoryStats;
  /** Per-category dedup exclusions */
  dedupExcluded: { pulled: number; preflight: number };
  /** Per-category imported/skipped from server response */
  imported: MemCategoryStats;
  skippedDetail: MemCategoryStats;
}

export interface MemPullResult {
  pulled: number;
  skipped: number;
  serverUrl: string;
  importMethod: "api" | "sqlite";
  /** Per-category counts received from server */
  received: MemCategoryStats;
  /** Per-category imported/skipped */
  imported: MemCategoryStats;
  skippedDetail: MemCategoryStats;
}

export interface MemStatus {
  config: MemSyncConfig;
  localObservations: number;
  localDuplicates: number;
  pulledHashesTracked: number;
  pendingPushCount: number;
  remoteStatus: {
    sessions?: number;
    observations?: number;
    summaries?: number;
    prompts?: number;
    devices?: number;
  } | null;
}

export interface MemAutoSyncResult {
  enabled: boolean;
  scheduler: "launchd" | "systemd" | "cron";
  message: string;
}

export interface MemReindexResult {
  total: number;
  missing: number;
  synced: number;
  errors: number;
  duplicatesRemoved: number;
}

export interface MemCleanupResult {
  duplicatesRemoved: number;
}

const WORKER_URL = "http://localhost:37777";
const PULLED_HASHES_FILENAME = "pulled-hashes.txt";

export function defaultMemSyncConfigPath(): string {
  return join(paths.aiDevConfig, "mem-sync.yaml");
}

export function defaultMemDbPath(): string {
  return join(homedir(), ".claude-mem", "claude-mem.db");
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

type RawMemSyncConfig = Partial<MemSyncConfig> & {
  server_url?: unknown;
  api_key?: unknown;
  device_name?: unknown;
  device_id?: unknown;
  last_push_epoch?: unknown;
  last_pull_epoch?: unknown;
  auto_sync?: unknown;
  auto_sync_interval_minutes?: unknown;
};

function toStringOrUndefined(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function toNumberOrUndefined(value: unknown): number | undefined {
  return typeof value === "number" ? value : undefined;
}

function toBooleanOrUndefined(value: unknown): boolean | undefined {
  return typeof value === "boolean" ? value : undefined;
}

function normalizeMemSyncConfig(
  raw: RawMemSyncConfig | null,
): Partial<MemSyncConfig> {
  if (!raw) {
    return {};
  }

  return {
    serverUrl: toStringOrUndefined(raw.serverUrl) ?? toStringOrUndefined(raw.server_url),
    apiKey: toStringOrUndefined(raw.apiKey) ?? toStringOrUndefined(raw.api_key),
    deviceName:
      toStringOrUndefined(raw.deviceName) ?? toStringOrUndefined(raw.device_name),
    deviceId: toStringOrUndefined(raw.deviceId) ?? toStringOrUndefined(raw.device_id),
    lastPushEpoch:
      toNumberOrUndefined(raw.lastPushEpoch) ??
      toNumberOrUndefined(raw.last_push_epoch),
    lastPullEpoch:
      toNumberOrUndefined(raw.lastPullEpoch) ??
      toNumberOrUndefined(raw.last_pull_epoch),
    autoSync: toBooleanOrUndefined(raw.autoSync) ?? toBooleanOrUndefined(raw.auto_sync),
    autoSyncIntervalMinutes:
      toNumberOrUndefined(raw.autoSyncIntervalMinutes) ??
      toNumberOrUndefined(raw.auto_sync_interval_minutes),
  };
}

function legacyMemSyncConfigPath(configPath: string): string {
  return join(configPath, "..", "sync-server.yaml");
}

export async function loadMemSyncConfig(
  configPath = defaultMemSyncConfigPath(),
): Promise<MemSyncConfig> {
  const candidatePaths = existsSync(configPath)
    ? [configPath]
    : [configPath, legacyMemSyncConfigPath(configPath)];

  for (const path of candidatePaths) {
    try {
      const content = await readFile(path, "utf8");
      const parsed = YAML.parse(content) as RawMemSyncConfig | null;
      return {
        ...defaultConfig(),
        ...normalizeMemSyncConfig(parsed),
      };
    } catch {
      continue;
    }
  }

  return defaultConfig();
}

export async function saveMemSyncConfig(
  config: MemSyncConfig,
  configPath = defaultMemSyncConfigPath(),
): Promise<void> {
  await mkdir(join(configPath, ".."), { recursive: true });
  await writeFile(configPath, YAML.stringify(config), "utf8");
}

function normalizeServerUrl(serverUrl: string): string {
  return serverUrl.replace(/\/+$/, "");
}

async function requestJson<T>(
  url: string,
  init: RequestInit,
  timeoutMs = 10_000,
): Promise<T | null> {
  try {
    const response = await fetch(url, {
      ...init,
      signal: AbortSignal.timeout(timeoutMs),
    });

    if (!response.ok) {
      return null;
    }

    return (await response.json()) as T;
  } catch {
    return null;
  }
}

function chunkArray<T>(items: T[], chunkSize: number): T[][] {
  const chunks: T[][] = [];
  for (let index = 0; index < items.length; index += chunkSize) {
    chunks.push(items.slice(index, index + chunkSize));
  }
  return chunks;
}

function readAllObservations(dbPath: string): Record<string, unknown>[] {
  if (!existsSync(dbPath)) {
    return [];
  }

  try {
    const db = openDb(dbPath, true);
    try {
      return db.query("SELECT * FROM observations ORDER BY id").all() as Record<
        string,
        unknown
      >[];
    } finally {
      db.close();
    }
  } catch {
    return [];
  }
}

function readRowsSince(
  dbPath: string,
  tableName: string,
  epochColumn: string,
  lastEpoch: number,
): Record<string, unknown>[] {
  if (!existsSync(dbPath)) {
    return [];
  }

  try {
    const db = openDb(dbPath, true);
    try {
      const tableExists = db
        .query(
          "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ? LIMIT 1",
        )
        .get(tableName) as { 1?: number } | null;
      if (!tableExists) {
        return [];
      }

      const columnRows = db.query(`PRAGMA table_info(${tableName})`).all() as {
        name: string;
      }[];
      const hasEpochColumn = columnRows.some((row) => row.name === epochColumn);
      if (!hasEpochColumn) {
        return db.query(`SELECT * FROM ${tableName}`).all() as Record<
          string,
          unknown
        >[];
      }

      return db
        .query(`SELECT * FROM ${tableName} WHERE ${epochColumn} > ?`)
        .all(lastEpoch) as Record<string, unknown>[];
    } finally {
      db.close();
    }
  } catch {
    return [];
  }
}

function pulledHashesPath(configPath = defaultMemSyncConfigPath()): string {
  return join(configPath, "..", PULLED_HASHES_FILENAME);
}

async function loadPulledHashes(
  configPath = defaultMemSyncConfigPath(),
): Promise<Set<string>> {
  try {
    const content = await readFile(pulledHashesPath(configPath), "utf8");
    return new Set(
      content
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter((line) => line.length > 0),
    );
  } catch {
    return new Set();
  }
}

async function appendPulledHashes(
  hashes: string[],
  configPath = defaultMemSyncConfigPath(),
): Promise<void> {
  const nextHashes = hashes
    .map((hash) => hash.trim())
    .filter((hash) => hash.length > 0);
  if (nextHashes.length === 0) {
    return;
  }

  const allHashes = await loadPulledHashes(configPath);
  let changed = false;
  for (const hash of nextHashes) {
    if (!allHashes.has(hash)) {
      allHashes.add(hash);
      changed = true;
    }
  }
  if (!changed) {
    return;
  }

  const filePath = pulledHashesPath(configPath);
  await mkdir(join(filePath, ".."), { recursive: true });
  await writeFile(filePath, `${Array.from(allHashes).join("\n")}\n`, "utf8");
}

function withSyncContentHash(
  observation: Record<string, unknown>,
): Record<string, unknown> {
  if (
    typeof observation.sync_content_hash === "string" &&
    observation.sync_content_hash.length > 0
  ) {
    return observation;
  }

  return {
    ...observation,
    sync_content_hash: computeContentHash({
      title: String(observation.title ?? ""),
      narrative: String(observation.narrative ?? ""),
      facts: String(observation.facts ?? ""),
      project: String(observation.project ?? ""),
      type: String(observation.type ?? ""),
    }),
  };
}

async function fetchMissingHashes(
  serverUrl: string,
  apiKey: string,
  hashes: string[],
): Promise<Set<string>> {
  const payload = await requestJson<{ missing?: string[] }>(
    `${normalizeServerUrl(serverUrl)}/api/sync/push-preflight`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey,
      },
      body: JSON.stringify({ hashes }),
    },
  );

  if (!payload?.missing) {
    return new Set(hashes);
  }

  return new Set(payload.missing);
}

function ensureObservationsTable(dbPath: string): void {
  const db = openDb(dbPath, false);
  try {
    db.run(
      `CREATE TABLE IF NOT EXISTS observations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        narrative TEXT,
        facts TEXT,
        project TEXT,
        type TEXT,
        content_hash TEXT,
        created_at TEXT,
        created_at_epoch INTEGER,
        sync_content_hash TEXT UNIQUE
      )`,
    );
  } finally {
    db.close();
  }
}

function upsertPulledObservations(
  dbPath: string,
  observations: Record<string, unknown>[],
): number {
  if (observations.length === 0) {
    return 0;
  }

  ensureObservationsTable(dbPath);

  const db = openDb(dbPath, false);
  try {
    const columnRows = db.query("PRAGMA table_info(observations)").all() as {
      name: string;
    }[];
    const availableColumns = new Set(columnRows.map((row) => row.name));
    let inserted = 0;

    for (const rawObservation of observations) {
      const observation = withSyncContentHash(rawObservation);
      const syncHash = String(observation.sync_content_hash ?? "");

      if (availableColumns.has("sync_content_hash") && syncHash.length > 0) {
        const existing = db
          .query(
            "SELECT 1 FROM observations WHERE sync_content_hash = ? LIMIT 1",
          )
          .get(syncHash) as { 1?: number } | null;
        if (existing) {
          continue;
        }
      }

      const columns = Object.keys(observation).filter(
        (key) =>
          key !== "id" &&
          availableColumns.has(key) &&
          observation[key] !== undefined,
      );

      if (columns.length === 0) {
        continue;
      }

      const placeholders = columns.map(() => "?").join(", ");
      const sql = `INSERT OR IGNORE INTO observations (${columns.join(", ")}) VALUES (${placeholders})`;
      const values = columns.map((column) => observation[column] ?? null);
      db.run(sql, ...values);
      inserted += 1;
    }

    return inserted;
  } finally {
    db.close();
  }
}

interface MemImportStats {
  sessionsImported: number;
  sessionsSkipped: number;
  observationsImported: number;
  observationsSkipped: number;
  summariesImported: number;
  summariesSkipped: number;
  promptsImported: number;
  promptsSkipped: number;
}

interface MemPullPayload {
  sessions: Record<string, unknown>[];
  observations: Record<string, unknown>[];
  summaries: Record<string, unknown>[];
  prompts: Record<string, unknown>[];
}

function zeroImportStats(): MemImportStats {
  return {
    sessionsImported: 0,
    sessionsSkipped: 0,
    observationsImported: 0,
    observationsSkipped: 0,
    summariesImported: 0,
    summariesSkipped: 0,
    promptsImported: 0,
    promptsSkipped: 0,
  };
}

function normalizeImportStats(
  stats: Partial<MemImportStats> | undefined,
): MemImportStats {
  const base = zeroImportStats();
  if (!stats) {
    return base;
  }

  return {
    sessionsImported:
      typeof stats.sessionsImported === "number" ? stats.sessionsImported : 0,
    sessionsSkipped:
      typeof stats.sessionsSkipped === "number" ? stats.sessionsSkipped : 0,
    observationsImported:
      typeof stats.observationsImported === "number"
        ? stats.observationsImported
        : 0,
    observationsSkipped:
      typeof stats.observationsSkipped === "number"
        ? stats.observationsSkipped
        : 0,
    summariesImported:
      typeof stats.summariesImported === "number" ? stats.summariesImported : 0,
    summariesSkipped:
      typeof stats.summariesSkipped === "number" ? stats.summariesSkipped : 0,
    promptsImported:
      typeof stats.promptsImported === "number" ? stats.promptsImported : 0,
    promptsSkipped:
      typeof stats.promptsSkipped === "number" ? stats.promptsSkipped : 0,
  };
}

function ensurePullImportTables(dbPath: string): void {
  const db = openDb(dbPath, false);
  try {
    db.run(
      `CREATE TABLE IF NOT EXISTS sdk_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content_session_id TEXT UNIQUE,
        memory_session_id TEXT,
        project TEXT,
        user_prompt TEXT,
        custom_title TEXT,
        started_at TEXT,
        started_at_epoch INTEGER,
        completed_at TEXT,
        completed_at_epoch INTEGER,
        status TEXT,
        worker_port INTEGER,
        prompt_counter INTEGER
      )`,
    );
    db.run(
      `CREATE TABLE IF NOT EXISTS session_summaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT UNIQUE,
        memory_session_id TEXT,
        project TEXT,
        request TEXT,
        investigated TEXT,
        learned TEXT,
        completed TEXT,
        next_steps TEXT,
        files_read TEXT,
        files_edited TEXT,
        notes TEXT,
        prompt_number INTEGER,
        discovery_tokens INTEGER,
        created_at TEXT,
        created_at_epoch INTEGER
      )`,
    );
    db.run(
      `CREATE TABLE IF NOT EXISTS user_prompts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content_session_id TEXT,
        project TEXT,
        prompt_number INTEGER,
        prompt_text TEXT,
        created_at TEXT,
        created_at_epoch INTEGER,
        UNIQUE(content_session_id, prompt_number)
      )`,
    );
  } finally {
    db.close();
  }
}

function tableColumns(db: ReturnType<typeof openDb>, tableName: string): Set<string> {
  try {
    const rows = db.query(`PRAGMA table_info(${tableName})`).all() as {
      name: string;
    }[];
    return new Set(rows.map((row) => row.name));
  } catch {
    return new Set();
  }
}

function insertRowWithAvailableColumns(
  db: ReturnType<typeof openDb>,
  tableName: string,
  row: Record<string, unknown>,
  availableColumns: Set<string>,
): boolean {
  const columns = Object.keys(row).filter(
    (key) => key !== "id" && availableColumns.has(key) && row[key] !== undefined,
  );
  if (columns.length === 0) {
    return false;
  }

  const placeholders = columns.map(() => "?").join(", ");
  const values = columns.map((column) => row[column] ?? null);
  try {
    db.run(
      `INSERT OR IGNORE INTO ${tableName} (${columns.join(", ")}) VALUES (${placeholders})`,
      ...values,
    );
    return true;
  } catch {
    return false;
  }
}

function rowExists(
  db: ReturnType<typeof openDb>,
  tableName: string,
  clauses: Array<{ column: string; value: unknown }>,
): boolean {
  const filtered = clauses.filter(
    ({ column, value }) =>
      column.trim().length > 0 && value !== undefined && value !== null,
  );
  if (filtered.length === 0) {
    return false;
  }

  const where = filtered.map(({ column }) => `${column} = ?`).join(" AND ");
  const values = filtered.map(({ value }) => value);
  try {
    const existing = db
      .query(`SELECT 1 FROM ${tableName} WHERE ${where} LIMIT 1`)
      .get(...values) as { 1?: number } | null;
    return existing !== null;
  } catch {
    return false;
  }
}

function importPulledDataWithSqlite(
  dbPath: string,
  payload: MemPullPayload,
): MemImportStats {
  ensurePullImportTables(dbPath);
  const stats = zeroImportStats();

  const db = openDb(dbPath, false);
  try {
    const sessionColumns = tableColumns(db, "sdk_sessions");
    const summaryColumns = tableColumns(db, "session_summaries");
    const promptColumns = tableColumns(db, "user_prompts");

    for (const rawSession of payload.sessions) {
      const session = rawSession as Record<string, unknown>;
      const sessionId = session.content_session_id;
      if (
        sessionColumns.has("content_session_id") &&
        rowExists(db, "sdk_sessions", [
          { column: "content_session_id", value: sessionId },
        ])
      ) {
        stats.sessionsSkipped += 1;
        continue;
      }

      if (insertRowWithAvailableColumns(db, "sdk_sessions", session, sessionColumns)) {
        stats.sessionsImported += 1;
      } else {
        stats.sessionsSkipped += 1;
      }
    }

    const importedObservations = upsertPulledObservations(
      dbPath,
      payload.observations,
    );
    stats.observationsImported += importedObservations;
    stats.observationsSkipped += payload.observations.length - importedObservations;

    for (const rawSummary of payload.summaries) {
      const summary = { ...rawSummary } as Record<string, unknown>;
      const summarySessionId =
        summary.session_id ?? summary.memory_session_id ?? null;

      if (summarySessionId !== null && summary.session_id === undefined) {
        summary.session_id = summarySessionId;
      }
      if (summarySessionId !== null && summary.memory_session_id === undefined) {
        summary.memory_session_id = summarySessionId;
      }

      const summaryChecks: Array<{ column: string; value: unknown }> = [];
      if (summaryColumns.has("session_id")) {
        summaryChecks.push({
          column: "session_id",
          value: summary.session_id,
        });
      }
      if (summaryChecks.length === 0 && summaryColumns.has("memory_session_id")) {
        summaryChecks.push({
          column: "memory_session_id",
          value: summary.memory_session_id,
        });
      }

      if (rowExists(db, "session_summaries", summaryChecks)) {
        stats.summariesSkipped += 1;
        continue;
      }

      if (
        insertRowWithAvailableColumns(
          db,
          "session_summaries",
          summary,
          summaryColumns,
        )
      ) {
        stats.summariesImported += 1;
      } else {
        stats.summariesSkipped += 1;
      }
    }

    for (const rawPrompt of payload.prompts) {
      const prompt = rawPrompt as Record<string, unknown>;
      const promptChecks: Array<{ column: string; value: unknown }> = [];
      if (
        promptColumns.has("content_session_id") &&
        promptColumns.has("prompt_number")
      ) {
        promptChecks.push({
          column: "content_session_id",
          value: prompt.content_session_id,
        });
        promptChecks.push({
          column: "prompt_number",
          value: prompt.prompt_number,
        });
      }

      if (rowExists(db, "user_prompts", promptChecks)) {
        stats.promptsSkipped += 1;
        continue;
      }

      if (
        insertRowWithAvailableColumns(db, "user_prompts", prompt, promptColumns)
      ) {
        stats.promptsImported += 1;
      } else {
        stats.promptsSkipped += 1;
      }
    }
  } finally {
    db.close();
  }

  return stats;
}

async function importPulledData(
  dbPath: string,
  payload: MemPullPayload,
): Promise<{ method: "api" | "sqlite"; stats: MemImportStats }> {
  const apiPayload = await requestJson<{ stats?: Partial<MemImportStats> }>(
    `${WORKER_URL}/api/import`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
    120_000,
  );

  if (apiPayload) {
    return {
      method: "api",
      stats: normalizeImportStats(apiPayload.stats),
    };
  }

  return {
    method: "sqlite",
    stats: importPulledDataWithSqlite(dbPath, payload),
  };
}

function countPendingObservations(
  dbPath: string,
  lastPushEpoch: number,
): number {
  if (!existsSync(dbPath)) {
    return 0;
  }

  try {
    const db = openDb(dbPath, true);
    try {
      const columnRows = db.query("PRAGMA table_info(observations)").all() as {
        name: string;
      }[];
      const hasEpochColumn = columnRows.some(
        (row) => row.name === "created_at_epoch",
      );

      if (!hasEpochColumn) {
        return (
          (
            db.query("SELECT COUNT(*) AS count FROM observations").get() as {
              count?: number;
            }
          ).count ?? 0
        );
      }

      return (
        (
          db
            .query(
              "SELECT COUNT(*) AS count FROM observations WHERE created_at_epoch > ?",
            )
            .get(lastPushEpoch) as {
            count?: number;
          }
        ).count ?? 0
      );
    } finally {
      db.close();
    }
  } catch {
    return 0;
  }
}

async function fetchRemoteStatus(
  serverUrl: string,
  apiKey: string,
): Promise<MemStatus["remoteStatus"]> {
  return await requestJson<MemStatus["remoteStatus"]>(
    `${normalizeServerUrl(serverUrl)}/api/sync/status`,
    {
      method: "GET",
      headers: {
        "X-API-Key": apiKey,
      },
    },
  );
}

function resolveScheduler(): "launchd" | "systemd" | "cron" {
  if (process.platform === "darwin") {
    return "launchd";
  }
  if (process.platform === "linux") {
    return "systemd";
  }
  return "cron";
}

// ---------------------------------------------------------------------------
// Scheduler installation helpers (launchd / cron) — parity with v1
// ---------------------------------------------------------------------------

const LAUNCHD_LABEL = "com.ai-dev.mem-sync";
const CRON_MARKER = "# ai-dev-mem-sync";

function launchdPlistPath(): string {
  return join(homedir(), "Library", "LaunchAgents", `${LAUNCHD_LABEL}.plist`);
}

function findAiDev(): string {
  try {
    return execSync("which ai-dev", { encoding: "utf-8" }).trim() || "ai-dev";
  } catch {
    return "ai-dev";
  }
}

async function installLaunchd(intervalMinutes: number): Promise<void> {
  const aiDev = findAiDev();
  const plist = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${LAUNCHD_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/sh</string>
        <string>-c</string>
        <string>${aiDev} mem push &amp;&amp; ${aiDev} mem pull</string>
    </array>
    <key>StartInterval</key>
    <integer>${intervalMinutes * 60}</integer>
    <key>StandardOutPath</key>
    <string>/tmp/ai-dev-mem-sync.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/ai-dev-mem-sync.log</string>
</dict>
</plist>
`;
  const plistPath = launchdPlistPath();
  await mkdir(join(plistPath, ".."), { recursive: true });
  await writeFile(plistPath, plist, "utf-8");
  try {
    execSync(`launchctl unload "${plistPath}"`, { stdio: "ignore" });
  } catch {
    // ignore if not loaded
  }
  try {
    execSync(`launchctl load "${plistPath}"`, { stdio: "ignore" });
  } catch {
    // ignore load errors
  }
}

async function removeLaunchd(): Promise<void> {
  const plistPath = launchdPlistPath();
  try {
    execSync(`launchctl unload "${plistPath}"`, { stdio: "ignore" });
  } catch {
    // ignore if not loaded
  }
  try {
    await unlink(plistPath);
  } catch {
    // ignore if not exists
  }
}

function installCron(intervalMinutes: number): void {
  const aiDev = findAiDev();
  const job = `*/${intervalMinutes} * * * * ${aiDev} mem push && ${aiDev} mem pull ${CRON_MARKER}`;
  let existing = "";
  try {
    existing = execSync("crontab -l", { encoding: "utf-8" });
  } catch {
    // no crontab
  }
  const lines = existing
    .split("\n")
    .filter((line) => !line.includes(CRON_MARKER));
  lines.push(job);
  const newCrontab = `${lines.join("\n")}\n`;
  execSync("crontab -", { input: newCrontab, encoding: "utf-8" });
}

function removeCron(): void {
  let existing = "";
  try {
    existing = execSync("crontab -l", { encoding: "utf-8" });
  } catch {
    return;
  }
  const lines = existing
    .split("\n")
    .filter((line) => !line.includes(CRON_MARKER));
  const newCrontab = `${lines.join("\n")}\n`;
  execSync("crontab -", { input: newCrontab, encoding: "utf-8" });
}

export async function configureAutoSync(
  options: {
    enable?: boolean;
    disable?: boolean;
    status?: boolean;
    intervalMinutes?: number;
    configPath?: string;
  } = {},
): Promise<MemAutoSyncResult> {
  const config = await loadMemSyncConfig(options.configPath);
  const scheduler = resolveScheduler();

  if (options.enable) {
    config.autoSync = true;
    if (options.intervalMinutes && options.intervalMinutes > 0) {
      config.autoSyncIntervalMinutes = options.intervalMinutes;
    }
    // Actually install the scheduler (launchd or cron)
    if (scheduler === "launchd") {
      await installLaunchd(config.autoSyncIntervalMinutes);
    } else {
      installCron(config.autoSyncIntervalMinutes);
    }
    await saveMemSyncConfig(config, options.configPath);
    return {
      enabled: true,
      scheduler,
      message: `Auto-sync enabled (${scheduler}) every ${config.autoSyncIntervalMinutes} minutes`,
    };
  }

  if (options.disable) {
    config.autoSync = false;
    // Actually remove the scheduler (launchd or cron)
    if (scheduler === "launchd") {
      await removeLaunchd();
    } else {
      removeCron();
    }
    await saveMemSyncConfig(config, options.configPath);
    return {
      enabled: false,
      scheduler,
      message: `Auto-sync disabled (${scheduler})`,
    };
  }

  return {
    enabled: config.autoSync,
    scheduler,
    message: config.autoSync
      ? `Auto-sync is enabled (${scheduler}) every ${config.autoSyncIntervalMinutes} minutes`
      : `Auto-sync is disabled (${scheduler})`,
  };
}

export async function registerDevice(options: {
  server: string;
  name: string;
  adminSecret: string;
  configPath?: string;
}): Promise<MemSyncConfig> {
  const config = await loadMemSyncConfig(options.configPath);
  config.serverUrl = normalizeServerUrl(options.server);
  config.deviceName = options.name;

  const payload = await requestJson<{
    api_key?: string;
    device_id?: number | string;
  }>(`${config.serverUrl}/api/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Admin-Secret": options.adminSecret,
    },
    body: JSON.stringify({ name: options.name }),
  });

  if (payload?.api_key) {
    config.apiKey = payload.api_key;
    config.deviceId = String(payload.device_id ?? "");
  } else {
    config.deviceId = randomUUID();
    config.apiKey = `local-${randomUUID()}`;
  }

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
  const sessions = readRowsSince(
    dbPath,
    "sdk_sessions",
    "started_at_epoch",
    config.lastPushEpoch,
  );
  const observations = readRowsSince(
    dbPath,
    "observations",
    "created_at_epoch",
    config.lastPushEpoch,
  ).map(withSyncContentHash);
  const summaries = readRowsSince(
    dbPath,
    "session_summaries",
    "created_at_epoch",
    config.lastPushEpoch,
  );
  const prompts = readRowsSince(
    dbPath,
    "user_prompts",
    "created_at_epoch",
    config.lastPushEpoch,
  );
  let pushed = 0;
  let skipped = 0;
  let errors = 0;

  const zeroCat = (): MemCategoryStats => ({
    sessions: 0,
    observations: 0,
    summaries: 0,
    prompts: 0,
  });
  const sent = zeroCat();
  const imported = zeroCat();
  const skippedDetail = zeroCat();
  const dedupExcluded = { pulled: 0, preflight: 0 };
  let latestServerEpoch: number | null = null;

  if (!config.serverUrl || !config.apiKey) {
    throw new Error("找不到 sync server 設定，請先執行 ai-dev mem register");
  }

  const hashes = observations
    .map((item) => String(item.sync_content_hash ?? ""))
    .filter((hash) => hash.length > 0);
  const missingHashes = await fetchMissingHashes(
    config.serverUrl,
    config.apiKey,
    hashes,
  );

  const toUpload = observations.filter((item) =>
    missingHashes.has(String(item.sync_content_hash ?? "")),
  );

  dedupExcluded.pulled = observations.length - hashes.length;
  dedupExcluded.preflight = hashes.length - missingHashes.size;
  sent.sessions = sessions.length;
  sent.observations = toUpload.length;
  sent.summaries = summaries.length;
  sent.prompts = prompts.length;

  const batches = chunkArray(toUpload, 100);
  if (batches.length === 0) {
    batches.push([]);
  }

  for (const [index, batch] of batches.entries()) {
    const payload = await requestJson<{
      server_epoch?: number;
      stats?: {
        sessionsImported?: number;
        observationsImported?: number;
        summariesImported?: number;
        promptsImported?: number;
        sessionsSkipped?: number;
        observationsSkipped?: number;
        summariesSkipped?: number;
        promptsSkipped?: number;
      };
    }>(
      `${normalizeServerUrl(config.serverUrl)}/api/sync/push`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": config.apiKey,
        },
        body: JSON.stringify({
          sessions: index === 0 ? sessions : [],
          summaries: index === 0 ? summaries : [],
          prompts: index === 0 ? prompts : [],
          observations: batch,
        }),
      },
      15_000,
    );

    if (!payload) {
      errors += batch.length;
      continue;
    }

    if (typeof payload.server_epoch === "number") {
      latestServerEpoch = payload.server_epoch;
    }

    const stats = payload.stats;
    if (stats?.observationsImported !== undefined) {
      pushed += stats.observationsImported;
      imported.sessions += stats.sessionsImported ?? 0;
      imported.observations += stats.observationsImported;
      imported.summaries += stats.summariesImported ?? 0;
      imported.prompts += stats.promptsImported ?? 0;
      skippedDetail.sessions += stats.sessionsSkipped ?? 0;
      skippedDetail.observations += stats.observationsSkipped ?? 0;
      skippedDetail.summaries += stats.summariesSkipped ?? 0;
      skippedDetail.prompts += stats.promptsSkipped ?? 0;
    } else {
      pushed += batch.length;
      imported.observations += batch.length;
    }
  }

  skipped = observations.length - toUpload.length;
  if (latestServerEpoch !== null) {
    config.lastPushEpoch = latestServerEpoch;
  }
  await saveMemSyncConfig(config, options.configPath);

  return {
    pushed,
    skipped,
    errors,
    serverUrl: config.serverUrl,
    sent,
    dedupExcluded,
    imported,
    skippedDetail,
  };
}

export async function pullMemData(
  options: { configPath?: string; dbPath?: string; chromaDbPath?: string } = {},
): Promise<MemPullResult> {
  const config = await loadMemSyncConfig(options.configPath);
  const dbPath = options.dbPath ?? defaultMemDbPath();
  const chromaDbPath = options.chromaDbPath ?? defaultChromaDbPath();

  let pulled = 0;
  let totalReceived = 0;
  let latestServerEpoch: number | null = null;

  const zeroCat = (): MemCategoryStats => ({
    sessions: 0,
    observations: 0,
    summaries: 0,
    prompts: 0,
  });
  const received = zeroCat();
  const imported = zeroCat();
  const skippedDetail = zeroCat();
  let importMethod: "api" | "sqlite" =
    config.serverUrl && config.apiKey ? "api" : "sqlite";
  const pulledData: MemPullPayload = {
    sessions: [],
    observations: [],
    summaries: [],
    prompts: [],
  };

  if (config.serverUrl && config.apiKey) {
    let since = config.lastPullEpoch > 0 ? config.lastPullEpoch * 1000 : 0;
    let hasMore = true;

    while (hasMore) {
      const payload = await requestJson<{
        sessions?: Record<string, unknown>[];
        observations?: Record<string, unknown>[];
        summaries?: Record<string, unknown>[];
        prompts?: Record<string, unknown>[];
        server_epoch?: number;
        has_more?: boolean;
        next_since?: number;
      }>(
        `${normalizeServerUrl(config.serverUrl)}/api/sync/pull?since=${since}&limit=100`,
        {
          method: "GET",
          headers: {
            "X-API-Key": config.apiKey,
          },
        },
        15_000,
      );

      if (!payload) {
        break;
      }

      const observations = payload.observations ?? [];
      const sessions = payload.sessions ?? [];
      const summaries = payload.summaries ?? [];
      const prompts = payload.prompts ?? [];
      if (typeof payload.server_epoch === "number") {
        latestServerEpoch = payload.server_epoch;
      }

      received.sessions += sessions.length;
      received.observations += observations.length;
      received.summaries += summaries.length;
      received.prompts += prompts.length;
      totalReceived += observations.length;

      pulledData.sessions.push(...sessions);
      pulledData.observations.push(...observations);
      pulledData.summaries.push(...summaries);
      pulledData.prompts.push(...prompts);

      hasMore = Boolean(payload.has_more);
      if (typeof payload.next_since === "number") {
        since = payload.next_since;
      } else {
        hasMore = false;
      }
    }

    if (
      pulledData.sessions.length > 0 ||
      pulledData.observations.length > 0 ||
      pulledData.summaries.length > 0 ||
      pulledData.prompts.length > 0
    ) {
      const importResult = await importPulledData(dbPath, pulledData);
      importMethod = importResult.method;
      const stats = importResult.stats;
      pulled += stats.observationsImported;
      imported.sessions += stats.sessionsImported;
      imported.observations += stats.observationsImported;
      imported.summaries += stats.summariesImported;
      imported.prompts += stats.promptsImported;
      skippedDetail.sessions += stats.sessionsSkipped;
      skippedDetail.observations += stats.observationsSkipped;
      skippedDetail.summaries += stats.summariesSkipped;
      skippedDetail.prompts += stats.promptsSkipped;

      const pulledHashes = pulledData.observations
        .map((row) => String(row.sync_content_hash ?? ""))
        .filter((hash) => hash.length > 0);
      await appendPulledHashes(pulledHashes, options.configPath);

      if (stats.observationsImported > 0 && (await workerAvailable())) {
        await reindexMemData({ dbPath, chromaDbPath });
      }
    }
  }

  if (latestServerEpoch !== null) {
    config.lastPullEpoch = latestServerEpoch;
  }
  await saveMemSyncConfig(config, options.configPath);

  return {
    pulled,
    skipped: totalReceived - pulled,
    serverUrl: config.serverUrl,
    importMethod,
    received,
    imported,
    skippedDetail,
  };
}

function countDuplicates(dbPath: string): number {
  if (!existsSync(dbPath)) return 0;
  try {
    const db = openDb(dbPath, true);
    try {
      const allObs = db
        .query(
          "SELECT id, title, narrative, facts, project, type FROM observations ORDER BY id",
        )
        .all() as ObservationRow[];

      const hashGroups = new Map<string, number>();
      let duplicates = 0;
      for (const obs of allObs) {
        const hash = computeContentHash(obs);
        const count = (hashGroups.get(hash) ?? 0) + 1;
        hashGroups.set(hash, count);
        if (count > 1) duplicates++;
      }
      return duplicates;
    } finally {
      db.close();
    }
  } catch {
    return 0;
  }
}

function countPulledHashes(dbPath: string): number {
  if (!existsSync(dbPath)) return 0;
  try {
    const db = openDb(dbPath, true);
    try {
      const row = db
        .query(
          "SELECT COUNT(*) AS count FROM observations WHERE sync_content_hash IS NOT NULL AND sync_content_hash != ''",
        )
        .get() as { count?: number };
      return row?.count ?? 0;
    } finally {
      db.close();
    }
  } catch {
    return 0;
  }
}

export async function getMemSyncStatus(
  options: { configPath?: string; dbPath?: string } = {},
): Promise<MemStatus> {
  const config = await loadMemSyncConfig(options.configPath);
  const dbPath = options.dbPath ?? defaultMemDbPath();

  let remoteStatus: MemStatus["remoteStatus"] = null;
  if (config.serverUrl && config.apiKey) {
    remoteStatus = await fetchRemoteStatus(config.serverUrl, config.apiKey);
  }

  return {
    config,
    localObservations: await countObservations(dbPath),
    localDuplicates: countDuplicates(dbPath),
    pulledHashesTracked: countPulledHashes(dbPath),
    pendingPushCount: countPendingObservations(dbPath, config.lastPushEpoch),
    remoteStatus,
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
  return createHash("sha256")
    .update(parts.join("\n"))
    .digest("hex")
    .slice(0, 32);
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
  if (readonly) {
    return new sqlite.Database(dbPath, { readonly: true, create: false });
  }
  return new sqlite.Database(dbPath);
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
    return new Set(
      rows.map((r) => r.int_value).filter((v): v is number => v != null),
    );
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
 *
 * 兩輪去重：
 * 1. content hash 分組（精確重複）
 * 2. text+project 分組（抓原始 vs worker 副本，因副本缺少 facts/type 導致 hash 不同）
 *
 * 優先保留已被 ChromaDB 索引的記錄；若都未索引則保留最小 ID。
 */
export async function cleanupDuplicates(
  options: { dbPath?: string; chromaDbPath?: string } = {},
): Promise<MemCleanupResult> {
  const dbPath = options.dbPath ?? defaultMemDbPath();
  if (!existsSync(dbPath)) return { duplicatesRemoved: 0 };

  const chromaDbPath = options.chromaDbPath ?? defaultChromaDbPath();
  const indexedIds = getIndexedObservationIds(chromaDbPath);

  const db = openDb(dbPath, true);
  let allObs: Array<ObservationRow & { text?: string }>;
  try {
    try {
      allObs = db
        .query(
          "SELECT id, title, narrative, text, facts, project, type FROM observations ORDER BY id",
        )
        .all() as Array<ObservationRow & { text?: string }>;
    } catch {
      // text 欄位可能不存在（舊版 schema）
      allObs = db
        .query(
          "SELECT id, title, narrative, facts, project, type FROM observations ORDER BY id",
        )
        .all() as Array<ObservationRow & { text?: string }>;
    }
  } finally {
    db.close();
  }

  // Phase 1: content hash 分組（精確重複）
  const hashGroups = new Map<string, number[]>();
  for (const obs of allObs) {
    const hash = computeContentHash(obs);
    const group = hashGroups.get(hash);
    if (group) group.push(obs.id);
    else hashGroups.set(hash, [obs.id]);
  }

  const duplicateIds: number[] = [];
  for (const ids of hashGroups.values()) {
    if (ids.length <= 1) continue;
    const indexedInGroup = ids.filter((id) => indexedIds.has(id));
    const keep = indexedInGroup.length > 0 ? indexedInGroup[0] : ids[0];
    duplicateIds.push(...ids.filter((id) => id !== keep));
  }

  // Phase 2: text+project 分組（原始 vs worker 副本）
  // Worker save 建立的副本只有 text/title/project，缺少 facts/type，
  // 導致 content hash 不同。用主文字內容 + project 做二次分組。
  const deleteSet = new Set(duplicateIds);
  const textGroups = new Map<string, number[]>();
  for (const obs of allObs) {
    if (deleteSet.has(obs.id)) continue;
    const text = (
      (obs as any).narrative ||
      (obs as any).text ||
      obs.title ||
      ""
    ).trim();
    if (!text) continue;
    const key = `${text}\0${obs.project ?? ""}`;
    const group = textGroups.get(key);
    if (group) group.push(obs.id);
    else textGroups.set(key, [obs.id]);
  }

  for (const ids of textGroups.values()) {
    if (ids.length <= 1) continue;
    const indexedInGroup = ids.filter((id) => indexedIds.has(id));
    const keep = indexedInGroup.length > 0 ? indexedInGroup[0] : ids[0];
    duplicateIds.push(...ids.filter((id) => id !== keep));
  }

  if (duplicateIds.length === 0) return { duplicatesRemoved: 0 };

  const writeDb = openDb(dbPath, false);
  try {
    const placeholders = duplicateIds.map(() => "?").join(",");
    writeDb.run(
      `DELETE FROM observations WHERE id IN (${placeholders})`,
      ...duplicateIds,
    );
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
    return { total: 0, missing: 0, synced: 0, errors: 0, duplicatesRemoved: 0 };
  }

  if (!(await workerAvailable())) {
    const total = await countObservations(dbPath);
    return { total, missing: 0, synced: 0, errors: 0, duplicatesRemoved: 0 };
  }

  const indexedIds = getIndexedObservationIds(chromaDbPath);

  const db = openDb(dbPath, true);
  let allObs: Array<ObservationRow & { text?: string }>;
  try {
    try {
      allObs = db
        .query(
          "SELECT id, title, narrative, text, facts, project, type FROM observations ORDER BY id",
        )
        .all() as Array<ObservationRow & { text?: string }>;
    } catch {
      allObs = db
        .query(
          "SELECT id, title, narrative, facts, project, type FROM observations ORDER BY id",
        )
        .all() as Array<ObservationRow & { text?: string }>;
    }
  } finally {
    db.close();
  }

  // 用「reindex 實際送出的 text」判斷該內容是否已有索引
  // 防止 narrative=null 的原始記錄和 narrative=title 的副本被視為不同
  const indexedTexts = new Set<string>();
  for (const obs of allObs) {
    if (!indexedIds.has(obs.id)) continue;
    const text = (
      (obs as any).narrative ||
      (obs as any).text ||
      obs.title ||
      ""
    ).trim();
    if (text) indexedTexts.add(text);
  }

  const missingObs: typeof allObs = [];
  for (const obs of allObs) {
    if (indexedIds.has(obs.id)) continue;
    const text = (
      (obs as any).narrative ||
      (obs as any).text ||
      obs.title ||
      ""
    ).trim();
    if (!text) continue;
    if (indexedTexts.has(text)) continue; // 該內容已透過其他記錄被索引
    missingObs.push(obs);
  }

  let synced = 0;
  let errors = 0;

  for (const obs of missingObs) {
    const text = (obs as any).narrative || (obs as any).text || obs.title || "";

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
      if (resp.ok) {
        synced++;
        // 將已同步的文字加入 indexedTexts，防止同一 session 內重複偵測
        // 同時防止跨呼叫循環：worker 建立副本 → cleanup 保留已索引副本 → 原始記錄被刪除
        indexedTexts.add(text.trim());
      } else {
        errors++;
      }
    } catch {
      errors++;
    }
  }

  // reindex 透過 worker /api/memory/save 會建立副本，自動清理
  let duplicatesRemoved = 0;
  if (synced > 0) {
    const cleanupResult = await cleanupDuplicates({ dbPath, chromaDbPath });
    duplicatesRemoved = cleanupResult.duplicatesRemoved;
  }

  return {
    total: allObs.length,
    missing: missingObs.length,
    synced,
    errors,
    duplicatesRemoved,
  };
}
