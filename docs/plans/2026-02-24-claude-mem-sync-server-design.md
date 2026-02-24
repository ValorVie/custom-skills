# claude-mem Sync Server 設計文件

**日期：** 2026-02-24
**狀態：** 已核准
**方案：** Thin Relay（方案 A）

## 背景

claude-mem 的 SQLite 資料庫透過 ai-dev sync（rsync）在多台機器間同步時，
因 WAL 模式的 `.db-wal` / `.db-shm` 被排除但 `.db` 未排除，
導致資料庫損壞（database disk image is malformed）。

官方 Pro cloud sync（Supabase + Pinecone）已設計但後端從未上線（PR #853/#854）。

本方案自架一個輕量 sync server，透過 HTTP API 實現安全的多機同步。

## 架構總覽

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
│                                                          │
│  ┌──────────────────┐    ┌──────────────────────────┐   │
│  │  PostgreSQL 18    │◄──│  claude-mem-sync-server   │   │
│  │                   │   │  (Bun / Node.js)          │   │
│  │  4 tables:        │   │                           │   │
│  │  - sdk_sessions   │   │  POST /api/sync/push      │   │
│  │  - observations   │   │  GET  /api/sync/pull      │   │
│  │  - summaries      │   │  GET  /api/sync/status    │   │
│  │  - user_prompts   │   │  POST /api/auth/register  │   │
│  └──────────────────┘   └──────────────────────────┘   │
│                              ▲                           │
└──────────────────────────────┼───────────────────────────┘
                               │ HTTPS (Traefik/Nginx)
            ┌──────────────────┼──────────────────┐
            │                  │                  │
     ┌──────┴──────┐   ┌──────┴──────┐   ┌──────┴──────┐
     │  Machine A   │   │  Machine B   │   │  Machine C   │
     │  claude-mem  │   │  claude-mem  │   │  claude-mem  │
     │  worker      │   │  worker      │   │  worker      │
     │  :37777      │   │  :37777      │   │  :37777      │
     │  ai-dev CLI  │   │  ai-dev CLI  │   │  ai-dev CLI  │
     └─────────────┘   └─────────────┘   └─────────────┘
```

**核心概念：**
- Server 是中央資料倉庫，PostgreSQL 存放所有機器的合併資料
- 各 Client 保留本地 SQLite + ChromaDB（不變）
- Push = 本地新增資料 → Server
- Pull = Server 新資料 → 本地 `/api/import`（dedup 由 claude-mem 處理）
- 每台機器記錄自己的 `last_sync_epoch`，實現增量同步

## PostgreSQL Schema

```sql
-- 裝置註冊表
CREATE TABLE devices (
  id          SERIAL PRIMARY KEY,
  api_key     TEXT UNIQUE NOT NULL,       -- SHA-256 hash of cm_sync_<32hex>
  name        TEXT NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT now()
);

-- 以下 4 張表與 claude-mem SQLite schema 對齊

CREATE TABLE sdk_sessions (
  id                  SERIAL PRIMARY KEY,
  content_session_id  TEXT UNIQUE NOT NULL,  -- dedup key
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

CREATE TABLE observations (
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

CREATE TABLE session_summaries (
  id                  SERIAL PRIMARY KEY,
  session_id          TEXT UNIQUE NOT NULL,  -- = memory_session_id
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

CREATE TABLE user_prompts (
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

-- 增量查詢用索引
CREATE INDEX idx_sessions_synced    ON sdk_sessions(synced_at);
CREATE INDEX idx_observations_synced ON observations(synced_at);
CREATE INDEX idx_summaries_synced   ON session_summaries(synced_at);
CREATE INDEX idx_prompts_synced     ON user_prompts(synced_at);
```

## 同步協議

### Push 流程

1. Client 查詢本地 SQLite：`WHERE created_at_epoch > last_push_epoch`
2. `POST /api/sync/push` 帶 4 個陣列（sessions, observations, summaries, prompts）
3. Server 使用 `INSERT ... ON CONFLICT DO NOTHING`（冪等）
4. Server 回傳 `server_epoch`，Client 更新 `last_push_epoch`

### Pull 流程

1. `GET /api/sync/pull?since=<last_pull_epoch>&limit=500`
2. Server 查詢 `synced_at > since`，排除 `origin_device_id == caller`
3. Client 將結果 POST 到 `localhost:37777/api/import`（claude-mem 處理 dedup）
4. Client 更新 `last_pull_epoch`

### 關鍵設計決策

| 決策 | 選擇 | 理由 |
|------|------|------|
| Dedup 責任 | Server UPSERT + Client import | 雙重保險 |
| 增量基準 | `synced_at`（Server 端時間戳）| 避免各機器時鐘差異 |
| Pull 排除自己 | `origin_device_id != caller` | 避免拉回剛推的資料 |
| Push 順序 | sessions → observations (FK) | Server 端維護 FK |
| 分頁 | `limit=500` + `has_more` | 防止大量資料一次傳輸 |

## API 端點

| Method | Path | 說明 |
|--------|------|------|
| `POST` | `/api/auth/register` | 註冊裝置（需 `X-Admin-Secret`） |
| `POST` | `/api/sync/push` | 推送本地新資料 |
| `GET` | `/api/sync/pull?since=&limit=` | 拉取其他裝置的新資料 |
| `GET` | `/api/sync/status` | 同步狀態 |
| `GET` | `/api/health` | 健康檢查 |

認證：`X-API-Key: cm_sync_<32hex>`（register 回傳，Server 存 SHA-256 hash）

## Client 整合

### 新增 CLI 指令

```
ai-dev mem push    # 手動推送
ai-dev mem pull    # 手動拉取
ai-dev mem status  # 查看同步狀態
ai-dev mem auto    # 切換自動同步 on/off
```

### 與現有 sync 的關係

- `ai-dev sync push/pull` — 同步 ~/.claude 設定檔（rsync/git，不變）
- `ai-dev mem push/pull` — 同步 claude-mem 資料（HTTP API，新增）
- `CLAUDE_MEM_IGNORE_PATTERNS` 加入 `*.db`，不再 rsync 資料庫

### 自動同步

`ai-dev mem auto on` 安裝 cron/launchd job：
- macOS: `~/Library/LaunchAgents/com.ai-dev.mem-sync.plist`
- Linux: crontab `*/10 * * * *`
- 每 10 分鐘執行 `ai-dev mem push && ai-dev mem pull`

### 設定檔

```yaml
# ~/.config/ai-dev/sync-server.yaml
server_url: https://claude-mem-sync.your-domain.com
api_key: cm_sync_<32hex>
device_name: Valor-20201218
registered_at: 2026-02-24T15:00:00Z
last_push_epoch: 0
last_pull_epoch: 0
auto_sync: false
auto_sync_interval_minutes: 10
```

## 錯誤處理

| 場景 | 處理方式 |
|------|----------|
| Server 不可達 | 靜默失敗，記錄 warning，下次重試 |
| Push 中途斷線 | Server 使用 DB transaction，全量回滾 |
| Pull 後 import 失敗 | 不更新 `last_pull_epoch`，下次重拉 |
| claude-mem worker 未啟動 | 提示使用者啟動 Claude Code |
| SQLite WAL lock | Push 使用 `PRAGMA query_only = ON` 唯讀開啟 |
| API Key 無效 | Server 回 401，提示重新 register |
| 重複推送 | `ON CONFLICT DO NOTHING`，冪等安全 |

## 專案結構

```
claude-mem-sync/
├── docker-compose.yml
├── .env.example
├── server/
│   ├── package.json
│   ├── tsconfig.json
│   ├── src/
│   │   ├── index.ts              # 入口，Express app
│   │   ├── config.ts             # 環境變數讀取
│   │   ├── db.ts                 # PostgreSQL 連線池
│   │   ├── middleware/
│   │   │   └── auth.ts           # API Key 驗證
│   │   └── routes/
│   │       ├── auth.ts           # POST /api/auth/register
│   │       ├── sync.ts           # push, pull, status
│   │       └── health.ts         # GET /api/health
│   ├── migrations/
│   │   └── 001_init.sql
│   └── Dockerfile
└── tests/
    └── sync.test.ts
```

## 技術選型

| 元件 | 選擇 | 理由 |
|------|------|------|
| Runtime | Bun (fallback Node.js) | 與 claude-mem 一致 |
| HTTP | Express | 邏輯簡單，生態成熟 |
| DB driver | pg (node-postgres) | 穩定，原生 Promise |
| DB | PostgreSQL 18 | Docker 易部署，未來可加 pgvector |
| Migration | 手動 SQL | 只有 1 個 migration |
| 認證 | Stateless API Key | 無需 session 管理 |
