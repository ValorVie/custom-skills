# ai-dev sync 跨裝置同步教學

> 使用 `ai-dev sync` 指令透過 Git 同步 Claude Code 配置、記憶資料庫與自訂目錄。

---

## 前置條件

- **Git** 已安裝且可用
- **私有 Git 遠端倉庫**（GitHub / GitLab / 自架）— 同步內容可能包含敏感資訊
- **SSH Key 認證**（建議）— 避免每次 push/pull 輸入密碼
- **Git LFS**（建議）— 自動處理超過 50 MB 的檔案（如 SQLite 資料庫），避免 GitHub push 失敗
  - macOS: `brew install git-lfs`
  - Linux: `sudo apt install git-lfs`（或 `sudo dnf install git-lfs`）
  - Windows: `winget install GitHub.GitLFS`（或從 [git-lfs.com](https://git-lfs.com) 下載安裝）
  - 安裝後無需額外設定，`ai-dev sync` 會自動偵測並啟用

---

## 快速開始

### 第一台機器：初始化

```bash
# 初始化同步，指定遠端倉庫
ai-dev sync init --remote git@github.com:<user>/claude-sync.git
```

這會：
1. Clone 或建立 `~/.config/ai-dev/sync-repo/` Git 倉庫
2. 預設同步 `~/.claude` 和 `~/.claude-mem` 兩個目錄
3. 產生 `.gitignore`（自動排除快取、debug 等不需要的檔案）
4. 產生 `plugin-manifest.json`（可攜帶的 plugin 狀態記錄）
5. 執行首次同步並推送到遠端

### 第二台機器：加入同步

```bash
# 初始化，指向相同遠端倉庫（自動從遠端還原配置 + 安裝 plugin）
ai-dev sync init --remote git@github.com:<user>/claude-sync.git

# 登入 Claude Code（token 存在系統 keychain，不會被同步）
claude
```

init 會自動完成：
1. 從遠端還原 `~/.claude` 和 `~/.claude-mem` 的內容
2. Clone 各 marketplace 的 Git repo
3. 從 marketplace 複製 plugin 到 cache
4. 寫入 `installed_plugins.json` 和 `known_marketplaces.json`（本機路徑）
5. 還原 `settings.json` 的 `enabledPlugins`

> **只需獨立登入 Claude Code**，plugin 會自動安裝。若有 `directory` 類型的 marketplace（如本機 npm 套件），需手動處理。

---

## 日常使用

### 離開前：推送變更

```bash
ai-dev sync push
```

將本機所有同步目錄的變更推送到遠端。push 時會自動更新 `plugin-manifest.json`。

### 換到另一台機器：拉取變更

```bash
ai-dev sync pull
```

從遠端拉取最新變更，同步到本機目錄。`pull` 預設會先偵測本機是否有未推送的變更：

1. 先 push 再 pull（推薦）
2. 強制 pull（覆蓋本機變更）
3. 取消

若你在腳本中需要非互動式操作，可使用 `--force` 跳過偵測：

```bash
ai-dev sync pull --force
```

> **提示**：`pull` 預設會刪除「遠端沒有但本機有」的檔案。若要保留本機獨有檔案：
>
> ```bash
> ai-dev sync pull --no-delete
> ```

### 查看同步狀態

```bash
ai-dev sync status
```

輸出表格顯示每個同步目錄的：

| 欄位 | 說明 |
|------|------|
| Path | 本機目錄路徑 |
| Local Changes | 與倉庫不同的檔案數量 |
| Remote | 「最新」或「落後 N commits」 |
| Last Sync | 上次同步時間 |

---

## 管理同步目錄

### 新增目錄

```bash
# 基本用法
ai-dev sync add ~/.gemini

# 指定忽略規則
ai-dev sync add ~/Projects --ignore "node_modules/" --ignore "*.log"

# 指定 ignore profile（可選：claude / claude-mem / custom）
ai-dev sync add ~/.config/ai-tools --profile custom --ignore "cache/"
```

### 移除目錄

```bash
ai-dev sync remove ~/.gemini
```

移除時會詢問是否同時刪除倉庫中對應的子目錄。至少需保留一個同步目錄。

---

## 指令總覽

| 指令 | 說明 | 範例 |
|------|------|------|
| `init --remote <url>` | 初始化同步倉庫 | `ai-dev sync init --remote git@github.com:user/repo.git` |
| `push` | 推送本機變更到遠端 | `ai-dev sync push` |
| `pull` | 拉取遠端變更到本機（支援 `--force`、`--no-delete`） | `ai-dev sync pull --force --no-delete` |
| `status` | 查看同步狀態 | `ai-dev sync status` |
| `add <path>` | 新增同步目錄 | `ai-dev sync add ~/.gemini --ignore "cache/"` |
| `remove <path>` | 移除同步目錄 | `ai-dev sync remove ~/.gemini` |

---

## 設定檔

位置：`~/.config/ai-dev/sync.yaml`

```yaml
version: "1"
remote: git@github.com:<user>/claude-sync.git
last_sync: "2026-02-13T10:30:45+00:00"
directories:
  - path: ~/.claude
    repo_subdir: claude
    ignore_profile: claude
    custom_ignore: []
  - path: ~/.claude-mem
    repo_subdir: claude-mem
    ignore_profile: claude-mem
    custom_ignore: []
```

一般情況不需手動編輯，透過 `add` / `remove` 指令管理即可。

---

## Plugin 同步機制

Plugin 的程式碼和 metadata（含機器專屬絕對路徑）**不會直接同步**。取而代之，sync 使用 **plugin manifest** 機制：

### Push 時（第一台機器）

自動從 `installed_plugins.json` 和 `known_marketplaces.json` 產生可攜帶的 `plugin-manifest.json`，記錄：
- Marketplace 名稱與來源 URL（不含本機路徑）
- 已安裝 plugin 名稱與版本
- 已啟用 plugin 清單

### Init 時（第二台機器）

自動執行以下步驟：
1. 讀取 `plugin-manifest.json`
2. `git clone --depth 1` 各 marketplace repo 到 `~/.claude/plugins/marketplaces/`
3. 讀取各 marketplace 的 `.claude-plugin/marketplace.json` 解析 plugin 來源
4. 根據來源類型安裝 plugin 到 `~/.claude/plugins/cache/`
5. 產生本機版 `installed_plugins.json` 和 `known_marketplaces.json`
6. 還原 `settings.json` 的 `enabledPlugins`（只啟用成功安裝的 plugin）

**支援三種 marketplace plugin 來源：**

| 來源類型 | 範例 | 安裝方式 |
|----------|------|----------|
| 相對路徑（內嵌） | `"./plugins/code-simplifier"` | 從 marketplace repo 內複製 |
| 相對路徑（非標準） | `"./plugin"` | 從 marketplace repo 內複製 |
| 外部 Git URL | `{"source": "url", "url": "https://..."}` | 另外 `git clone --depth 1` |
| `directory` 類型 | 本機 npm 套件路徑 | 無法自動 clone，顯示跳過訊息 |

### 排除的 Plugin 檔案

| 檔案 | 排除原因 |
|------|----------|
| `plugins/installed_plugins.json` | 含 `installPath` 絕對路徑 |
| `plugins/known_marketplaces.json` | 含 `installLocation` 絕對路徑 |
| `plugins/cache/` | 可重建的快取 |
| `plugins/marketplaces/` | Git repos + node_modules，可重新 clone |
| `plugins/repos/` | 可重新 clone |
| `plugins/install-counts-cache.json` | 可重建 |

---

## 預設 Ignore Profile

### claude

排除 `~/.claude` 中不需同步的檔案：

```
debug/  cache/  paste-cache/  downloads/  shell-snapshots/
session-env/  ide/  statsig/  telemetry/  stats-cache.json
plugins/cache/  plugins/marketplaces/  plugins/repos/
plugins/install-counts-cache.json  plugins/installed_plugins.json
plugins/known_marketplaces.json
```

### claude-mem

排除 `~/.claude-mem` 中的暫存檔：

```
logs/  worker.pid  *.db-wal  *.db-shm
```

### 全域排除

所有目錄皆排除：`.DS_Store`、`Thumbs.db`、`desktop.ini`

---

## 注意事項

### 新機器必做步驟

| 項目 | 自動/手動 | 說明 |
|------|-----------|------|
| 登入 Claude Code | 手動 | Token 存在系統 keychain，需執行 `claude` |
| Marketplace + Plugin | **自動** | init 時自動 clone marketplace 並安裝 plugin |
| `directory` 類型 Marketplace | 手動 | 如 npm 全域套件，需在本機另行安裝 |
| MCP Server | 手動 | 依賴本機環境，依各 MCP 文件安裝 |

### SQLite 資料庫安全

`claude-mem.db` 為 SQLite 資料庫，同步期間若正在寫入可能損壞。

**建議**：同步前先確認 claude-mem worker 已停止（或至少沒有活躍的寫入操作）。

### Git LFS 運作原理

一般 Git 對每個版本存完整快照。文字檔可以 delta 壓縮（只存差異），但 **binary 檔案（如 SQLite）無法 delta**，每次 commit 都是完整副本，導致 repo 快速膨脹。

Git LFS 將大檔案的實際內容存到獨立的 LFS Storage，Git repo 中只追蹤一個約 130 bytes 的 **pointer 檔案**：

```
version https://git-lfs.github.com/spec/v1
oid sha256:4d7a214614ab2935c943f9e0ff69d22eadbb8f32...
size 63832064
```

| | 一般 Git | Git LFS |
|---|---|---|
| 儲存位置 | 全部在 `.git/objects/` | 大檔在獨立 LFS storage |
| 歷史版本 | 每版存完整副本 | 每版只存 pointer，大檔按需下載 |
| Clone 速度 | 下載所有歷史版本 | 只下載最新版大檔案 |
| Repo 大小 | 隨 commit 線性膨脹 | Repo 本身很小 |
| GitHub 限制 | 單檔 100 MB 硬限 | 單檔 2 GB |
| Diff/Merge | 文字檔可 diff/merge | LFS 檔案視為 binary，無法 merge |

`.gitattributes` 中的 LFS 規則告訴 Git「這類檔案走 LFS filter」：

```
*.sqlite3 filter=lfs diff=lfs merge=lfs -text
```

`git add` 時 Git 自動將實際內容存到 LFS、在 staging area 放入 pointer，使用者完全無感。

### Git LFS 自動追蹤

sync 在 `push` 和 `init` 時會自動掃描 repo 中超過 **50 MB** 的檔案，以副檔名為單位產生 Git LFS track 規則並寫入 `.gitattributes`。

**自動偵測行為：**

| 情境 | 行為 |
|------|------|
| 有 git-lfs + 有大檔案 | 自動啟用 LFS，寫入 track 規則，顯示追蹤訊息 |
| 有 git-lfs + 無大檔案 | 不寫入 LFS 規則，正常運作 |
| 無 git-lfs + 有大檔案 | 顯示黃色警告建議安裝，不阻擋操作 |
| 無 git-lfs + 無大檔案 | 完全靜默，正常運作 |

**排除 JSONL**：`*.jsonl` 不會被 LFS 追蹤，即使超過 50 MB。因為 JSONL 使用 `merge=union` 自動合併策略，LFS 會將其視為 binary 而失去此能力。兩台機器同時新增 session 記錄時，`merge=union` 可自動按行合併避免衝突。

**GitHub LFS 配額**：免費帳號 1 GB storage + 1 GB/月 bandwidth，一般使用足夠。

**手動操作（通常不需要）：**

```bash
# 查看 LFS 追蹤的檔案
cd ~/.config/ai-dev/sync-repo && git lfs ls-files

# 手動將既有大檔案遷移到 LFS（會改寫 git history）
cd ~/.config/ai-dev/sync-repo
git lfs migrate import --include="*.sqlite3" --everything
git push --force
```

### 大型檔案與倉庫膨脹

`~/.claude/projects/` 與 `~/.claude-mem` 可能逐步累積大型 binary（例如 `*.sqlite3`、`*.db`）。

目前 `ai-dev sync` 會在 `init`/`push` 時自動偵測超過 50 MB 的檔案並加入 Git LFS（排除 `*.jsonl`），可避免觸發 GitHub 大檔案限制並降低歷史膨脹速度。

長期維運建議：

- 確保所有機器都已安裝 git-lfs（避免只拉到 pointer file）
- 既有歷史已包含大型 binary 時，優先在初始化階段完成 migrate
- 定期在 sync-repo 執行 `git gc --aggressive` 維持倉庫健康

### 跨平台路徑差異

`~/.claude/projects/` 和 `history.jsonl` 包含機器專屬路徑（如 `-Users-arlen-Documents-project`）。不同機器若專案路徑不同，Claude Code 不會自動關聯。

**解決方式**：統一各機器的專案路徑，或手動重新命名目錄。

### 合併衝突

- 使用 `git pull --rebase` 減少衝突機率
- `.gitattributes` 已設定 `*.jsonl merge=union` 自動合併 JSONL 檔案
- JSON 檔案若發生衝突需手動解決

---

## 相關文件

- [Claude Code 跨裝置同步指南](../ai-tools/CLAUDE-CODE-SYNC.md) — Syncthing / Git 兩種方案的完整比較
- [ai-dev CLI 框架技術架構](ai-dev-framework-architecture.md) — ai-dev 整體架構說明
