# Content Hash 去重設計：claude-mem-sync 同步防重複機制

> 日期：2026-02-24
> 狀態：已核准

## 背景

claude-mem-sync 透過中間的 PostgreSQL 同步多台裝置的 claude-mem 資料。現有去重機制存在以下問題：

1. **Push 重複推送** — epoch 斷點 crash 或重推時，同內容資料重複進入 server
2. **Pull 重複匯入** — 從 server 拉回的資料在本地產生重複
3. **跨裝置同步迴圈** — Device A → Server → Device B → Server → Device A 的資料迴流
4. **ChromaDB 索引膨脹** — reindex 透過 worker API 建立淺拷貝

## 方案選擇

| 方案 | 核心思路 | 優點 | 缺點 |
|------|----------|------|------|
| **A: Content Hash 去重（採用）** | `sync_content_hash` UNIQUE 約束 | 根本解決所有場景 | 需 migration |
| B: Server-Side 增強 | 模糊比對 + sync_version | 不改 client | 假陽性風險 |
| C: Client-Side 防禦 | 純 client 端去重 | Server 零改動 | 治標不治本 |

## 設計

### 1. Content Hash 定義

**Hash 演算法：** SHA-256 截取前 32 hex chars（128 bits）

**參與欄位：** `title`, `narrative`, `facts`, `project`, `type`

**不參與欄位：** `id`, `memory_session_id`, `created_at_epoch`, `origin_device_id`, `synced_at`

```python
import hashlib, json

def compute_content_hash(obs: dict) -> str:
    payload = json.dumps({
        "title": obs.get("title", ""),
        "narrative": obs.get("narrative", ""),
        "facts": obs.get("facts", "[]"),
        "project": obs.get("project", ""),
        "type": obs.get("type", ""),
    }, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()[:32]
```

**設計理由：**
- `title` + `narrative` + `facts` = 記憶核心內容
- `project` + `type` = 避免不同 project 的同名記憶被誤判
- 排除 `created_at_epoch` 因為同筆記憶在不同裝置可能有微小時間差
- 128 bits 在百萬筆資料下衝突率約 10⁻²⁰，遠超安全需求

### 2. Schema 變更

#### Server PostgreSQL Migration (002)

```sql
-- 1. 加欄位
ALTER TABLE observations ADD COLUMN sync_content_hash TEXT;

-- 2. 回填（由 server 啟動時用 TypeScript 執行，確保 hash 邏輯與 client 一致）

-- 3. 加 UNIQUE 約束
ALTER TABLE observations ADD CONSTRAINT observations_sync_content_hash_unique
  UNIQUE (sync_content_hash);

-- 4. 清理現有重複（保留最早 synced_at）
WITH dupes AS (
  SELECT id, sync_content_hash,
    ROW_NUMBER() OVER (PARTITION BY sync_content_hash ORDER BY synced_at ASC) AS rn
  FROM observations
  WHERE sync_content_hash IS NOT NULL
)
DELETE FROM observations WHERE id IN (
  SELECT id FROM dupes WHERE rn > 1
);
```

**回填注意：** 必須用與 client 相同的 `json.dumps(sort_keys=True)` 邏輯。Server 端用 TypeScript 實作等效邏輯。

#### Push UPSERT 變更

```sql
-- 現有
INSERT INTO observations (...) VALUES (...)
ON CONFLICT (memory_session_id, title, created_at_epoch) DO NOTHING;

-- 改為
INSERT INTO observations (..., sync_content_hash) VALUES (..., $hash)
ON CONFLICT (sync_content_hash) DO NOTHING;
```

保留舊 UNIQUE 約束 `(memory_session_id, title, created_at_epoch)` 作為備份，未來可移除。

#### Client 端不需要 schema 變更

Hash 計算為 on-the-fly，不儲存在本地 SQLite。

### 3. Push 流程改善

```
1. Client 查詢 observations WHERE created_at_epoch > last_push_epoch
2. 排除 pulled_hashes 中的 observations（見 Section 5）
3. 計算每筆的 sync_content_hash
4. POST /api/sync/push-preflight { hashes: [...] }
   → Server 回傳 { missing: [...] }
5. Client 只推送 missing 中的 observations
6. POST /api/sync/push { sessions, observations, summaries, prompts }
   → Server 回傳 { server_epoch, stats }
7. Client 儲存 last_push_epoch = server_epoch
```

#### 新增 API：POST /api/sync/push-preflight

```typescript
// Request
{ hashes: string[] }

// Response
{ missing: string[] }

// Server 實作
SELECT sync_content_hash FROM observations
WHERE sync_content_hash = ANY($1);
// missing = request.hashes - found
```

#### Sessions / Summaries / Prompts

不需 preflight，保持現有 UNIQUE 約束 + `DO NOTHING`。

### 4. Pull 流程改善

```
1. 計算本地所有 observations 的 content hash set（in-memory）
2. GET /api/sync/pull?since={epoch}&limit=500
   → Server 回傳 observations（含 sync_content_hash）
3. 過濾：new_obs = [o for o in pulled if o.sync_content_hash not in local_hashes]
4. 只匯入 new_obs
5. 將匯入的 hash 追加到 pulled_hashes 檔案
6. 更新 last_pull_epoch
7. 如有新增 → reindex ChromaDB（直寫 ChromaDB，不走 worker API）
```

Server Pull response 加入 `sync_content_hash` 欄位。

### 5. 跨裝置防迴圈

#### Server 端防禦（主要）

`ON CONFLICT (sync_content_hash) DO NOTHING` 保證同內容不會有兩行。

```
Device A push O1 (hash=abc123) → Server 存入
Device B pull O1 → 匯入本地
Device B push O1 (hash=abc123) → Server: DO NOTHING → 跳過
Device A pull → 不會收到重複
```

#### Client 端防禦（輔助）

`~/.config/ai-dev/pulled-hashes.txt` 記錄所有 pull 匯入的 hash，一行一個：

```
a1b2c3d4e5f67890a1b2c3d4e5f67890
f7e8d9c0b1a23456f7e8d9c0b1a23456
```

Push 時讀取為 set，排除匹配的 observations，避免無效傳輸。

### 6. 資料清理與驗證

#### Server Migration 自動清理

Migration 002 回填 hash 後自動刪除重複（保留最早 synced_at）。

#### ai-dev mem cleanup

新增子命令：

```
1. 計算本地所有 observations 的 content hash
2. 找出相同 hash 的記錄，保留 id 最小的
3. 刪除重複
4. 輸出 {total, duplicates_removed}
```

#### ai-dev mem status 增強

```
=== Memory Sync Status ===
Local observations:  1,234
Server observations: 1,230
Local duplicates:    4
Hash coverage:       100%
Last push:           2026-02-24 17:00
Last pull:           2026-02-24 16:55
```

## 影響範圍

| 元件 | 變更 |
|------|------|
| `server/migrations/` | 新增 002_add_sync_content_hash.sql |
| `server/src/routes/sync.ts` | push 加 hash、新增 preflight API、pull 回傳 hash |
| `server/src/index.ts` | 啟動時回填 hash |
| `script/commands/mem.py` | push/pull 流程重構、新增 cleanup 子命令、status 增強 |
| `script/utils/mem_sync.py` | 新增 compute_content_hash()、pulled_hashes 管理 |

## 向後相容

- 舊版 client 推送不帶 hash 的 observations → server 可計算 hash 後存入
- 回填 migration 確保現有資料都有 hash
- 舊 UNIQUE 約束保留，雙重保護
