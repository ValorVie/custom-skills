## Context

`ai-dev sync pull` 目前的流程：`git pull --rebase` → `sync_directory(repo → local)`。sync_directory 使用 rsync（或 shutil fallback），直接將 repo 內容覆蓋到本機目錄，不偵測本機是否有未 push 的異動。

現有基礎設施：
- `count_directory_changes(local_path, repo_path, excludes)` — 已存在，用於 `sync status` 表格中計算 Local Changes 欄位
- `_collect_files(root, excludes)` — 已存在，用於 shutil sync 時收集檔案清單
- `_files_equal(left, right)` — 已存在，用 `filecmp.cmp` 比較檔案內容

## Goals / Non-Goals

**Goals:**
- pull 前偵測本機目錄與 sync repo 的差異（未 push 的本機異動）
- 有異動時顯示變更清單並提供互動式選項
- 提供 `--force` flag 跳過偵測，供腳本/自動化使用
- 無異動時行為完全不變

**Non-Goals:**
- 不做檔案層級 merge（同步內容含 binary，自動合併不可靠）
- 不做自動備份機制（git history 本身就是備份，push 後變更都在遠端）
- 不修改 push 流程
- 不處理 git rebase 衝突（由 git 本身處理）

## Decisions

### D1: 偵測方式 — 比較 local 與 repo

**選擇**：比較本機目錄與 sync repo 中的對應子目錄，列出差異檔案

**替代方案**：追蹤 last_push 時間戳，比較檔案 mtime

**理由**：已有 `count_directory_changes()` 計算差異數量。需擴充為回傳差異檔案清單（不只是數量），重用同一套比較邏輯，結果準確且不依賴時間戳。

### D2: 互動式選項設計

**選擇**：三個選項 — 先 push 再 pull（推薦）、強制覆蓋、取消

**替代方案**：只顯示警告 + `--force` 確認、自動 push 後 pull

**理由**：
- 「先 push 再 pull」最安全：本機異動先推到遠端（git rebase 處理順序），再拉取最新。兩邊變更都保留在 git history。
- 「強制覆蓋」對應明確不需要本機異動的場景。
- 「取消」讓使用者有機會先手動檢查。
- 不自動 push：使用者可能不想推送當前狀態（例如正在調試中的 config）。

### D3: `--force` flag 行為

**選擇**：`--force` 跳過偵測，直接執行原有 pull 流程

**理由**：腳本自動化（如 cron job）需要非互動式操作。`--force` 等同現有行為，向後相容。

### D4: 變更清單顯示上限

**選擇**：最多顯示 10 個檔案，超過則顯示「...及其他 N 個檔案」

**理由**：sync 目錄可能有大量小變更（如 projects/ 下的多個 CLAUDE.md），全部列出會淹沒終端。10 個足以讓使用者判斷是否重要。

### D5: 「先 push 再 pull」的實作方式

**選擇**：直接呼叫現有的 push 流程函式，完成後再執行 pull

**替代方案**：重新實作 push 邏輯

**理由**：復用現有 push 流程（含 LFS 偵測、plugin manifest、gitattributes 等），避免重複程式碼。push 成功後自然進入 pull 流程。

## Risks / Trade-offs

- **[Risk] push 失敗** → 「先 push 再 pull」時若 push 失敗（如網路問題、rebase 衝突），顯示錯誤並中止，不繼續 pull。使用者可手動解決後重試。
- **[Risk] 偵測延遲** → 每個同步目錄都要掃描差異，目錄大時可能數秒。可接受，因為 pull 本身就需要網路 IO。
- **[Trade-off] 不做備份** → 依賴 git history 作為備份。若使用者選「強制覆蓋」但從未 push 過，變更會永久遺失。互動式提示已足夠警告。
