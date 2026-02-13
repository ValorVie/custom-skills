## Context

`ai-dev status` 目前顯示三張表（核心工具、NPM 套件、設定儲存庫），其中「設定儲存庫」只檢查 4 個 repo 的目錄是否存在，不查 git 狀態，也不包含上游同步資訊。使用者與維護者共用同一環境，需要分開顯示「本地是否最新」和「上游是否需要同步」。

## Goals / Non-Goals

**Goals:**
- 補齊設定儲存庫表至 `REPOS` 字典的全部 6 個 repo
- 改善設定儲存庫表，顯示本地 HEAD vs origin HEAD 的比對結果
- 新增「上游同步狀態」表，讀取 `upstream/last-sync.yaml` 比對各 repo HEAD
- 顯示落後 commit 數，讓維護者快速判斷是否需要 sync

**Non-Goals:**
- 不修改 `ai-dev update` 的行為或輸出
- 不自動觸發同步操作
- 不修改 `upstream/last-sync.yaml` 的格式或寫入邏輯

## Decisions

### 1. Repo 清單來源：使用 `REPOS` 字典 + `upstream/sources.yaml`

**選擇**：設定儲存庫表使用 `shared.py` 的 `REPOS` 字典取得完整清單；上游同步狀態表使用 `upstream/last-sync.yaml` 的 key 作為清單，並從 `upstream/sources.yaml` 讀取各 repo 的 `local_path` 以建立路徑對應。

**理由**：`REPOS` 已是 update 指令的 single source of truth，保持一致。`last-sync.yaml` 明確定義了哪些 repo 有上游追蹤。由於 `REPOS` 字典 key 使用 snake_case（如 `uds`）而 `last-sync.yaml` 使用 kebab-case（如 `universal-dev-standards`），無法靠簡單轉換對應，因此上游同步表需讀取 `sources.yaml` 的 `local_path` 來正確定位各 repo 目錄。

**替代方案**：在 status.py 中硬編碼 REPOS key → last-sync.yaml key 的映射表 — 但會引入重複維護成本。

### 2. 本地狀態比對方式：fetch-free 比對

**選擇**：設定儲存庫表只執行 `git rev-parse HEAD` 和 `git rev-parse origin/{branch}`，不執行 `git fetch`。

**理由**：`ai-dev status` 應是快速的唯讀查詢。fetch 是 `ai-dev update` 的職責。使用者通常會先 update 再 status，或直接 status 查看上次 update 後的狀態。

**替代方案**：每次 status 都 fetch — 會增加延遲且語意上不合適（status = 查看，不應有副作用）。

### 3. 上游同步落後計算：`git rev-list --count`

**選擇**：使用 `git rev-list --count <last-sync-commit>..HEAD` 在各 repo 的 local path 中計算落後 commit 數。

**理由**：`last-sync.yaml` 記錄的是本專案最後同步時的上游 commit。與 repo 目前 HEAD 比對就能得知落後多少。

### 4. 輸出格式：Rich Table，與現有表格風格一致

**選擇**：沿用 Rich Table，新增「上游同步狀態」表放在設定儲存庫表之後。

**理由**：保持 `ai-dev status` 輸出風格一致。

## Risks / Trade-offs

- **[Risk] last-sync.yaml 中的 commit 在本地 repo 不存在（未 fetch）** → 顯示「無法比對」而非錯誤，提示使用者先執行 `ai-dev update`
- **[Risk] repo 本地目錄不存在** → 顯示「未安裝」，與現有行為一致
- **[Trade-off] 不 fetch 意味著資訊可能不是最即時** → 可接受，status 定位為查看快照狀態
