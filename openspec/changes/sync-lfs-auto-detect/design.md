## Context

`ai-dev sync` 使用 Git 同步 `~/.claude` 和 `~/.claude-mem` 到遠端倉庫。其中 `chroma.sqlite3`（ChromaDB 向量資料庫）已達 60.85 MB，接近 GitHub 100 MB 硬限制。SQLite 為 binary 格式，git 無法 delta 壓縮，每次 commit 存完整副本，加速 repo 膨脹。

現有架構：
- `generate_gitattributes()` 產生固定內容（`*.jsonl merge=union` + `*.md text eol=lf`）
- `write_gitattributes(repo_dir)` 寫入 `.gitattributes`
- `init` 與 `push` 流程中在 `_sync_local_to_repo()` 後呼叫 `write_gitattributes()`
- 無任何 LFS 相關程式碼

## Goals / Non-Goals

**Goals:**
- 自動偵測 sync repo 中超過 50 MB 的檔案，以副檔名產生 LFS track pattern
- 整合到 init/push 流程，無需使用者手動設定
- 未安裝 git-lfs 時 graceful degradation（警告不阻擋）
- 既有 repo 中的大檔案可自動 migrate 為 LFS 物件

**Non-Goals:**
- 不對 `*.jsonl` 使用 LFS（需保留 `merge=union` 合併策略）
- 不提供 CLI 手動設定 LFS pattern 的介面
- 不處理 GitHub LFS storage quota 管理
- 不修改 `sync.yaml` schema（LFS 狀態無需持久化，每次動態偵測）

## Decisions

### D1: 動態偵測 vs 寫死 pattern

**選擇**：動態掃描 repo 中超過閾值的檔案，以副檔名為單位產生 pattern

**替代方案**：寫死 `["*.sqlite3", "*.db"]`

**理由**：使用者可能新增自訂同步目錄（`ai-dev sync add`），其中可能包含任何類型的大檔案。動態偵測確保所有場景都能自動處理，不需要維護 pattern 清單。

### D2: 偵測時機 — sync 後、commit 前

**選擇**：在 `_sync_local_to_repo()` 完成後（檔案已在 repo 中）、`git_add_commit()` 之前掃描

**替代方案**：在 sync 前掃描本機目錄 / 在 git add 時攔截

**理由**：sync 後 repo 中的檔案即為實際要 commit 的內容，此時掃描最準確。在 sync 前掃描可能因 ignore 規則而不一致。

### D3: LFS migrate 策略

**選擇**：`init` 時若偵測到已追蹤的大檔案，執行 `git lfs migrate import --include=<patterns> --everything`

**替代方案**：不做 migrate，只從下一次 commit 開始走 LFS

**理由**：不 migrate 的話，已追蹤的大檔案仍以原始方式存在 history 中，GitHub 警告不會消失。migrate 可以清理整個 history。但 migrate 會改寫 history，需要 force push。因此僅在 `init`（首次設定）時執行，`push` 不做 migrate。

### D4: JSONL 排除機制

**選擇**：在 `detect_lfs_patterns()` 中用 `LFS_EXCLUDE_EXTENSIONS` set 排除

**理由**：JSONL 使用 `*.jsonl merge=union` 讓 git 自動按行合併，是解決跨機器 session 衝突的關鍵機制。LFS 會將檔案視為 binary，完全失去此能力。

### D5: `git lfs install` 範圍

**選擇**：`git lfs install --local`（僅影響 sync repo，不修改全域 git config）

**理由**：避免影響使用者其他 git repo 的行為。

## Risks / Trade-offs

- **[Risk] migrate 改寫 git history** → 僅在 `init` 時執行（首次設定場景），且 init 本來就會 force push 建立倉庫。`push` 不做 migrate。
- **[Risk] 第二台機器未安裝 git-lfs** → `git clone` 不會拉取 LFS 物件，只下載 pointer file。偵測到後顯示警告訊息，提示安裝 git-lfs 並執行 `git lfs pull`。
- **[Risk] 閾值邊緣 — 檔案在 49-51 MB 間波動** → 閾值設 50 MB 與 GitHub 建議一致。一旦觸發過 LFS track，`.gitattributes` 會保留規則，不會因檔案縮小而移除。
- **[Trade-off] 副檔名 vs 完整路徑** → 用副檔名 pattern（`*.sqlite3`）而非完整路徑，覆蓋範圍更廣但可能誤觸同類型小檔案。考慮到 sync repo 內容可控（`~/.claude` 和 `~/.claude-mem`），誤觸風險極低。
