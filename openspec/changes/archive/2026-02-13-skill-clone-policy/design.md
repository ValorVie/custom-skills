## Context

`_copy_with_log()` 在複製 skills 時使用 `shutil.copytree(item, dst_item, dirs_exist_ok=True)`，以整個目錄為單位複製。ManifestTracker 提供目錄層級的 hash 衝突檢測（`compute_dir_hash`），但無法區分「哪些檔案是上游程式碼、哪些是使用者資料」。

`auto-skill` 的 `knowledge-base/` 和 `experience/` 含有使用者累積的知識條目，每次 clone 會被來源的空模板覆蓋。使用者只能在衝突提示中選擇「全部覆蓋」或「全部跳過」，無法精細控制。

現有程式碼已有先例：`integrate_to_dev_project()` 在複製 auto-skill 時使用 `shutil.ignore_patterns(".git", "assets", "README.md")` 進行過濾（shared.py:1245）。

## Goals / Non-Goals

**Goals:**
- 允許 skill 作者透過 `.clonepolicy.json` 宣告檔案層級的複製策略
- 支援三種策略：default（hash 比對 + 互動提示）、key-merge（JSON 合併）、skip-if-exists
- 為 `auto-skill` 配置 `.clonepolicy.json`，保護使用者知識庫
- 與現有 ManifestTracker 衝突檢測機制相容

**Non-Goals:**
- 不改變無 `.clonepolicy.json` 的 skill 行為（零破壞性）
- 不新增檔案層級的 manifest 追蹤（維持目錄層級 hash）
- 不支援 skills 以外的資源類型（commands、agents 等無此需求）
- 不支援任意合併策略（僅 key-merge，不做深度 JSON merge）

## Decisions

### D1: 配置驅動而非程式碼硬編碼

**選擇**：使用 `.clonepolicy.json` 配置檔宣告策略
**替代方案**：在 `_copy_with_log` 中硬編碼 `auto-skill` 的排除規則
**理由**：配置檔讓任何 skill 作者都能使用此機制，不需修改核心程式碼。且 `.clonepolicy.json` 以 `.` 開頭，不會被當成 skill 內容處理。

### D2: 逐檔複製取代 copytree

**選擇**：偵測到 `.clonepolicy.json` 時，改用 `os.walk` + 逐檔複製，依規則決定每個檔案的處理方式
**替代方案**：使用 `shutil.copytree` 的 `ignore` 參數 + 後處理
**理由**：`copytree` 的 `ignore` 只能跳過，無法實現 key-merge 或互動提示。逐檔複製提供最大的控制彈性。

### D3: key-merge 僅做一層 key 合併

**選擇**：對 `_index.json` 中的陣列欄位（`categories`/`skills`），以 `id`/`skillId` 為 key 做合併——來源有但目標沒有的條目新增，目標已有的保留不動
**替代方案**：深度遞迴 merge 或 JSON patch
**理由**：`_index.json` 結構簡單且固定（頂層 metadata + 一個 array of objects），一層合併即可覆蓋所有需求場景。深度 merge 引入不必要的複雜度。

### D4: default 策略使用檔案層級 hash 比對

**選擇**：對未匹配任何規則的檔案（如 `SKILL.md`），計算 source hash vs target hash，不同時互動提示
**替代方案**：直接覆蓋
**理由**：使用者可能自訂 `SKILL.md`，與現有目錄層級衝突檢測的設計精神一致。復用 `manifest.py` 的 `compute_file_hash()` 函式。

### D5: `.clonepolicy.json` 不被複製到目標

**選擇**：複製邏輯自動跳過 `.clonepolicy.json` 本身
**理由**：此檔案是給 clone 流程使用的 metadata，不是 skill 內容的一部分。

## Risks / Trade-offs

- **[Risk] 互動提示中斷自動化流程** → 現有 `--force` / `--skip-conflicts` flag 同樣適用於檔案層級策略，維持一致行為
- **[Risk] key-merge 遺失欄位** → 僅對 array-of-objects 合併，metadata 欄位（`version`、`lastUpdated`）保留目標值，不做覆蓋
- **[Trade-off] 逐檔複製效能略差於 copytree** → 只有含 `.clonepolicy.json` 的 skill 走此路徑，影響範圍極小
- **[Trade-off] ManifestTracker 的目錄 hash 含使用者資料** → 有 policy 的 skill 每次 clone 都會因使用者資料不同而觸發衝突偵測，但因已改用逐檔處理，目錄層級的衝突偵測可跳過此 skill
