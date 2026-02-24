# claude-mem Sync Server 實作計畫

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 自架 Thin Relay sync server，讓 claude-mem 資料安全地跨多台機器同步。

**Architecture:** Docker Compose 部署 Bun/Express API server + PostgreSQL 18。Client 端整合到 ai-dev CLI 的 `ai-dev mem` 子命令，透過 HTTP API push/pull 資料，利用 claude-mem 現有 `/api/import` 的 dedup 機制。

**Tech Stack:** Bun, Express, pg (node-postgres), PostgreSQL 18, Docker Compose, Python (ai-dev CLI client)

**設計文件：** `docs/plans/2026-02-24-claude-mem-sync-server-design.md`

---

## Phase 1: Server — Docker Compose + PostgreSQL + API

### Task 1: 專案骨架與 Docker Compose

**Files:**
- Create: `services/claude-mem-sync/docker-compose.yml`
- Create: `services/claude-mem-sync/.env.example`
- Create: `services/claude-mem-sync/server/package.json`
- Create: `services/claude-mem-sync/server/tsconfig.json`
- Create: `services/claude-mem-sync/server/Dockerfile`
- Create: `services/claude-mem-sync/.gitignore`

**Step 1: 建立 docker-compose.yml**

```yaml
services:
  postgres:
    image: postgres:18-alpine
    environment:
      POSTGRES_DB: claude_mem_sync
      POSTGRES_USER: ${DB_USER:-claude_mem}
      POSTGRES_PASSWORD: ${DB_PASSWORD:?DB_PASSWORD is required}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-claude_mem}"]
      interval: 5s
      retries: 5

  server:
    build: ./server
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgres://${DB_USER:-claude_mem}:${DB_PASSWORD}@postgres:5432/claude_mem_sync
      ADMIN_SECRET: ${ADMIN_SECRET:?ADMIN_SECRET is required}
      PORT: ${PORT:-3000}
    ports:
      - "${PORT:-3000}:${PORT:-3000}"

volumes:
  pgdata:
```

**Step 2: 建立 .env.example**

```env
DB_USER=claude_mem
DB_PASSWORD=change-me-to-strong-password
ADMIN_SECRET=change-me-to-admin-secret
PORT=3000
```

**Step 3: 建立 package.json**

```json
{
  "name": "claude-mem-sync-server",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "bun run --watch src/index.ts",
    "start": "bun run src/index.ts",
    "migrate": "bun run src/migrate.ts",
    "test": "bun test"
  },
  "dependencies": {
    "express": "^5.1.0",
    "pg": "^8.16.0"
  },
  "devDependencies": {
    "@types/express": "^5.0.0",
    "@types/pg": "^8.11.0",
    "typescript": "^5.7.0",
    "@types/bun": "latest"
  }
}
```

**Step 4: 建立 tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "types": ["bun"]
  },
  "include": ["src"]
}
```

**Step 5: 建立 Dockerfile**

```dockerfile
FROM oven/bun:1-alpine

WORKDIR /app
COPY package.json bun.lock* ./
RUN bun install --frozen-lockfile --production
COPY . .

EXPOSE 3000
CMD ["bun", "run", "src/index.ts"]
```

**Step 6: 建立 .gitignore**

```
node_modules/
dist/
.env
*.log
```

**Step 7: Commit**

```bash
git add services/claude-mem-sync/
git commit -m "功能(mem-sync): 建立專案骨架與 Docker Compose"
```

---

### Task 2: PostgreSQL Migration

**Files:**
- Create: `services/claude-mem-sync/server/src/migrate.ts`
- Create: `services/claude-mem-sync/server/migrations/001_init.sql`

**Step 1: 建立 001_init.sql**

完整 SQL 來自設計文件的 Schema 章節（devices + 4 張資料表 + 索引）。

```sql
-- 裝置註冊表
CREATE TABLE IF NOT EXISTS devices (
  id          SERIAL PRIMARY KEY,
  api_key_hash TEXT UNIQUE NOT NULL,
  name        TEXT NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sdk_sessions (
  id                  SERIAL PRIMARY KEY,
  content_session_id  TEXT UNIQUE NOT NULL,
  memory_session_id   TEXT UNIQUE,
  project             TEXT NOT NULL,
  user_prompt         TEXT,
  custom_title        TEXT,
  started_at          TEXT NOT NULL,
  started_at_epoch    BIGINT NOT NULL,
  completed_at        TEXT,
  completed_at_epoch  BIGINT,
  status              TEXT NOT NULL DEFAULT 'active',
  worker_port         INTEGER,
  prompt_counter      INTEGER DEFAULT 0,
  origin_device_id    INTEGER REFERENCES devices(id),
  synced_at           TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS observations (
  id                  SERIAL PRIMARY KEY,
  memory_session_id   TEXT NOT NULL REFERENCES sdk_sessions(memory_session_id),
  project             TEXT NOT NULL,
  type                TEXT NOT NULL,
  title               TEXT,
  subtitle            TEXT,
  narrative           TEXT,
  text                TEXT,
  facts               TEXT,
  concepts            TEXT,
  files_read          TEXT,
  files_modified      TEXT,
  prompt_number       INTEGER,
  content_hash        TEXT,
  created_at          TEXT NOT NULL,
  created_at_epoch    BIGINT NOT NULL,
  origin_device_id    INTEGER REFERENCES devices(id),
  synced_at           TIMESTAMPTZ DEFAULT now(),
  UNIQUE(memory_session_id, title, created_at_epoch)
);

CREATE TABLE IF NOT EXISTS session_summaries (
  id                  SERIAL PRIMARY KEY,
  session_id          TEXT UNIQUE NOT NULL,
  request             TEXT,
  investigated        TEXT,
  learned             TEXT,
  completed           TEXT,
  next_steps          TEXT,
  project             TEXT,
  files_read          TEXT,
  files_edited        TEXT,
  notes               TEXT,
  prompt_number       INTEGER,
  discovery_tokens    INTEGER DEFAULT 0,
  created_at          TEXT NOT NULL,
  created_at_epoch    BIGINT NOT NULL,
  origin_device_id    INTEGER REFERENCES devices(id),
  synced_at           TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_prompts (
  id                  SERIAL PRIMARY KEY,
  content_session_id  TEXT NOT NULL,
  project             TEXT,
  prompt_number       INTEGER NOT NULL,
  prompt_text         TEXT,
  created_at          TEXT NOT NULL,
  created_at_epoch    BIGINT NOT NULL,
  origin_device_id    INTEGER REFERENCES devices(id),
  synced_at           TIMESTAMPTZ DEFAULT now(),
  UNIQUE(content_session_id, prompt_number)
);

CREATE INDEX IF NOT EXISTS idx_sessions_synced    ON sdk_sessions(synced_at);
CREATE INDEX IF NOT EXISTS idx_observations_synced ON observations(synced_at);
CREATE INDEX IF NOT EXISTS idx_summaries_synced   ON session_summaries(synced_at);
CREATE INDEX IF NOT EXISTS idx_prompts_synced     ON user_prompts(synced_at);
```

**Step 2: 建立 migrate.ts**

```typescript
import { Pool } from "pg";
import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));

async function migrate() {
  const pool = new Pool({ connectionString: process.env.DATABASE_URL });
  const sql = readFileSync(join(__dirname, "../migrations/001_init.sql"), "utf-8");
  await pool.query(sql);
  console.log("Migration complete");
  await pool.end();
}

migrate().catch((err) => {
  console.error("Migration failed:", err);
  process.exit(1);
});
```

**Step 3: Commit**

```bash
git add services/claude-mem-sync/server/migrations/ services/claude-mem-sync/server/src/migrate.ts
git commit -m "功能(mem-sync): PostgreSQL schema migration"
```

---

### Task 3: Server 核心 — config, db, health

**Files:**
- Create: `services/claude-mem-sync/server/src/index.ts`
- Create: `services/claude-mem-sync/server/src/config.ts`
- Create: `services/claude-mem-sync/server/src/db.ts`
- Create: `services/claude-mem-sync/server/src/routes/health.ts`

**Step 1: 建立 config.ts**

```typescript
export const config = {
  port: parseInt(process.env.PORT || "3000", 10),
  databaseUrl: process.env.DATABASE_URL || "",
  adminSecret: process.env.ADMIN_SECRET || "",
};
```

**Step 2: 建立 db.ts**

```typescript
import { Pool } from "pg";
import { config } from "./config.js";

export const pool = new Pool({ connectionString: config.databaseUrl });
```

**Step 3: 建立 routes/health.ts**

```typescript
import { Router } from "express";
import { pool } from "../db.js";

const router = Router();

router.get("/api/health", async (_req, res) => {
  try {
    await pool.query("SELECT 1");
    res.json({ status: "ok" });
  } catch {
    res.status(503).json({ status: "error", message: "database unavailable" });
  }
});

export default router;
```

**Step 4: 建立 index.ts**

```typescript
import express from "express";
import { config } from "./config.js";
import { pool } from "./db.js";
import healthRoutes from "./routes/health.js";

// 啟動時自動執行 migration
import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));

const app = express();
app.use(express.json({ limit: "50mb" }));
app.use(healthRoutes);

async function start() {
  const migrationSql = readFileSync(
    join(__dirname, "../migrations/001_init.sql"),
    "utf-8"
  );
  await pool.query(migrationSql);
  console.log("Database migration applied");

  app.listen(config.port, () => {
    console.log(`claude-mem-sync-server listening on :${config.port}`);
  });
}

start().catch((err) => {
  console.error("Failed to start:", err);
  process.exit(1);
});

export { app };
```

**Step 5: 啟動測試**

```bash
cd services/claude-mem-sync
cp .env.example .env  # 編輯密碼
docker compose up --build
# 另一個 terminal:
curl http://localhost:3000/api/health
# Expected: {"status":"ok"}
```

**Step 6: Commit**

```bash
git add services/claude-mem-sync/server/src/
git commit -m "功能(mem-sync): Server 核心 — config, db pool, health endpoint"
```

---

### Task 4: Auth — 裝置註冊與 API Key 驗證

**Files:**
- Create: `services/claude-mem-sync/server/src/middleware/auth.ts`
- Create: `services/claude-mem-sync/server/src/routes/auth.ts`

**Step 1: 建立 middleware/auth.ts**

```typescript
import { Request, Response, NextFunction } from "express";
import { createHash } from "crypto";
import { pool } from "../db.js";

export function hashApiKey(key: string): string {
  return createHash("sha256").update(key).digest("hex");
}

export async function requireApiKey(req: Request, res: Response, next: NextFunction) {
  const apiKey = req.headers["x-api-key"] as string;
  if (!apiKey) {
    res.status(401).json({ error: "Missing X-API-Key header" });
    return;
  }

  const hash = hashApiKey(apiKey);
  const result = await pool.query(
    "SELECT id, name FROM devices WHERE api_key_hash = $1",
    [hash]
  );

  if (result.rows.length === 0) {
    res.status(401).json({ error: "Invalid API key" });
    return;
  }

  (req as any).device = result.rows[0];
  next();
}
```

**Step 2: 建立 routes/auth.ts**

```typescript
import { Router } from "express";
import { randomBytes } from "crypto";
import { pool } from "../db.js";
import { config } from "../config.js";
import { hashApiKey } from "../middleware/auth.js";

const router = Router();

router.post("/api/auth/register", async (req, res) => {
  const adminSecret = req.headers["x-admin-secret"] as string;
  if (!adminSecret || adminSecret !== config.adminSecret) {
    res.status(403).json({ error: "Invalid admin secret" });
    return;
  }

  const { name } = req.body;
  if (!name || typeof name !== "string") {
    res.status(400).json({ error: "name is required" });
    return;
  }

  const apiKey = `cm_sync_${randomBytes(16).toString("hex")}`;
  const hash = hashApiKey(apiKey);

  const result = await pool.query(
    "INSERT INTO devices (api_key_hash, name) VALUES ($1, $2) RETURNING id",
    [hash, name]
  );

  res.json({ api_key: apiKey, device_id: result.rows[0].id, name });
});

export default router;
```

**Step 3: 註冊 routes 到 index.ts**

在 `index.ts` 加入：
```typescript
import authRoutes from "./routes/auth.js";
app.use(authRoutes);
```

**Step 4: 測試註冊**

```bash
curl -X POST http://localhost:3000/api/auth/register \
  -H "Content-Type: application/json" \
  -H "X-Admin-Secret: <your-admin-secret>" \
  -d '{"name": "test-device"}'
# Expected: {"api_key":"cm_sync_...","device_id":1,"name":"test-device"}
```

**Step 5: Commit**

```bash
git add services/claude-mem-sync/server/src/middleware/ services/claude-mem-sync/server/src/routes/auth.ts
git commit -m "功能(mem-sync): 裝置註冊與 API Key 認證 middleware"
```

---

### Task 5: Sync Routes — push, pull, status

**Files:**
- Create: `services/claude-mem-sync/server/src/routes/sync.ts`

**Step 1: 建立 routes/sync.ts**

這是核心檔案，包含 push / pull / status 三個端點。

```typescript
import { Router, Request, Response } from "express";
import { pool } from "../db.js";
import { requireApiKey } from "../middleware/auth.js";

const router = Router();
router.use(requireApiKey);

// ─── POST /api/sync/push ───
router.post("/api/sync/push", async (req: Request, res: Response) => {
  const device = (req as any).device;
  const { sessions = [], observations = [], summaries = [], prompts = [] } = req.body;

  const client = await pool.connect();
  try {
    await client.query("BEGIN");

    const stats = {
      sessionsImported: 0, sessionsSkipped: 0,
      observationsImported: 0, observationsSkipped: 0,
      summariesImported: 0, summariesSkipped: 0,
      promptsImported: 0, promptsSkipped: 0,
    };

    // sessions first (FK parent)
    for (const s of sessions) {
      const r = await client.query(
        `INSERT INTO sdk_sessions
          (content_session_id, memory_session_id, project, user_prompt, custom_title,
           started_at, started_at_epoch, completed_at, completed_at_epoch,
           status, worker_port, prompt_counter, origin_device_id)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
         ON CONFLICT (content_session_id) DO NOTHING`,
        [s.content_session_id, s.memory_session_id, s.project, s.user_prompt,
         s.custom_title, s.started_at, s.started_at_epoch, s.completed_at,
         s.completed_at_epoch, s.status || "active", s.worker_port,
         s.prompt_counter, device.id]
      );
      if (r.rowCount && r.rowCount > 0) stats.sessionsImported++;
      else stats.sessionsSkipped++;
    }

    // observations
    for (const o of observations) {
      const r = await client.query(
        `INSERT INTO observations
          (memory_session_id, project, type, title, subtitle, narrative, text,
           facts, concepts, files_read, files_modified, prompt_number,
           content_hash, created_at, created_at_epoch, origin_device_id)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16)
         ON CONFLICT (memory_session_id, title, created_at_epoch) DO NOTHING`,
        [o.memory_session_id, o.project, o.type, o.title, o.subtitle,
         o.narrative, o.text, o.facts, o.concepts, o.files_read,
         o.files_modified, o.prompt_number, o.content_hash,
         o.created_at, o.created_at_epoch, device.id]
      );
      if (r.rowCount && r.rowCount > 0) stats.observationsImported++;
      else stats.observationsSkipped++;
    }

    // summaries
    for (const s of summaries) {
      const r = await client.query(
        `INSERT INTO session_summaries
          (session_id, request, investigated, learned, completed, next_steps,
           project, files_read, files_edited, notes, prompt_number,
           discovery_tokens, created_at, created_at_epoch, origin_device_id)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
         ON CONFLICT (session_id) DO NOTHING`,
        [s.session_id, s.request, s.investigated, s.learned, s.completed,
         s.next_steps, s.project, s.files_read, s.files_edited, s.notes,
         s.prompt_number, s.discovery_tokens, s.created_at,
         s.created_at_epoch, device.id]
      );
      if (r.rowCount && r.rowCount > 0) stats.summariesImported++;
      else stats.summariesSkipped++;
    }

    // prompts
    for (const p of prompts) {
      const r = await client.query(
        `INSERT INTO user_prompts
          (content_session_id, project, prompt_number, prompt_text,
           created_at, created_at_epoch, origin_device_id)
         VALUES ($1,$2,$3,$4,$5,$6,$7)
         ON CONFLICT (content_session_id, prompt_number) DO NOTHING`,
        [p.content_session_id, p.project, p.prompt_number, p.prompt_text,
         p.created_at, p.created_at_epoch, device.id]
      );
      if (r.rowCount && r.rowCount > 0) stats.promptsImported++;
      else stats.promptsSkipped++;
    }

    await client.query("COMMIT");
    res.json({ success: true, stats, server_epoch: Date.now() });
  } catch (err: any) {
    await client.query("ROLLBACK");
    res.status(500).json({ error: err.message });
  } finally {
    client.release();
  }
});

// ─── GET /api/sync/pull ───
router.get("/api/sync/pull", async (req: Request, res: Response) => {
  const device = (req as any).device;
  const since = req.query.since ? new Date(Number(req.query.since)).toISOString() : new Date(0).toISOString();
  const limit = Math.min(Number(req.query.limit) || 500, 1000);

  // 排除自己推送的資料
  const deviceFilter = "AND origin_device_id IS DISTINCT FROM $2";

  const [sessions, observations, summaries, prompts] = await Promise.all([
    pool.query(
      `SELECT * FROM sdk_sessions WHERE synced_at > $1 ${deviceFilter}
       ORDER BY synced_at LIMIT $3`,
      [since, device.id, limit]
    ),
    pool.query(
      `SELECT * FROM observations WHERE synced_at > $1 ${deviceFilter}
       ORDER BY synced_at LIMIT $3`,
      [since, device.id, limit]
    ),
    pool.query(
      `SELECT * FROM session_summaries WHERE synced_at > $1 ${deviceFilter}
       ORDER BY synced_at LIMIT $3`,
      [since, device.id, limit]
    ),
    pool.query(
      `SELECT * FROM user_prompts WHERE synced_at > $1 ${deviceFilter}
       ORDER BY synced_at LIMIT $3`,
      [since, device.id, limit]
    ),
  ]);

  const hasMore = [sessions, observations, summaries, prompts]
    .some((r) => r.rows.length >= limit);

  // 計算 next_since：所有結果中最大的 synced_at
  let maxSyncedAt = since;
  for (const result of [sessions, observations, summaries, prompts]) {
    for (const row of result.rows) {
      if (row.synced_at > maxSyncedAt) maxSyncedAt = row.synced_at;
    }
  }

  res.json({
    sessions: sessions.rows,
    observations: observations.rows,
    summaries: summaries.rows,
    prompts: prompts.rows,
    has_more: hasMore,
    next_since: new Date(maxSyncedAt).getTime(),
    server_epoch: Date.now(),
  });
});

// ─── GET /api/sync/status ───
router.get("/api/sync/status", async (_req: Request, res: Response) => {
  const counts = await pool.query(`
    SELECT
      (SELECT COUNT(*) FROM sdk_sessions)::int AS sessions,
      (SELECT COUNT(*) FROM observations)::int AS observations,
      (SELECT COUNT(*) FROM session_summaries)::int AS summaries,
      (SELECT COUNT(*) FROM user_prompts)::int AS prompts,
      (SELECT COUNT(*) FROM devices)::int AS devices
  `);
  res.json(counts.rows[0]);
});

export default router;
```

**Step 2: 註冊 sync routes 到 index.ts**

```typescript
import syncRoutes from "./routes/sync.js";
app.use(syncRoutes);
```

**Step 3: End-to-end 測試（手動）**

```bash
# Register device
API_KEY=$(curl -s -X POST http://localhost:3000/api/auth/register \
  -H "Content-Type: application/json" \
  -H "X-Admin-Secret: <secret>" \
  -d '{"name":"test"}' | jq -r .api_key)

# Push test data
curl -s -X POST http://localhost:3000/api/sync/push \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"sessions":[{"content_session_id":"test-001","memory_session_id":"mem-001","project":"test","started_at":"2026-02-24T00:00:00Z","started_at_epoch":1771855200000,"status":"completed"}],"observations":[],"summaries":[],"prompts":[]}'
# Expected: {"success":true,"stats":{"sessionsImported":1,...}}

# Pull (should be empty since same device)
curl -s "http://localhost:3000/api/sync/pull?since=0" \
  -H "X-API-Key: $API_KEY"
# Expected: sessions=[], observations=[] (filtered out own data)

# Status
curl -s http://localhost:3000/api/sync/status -H "X-API-Key: $API_KEY"
# Expected: {"sessions":1,"observations":0,...}
```

**Step 4: Commit**

```bash
git add services/claude-mem-sync/server/src/routes/sync.ts
git commit -m "功能(mem-sync): push / pull / status 同步端點"
```

---

## Phase 2: Client — ai-dev CLI 整合

### Task 6: sync-server 設定檔管理

**Files:**
- Create: `script/utils/mem_sync.py`

**Step 1: 建立 mem_sync.py**

管理 `~/.config/ai-dev/sync-server.yaml` 設定檔和 HTTP 呼叫。

```python
"""claude-mem sync server 客戶端工具函式。"""
from __future__ import annotations

import json
import sqlite3
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

import yaml

from .paths import get_ai_dev_config_dir

SYNC_SERVER_CONFIG_NAME = "sync-server.yaml"
CLAUDE_MEM_DB_PATH = Path("~/.claude-mem/claude-mem.db").expanduser()


def get_server_config_path() -> Path:
    return get_ai_dev_config_dir() / SYNC_SERVER_CONFIG_NAME


def load_server_config() -> dict[str, Any]:
    path = get_server_config_path()
    if not path.exists():
        raise FileNotFoundError(
            f"找不到 sync server 設定：{path}。請先執行 `ai-dev mem register`"
        )
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_server_config(config: dict[str, Any]) -> None:
    path = get_server_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def api_request(
    config: dict[str, Any],
    method: str,
    path: str,
    body: dict | None = None,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """對 sync server 發送 HTTP 請求。"""
    url = f"{config['server_url'].rstrip('/')}{path}"
    headers = {"Content-Type": "application/json"}
    if config.get("api_key"):
        headers["X-API-Key"] = config["api_key"]
    if extra_headers:
        headers.update(extra_headers)

    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {error_body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Server 不可達: {e.reason}") from e


def query_local_db(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    """唯讀查詢本地 claude-mem SQLite。"""
    db_path = CLAUDE_MEM_DB_PATH
    if not db_path.exists():
        return []
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
```

**Step 2: Commit**

```bash
git add script/utils/mem_sync.py
git commit -m "功能(mem-sync): sync server 客戶端工具函式"
```

---

### Task 7: ai-dev mem 子命令 — register, push, pull, status

**Files:**
- Create: `script/commands/mem.py`
- Modify: `script/main.py` — 註冊 `mem` 子命令

**Step 1: 建立 script/commands/mem.py**

```python
"""ai-dev mem — claude-mem sync server 客戶端指令。"""
from __future__ import annotations

from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from ..utils.mem_sync import (
    api_request,
    load_server_config,
    query_local_db,
    save_server_config,
)

app = typer.Typer(help="管理 claude-mem 跨裝置同步（HTTP API backend）")
console = Console()


@app.command()
def register(
    server: str = typer.Option(..., "--server", help="Sync server URL"),
    name: str = typer.Option(..., "--name", help="裝置名稱"),
    admin_secret: str = typer.Option(..., "--admin-secret", help="Admin secret"),
) -> None:
    """向 sync server 註冊本裝置。"""
    config: dict[str, Any] = {"server_url": server}
    result = api_request(
        config,
        "POST",
        "/api/auth/register",
        body={"name": name},
        extra_headers={"X-Admin-Secret": admin_secret},
    )
    config.update({
        "api_key": result["api_key"],
        "device_name": name,
        "device_id": result["device_id"],
        "last_push_epoch": 0,
        "last_pull_epoch": 0,
        "auto_sync": False,
        "auto_sync_interval_minutes": 10,
    })
    save_server_config(config)
    console.print(f"[bold green]註冊成功[/bold green] device_id={result['device_id']}")


@app.command()
def push() -> None:
    """推送本地 claude-mem 新資料到 sync server。"""
    config = load_server_config()
    last_epoch = config.get("last_push_epoch", 0)

    sessions = query_local_db(
        "SELECT * FROM sdk_sessions WHERE started_at_epoch > ?", (last_epoch,)
    )
    observations = query_local_db(
        "SELECT * FROM observations WHERE created_at_epoch > ?", (last_epoch,)
    )
    summaries = query_local_db(
        "SELECT * FROM session_summaries WHERE created_at_epoch > ?", (last_epoch,)
    )
    prompts = query_local_db(
        "SELECT * FROM user_prompts WHERE created_at_epoch > ?", (last_epoch,)
    )

    total = len(sessions) + len(observations) + len(summaries) + len(prompts)
    if total == 0:
        console.print("[green]無新資料需要推送[/green]")
        return

    console.print(
        f"[cyan]推送中：{len(sessions)} sessions, {len(observations)} observations, "
        f"{len(summaries)} summaries, {len(prompts)} prompts[/cyan]"
    )

    result = api_request(config, "POST", "/api/sync/push", body={
        "sessions": sessions,
        "observations": observations,
        "summaries": summaries,
        "prompts": prompts,
    })

    config["last_push_epoch"] = result["server_epoch"]
    save_server_config(config)

    stats = result.get("stats", {})
    console.print(
        f"[bold green]Push 完成[/bold green] "
        f"imported: {stats.get('sessionsImported', 0)}s "
        f"{stats.get('observationsImported', 0)}o "
        f"{stats.get('summariesImported', 0)}sm "
        f"{stats.get('promptsImported', 0)}p | "
        f"skipped: {stats.get('sessionsSkipped', 0)}s "
        f"{stats.get('observationsSkipped', 0)}o "
        f"{stats.get('summariesSkipped', 0)}sm "
        f"{stats.get('promptsSkipped', 0)}p"
    )


@app.command()
def pull() -> None:
    """從 sync server 拉取其他裝置的新資料。"""
    import urllib.request
    import json

    config = load_server_config()
    last_epoch = config.get("last_pull_epoch", 0)

    all_data: dict[str, list] = {
        "sessions": [], "observations": [], "summaries": [], "prompts": []
    }
    since = last_epoch
    server_epoch = since

    while True:
        result = api_request(config, "GET", f"/api/sync/pull?since={since}&limit=500")
        for key in all_data:
            all_data[key].extend(result.get(key, []))
        server_epoch = result.get("server_epoch", server_epoch)
        if not result.get("has_more"):
            break
        since = result.get("next_since", since)

    total = sum(len(v) for v in all_data.values())
    if total == 0:
        console.print("[green]無新資料需要拉取[/green]")
        return

    console.print(
        f"[cyan]拉取到：{len(all_data['sessions'])} sessions, "
        f"{len(all_data['observations'])} observations, "
        f"{len(all_data['summaries'])} summaries, "
        f"{len(all_data['prompts'])} prompts[/cyan]"
    )

    # 透過 claude-mem 的 /api/import 匯入（含 dedup）
    import_payload = {
        "sessions": all_data["sessions"],
        "summaries": all_data["summaries"],
        "observations": all_data["observations"],
        "prompts": all_data["prompts"],
    }

    try:
        req = urllib.request.Request(
            "http://localhost:37777/api/import",
            data=json.dumps(import_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            import_result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError:
        console.print(
            "[bold red]claude-mem worker 未啟動（localhost:37777）。"
            "請先啟動 Claude Code。[/bold red]"
        )
        raise typer.Exit(code=1)

    config["last_pull_epoch"] = server_epoch
    save_server_config(config)

    stats = import_result.get("stats", {})
    console.print(
        f"[bold green]Pull 完成[/bold green] "
        f"imported: {stats.get('sessionsImported', 0)}s "
        f"{stats.get('observationsImported', 0)}o "
        f"{stats.get('summariesImported', 0)}sm "
        f"{stats.get('promptsImported', 0)}p | "
        f"skipped: {stats.get('sessionsSkipped', 0)}s "
        f"{stats.get('observationsSkipped', 0)}o "
        f"{stats.get('summariesSkipped', 0)}sm "
        f"{stats.get('promptsSkipped', 0)}p"
    )


@app.command()
def status() -> None:
    """顯示 sync server 同步狀態。"""
    config = load_server_config()
    result = api_request(config, "GET", "/api/sync/status")

    table = Table(title="claude-mem Sync Status")
    table.add_column("項目", style="cyan")
    table.add_column("Server 數量", style="green")
    table.add_row("Sessions", str(result.get("sessions", 0)))
    table.add_row("Observations", str(result.get("observations", 0)))
    table.add_row("Summaries", str(result.get("summaries", 0)))
    table.add_row("Prompts", str(result.get("prompts", 0)))
    table.add_row("Devices", str(result.get("devices", 0)))
    console.print(table)

    console.print(f"[dim]Last push epoch: {config.get('last_push_epoch', 0)}[/dim]")
    console.print(f"[dim]Last pull epoch: {config.get('last_pull_epoch', 0)}[/dim]")
```

**Step 2: 修改 script/main.py 註冊 mem 子命令**

在 imports 區塊加入：
```python
from .commands import mem
```

在 `app.add_typer` 區塊加入：
```python
app.add_typer(mem.app, name="mem")
```

**Step 3: 測試 CLI**

```bash
ai-dev mem --help
# Expected: 顯示 register, push, pull, status 子命令

ai-dev mem register --server http://localhost:3000 --name "test" --admin-secret "<secret>"
# Expected: 註冊成功 device_id=1

ai-dev mem push
# Expected: 推送 3700+ observations 到 server

ai-dev mem status
# Expected: 顯示 server 上的資料量
```

**Step 4: Commit**

```bash
git add script/commands/mem.py script/main.py
git commit -m "功能(mem-sync): ai-dev mem 子命令 — register, push, pull, status"
```

---

### Task 8: 防止 ai-dev sync 繼續 rsync claude-mem.db

**Files:**
- Modify: `script/utils/sync_config.py:47` — 加入 `*.db` 到 ignore patterns

**Step 1: 修改 CLAUDE_MEM_IGNORE_PATTERNS**

```python
# Before:
CLAUDE_MEM_IGNORE_PATTERNS = ["logs/", "worker.pid", "*.db-wal", "*.db-shm"]

# After:
CLAUDE_MEM_IGNORE_PATTERNS = [
    "logs/", "worker.pid",
    "*.db", "*.db-wal", "*.db-shm",
    "chroma/", "vector-db/",
]
```

新增 `*.db`（防止 rsync 損壞）和 `chroma/`、`vector-db/`（向量索引不需要同步，由各機器本地重建）。

**Step 2: 驗證**

```bash
ai-dev sync status
# 確認 claude-mem 欄位不再偵測到 db 檔案變更
```

**Step 3: Commit**

```bash
git add script/utils/sync_config.py
git commit -m "修正(sync): claude-mem ignore patterns 加入 *.db 與向量索引目錄"
```

---

## Phase 3: 自動同步

### Task 9: ai-dev mem auto — cron/launchd 排程

**Files:**
- Modify: `script/commands/mem.py` — 加入 `auto` 子命令

**Step 1: 加入 auto 命令**

```python
import platform
import subprocess
from pathlib import Path

LAUNCHD_LABEL = "com.ai-dev.mem-sync"
LAUNCHD_PLIST_PATH = Path("~/Library/LaunchAgents").expanduser() / f"{LAUNCHD_LABEL}.plist"
CRON_MARKER = "# ai-dev-mem-sync"


@app.command()
def auto(
    enable: bool = typer.Option(None, "--on/--off", help="啟用或停用自動同步"),
) -> None:
    """切換 claude-mem 自動同步排程。"""
    if enable is None:
        # 顯示狀態
        config = load_server_config()
        status_text = "啟用" if config.get("auto_sync") else "停用"
        interval = config.get("auto_sync_interval_minutes", 10)
        console.print(f"自動同步：[bold]{status_text}[/bold]（每 {interval} 分鐘）")
        return

    config = load_server_config()
    system = platform.system()

    if enable:
        interval = config.get("auto_sync_interval_minutes", 10)
        ai_dev_path = shutil.which("ai-dev") or "ai-dev"

        if system == "Darwin":
            _install_launchd(ai_dev_path, interval)
        else:
            _install_cron(ai_dev_path, interval)

        config["auto_sync"] = True
        save_server_config(config)
        console.print(f"[bold green]自動同步已啟用[/bold green]（每 {interval} 分鐘）")
    else:
        if system == "Darwin":
            _remove_launchd()
        else:
            _remove_cron()

        config["auto_sync"] = False
        save_server_config(config)
        console.print("[bold yellow]自動同步已停用[/bold yellow]")
```

macOS launchd 和 Linux cron 的安裝/移除 helper 函式依平台實作。

**Step 2: 測試**

```bash
ai-dev mem auto         # 顯示狀態
ai-dev mem auto --on    # 啟用
ai-dev mem auto --off   # 停用
```

**Step 3: Commit**

```bash
git add script/commands/mem.py
git commit -m "功能(mem-sync): ai-dev mem auto — cron/launchd 自動同步排程"
```

---

## Phase 4: 測試與文件

### Task 10: Server 測試

**Files:**
- Create: `services/claude-mem-sync/tests/sync.test.ts`

**Step 1: 建立 round-trip 測試**

測試完整流程：register → push → pull（另一個 device）→ 驗證 dedup。

使用 Bun 內建 test runner。需要 PostgreSQL 測試實例（可用 docker compose 啟動）。

**Step 2: Commit**

```bash
git add services/claude-mem-sync/tests/
git commit -m "測試(mem-sync): push/pull round-trip 整合測試"
```

---

### Task 11: 清理 sync-repo 中的殘留 binary

**Step 1: 從 sync-repo 移除不需要的 binary**

```bash
cd ~/.config/ai-dev/sync-repo
git rm -r claude-mem/claude-mem.db claude-mem/chroma/ claude-mem/vector-db/ 2>/dev/null
git commit -m "chore: 移除 claude-mem binary 檔案（改用 HTTP sync）"
```

**Step 2: 執行 ai-dev sync push 確認新 ignore 生效**

```bash
ai-dev sync push
# 確認 claude-mem.db, chroma/, vector-db/ 不再出現在同步檔案中
```

**Step 3: Commit（custom-skills repo 已在 Task 8 完成）**

---

## 執行順序摘要

| Phase | Task | 說明 | 預估 |
|-------|------|------|------|
| 1 | 1 | 專案骨架 + Docker Compose | 5 min |
| 1 | 2 | PostgreSQL migration | 3 min |
| 1 | 3 | Server 核心（config, db, health）| 5 min |
| 1 | 4 | Auth（register + API Key middleware）| 5 min |
| 1 | 5 | Sync routes（push, pull, status）| 10 min |
| 2 | 6 | Client 工具函式 (mem_sync.py) | 5 min |
| 2 | 7 | ai-dev mem CLI 子命令 | 10 min |
| 2 | 8 | 修正 sync ignore patterns | 2 min |
| 3 | 9 | 自動同步排程 | 5 min |
| 4 | 10 | Server 測試 | 10 min |
| 4 | 11 | 清理 sync-repo binary | 3 min |
