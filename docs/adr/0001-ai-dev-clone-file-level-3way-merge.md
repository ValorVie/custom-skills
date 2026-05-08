# ADR 0001：ai-dev clone 採 file-level 3-way merge 與 manifest v2

- **狀態**：Accepted
- **日期**：2026-05-08
- **相關來源**：mp-grill-with-docs 對話沉澱

## Context

`ai-dev clone` 將 `~/.config/custom-skills/`、`~/.config/qdm-ai-tools/`、`ecc` 三個 git repo 的 skills 分發到 claude / codex / gemini / antigravity / opencode 等 target 平台。

當 dst 與 src 內容不同時，`script/utils/smart_merge.py` 進入互動式 prompt：`[A]` append、`[I]` incremental、`[O]` overwrite、`[S]` skip、`[D]` 顯示 unified diff。

現行模型的不足：

1. 比對僅 src ↔ dst 二路，沒有「使用者上次接受的 base 版本」紀錄。
2. 即使來源 commit 未變，使用者改過 dst 後每次 clone 都會被重複追問同一個檔案。
3. 使用者無法判斷「本次來源是否真的更新了」，只能憑記憶。
4. `[D]` 只能看 src vs dst，看不到「我自己改了什麼」與「來源新加了什麼」分別是哪些。
5. 既有 `~/.config/ai-dev/manifests/<target>.yaml` 已經以 skill-level 紀錄 src hash 與 last_sync，但顆粒度過粗，無法用來做 3-way 判斷。

## Decision

### 1. 升級為 file-level 3-way merge tracking

每筆紀錄的 key 為 `(target, source, file relative path)`，紀錄欄位至少包含：

- `src_hash`：上次 sync 寫進 dst 時的 src 內容 hash。
- `src_commit`：對應 source repo 的 git commit。
- `src_source`：來源 repo 名（custom-skills / qdm-ai-tools / ecc）。
- `dst_hash_at_sync`：寫入 dst 時 dst 的 hash，用以偵測使用者後來是否動過 dst。
- `decision`：`accepted` / `skipped` / `overwritten` / `appended` / `incremental`。
- `decided_at`：時間戳。

### 2. 衝突分類採 3-way

| 分類 | 條件 | 行為 |
|------|------|------|
| `clean` | dst == base，src 動 | 自動套用新版，不 prompt |
| `local-only` | src == base，dst 動 | 靜默保留本地版，輸出一行提示 |
| `both-changed` | 兩邊皆動 | prompt 使用者 |
| `no-base` | manifest 無此筆紀錄 | 退回現行二路 prompt |

### 3. Skip 記憶以 `(file, src_commit)` 為 key

使用者選 skip 後，同一 src_commit 不再提示；src_commit 一變就重評估為 both-changed。

### 4. Manifest 原地擴充至 schema v2

沿用 `~/.config/ai-dev/manifests/<target>.yaml`，於 root 加 `schema_version: 2`（與既有 `version` 不衝突）。原 `files.skills.<skill-name>.hash` 結構升為 `files.skills.<skill-name>.files.<rel-path>`。

### 5. clone 啟動時輸出 per-source update summary

逐 source 列出：上次 sync commit、本次 commit、來源變動檔數、影響本 target 檔數。

### 6. Diff UI 三向化

`[D]` 拆為 `[Ds]` src vs base、`[Dl]` dst vs base、`[Dc]` src vs dst。預設先輸出三行摘要：「來源動了 +N -M」「你動了 +P -Q」「兩邊重疊改動 +R -S」。

## Alternatives Considered

- **以 skill 為單位**：粒度過粗，使用者改一個檔即整個 skill 標 dirty，犧牲精確度。
- **以整個 repo 為單位**：無法處理使用者只改一個 skill 的常見情境。
- **新開 `tracking/<target>.yaml` 與 manifests 平行**：三個評估點分散兩處，後續維護要同步兩份檔案。
- **廢棄 manifests/ 全新設計**：所有讀 manifests 的程式都要改名，風險高且無收益。
- **保留二路比對僅在提示文字加分類**：使用者仍會被 local-only 情境反覆打擾，治標不治本。
- **dst 端 sidecar `<dst>.ai-dev-base`**：在使用者目錄留下 sidecar 檔案，污染檔案結構。

## Consequences

**正面：**

- 使用者只在真正衝突（both-changed）時被打斷。
- 來源未變時的 skip 決定會被尊重，不再被反覆追問。
- 多來源摘要讓使用者一眼判斷「本次有沒有需要動的」。
- 復用既有 manifests 路徑，沒有額外目錄。

**負面：**

- Manifest 體積增長：file-level 紀錄會比 skill-level 大數倍。
- 首次升級需要 schema migration（細節見 OpenSpec change 的 open questions）。
- 3-way 衝突分類若 `dst_hash_at_sync` 漂移（例如使用者外部工具改檔），需要明確 fallback。
- 三向 diff 增加互動成本，需要良好的提示說明，否則使用者學不會 `[Ds]/[Dl]/[Dc]`。

## 已敲定的決議補充

- **三個來源都是 git repo**（custom-skills、qdm-ai-tools、ecc），所有 src_commit 都從各自 git log 取得，不需要備援識別。
- **Schema v1 → v2 migration**：採方案 C。Migration 過程只對 `dst hash == src hash` 的檔案自動標 base（從現有 manifest 的 `last_sync` 對應到 source repo 的 commit），其餘 entry 一律退回 no-base，第一次遇到時走現行 prompt 流程。理由：B 會把使用者明明改過、與 src 不同的 dst 誤標 base，下次 src 動就靜默覆蓋本地修改；A 等於全部重答；C 物理上等同事實，唯一安全選項。
- **`--target X` 時的 summary 範圍**：全列所有來源變動，但每筆顯示「影響本次 target」為主欄、「影響其他 target」為 dim 次欄。理由：summary 屬於來源層資訊，不應因本次 flag 變動；多 target 使用者輪流跑時資訊保持一致；dim 化降低視覺干擾。輸出格式：

  ```
  來源更新摘要（自上次 sync）
    custom-skills    abc1234 → def5678   檔案變動 12   影響 claude 3   [其他 target 9]
    qdm-ai-tools     未變更
    ecc              5e6f789 → f9a8b7c   檔案變動 1    影響 claude 1   [其他 target 0]
  ```

- **`--untrack` 反向指令**：本輪不做。
- **既有 `version: 1.2.8` 欄位**：忽略，以實際檔案為主；v2 用獨立的 `schema_version: 2` 欄位辨識。

## Status 變更紀錄

- 2026-05-08：Proposed → Accepted（mp-grill-with-docs 對話沉澱、open questions 全數收斂）
