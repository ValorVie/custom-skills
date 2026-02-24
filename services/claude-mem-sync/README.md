# claude-mem Sync Server

跨裝置同步 [claude-mem](https://github.com/thedotmack/claude-mem) 資料的自建伺服器。採用 **Thin Relay** 架構 — Server 端使用 PostgreSQL 作為中繼儲存，各 Client 端保留本地 SQLite + ChromaDB 作為工作資料庫。

## 為什麼需要這個？

claude-mem 將記憶存放在本地 SQLite，跨裝置同步時直接 rsync `.db` 檔案會因 WAL mode 導致資料庫損壞。此 sync server 透過 HTTP API 進行結構化資料同步，利用 claude-mem 自帶的 `/api/import` 做 dedup 匯入，徹底避免檔案層級的衝突。

## 架構

```
┌──────────┐         ┌───────────────────┐         ┌──────────┐
│ Device A │──push──▶│  Sync Server      │◀──push──│ Device B │
│ (SQLite) │◀──pull──│  (PostgreSQL)     │──pull──▶│ (SQLite) │
└──────────┘         └───────────────────┘         └──────────┘
```

- **Push**：Client 查詢本地 SQLite `WHERE epoch > last_push_epoch`，POST 到 Server
- **Pull**：Client 向 Server GET 增量資料，再 POST 到本地 claude-mem `/api/import`（含 dedup）
- **衝突處理**：Server 端 `ON CONFLICT DO NOTHING`，Client 端由 claude-mem import API dedup

## 專案結構

```
services/claude-mem-sync/
├── docker-compose.yml          # PostgreSQL 18 + Bun server
├── .env.example                # 環境變數範本
├── server/
│   ├── Dockerfile              # oven/bun:1-alpine
│   ├── package.json            # express ^5.1.0, pg ^8.16.0
│   ├── tsconfig.json
│   ├── migrations/
│   │   └── 001_init.sql        # Schema: devices, sdk_sessions, observations, session_summaries, user_prompts
│   └── src/
│       ├── index.ts            # Express app，啟動時自動執行 migration
│       ├── config.ts           # 環境變數讀取
│       ├── db.ts               # pg Pool
│       ├── migrate.ts          # 獨立 migration runner
│       ├── middleware/
│       │   └── auth.ts         # API Key 驗證（SHA-256 hash 比對）
│       └── routes/
│           ├── health.ts       # GET /api/health
│           ├── auth.ts         # POST /api/auth/register
│           └── sync.ts         # POST /api/sync/push, GET /api/sync/pull, GET /api/sync/status
└── tests/
    └── sync.test.ts            # Bun 整合測試
```

## 快速開始

### 1. 啟動 Server

```bash
cd services/claude-mem-sync

# 複製並編輯環境變數
cp .env.example .env
# 修改 DB_PASSWORD 和 ADMIN_SECRET 為強密碼
vi .env

# 啟動
docker compose up -d
```

Server 啟動後會自動執行 database migration，無需手動操作。

PostgreSQL 18 Alpine 建議固定 `PGDATA` 並將 volume 掛到 `/var/lib/postgresql`，避免容器重建後資料落在匿名 volume。

### 2. 註冊裝置

每台裝置用固定 `--name` 註冊，取得專屬的 API Key：

```bash
ai-dev mem register \
  --server https://your-server:3000 \
  --name my-macbook \
  --admin-secret YOUR_ADMIN_SECRET
```

成功後設定會儲存到 `~/.config/ai-dev/sync-server.yaml`。

若同一台裝置再次用相同 `--name` 註冊，Server 會保留原 `device_id` 並旋轉 API Key（舊 key 立即失效）。

### 3. 手動同步

```bash
# 推送本地新資料到 server
ai-dev mem push

# 從 server 拉取其他裝置的資料
ai-dev mem pull

# 查看 server 狀態
ai-dev mem status
```

### 4. 自動同步

```bash
# 啟用自動同步（macOS: launchd, Linux: cron，預設每 10 分鐘）
ai-dev mem auto --on

# 停用
ai-dev mem auto --off

# 查看目前狀態
ai-dev mem auto
```

## API 參考

所有 API 除 `/api/health` 和 `/api/auth/register` 外，皆需在 Header 帶入 `X-API-Key`。

### `GET /api/health`

健康檢查，含 DB 連線測試。

```json
{ "status": "ok" }
```

### `POST /api/auth/register`

註冊新裝置。需要 `X-Admin-Secret` Header。

**Request:**
```json
{ "name": "my-device" }
```

**Response:**
```json
{
  "api_key": "cm_sync_a1b2c3d4...",
  "device_id": 1,
  "name": "my-device",
  "rotated": false
}
```

API Key 只在註冊時回傳一次，Server 端僅儲存 SHA-256 hash。

- `rotated = false`：首次註冊
- `rotated = true`：同名裝置重新註冊（API Key 已輪替）

### `POST /api/sync/push`

推送資料到 Server。在 transaction 內依序寫入，重複資料自動跳過（`ON CONFLICT DO NOTHING`）。

**Request:**
```json
{
  "sessions": [{ "content_session_id": "...", "memory_session_id": "...", ... }],
  "observations": [{ "memory_session_id": "...", "type": "...", ... }],
  "summaries": [{ "session_id": "...", ... }],
  "prompts": [{ "content_session_id": "...", "prompt_number": 1, ... }]
}
```

**Response:**
```json
{
  "success": true,
  "stats": {
    "sessionsImported": 5, "sessionsSkipped": 0,
    "observationsImported": 12, "observationsSkipped": 3,
    "summariesImported": 5, "summariesSkipped": 0,
    "promptsImported": 8, "promptsSkipped": 0
  },
  "server_epoch": 1771855200000
}
```

寫入順序：sessions → observations → summaries → prompts（observations 有 FK 依賴 sessions）。

### `GET /api/sync/pull`

增量拉取其他裝置的資料。自動排除自己推送的資料（依 `origin_device_id`）。

| 參數 | 說明 | 預設 |
|------|------|------|
| `since` | 起始時間戳 (ms epoch) | `0` |
| `limit` | 每類資料筆數上限 | `500`（最大 `1000`） |

**Response:**
```json
{
  "sessions": [...],
  "observations": [...],
  "summaries": [...],
  "prompts": [...],
  "has_more": false,
  "next_since": 1771855200000,
  "server_epoch": 1771855300000
}
```

`has_more` 為 `true` 時，使用 `next_since` 繼續分頁拉取。

### `GET /api/sync/status`

Server 各資料表的筆數統計。

```json
{
  "sessions": 42,
  "observations": 156,
  "summaries": 38,
  "prompts": 89,
  "devices": 3
}
```

## Database Schema

Server 端使用 PostgreSQL，共 5 張表：

| Table | Dedup Key | 說明 |
|-------|-----------|------|
| `devices` | `api_key_hash` | 已註冊裝置 |
| `sdk_sessions` | `content_session_id` | Claude Code 對話 session |
| `observations` | `(memory_session_id, title, created_at_epoch)` | 記憶觀察紀錄 |
| `session_summaries` | `session_id` | Session 摘要 |
| `user_prompts` | `(content_session_id, prompt_number)` | 使用者輸入 |

每張資料表都有 `synced_at` 欄位（`TIMESTAMPTZ DEFAULT now()`）用於增量同步，並建有對應索引。

## 開發

### 本地開發

```bash
cd services/claude-mem-sync

# 啟動 PostgreSQL
docker compose up -d postgres

# 安裝依賴
cd server && bun install

# 開發模式（自動重載）
DATABASE_URL=postgres://claude_mem:yourpwd@localhost:5432/claude_mem_sync \
ADMIN_SECRET=dev-secret \
bun run dev
```

### 執行測試

測試需要完整的 Docker Compose 環境：

```bash
cd services/claude-mem-sync
docker compose up -d

ADMIN_SECRET=your-secret \
TEST_SERVER_URL=http://localhost:3000 \
bun test
```

## 設定檔

Client 端設定儲存在 `~/.config/ai-dev/sync-server.yaml`：

```yaml
server_url: https://your-server:3000
api_key: cm_sync_a1b2c3d4...
device_name: my-macbook
device_id: 1
last_push_epoch: 1771855200000
last_pull_epoch: 1771855200000
auto_sync: true
auto_sync_interval_minutes: 10
```

## 從 ai-dev sync 遷移

此服務取代了 `ai-dev sync` 中的 claude-mem 同步功能（rsync `.db` 檔案方式）。升級後需在每台裝置上執行以下步驟：

### 1. 移除 ai-dev sync 中的 claude-mem 目錄

```bash
ai-dev sync remove ~/.claude-mem
```

### 2. 清除 GitHub sync repo 中的 claude-mem 資料

sync repo 中已有的 `claude-mem/` 目錄需要手動刪除並推送：

```bash
# 進入 sync repo（預設路徑）
cd ~/.config/ai-dev/sync-repo

# 刪除 claude-mem 目錄
rm -rf claude-mem/

# 提交並推送
git add -A && git commit -m "chore: remove claude-mem from sync repo (migrated to sync server)"
git push
```

完成後，在其他裝置執行 `ai-dev sync pull` 即可同步移除。

### 3. 註冊並啟用 sync server

參照上方「快速開始」的步驟 2-4，在每台裝置上註冊並啟用自動同步。

## 部署建議

- 搭配 Traefik 或 Nginx reverse proxy 提供 HTTPS
- `DB_PASSWORD` 和 `ADMIN_SECRET` 使用強隨機密碼
- PostgreSQL volume (`pgdata`) 建議定期備份
- 避免使用 `docker compose down -v`（會刪除資料 volume）
- 日誌位於 container stdout，可透過 Docker logging driver 收集

## 同步原理

1. **Push**：Client 查詢本地 SQLite `WHERE epoch > last_push_epoch`，批次 POST 到 Server
2. **Server 寫入**：在 transaction 中依序 INSERT，`ON CONFLICT DO NOTHING` 跳過重複
3. **Pull**：Client 用 `since` 時間戳向 Server 增量查詢，Server 自動排除該裝置推送的資料
4. **Client 匯入**：Pull 到的資料 POST 到本地 claude-mem `localhost:37777/api/import`，由 claude-mem 自行 dedup
5. **時間戳管理**：使用 Server 端 `synced_at`（`DEFAULT now()`）避免 Client 時鐘偏差問題
