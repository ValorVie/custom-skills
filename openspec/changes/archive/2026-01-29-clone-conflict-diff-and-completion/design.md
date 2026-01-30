## Context

`ai-dev clone` 分發資源時，透過 `ManifestTracker` 預掃描計算 hash，再用 `detect_conflicts()` 比對舊 manifest 與目標檔案現有 hash。衝突時顯示 hash 差異，提供 4 個選項（force/skip/backup/abort）。使用者無法看到具體改了什麼。

Shell completion 方面，Typer 內建 `--install-completion` 支援，但需要使用者手動執行。

## Goals / Non-Goals

**Goals:**
- 衝突時讓使用者能查看來源與目標的具體 diff，做出知情的決策
- `ai-dev install` 自動安裝 shell completion

**Non-Goals:**
- 不做逐檔選擇性覆蓋（全部覆蓋或全部跳過）
- 不做自訂 completion（Typer 內建即足夠）
- 不做 diff 工具的自訂選擇

## Decisions

### 1. diff 顯示方式：系統 `diff` 指令

**選擇**：呼叫系統 `diff --color -u` / `diff --color -ruN`（目錄）

**理由**：
- 系統 `diff` 在 macOS/Linux 上普遍存在
- `--color` 旗標提供彩色輸出
- `-u` 為 unified diff 格式，易讀
- 不需引入新的 Python 依賴（如 `difflib`）
- 使用者熟悉 diff 格式

**替代方案（不採用）**：
- Python `difflib`：輸出格式較不美觀，需要自行處理 Rich 格式化
- 外部工具（delta, difft）：不保證安裝

### 2. 路徑追蹤：在 FileRecord 與 ConflictInfo 中記錄路徑

**選擇**：`FileRecord` 新增 `source_path: Path | None`，`ConflictInfo` 新增 `source_path` 和 `target_path`

**理由**：
- `detect_conflicts()` 已經計算 `target_path`，只需保留而非丟棄
- `source_path` 需從 `new_tracker` 的 `FileRecord` 取得，因此 `FileRecord` 也需記錄
- 路徑為 optional（`None`），不影響既有功能

### 3. 互動選單順序

**選擇**：查看差異排在第 4 位（備份後覆蓋之後、取消分發之前）

```
1. 強制覆蓋所有衝突檔案
2. 跳過衝突檔案
3. 備份後覆蓋
4. 查看差異
5. 取消分發
```

**理由**：使用者通常先決定處理方式，查看差異是輔助決策。取消分發作為最後一個選項（安全出口）。

### 4. diff 後行為：重新顯示選單

**選擇**：查看 diff 後回到衝突清單和選單

**理由**：查看差異是「資訊收集」而非「動作」，使用者看完後需要選擇實際處理方式。

### 5. Shell completion 安裝方式：subprocess 呼叫

**選擇**：在 `install.py` 中用 `subprocess.run(["ai-dev", "--install-completion"])` 自動安裝

**理由**：
- Typer 內部的 completion install API 不是公開穩定介面
- subprocess 呼叫更穩定，且與使用者手動執行效果一致
- 失敗時只顯示提示，不阻擋安裝流程

## Risks / Trade-offs

- **[Risk] 系統無 diff 指令** → macOS/Linux 預設都有；如果 `diff` 不存在，捕獲例外並顯示「diff 工具未安裝」提示
- **[Risk] diff 輸出過長（大型 skill 目錄）** → 直接輸出到 terminal，使用者可用 scroll 查看；不做分頁
- **[Risk] completion install 在非互動環境失敗** → 捕獲例外，只輸出提示訊息
