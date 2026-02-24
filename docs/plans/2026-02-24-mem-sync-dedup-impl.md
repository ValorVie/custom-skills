# Content Hash 去重實作計畫

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 claude-mem-sync 中實作基於 content hash 的去重機制，消除 push/pull/跨裝置同步的重複資料。

**Architecture:** Server 端新增 `sync_content_hash` UNIQUE 欄位，push 前透過 preflight API 計算差集只傳新資料，pull 後用 hash 過濾已存在的 observations。Client 端維護 `pulled-hashes.txt` 防止推回外來資料。

**Tech Stack:** TypeScript/Bun (server), Python 3.12+ (client), PostgreSQL (server DB), SQLite (client DB)

**Design Doc:** `docs/plans/2026-02-24-mem-sync-dedup-design.md`

---

### Task 1: Content Hash 工具函式（Python Client）

**Files:**
- Modify: `script/utils/mem_sync.py:1-17` (imports)
- Modify: `script/utils/mem_sync.py` (新增函式)
- Create: `tests/test_mem_sync_hash.py`

**Step 1: Write the failing test**

```python
# tests/test_mem_sync_hash.py
"""Tests for compute_content_hash."""
from script.utils.mem_sync import compute_content_hash


def test_basic_hash():
    obs = {
        "title": "Test observation",
        "narrative": "This is a test",
        "facts": '["fact1"]',
        "project": "test-project",
        "type": "discovery",
    }
    h = compute_content_hash(obs)
    assert isinstance(h, str)
    assert len(h) == 32  # 128 bits = 32 hex chars


def test_same_content_same_hash():
    obs1 = {"title": "A", "narrative": "B", "facts": "[]", "project": "p", "type": "t"}
    obs2 = {"title": "A", "narrative": "B", "facts": "[]", "project": "p", "type": "t"}
    assert compute_content_hash(obs1) == compute_content_hash(obs2)


def test_different_content_different_hash():
    obs1 = {"title": "A", "narrative": "B", "facts": "[]", "project": "p", "type": "t"}
    obs2 = {"title": "A", "narrative": "C", "facts": "[]", "project": "p", "type": "t"}
    assert compute_content_hash(obs1) != compute_content_hash(obs2)


def test_ignores_metadata_fields():
    """id, memory_session_id, created_at_epoch 等 metadata 不影響 hash。"""
    base = {"title": "A", "narrative": "B", "facts": "[]", "project": "p", "type": "t"}
    with_meta = {
        **base,
        "id": 42,
        "memory_session_id": "ms-001",
        "created_at_epoch": 1234567890,
        "origin_device_id": 1,
    }
    assert compute_content_hash(base) == compute_content_hash(with_meta)


def test_missing_fields_default_to_empty():
    obs = {"title": "A"}
    h = compute_content_hash(obs)
    assert len(h) == 32
```

**Step 2: Run test to verify it fails**

Run: `cd /home/valor/Code/custom-skills && python -m pytest tests/test_mem_sync_hash.py -v`
Expected: FAIL with ImportError (compute_content_hash not defined)

**Step 3: Write minimal implementation**

在 `script/utils/mem_sync.py` 的 imports 區域加入 `hashlib`，然後在 `query_local_db()` 之後加入：

```python
import hashlib  # 加到檔案頂部 imports

def compute_content_hash(obs: dict[str, Any]) -> str:
    """計算 observation 的 content hash（SHA-256 前 32 hex chars）。

    參與欄位：title, narrative, facts, project, type
    不參與欄位：id, memory_session_id, created_at_epoch 等 metadata
    """
    payload = json.dumps({
        "title": obs.get("title", ""),
        "narrative": obs.get("narrative", ""),
        "facts": obs.get("facts", "[]"),
        "project": obs.get("project", ""),
        "type": obs.get("type", ""),
    }, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()[:32]
```

**Step 4: Run test to verify it passes**

Run: `cd /home/valor/Code/custom-skills && python -m pytest tests/test_mem_sync_hash.py -v`
Expected: PASS (5 tests)

**Step 5: Export from `__init__` and commit**

更新 `script/utils/mem_sync.py` 的 imports 和 `script/commands/mem.py:19-27` 的 import 列表，加入 `compute_content_hash`。

```bash
git add script/utils/mem_sync.py tests/test_mem_sync_hash.py script/commands/mem.py
git commit -m "功能(mem-sync): 新增 compute_content_hash 工具函式"
```

---

### Task 2: Content Hash 工具函式（TypeScript Server）

**Files:**
- Create: `services/claude-mem-sync/server/src/utils/hash.ts`
- Create: `services/claude-mem-sync/tests/hash.test.ts`

**Step 1: Write the failing test**

```typescript
// services/claude-mem-sync/tests/hash.test.ts
import { describe, test, expect } from "bun:test";
import { computeContentHash } from "../server/src/utils/hash.js";

describe("computeContentHash", () => {
  test("returns 32-char hex string", () => {
    const h = computeContentHash({
      title: "Test", narrative: "Narrative",
      facts: "[]", project: "p", type: "t",
    });
    expect(h).toHaveLength(32);
    expect(h).toMatch(/^[0-9a-f]{32}$/);
  });

  test("same content produces same hash", () => {
    const obs = { title: "A", narrative: "B", facts: "[]", project: "p", type: "t" };
    expect(computeContentHash(obs)).toBe(computeContentHash(obs));
  });

  test("different content produces different hash", () => {
    const a = { title: "A", narrative: "B", facts: "[]", project: "p", type: "t" };
    const b = { title: "A", narrative: "C", facts: "[]", project: "p", type: "t" };
    expect(computeContentHash(a)).not.toBe(computeContentHash(b));
  });

  test("matches Python implementation", () => {
    // 這個 hash 值必須與 Python compute_content_hash 結果完全一致
    // 先用 Python 計算一個 known-good hash，填入這裡
    const obs = { title: "Test observation", narrative: "This is a test",
                  facts: '["fact1"]', project: "test-project", type: "discovery" };
    const expected = "PLACEHOLDER";  // Step 3 時由 Python 產生
    const h = computeContentHash(obs);
    expect(h).toBe(expected);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd /home/valor/Code/custom-skills/services/claude-mem-sync && bun test tests/hash.test.ts`
Expected: FAIL (module not found)

**Step 3: Write implementation + cross-validate with Python**

先用 Python 產生 known-good hash：

```bash
python3 -c "
from script.utils.mem_sync import compute_content_hash
print(compute_content_hash({
    'title': 'Test observation', 'narrative': 'This is a test',
    'facts': '[\"fact1\"]', 'project': 'test-project', 'type': 'discovery',
}))
"
```

用輸出值更新測試中的 `PLACEHOLDER`，然後實作：

```typescript
// services/claude-mem-sync/server/src/utils/hash.ts
import { createHash } from "crypto";

interface ObservationLike {
  title?: string | null;
  narrative?: string | null;
  facts?: string | null;
  project?: string | null;
  type?: string | null;
}

export function computeContentHash(obs: ObservationLike): string {
  // 必須與 Python json.dumps(sort_keys=True, ensure_ascii=False) 完全一致
  const payload = JSON.stringify({
    facts: obs.facts ?? "[]",
    narrative: obs.narrative ?? "",
    project: obs.project ?? "",
    title: obs.title ?? "",
    type: obs.type ?? "",
  });
  return createHash("sha256").update(payload, "utf-8").digest("hex").slice(0, 32);
}
```

注意：`JSON.stringify` 的 key 順序是 insertion order，需按字母排列以匹配 Python 的 `sort_keys=True`。

**Step 4: Run test to verify it passes**

Run: `cd /home/valor/Code/custom-skills/services/claude-mem-sync && bun test tests/hash.test.ts`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add services/claude-mem-sync/server/src/utils/hash.ts services/claude-mem-sync/tests/hash.test.ts
git commit -m "功能(mem-sync): 新增 TypeScript computeContentHash 工具函式"
```

---

### Task 3: Server Migration 002 — sync_content_hash 欄位

**Files:**
- Create: `services/claude-mem-sync/server/migrations/002_add_sync_content_hash.sql`
- Modify: `services/claude-mem-sync/server/src/index.ts:19-25` (apply migration)

**Step 1: Write migration SQL**

```sql
-- services/claude-mem-sync/server/migrations/002_add_sync_content_hash.sql
ALTER TABLE observations ADD COLUMN IF NOT EXISTS sync_content_hash TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS idx_observations_sync_content_hash
  ON observations (sync_content_hash);
```

注意：使用 `IF NOT EXISTS` 確保冪等性。回填和去重在 server 啟動時由 TypeScript 執行（Task 4）。

**Step 2: Update index.ts to apply migration 002**

在 `services/claude-mem-sync/server/src/index.ts:19-25` 修改 `start()` 函式：

```typescript
async function start() {
  const migration001 = readFileSync(
    join(__dirname, "../migrations/001_init.sql"), "utf-8"
  );
  await pool.query(migration001);

  const migration002 = readFileSync(
    join(__dirname, "../migrations/002_add_sync_content_hash.sql"), "utf-8"
  );
  await pool.query(migration002);
  console.log("Database migrations applied");

  app.listen(config.port, () => {
    console.log(`claude-mem-sync-server listening on :${config.port}`);
  });
}
```

**Step 3: Verify migration applies cleanly**

Run: `cd /home/valor/Code/custom-skills/services/claude-mem-sync && docker compose up -d && sleep 3 && docker compose logs server | tail -5`
Expected: "Database migrations applied"

**Step 4: Commit**

```bash
git add services/claude-mem-sync/server/migrations/002_add_sync_content_hash.sql services/claude-mem-sync/server/src/index.ts
git commit -m "功能(mem-sync): migration 002 — 新增 sync_content_hash 欄位"
```

---

### Task 4: Server 啟動時回填 Hash + 去重

**Files:**
- Modify: `services/claude-mem-sync/server/src/index.ts` (backfill logic)

**Step 1: Write the backfill + dedup logic**

在 `start()` 函式中，migration 002 之後加入：

```typescript
import { computeContentHash } from "./utils/hash.js";

// 在 start() 中 migration002 之後：
// Backfill sync_content_hash for existing observations
const unhashed = await pool.query(
  "SELECT id, title, narrative, facts, project, type FROM observations WHERE sync_content_hash IS NULL"
);
if (unhashed.rows.length > 0) {
  console.log(`Backfilling ${unhashed.rows.length} observations with sync_content_hash...`);
  for (const row of unhashed.rows) {
    const hash = computeContentHash(row);
    await pool.query(
      "UPDATE observations SET sync_content_hash = $1 WHERE id = $2",
      [hash, row.id]
    );
  }

  // Dedup: keep earliest synced_at per hash
  const deduped = await pool.query(`
    WITH dupes AS (
      SELECT id, sync_content_hash,
        ROW_NUMBER() OVER (PARTITION BY sync_content_hash ORDER BY synced_at ASC) AS rn
      FROM observations
      WHERE sync_content_hash IS NOT NULL
    )
    DELETE FROM observations WHERE id IN (
      SELECT id FROM dupes WHERE rn > 1
    )
  `);
  if (deduped.rowCount && deduped.rowCount > 0) {
    console.log(`Removed ${deduped.rowCount} duplicate observations`);
  }
  console.log("Backfill complete");
}
```

**Step 2: Test backfill is idempotent**

Run: 重啟 server 兩次，確認第二次 unhashed.rows.length = 0

```bash
docker compose restart server && sleep 3 && docker compose logs server --tail 10
```
Expected: 第二次不顯示 "Backfilling" 訊息

**Step 3: Commit**

```bash
git add services/claude-mem-sync/server/src/index.ts
git commit -m "功能(mem-sync): server 啟動時回填 sync_content_hash 並去重"
```

---

### Task 5: Server Push-Preflight API

**Files:**
- Modify: `services/claude-mem-sync/server/src/routes/sync.ts:8-107` (add endpoint)
- Modify: `services/claude-mem-sync/tests/sync.test.ts` (add tests)

**Step 1: Write the failing test**

在 `services/claude-mem-sync/tests/sync.test.ts` 的 `describe("Sync")` 區塊內追加：

```typescript
test("POST /api/sync/push-preflight returns missing hashes", async () => {
  // 先推一筆有 hash 的 observation
  const pushResult = await apiRequest(
    "POST", "/api/sync/push",
    {
      sessions: [{
        content_session_id: "preflight-cs-001",
        memory_session_id: "preflight-ms-001",
        project: "test-project",
        started_at: "2026-02-24T01:00:00Z",
        started_at_epoch: 1771858800000,
        status: "completed",
      }],
      observations: [{
        memory_session_id: "preflight-ms-001",
        project: "test-project",
        type: "discovery",
        title: "Existing observation",
        narrative: "Already on server",
        facts: "[]",
        created_at: "2026-02-24T01:00:00Z",
        created_at_epoch: 1771858800000,
        sync_content_hash: "aaaa1111bbbb2222cccc3333dddd4444",
      }],
      summaries: [],
      prompts: [],
    },
    { "X-API-Key": deviceAKey }
  );
  expect(pushResult.data.stats.observationsImported).toBe(1);

  // preflight: 一個已存在 + 一個新的
  const { status, data } = await apiRequest(
    "POST", "/api/sync/push-preflight",
    { hashes: ["aaaa1111bbbb2222cccc3333dddd4444", "newnewhash00000000000000000000000"] },
    { "X-API-Key": deviceAKey }
  );
  expect(status).toBe(200);
  expect(data.missing).toEqual(["newnewhash00000000000000000000000"]);
});

test("POST /api/sync/push-preflight with empty hashes", async () => {
  const { status, data } = await apiRequest(
    "POST", "/api/sync/push-preflight",
    { hashes: [] },
    { "X-API-Key": deviceAKey }
  );
  expect(status).toBe(200);
  expect(data.missing).toEqual([]);
});
```

**Step 2: Run test to verify it fails**

Run: `cd /home/valor/Code/custom-skills/services/claude-mem-sync && bun test tests/sync.test.ts`
Expected: FAIL (404 on /api/sync/push-preflight)

**Step 3: Implement the endpoint**

在 `services/claude-mem-sync/server/src/routes/sync.ts` 的 push endpoint 之後加入：

```typescript
// ─── POST /api/sync/push-preflight ───
router.post("/api/sync/push-preflight", async (req: Request, res: Response) => {
  const { hashes = [] } = req.body;

  if (!Array.isArray(hashes) || hashes.length === 0) {
    res.json({ missing: [] });
    return;
  }

  try {
    const result = await pool.query(
      "SELECT sync_content_hash FROM observations WHERE sync_content_hash = ANY($1)",
      [hashes]
    );
    const found = new Set(result.rows.map((r: any) => r.sync_content_hash));
    const missing = hashes.filter((h: string) => !found.has(h));
    res.json({ missing });
  } catch (err: any) {
    console.error("Preflight failed:", err.message);
    res.status(500).json({ error: "Preflight failed" });
  }
});
```

**Step 4: Update push to accept and store sync_content_hash**

修改 `sync.ts` 中 observations 的 INSERT 語句，加入 `sync_content_hash` 欄位，並改 UPSERT 為雙重衝突處理：

```typescript
// observations — 更新 INSERT 語句
for (const o of observations) {
  const r = await client.query(
    `INSERT INTO observations
      (memory_session_id, project, type, title, subtitle, narrative, text,
       facts, concepts, files_read, files_modified, prompt_number,
       content_hash, created_at, created_at_epoch, origin_device_id,
       sync_content_hash)
     VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17)
     ON CONFLICT (sync_content_hash) DO NOTHING`,
    [o.memory_session_id, o.project, o.type, o.title, o.subtitle,
     o.narrative, o.text, o.facts, o.concepts, o.files_read,
     o.files_modified, o.prompt_number, o.content_hash,
     o.created_at, o.created_at_epoch, device.id,
     o.sync_content_hash]
  );
  if (r.rowCount && r.rowCount > 0) stats.observationsImported++;
  else stats.observationsSkipped++;
}
```

注意：如果 client 沒提供 `sync_content_hash`（舊版 client），server 應在插入前計算。加入 fallback：

```typescript
import { computeContentHash } from "../utils/hash.js";

// 在 for loop 內 INSERT 之前：
if (!o.sync_content_hash) {
  o.sync_content_hash = computeContentHash(o);
}
```

**Step 5: Run tests to verify**

Run: `cd /home/valor/Code/custom-skills/services/claude-mem-sync && bun test tests/sync.test.ts`
Expected: ALL PASS

**Step 6: Commit**

```bash
git add services/claude-mem-sync/server/src/routes/sync.ts services/claude-mem-sync/tests/sync.test.ts
git commit -m "功能(mem-sync): push-preflight API 與 sync_content_hash UPSERT"
```

---

### Task 6: Server Pull 回傳 sync_content_hash

**Files:**
- Modify: `services/claude-mem-sync/server/src/routes/sync.ts:109-167` (pull endpoint)

**Step 1: Verify current pull response**

Pull endpoint 使用 `SELECT *`，已包含 `sync_content_hash` 欄位（因為 migration 002 新增了）。不需要修改 SQL。

**驗證：** 執行 pull 查看 response 中是否包含 `sync_content_hash`。

```bash
# 在測試中加入驗證
```

**Step 2: Add test to verify pull includes sync_content_hash**

在 `tests/sync.test.ts` 追加：

```typescript
test("GET /api/sync/pull includes sync_content_hash", async () => {
  const { data } = await apiRequest(
    "GET", "/api/sync/pull?since=0",
    undefined,
    { "X-API-Key": deviceBKey }
  );
  expect(data.observations.length).toBeGreaterThan(0);
  for (const obs of data.observations) {
    expect(obs.sync_content_hash).toBeTruthy();
    expect(obs.sync_content_hash).toHaveLength(32);
  }
});
```

**Step 3: Run test**

Run: `cd /home/valor/Code/custom-skills/services/claude-mem-sync && bun test tests/sync.test.ts`
Expected: PASS（因為 `SELECT *` 已包含新欄位）

**Step 4: Commit**

```bash
git add services/claude-mem-sync/tests/sync.test.ts
git commit -m "測試(mem-sync): 驗證 pull response 包含 sync_content_hash"
```

---

### Task 7: Pulled Hashes 管理（Python Client）

**Files:**
- Modify: `script/utils/mem_sync.py` (新增 pulled_hashes 函式)
- Create: `tests/test_pulled_hashes.py`

**Step 1: Write the failing test**

```python
# tests/test_pulled_hashes.py
"""Tests for pulled hashes management."""
import tempfile
from pathlib import Path
from unittest.mock import patch

from script.utils.mem_sync import load_pulled_hashes, append_pulled_hashes


def test_load_empty_when_file_missing():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "pulled-hashes.txt"
        with patch("script.utils.mem_sync._get_pulled_hashes_path", return_value=path):
            hashes = load_pulled_hashes()
            assert hashes == set()


def test_append_and_load():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "pulled-hashes.txt"
        with patch("script.utils.mem_sync._get_pulled_hashes_path", return_value=path):
            append_pulled_hashes(["abc123", "def456"])
            hashes = load_pulled_hashes()
            assert hashes == {"abc123", "def456"}


def test_append_is_additive():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "pulled-hashes.txt"
        with patch("script.utils.mem_sync._get_pulled_hashes_path", return_value=path):
            append_pulled_hashes(["aaa"])
            append_pulled_hashes(["bbb"])
            hashes = load_pulled_hashes()
            assert hashes == {"aaa", "bbb"}


def test_load_ignores_blank_lines():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "pulled-hashes.txt"
        path.write_text("abc\n\ndef\n\n")
        with patch("script.utils.mem_sync._get_pulled_hashes_path", return_value=path):
            hashes = load_pulled_hashes()
            assert hashes == {"abc", "def"}
```

**Step 2: Run test to verify it fails**

Run: `cd /home/valor/Code/custom-skills && python -m pytest tests/test_pulled_hashes.py -v`
Expected: FAIL (ImportError)

**Step 3: Implement**

在 `script/utils/mem_sync.py` 中加入：

```python
PULLED_HASHES_FILENAME = "pulled-hashes.txt"


def _get_pulled_hashes_path() -> Path:
    return get_ai_dev_config_dir() / PULLED_HASHES_FILENAME


def load_pulled_hashes() -> set[str]:
    """讀取所有 pull 匯入過的 content hash。"""
    path = _get_pulled_hashes_path()
    if not path.exists():
        return set()
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def append_pulled_hashes(hashes: list[str]) -> None:
    """追加 pull 匯入的 content hash。"""
    if not hashes:
        return
    path = _get_pulled_hashes_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for h in hashes:
            f.write(h + "\n")
```

更新 `script/commands/mem.py` 的 import 列表加入 `load_pulled_hashes`, `append_pulled_hashes`。

**Step 4: Run test to verify it passes**

Run: `cd /home/valor/Code/custom-skills && python -m pytest tests/test_pulled_hashes.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add script/utils/mem_sync.py tests/test_pulled_hashes.py script/commands/mem.py
git commit -m "功能(mem-sync): pulled-hashes 檔案管理函式"
```

---

### Task 8: Client Push 流程重構

**Files:**
- Modify: `script/commands/mem.py:116-197` (push command)
- Modify: `script/utils/mem_sync.py` (新增 push_preflight 函式)

**Step 1: Add push_preflight utility**

在 `script/utils/mem_sync.py` 加入：

```python
def push_preflight(
    config: dict[str, Any], hashes: list[str]
) -> list[str]:
    """呼叫 server push-preflight API，回傳 server 上不存在的 hash 列表。"""
    if not hashes:
        return []
    result = api_request(config, "POST", "/api/sync/push-preflight", body={"hashes": hashes})
    return result.get("missing", [])
```

**Step 2: Modify push command**

修改 `script/commands/mem.py` 的 `push()` 函式（line 116-197）：

```python
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

    # 補齊 observations 引用但不在本次 push 範圍內的 sessions（避免 FK 違規）
    pushed_session_ids = {s["memory_session_id"] for s in sessions if s.get("memory_session_id")}
    missing_session_ids = {
        o["memory_session_id"]
        for o in observations
        if o.get("memory_session_id") and o["memory_session_id"] not in pushed_session_ids
    }
    if missing_session_ids:
        placeholders = ",".join("?" for _ in missing_session_ids)
        dep_sessions = query_local_db(
            f"SELECT * FROM sdk_sessions WHERE memory_session_id IN ({placeholders})",
            tuple(missing_session_ids),
        )
        sessions.extend(dep_sessions)

    raw_summaries = query_local_db(
        "SELECT * FROM session_summaries WHERE created_at_epoch > ?", (last_epoch,)
    )
    summaries, skipped_summaries = _normalize_summaries_for_push(raw_summaries)
    prompts = query_local_db(
        "SELECT * FROM user_prompts WHERE created_at_epoch > ?", (last_epoch,)
    )

    # ── Content Hash 去重 ──
    # 1. 排除 pull 匯入的 observations（防止推回外來資料）
    pulled_hashes = load_pulled_hashes()
    for obs in observations:
        obs["sync_content_hash"] = compute_content_hash(obs)

    original_count = len(observations)
    observations = [o for o in observations if o["sync_content_hash"] not in pulled_hashes]
    pulled_excluded = original_count - len(observations)

    # 2. Preflight 差集計算（只推送 server 上不存在的）
    if observations:
        obs_hashes = [o["sync_content_hash"] for o in observations]
        try:
            missing_hashes = set(push_preflight(config, obs_hashes))
            preflight_before = len(observations)
            observations = [o for o in observations if o["sync_content_hash"] in missing_hashes]
            preflight_skipped = preflight_before - len(observations)
        except RuntimeError:
            preflight_skipped = 0  # preflight 失敗時退回全量推送
    else:
        preflight_skipped = 0

    total = len(sessions) + len(observations) + len(summaries) + len(prompts)
    if total == 0:
        dedup_msg = ""
        if pulled_excluded > 0 or preflight_skipped > 0:
            dedup_msg = f"（去重排除：{pulled_excluded} pulled + {preflight_skipped} preflight）"
        if skipped_summaries > 0:
            console.print(
                f"[yellow]無可推送資料{dedup_msg}（已略過 {skipped_summaries} 筆 summaries，缺少 session_id）[/yellow]"
            )
        else:
            console.print(f"[green]無新資料需要推送{dedup_msg}[/green]")
        return

    console.print(
        f"[cyan]推送中：{len(sessions)} sessions, {len(observations)} observations, "
        f"{len(summaries)} summaries, {len(prompts)} prompts[/cyan]"
    )
    if pulled_excluded > 0 or preflight_skipped > 0:
        console.print(
            f"[dim]去重排除：{pulled_excluded} pulled + {preflight_skipped} preflight[/dim]"
        )
    if skipped_summaries > 0:
        console.print(
            f"[yellow]略過 {skipped_summaries} 筆 summaries（缺少 session_id）[/yellow]"
        )

    result = _api_request_or_exit(
        config,
        "POST",
        "/api/sync/push",
        body={
            "sessions": sessions,
            "observations": observations,
            "summaries": summaries,
            "prompts": prompts,
        },
    )

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
```

**Step 3: Verify**

手動測試：`ai-dev mem push`（需要 server 運行中）

**Step 4: Commit**

```bash
git add script/commands/mem.py script/utils/mem_sync.py
git commit -m "功能(mem-sync): push 加入 content hash preflight 去重"
```

---

### Task 9: Client Pull 流程重構

**Files:**
- Modify: `script/commands/mem.py:200-303` (pull command)

**Step 1: Modify pull command**

修改 `pull()` 函式，在匯入前用 hash 過濾，匯入後記錄 hash：

```python
@app.command()
def pull() -> None:
    """從 sync server 拉取其他裝置的新資料。"""
    config = load_server_config()
    last_epoch = config.get("last_pull_epoch", 0)

    all_data: dict[str, list] = {
        "sessions": [],
        "observations": [],
        "summaries": [],
        "prompts": [],
    }
    since = last_epoch
    server_epoch = since

    while True:
        result = _api_request_or_exit(
            config,
            "GET",
            f"/api/sync/pull?since={since}&limit=500",
        )
        for key in all_data:
            all_data[key].extend(result.get(key, []))
        server_epoch = result.get("server_epoch", server_epoch)
        if not result.get("has_more"):
            break
        since = result.get("next_since", since)

    # ── Content Hash 去重：用本地 hash 集合過濾已存在的 observations ──
    local_obs = query_local_db("SELECT title, narrative, facts, project, type FROM observations")
    local_hashes = {compute_content_hash(o) for o in local_obs}

    original_obs_count = len(all_data["observations"])
    new_observations = [
        o for o in all_data["observations"]
        if o.get("sync_content_hash") and o["sync_content_hash"] not in local_hashes
    ]
    hash_excluded = original_obs_count - len(new_observations)
    all_data["observations"] = new_observations

    total = sum(len(v) for v in all_data.values())
    if total == 0:
        msg = "[green]無新資料需要拉取[/green]"
        if hash_excluded > 0:
            msg += f" [dim]（hash 去重排除 {hash_excluded} observations）[/dim]"
        console.print(msg)
        return

    console.print(
        f"[cyan]拉取到：{len(all_data['sessions'])} sessions, "
        f"{len(all_data['observations'])} observations, "
        f"{len(all_data['summaries'])} summaries, "
        f"{len(all_data['prompts'])} prompts[/cyan]"
    )
    if hash_excluded > 0:
        console.print(f"[dim]hash 去重排除 {hash_excluded} observations[/dim]")

    # 匯入到本地 claude-mem（優先 HTTP API，fallback 直接寫 SQLite）
    import_payload = {
        "sessions": all_data["sessions"],
        "summaries": all_data["summaries"],
        "observations": all_data["observations"],
        "prompts": all_data["prompts"],
    }

    import_result: dict[str, Any] = {}
    import_method = "api"

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
            "[yellow]claude-mem worker 未啟動，改用直接寫入 SQLite...[/yellow]"
        )
        import_method = "sqlite"
        try:
            import_result = import_to_local_db(import_payload)
        except FileNotFoundError as e:
            console.print(f"[bold red]{e}[/bold red]")
            raise typer.Exit(code=1)

    # 記錄匯入的 observation hash 到 pulled-hashes.txt
    imported_hashes = [
        o["sync_content_hash"]
        for o in all_data["observations"]
        if o.get("sync_content_hash")
    ]
    append_pulled_hashes(imported_hashes)

    config["last_pull_epoch"] = server_epoch
    save_server_config(config)

    stats = import_result.get("stats", {})
    method_label = "SQLite" if import_method == "sqlite" else "API"
    console.print(
        f"[bold green]Pull 完成[/bold green] ({method_label}) "
        f"imported: {stats.get('sessionsImported', 0)}s "
        f"{stats.get('observationsImported', 0)}o "
        f"{stats.get('summariesImported', 0)}sm "
        f"{stats.get('promptsImported', 0)}p | "
        f"skipped: {stats.get('sessionsSkipped', 0)}s "
        f"{stats.get('observationsSkipped', 0)}o "
        f"{stats.get('summariesSkipped', 0)}sm "
        f"{stats.get('promptsSkipped', 0)}p"
    )

    # 自動重建 ChromaDB 搜尋索引（worker 在線時）
    obs_imported = stats.get("observationsImported", 0)
    if obs_imported > 0 and worker_available():
        console.print("[cyan]正在同步 ChromaDB 搜尋索引...[/cyan]")
        try:
            reindex_stats = reindex_observations()
            synced = reindex_stats["synced"]
            errors = reindex_stats["errors"]
            if synced > 0 or errors > 0:
                console.print(
                    f"[green]索引同步完成[/green] synced={synced} errors={errors}"
                )
        except (FileNotFoundError, RuntimeError):
            console.print(
                "[yellow]ChromaDB 索引同步失敗，稍後可執行 ai-dev mem reindex 補建[/yellow]"
            )
```

**Step 2: Verify**

手動測試：`ai-dev mem pull`

**Step 3: Commit**

```bash
git add script/commands/mem.py
git commit -m "功能(mem-sync): pull 加入 content hash 去重過濾"
```

---

### Task 10: Client Cleanup 子命令

**Files:**
- Modify: `script/commands/mem.py` (新增 cleanup command)

**Step 1: Implement cleanup command**

在 `reindex()` 命令之後加入：

```python
@app.command()
def cleanup() -> None:
    """掃描並刪除本地 claude-mem 中的重複 observations。"""
    obs = query_local_db(
        "SELECT id, title, narrative, facts, project, type FROM observations ORDER BY id"
    )
    if not obs:
        console.print("[green]本地無 observations[/green]")
        return

    # 按 content hash 分組，保留 id 最小的
    hash_groups: dict[str, list[int]] = {}
    for o in obs:
        h = compute_content_hash(o)
        hash_groups.setdefault(h, []).append(o["id"])

    duplicate_ids: list[int] = []
    for ids in hash_groups.values():
        if len(ids) > 1:
            duplicate_ids.extend(ids[1:])  # 保留第一個（id 最小）

    if not duplicate_ids:
        console.print(f"[green]無重複 observations[/green]（共 {len(obs)} 筆）")
        return

    # 刪除重複
    conn = __import__("sqlite3").connect(str(CLAUDE_MEM_DB_PATH))
    try:
        placeholders = ",".join("?" for _ in duplicate_ids)
        conn.execute(
            f"DELETE FROM observations WHERE id IN ({placeholders})",
            duplicate_ids,
        )
        conn.commit()
    finally:
        conn.close()

    console.print(
        f"[bold green]Cleanup 完成[/bold green] "
        f"移除 {len(duplicate_ids)} 筆重複（共 {len(obs)} 筆）"
    )
```

注意：需要在檔案頂部匯入 `CLAUDE_MEM_DB_PATH`（已經透過 `mem_sync` 匯入路徑可用）。

**Step 2: Verify**

手動測試：`ai-dev mem cleanup`

**Step 3: Commit**

```bash
git add script/commands/mem.py
git commit -m "功能(mem-sync): 新增 ai-dev mem cleanup 去重指令"
```

---

### Task 11: Client Status 增強

**Files:**
- Modify: `script/commands/mem.py:306-323` (status command)

**Step 1: Enhance status command**

```python
@app.command()
def status() -> None:
    """顯示 sync server 同步狀態。"""
    config = load_server_config()
    result = _api_request_or_exit(config, "GET", "/api/sync/status")

    # 本地統計
    local_obs = query_local_db("SELECT id, title, narrative, facts, project, type FROM observations")
    hash_counts: dict[str, int] = {}
    for o in local_obs:
        h = compute_content_hash(o)
        hash_counts[h] = hash_counts.get(h, 0) + 1
    local_duplicates = sum(c - 1 for c in hash_counts.values() if c > 1)
    pulled_count = len(load_pulled_hashes())

    table = Table(title="claude-mem Sync Status")
    table.add_column("項目", style="cyan")
    table.add_column("值", style="green")
    table.add_row("Server sessions", str(result.get("sessions", 0)))
    table.add_row("Server observations", str(result.get("observations", 0)))
    table.add_row("Server summaries", str(result.get("summaries", 0)))
    table.add_row("Server prompts", str(result.get("prompts", 0)))
    table.add_row("Server devices", str(result.get("devices", 0)))
    table.add_row("───", "───")
    table.add_row("Local observations", str(len(local_obs)))
    table.add_row("Local duplicates", str(local_duplicates))
    table.add_row("Pulled hashes tracked", str(pulled_count))
    console.print(table)

    console.print(f"[dim]Last push epoch: {config.get('last_push_epoch', 0)}[/dim]")
    console.print(f"[dim]Last pull epoch: {config.get('last_pull_epoch', 0)}[/dim]")
```

**Step 2: Verify**

手動測試：`ai-dev mem status`

**Step 3: Commit**

```bash
git add script/commands/mem.py
git commit -m "功能(mem-sync): status 顯示本地去重統計"
```

---

### Task 12: 整合測試與最終驗證

**Files:**
- Modify: `services/claude-mem-sync/tests/sync.test.ts` (end-to-end dedup test)

**Step 1: Add cross-device dedup integration test**

```typescript
test("cross-device push dedup via sync_content_hash", async () => {
  // Device A pushes observation
  const obs = {
    memory_session_id: "dedup-ms-001",
    project: "dedup-test",
    type: "discovery",
    title: "Cross-device test",
    narrative: "Should not duplicate",
    facts: "[]",
    created_at: "2026-02-24T02:00:00Z",
    created_at_epoch: 1771862400000,
    sync_content_hash: null as string | null,
  };
  // Server will compute hash automatically

  await apiRequest("POST", "/api/sync/push", {
    sessions: [{
      content_session_id: "dedup-cs-001",
      memory_session_id: "dedup-ms-001",
      project: "dedup-test",
      started_at: "2026-02-24T02:00:00Z",
      started_at_epoch: 1771862400000,
      status: "completed",
    }],
    observations: [obs],
    summaries: [],
    prompts: [],
  }, { "X-API-Key": deviceAKey });

  // Device B pushes same content (different session context)
  const { data } = await apiRequest("POST", "/api/sync/push", {
    sessions: [{
      content_session_id: "dedup-cs-002",
      memory_session_id: "dedup-ms-002",
      project: "dedup-test",
      started_at: "2026-02-24T02:00:00Z",
      started_at_epoch: 1771862400000,
      status: "completed",
    }],
    observations: [{
      ...obs,
      memory_session_id: "dedup-ms-002",
      created_at_epoch: 1771862401000,  // slightly different epoch
    }],
    summaries: [],
    prompts: [],
  }, { "X-API-Key": deviceBKey });

  // Same content → should be skipped via sync_content_hash
  expect(data.stats.observationsSkipped).toBe(1);
});
```

**Step 2: Run full test suite**

Run: `cd /home/valor/Code/custom-skills/services/claude-mem-sync && bun test`
Expected: ALL PASS

Run: `cd /home/valor/Code/custom-skills && python -m pytest tests/test_mem_sync_hash.py tests/test_pulled_hashes.py -v`
Expected: ALL PASS

**Step 3: Commit**

```bash
git add services/claude-mem-sync/tests/sync.test.ts
git commit -m "測試(mem-sync): 跨裝置 content hash 去重整合測試"
```

---

## 任務依賴圖

```
Task 1 (Python hash) ─────┐
                           ├── Task 8 (Client push) ── Task 12 (整合測試)
Task 2 (TS hash) ──┐      │
                    ├── Task 5 (Server push+preflight)
Task 3 (Migration) ┤      │
                    ├── Task 4 (Backfill)
                    │      │
                    └── Task 6 (Server pull)
                           │
Task 7 (Pulled hashes) ───┤
                           ├── Task 9 (Client pull)
                           ├── Task 10 (Cleanup)
                           └── Task 11 (Status)
```

**可並行：** Task 1 + Task 2 + Task 3, Task 7 + Task 5 + Task 6, Task 10 + Task 11
