## Context

claude-mem-sync 是自架的跨裝置 claude-mem 同步系統，透過中央 PostgreSQL 作為 relay，各裝置用 HTTP API push/pull 資料。現有去重依賴 `(memory_session_id, title, created_at_epoch)` 組合鍵和 `origin_device_id IS DISTINCT FROM` 過濾器。

已知問題：
- 同內容不同 metadata 的 observation 繞過 UNIQUE 約束（#238/#100 重複案例）
- Push epoch 斷點 crash 導致重推
- 跨裝置同步迴圈（A→Server→B→Server→A）
- ChromaDB reindex 產生淺拷貝

相關設計文件：
- `docs/plans/2026-02-24-claude-mem-sync-server-design.md` — 原始 sync server 架構
- `docs/plans/2026-02-24-claude-mem-sync-server-impl.md` — 原始 sync server 實作
- `docs/plans/2026-02-24-mem-sync-dedup-design.md` — 去重設計（已核准）
- `docs/plans/2026-02-24-mem-sync-dedup-impl.md` — 去重實作計畫（12 tasks）

## Goals / Non-Goals

**Goals:**
- 以 content hash 作為全域唯一識別碼，從根本消除所有重複場景
- 減少 push/pull 傳輸量（只傳真正新的資料）
- 防止跨裝置同步迴圈
- 清理現有 server 和 client 中的重複資料
- Python 和 TypeScript 的 hash 計算結果完全一致

**Non-Goals:**
- 不變更 sessions / summaries / prompts 的去重機制（現有 UNIQUE 約束已足夠）
- 不重新設計 sync 協議的基本架構（push/pull relay 模式不變）
- 不處理 ChromaDB 直寫問題（reindex 機制已獨立處理）

## Decisions

### D1: Hash 演算法 — SHA-256 截取 128 bits

**選擇：** `hashlib.sha256(json_payload).hexdigest()[:32]`

**替代方案：**
- MD5（128 bits）— 已知碰撞攻擊，不適合去重場景
- SHA-256 完整（256 bits）— 浪費儲存空間，32 hex chars 已有 10⁻²⁰ 衝突率
- xxHash（非密碼學）— 速度快但不保證跨語言一致性

**理由：** SHA-256 前 128 bits 在百萬筆規模下衝突率遠低於安全門檻，且 Python/TypeScript 標準庫都有原生支援，跨語言一致性有保障。

### D2: Hash 參與欄位 — 5 個內容欄位

**選擇：** `title`, `narrative`, `facts`, `project`, `type`

**排除：** `id`, `memory_session_id`, `created_at_epoch`, `origin_device_id`, `synced_at`

**理由：** 同一筆記憶在不同裝置可能有不同的 `memory_session_id`（session 生命週期不同）和 `created_at_epoch`（時鐘偏移），但內容是相同的。排除 metadata 才能正確識別「相同內容」。

### D3: JSON 序列化標準化 — sort_keys=True

**選擇：** `json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))`

Python 端使用 `separators=(",", ":")` 產生 compact JSON（無多餘空格），與 TypeScript `JSON.stringify()` 的預設輸出格式一致。這確保相同輸入在兩個語言產生位元組完全相同的 JSON 字串。

**理由：** JSON key 順序不保證一致。Python 的 `sort_keys=True` 按字母排序，TypeScript 的 `JSON.stringify` 按 insertion order。因此 TypeScript 端必須按字母順序構造物件（facts, narrative, project, title, type）。跨語言測試以已知向量 `14e05009b56669e285c9338331d18dc7` 驗證一致性。

### D4: 去重層級 — Server UNIQUE + Client Preflight + Pulled-Hashes

**選擇：** 三層防禦

| 層級 | 機制 | 目的 |
|------|------|------|
| Server | `ON CONFLICT (sync_content_hash) DO NOTHING` | 最終保障，不可能繞過 |
| Client Push | Preflight API 差集 | 減少無效傳輸 |
| Client Push | pulled-hashes 排除 | 防止推回外來資料 |

**替代方案：** 只用 Server UNIQUE 約束（單層）— 功能正確但每次都全量傳輸。

**理由：** Server 約束是安全網，但 preflight 和 pulled-hashes 大幅減少網路傳輸。三層成本低但收益明確。

### D5: Pulled-Hashes 存儲 — 純文字檔案

**選擇：** `~/.config/ai-dev/pulled-hashes.txt`，一行一個 hash

**替代方案：**
- SQLite 表 — 過重，需要額外管理
- YAML config 內嵌 — list 過長影響 config 可讀性
- Bloom filter — 有假陽性，實作複雜

**理由：** 萬筆 × 32 chars ≈ 330KB，append-only，讀取為 set() 效率高。簡單可靠。

## Risks / Trade-offs

- **[Risk] JSON 序列化跨語言不一致** → 用已知測試向量交叉驗證 Python 和 TypeScript 的 hash 輸出。
- **[Risk] 舊版 client 不帶 sync_content_hash** → Server 端 fallback：push 時如果沒有 hash 則自動計算。保留舊 UNIQUE 約束作為備份。
- **[Risk] Migration 002 回填大量資料時 server 啟動慢** → 只有首次啟動需要回填，後續啟動跳過（`WHERE sync_content_hash IS NULL` 為空集合）。
- **[Risk] pulled-hashes.txt 檔案持續增長** → 月級別約 1000 行 × 32 chars ≈ 33KB，年級別 < 400KB。可忽略。未來可加定期 truncate。
- **[Trade-off] Preflight 增加一次 round-trip** → Payload 極小（32 chars × N），延遲 < 100ms。換來 90%+ 傳輸量減少。
- **[Trade-off] 保留舊 UNIQUE 約束造成雙重約束** → 過渡期安全，未來確認穩定後可移除。
