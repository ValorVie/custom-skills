# Change Proposal: v2 行為對齊 v1

## 摘要

v2 Bun/TypeScript migration 完成了 CLI 骨架和 core 層基本邏輯，但**缺少 v1 Python 版本的大量行為和輸出**。本 change 的目標是讓 v2 的所有指令行為與 v1 **完全一致**。

## 問題

使用者從 v1 升級到 v2 後，發現：
- 輸出格式從 Rich Table 退化為純文字
- install/update 流程大幅縮減（v1 有 16 步，v2 只有 3 步）
- clone 語意完全改變（v1=分發 Skills，v2=clone git repos）
- 多個指令的子命令行為是空殼

## 範圍

逐指令對齊，涵蓋所有 17 個 v1 指令。

---

## 逐指令差異分析

### 嚴重程度分級

| 等級 | 定義 |
|------|------|
| P0 | 語意錯誤或功能完全缺失，使用者無法完成任務 |
| P1 | 功能部分缺失，核心流程不完整 |
| P2 | UX 退化，功能存在但輸出/體驗大幅不同 |
| P3 | 小差異，不影響功能 |

---

### 1. `install` — P0

**v1 行為（351 行，16 步流程）：**
1. 前置需求檢查：Node.js 版本、Git、gh、Bun（含安裝指引）
2. Claude Code 安裝狀態顯示（`show_claude_status`）
3. NPM 套件安裝：顯示已安裝版本、`[1/6]` 進度計數器
4. Bun 套件安裝：同上
5. 建立 16 個目標目錄
6. Clone 7 個儲存庫 + OpenCode superpowers
7. Clone 自訂儲存庫（custom repos）
8. `copy_skills` 分發到各工具目錄
9. 已安裝 Skills 列表 + 命名衝突警告
10. `show_skills_npm_hint`
11. Shell Completion 自動安裝
12. `--skip-skills` 選項
13. `--sync-project` / `--no-sync-project` 選項

**v2 現狀（75 行 CLI + 169 行 core）：**
- 只做 NPM install、Bun install、git clone（3 步）
- 無前置需求檢查（版本、安裝指引）
- 無 `show_claude_status`
- 無目錄建立
- 無 `copy_skills` 分發
- 無自訂儲存庫
- 無 Skills 列表/衝突警告
- 無 Shell Completion
- 無 `--skip-skills`、`--sync-project` 選項
- 無 `[1/6]` 進度計數器
- 無已安裝版本顯示
- 儲存庫列表只有 REPOS 中的少數幾個（v1 有 7 個）

**需補齊項目（13 項）：**
- [ ] 前置需求檢查 + 安裝指引（Node.js >= 20、Git、gh、Bun）
- [ ] Claude Code 安裝狀態顯示
- [ ] `[i/total]` 進度計數器
- [ ] 已安裝套件版本偵測（`get_npm_package_version`）
- [ ] 建立所有目標目錄（16 個）
- [ ] 補齊缺少的 REPOS（obsidian-skills, anthropic-skills, everything-claude-code, auto-skill）
- [ ] OpenCode superpowers sync + symlink
- [ ] 自訂儲存庫 Clone（`custom_repos`）
- [ ] `copy_skills` 分發
- [ ] 已安裝 Skills 列表 + 命名衝突警告
- [ ] `show_skills_npm_hint`
- [ ] Shell Completion 安裝
- [ ] `--skip-skills`、`--sync-project` 選項

---

### 2. `update` — P0

**v1 行為（370 行）：**
1. Claude Code 更新（`update_claude_code`）
2. NPM 套件更新 + `uds update` + `npx skills update`
3. Bun 套件更新
4. 8 個儲存庫更新：fetch → 比較遠端 → 備份本地修改 → `git reset --hard`
5. 自訂儲存庫更新
6. OpenCode superpowers symlink 刷新
7. Plugin Marketplace 更新
8. 更新摘要（哪些 repo 有新更新）
9. 缺失儲存庫警告

**v2 現狀（72 行 CLI + 127 行 core）：**
- 只做 NPM install、Bun install、git pull（3 步）
- 無 Claude Code 更新
- 無 `uds update`、`npx skills update`
- 無 `git fetch` + 遠端比較
- 無本地修改偵測和備份
- 無自訂儲存庫更新
- 無 Plugin Marketplace 更新
- 無更新摘要
- 儲存庫列表不完整

**需補齊項目（12 項）：**
- [ ] Claude Code 更新（`update_claude_code`）
- [ ] `uds update`（如果已初始化）
- [ ] `npx skills update`
- [ ] `[i/total]` 進度計數器
- [ ] 補齊缺少的 REPOS
- [ ] `git fetch --all` + 遠端比較
- [ ] 本地修改偵測（`has_local_changes`）+ 自動備份（`backup_dirty_files`）
- [ ] `git reset --hard origin/{branch}`（取代 `git pull --ff-only`）
- [ ] 自訂儲存庫更新
- [ ] OpenCode superpowers symlink 刷新
- [ ] Plugin Marketplace 更新（`--skip-plugins` 選項）
- [ ] 更新摘要 + 缺失儲存庫警告

---

### 3. `clone` — P0（語意完全不同）

**v1 行為（138 行）：**
- **語意：分發 Skills 到各工具目錄**
- 開發者模式偵測（在 custom-skills 專案目錄中）
- `integrate_to_dev_project` 整合外部來源
- `copy_skills` 分發到 Claude/OpenCode/Gemini/Codex/Antigravity
- 衝突處理：`--force`、`--skip-conflicts`、`--backup`
- Metadata 變更偵測

**v2 現狀（35 行）：**
- **語意：clone git repos**（`runInstall(skipNpm=true, skipBun=true)`）
- 與 v1 **完全相反**

**需修正：**
- [ ] 完全重寫 clone，恢復 v1 語意（分發 Skills）
- [ ] 開發者模式偵測
- [ ] `integrate_to_dev_project`
- [ ] `copy_skills` 分發
- [ ] 衝突處理選項（`--force`、`--skip-conflicts`、`--backup`）
- [ ] `--sync-project` / `--no-sync-project`
- [ ] Metadata 變更偵測

---

### 4. `status` — P2

**v1 行為（213 行）：**
- Rich Table：核心工具版本表
- Rich Table：NPM 套件安裝狀態表
- Rich Table：儲存庫狀態表（`✓ 最新` / `↑ 有可用更新`）
- Rich Table：上游同步狀態表（commit 落後數）

**v2 現狀（core 完整，CLI 精簡）：**
- JSON 輸出功能完整 ✓
- 純文字輸出無格式化
- 缺少上游同步狀態

**需補齊項目（3 項）：**
- [ ] 非 JSON 模式使用格式化表格輸出
- [ ] 上游同步狀態（`upstream/last-sync.yaml` 比較）
- [ ] 儲存庫遠端比較狀態

---

### 5. `list` — P2

**v1 行為（103 行）：**
- Rich Table 分組顯示（按 tool + type）
- 顯示來源（source）
- 顯示啟用/停用狀態（`✓ 啟用` / `✗ 停用`）
- `--hide-disabled` 選項

**v2 現狀（98 行）：**
- 純文字 `target/type: name` 格式
- 無停用狀態顯示
- 無來源顯示
- 無 `--hide-disabled`

**需補齊項目（4 項）：**
- [ ] 啟用/停用狀態顯示
- [ ] 資源來源顯示
- [ ] `--hide-disabled` 選項
- [ ] 格式化表格輸出（非 JSON 模式）

---

### 6. `toggle` — P3（基本一致）

**v1 行為（154 行）** vs **v2 現狀（161 行）：**
- 核心邏輯一致 ✓
- v1 有 target/type 有效組合驗證，v2 無
- v1 `--list` 用 Rich Table，v2 用純文字

**需補齊項目（2 項）：**
- [ ] target/type 有效組合驗證
- [ ] `--list` 格式化表格

---

### 7. `sync` — P1（6 個子命令大部分是空殼）

**v1 行為（554 行，6 個子命令）：**
- `init --remote URL`：git clone/init + 預設目錄 + LFS 偵測
- `push [--force]`：local→repo 同步 + LFS + plugin manifest + git push
- `pull [--no-delete] [--force]`：本地變更偵測 + 3 選項互動選單 + repo→local 同步
- `status`：本地變更統計 + 遠端落後數
- `add <path>`：新增同步目錄
- `remove <path>`：移除同步目錄

**v2 現狀（70 行 CLI + 238 行 core/sync-engine.ts）：**
- `init`：只接受 `--remote`，呼叫 `SyncEngine.init()`（僅 mkdir + 寫入 sync.yaml） — 缺少 git clone/init、LFS 偵測
- `push`：呼叫 `SyncEngine.push()`（只做 `fs.cp` file copy，不做 git operations） — 缺少 LFS push、plugin manifest、git add/commit/push
- `pull`：呼叫 `SyncEngine.pull()`（只做 `fs.cp` 反向 copy） — 缺少本地變更偵測、3 選項互動選單、`--no-delete`
- `status`：呼叫 `SyncEngine.status()`（僅檢查 sync.yaml 存在性） — 缺少本地變更統計、遠端落後數
- `add`/`remove`：基本邏輯存在但只是操作 sync.yaml 設定 ✓
- 所有子命令都只用 `console.log(JSON.stringify(...))` 輸出

**需補齊項目（8 項）：**
- [ ] `init` 加入 git clone/init + LFS 偵測 + .gitignore 寫入
- [ ] `push` 改用 git operations（add → commit → push）+ LFS support + plugin manifest
- [ ] `pull` 加入本地變更偵測 + 3 選項互動選單（覆蓋/備份/取消）
- [ ] `pull` 加入 `--no-delete`、`--force` 選項
- [ ] `push` 加入 `--force` 選項
- [ ] `status` 顯示本地變更統計 + 遠端 commit 落後數
- [ ] 所有子命令加格式化輸出（非 JSON 模式）
- [ ] 缺少 `.gitattributes` LFS 追蹤設定

---

### 8. `hooks` — P3（基本一致）

**v1 行為（67 行）** vs **v2 現狀（52 行）：**
- 3 個子命令結構一致 ✓
- v1 uninstall 有確認提示，v2 無

**需補齊項目（1 項）：**
- [ ] uninstall 確認提示

---

### 9. `mem` — P1（8 個子命令需檢查）

**v1 行為（651 行，8 個子命令）：**
- `register`、`push`、`pull`、`status`、`cleanup`、`reindex`、`auto`
- 完整的 HTTP API 交互、SQLite 操作、ChromaDB 索引
- 去重機制、hash 快取、自動同步排程（launchd/cron）

**v2 現狀（75 行 CLI + 400 行 core/mem-sync.ts）：**
- `register`：呼叫 `MemSync.register()`（寫入 device.yaml） — 基本功能存在 ✓
- `push`：呼叫 `MemSync.push()`（**stub** — 只計算 observation 數量，不做 HTTP 上傳） — 缺少 HTTP API 呼叫、hash dedup、分批上傳
- `pull`：呼叫 `MemSync.pull()`（**stub** — 直接回傳 `{ pulled: 0 }`） — 缺少 HTTP API 拉取、paginated pull、merge 邏輯
- `status`：呼叫 `MemSync.status()` — 只顯示 device info + observation 計數
- `cleanup`：呼叫 `MemSync.cleanup()` — 基本清理功能存在 ✓
- `reindex`：呼叫 `MemSync.reindex()` — 基本重建索引功能存在 ✓
- 缺少 `auto` 子命令（自動同步排程 — launchd/cron）
- 缺少 `search` 子命令的 ChromaDB 語義搜尋
- 所有子命令只用 `console.log(JSON.stringify(...))` 輸出

**需補齊項目（7 項）：**
- [ ] `push` 實作 HTTP API 上傳（含 hash dedup、分批上傳）
- [ ] `pull` 實作 HTTP API 拉取（含 paginated pull、merge 邏輯）
- [ ] 新增 `auto` 子命令（自動同步排程 — launchd/cron/systemd）
- [ ] `status` 加入遠端同步狀態（上次同步時間、待推送數量）
- [ ] ChromaDB / 語義搜尋整合
- [ ] 所有子命令加格式化輸出（非 JSON 模式）
- [ ] hash 快取機制（避免重複上傳）

---

### 10. `project` — P1

**v1 行為（612 行，2 個子命令）：**
- `init [target] [--force]`：從 `project-template/` 複製、`.gitignore`/`.gitattributes` 合併、備份機制
- `update [--only tool]`：`uds update` + `openspec update`

**v2 現狀（48 行 CLI + 116 行 core/project-manager.ts）：**
- `init [target]`：呼叫 `ProjectManager.initProject()` — 從 `project-template/` 做 `fs.cp` 複製 ✓
  - 缺少：`.gitignore`/`.gitattributes` 智慧合併（v1 逐行比對、只添加不存在的行）
  - 缺少：備份機制（v1 在覆蓋前自動備份）
  - 缺少：`--force` 選項（v1 覆蓋已存在的檔案）
  - 缺少：開發者反向同步（`sync_project_to_template`）
- `update [--only tool]`：呼叫 `ProjectManager.updateProject()` — 只做 `uds update`
  - 缺少：`openspec update` 整合
  - 缺少：`--only` 選項過濾
  - 缺少：file-by-file diff 顯示
- 所有子命令只用 `console.log(JSON.stringify(...))` 輸出

**需補齊項目（7 項）：**
- [ ] `init` 加入 `.gitignore`/`.gitattributes` 智慧合併（逐行比對）
- [ ] `init` 加入備份機制（覆蓋前自動備份）
- [ ] `init` 加入 `--force` 選項
- [ ] `init` 加入開發者反向同步功能
- [ ] `update` 加入 `openspec update` 整合
- [ ] `update` 加入 `--only` 選項過濾特定工具
- [ ] 格式化輸出（非 JSON 模式）

---

### 11. `standards` — P1

**v1 行為（801 行，6 個子命令）：**
- `status`、`list`、`switch`、`show`、`overlaps`、`sync`
- Profile 管理、overlap 偵測、disabled.yaml 生成
- Rich Table/Panel/Tree 格式化

**v2 現狀（70 行 CLI + 168 行 core/standards-manager.ts）：**
- `status`：呼叫 `StandardsManager.status()` — 讀取 `active-profile.yaml` ✓
- `list`：呼叫 `StandardsManager.list()` — 列出所有 profile 設定 ✓
- `switch <profile>`：呼叫 `StandardsManager.switch()` — **只寫入 `active-profile.yaml`，不計算 disabled items**
  - 缺少：`compute_disabled_items()` 邏輯（v1 從 profile 差集計算出應停用的 standards）
  - 缺少：自動生成 `disabled.yaml`
  - 缺少：自動搬移檔案（停用的 standards 移到 `.disabled/`）
- `show <profile>`：呼叫 `StandardsManager.show()` — 基本顯示功能存在 ✓
- `overlaps`：呼叫 `StandardsManager.overlaps()` — 基本重疊偵測存在 ✓
- 缺少 `sync` 子命令（v1 同步 standards 到各工具目錄）
- 所有子命令只用 `console.log(JSON.stringify(...))` 輸出

**需補齊項目（5 項）：**
- [ ] `switch` 實作 `compute_disabled_items()` 差集計算
- [ ] `switch` 自動生成 `disabled.yaml` + 搬移檔案
- [ ] 新增 `sync` 子命令（同步 standards 到工具目錄）
- [ ] `overlaps` 改用格式化表格顯示（v1 用 Rich Table + Panel）
- [ ] 所有子命令加格式化輸出（非 JSON 模式）

---

### 12. `test` — P3（基本可用）

**v1 行為（54 行）：**
- 自動偵測測試框架（pytest/jest/bun test）
- `--verbose`、`--fail-fast`、`-k` 選項
- 原始測試框架輸出

**v2 現狀（45 行）：**
- 硬編碼使用 `bun test`（合理，因為 v2 是 Bun 專案）
- 支援 `--verbose`、`--fail-fast`、`-k` 選項 ✓
- 直接透傳測試框架輸出 ✓

**需補齊項目（1 項）：**
- [ ] 自動偵測測試框架（如果需要支援非 Bun 專案）— 可選，v2 主要用於 Bun 專案

---

### 13. `coverage` — P3（基本可用）

**v1 行為（58 行）：**
- 自動偵測測試框架
- `--source` 選項
- pytest-cov 輸出

**v2 現狀（28 行）：**
- 硬編碼使用 `bun test --coverage` ✓
- 直接透傳覆蓋率輸出 ✓
- 缺少 `--source` 選項

**需補齊項目（1 項）：**
- [ ] `--source` 選項（過濾覆蓋率來源目錄）— 可選

---

### 14. `derive-tests` — P3（功能一致）

**v1 行為（62 行）：**
- 讀取 spec 檔案並輸出內容

**v2 現狀（55 行）：**
- 功能一致 ✓ — 讀取 spec 並輸出
- 行為匹配 v1 ✓

**需補齊項目：** 無

---

### 15. `add-repo` — P1

**v1 行為（259 行）：**
- URL 解析（HTTPS/SSH/shorthand）
- Git clone 到 `upstream/` 目錄
- 格式偵測（UDS / claude-code-native / skills-repo）
- `upstream/sources.yaml` 寫入（追蹤已加入的上游來源）
- `--analyze` 選項（分析 repo 結構並建議整合方式）

**v2 現狀（57 行）：**
- URL 解析存在（從 URL 提取 repo name）✓
- Git clone 功能存在 ✓
- 缺少：格式偵測（不判斷 repo 類型）
- 缺少：`upstream/sources.yaml` 寫入
- 缺少：`--analyze` 選項
- 缺少：已存在 repo 的重複檢查

**需補齊項目（4 項）：**
- [ ] 格式偵測（UDS / claude-code-native / skills-repo）
- [ ] `upstream/sources.yaml` 寫入
- [ ] `--analyze` 選項
- [ ] 已存在 repo 的重複檢查

---

### 16. `add-custom-repo` — P2

**v1 行為（111 行）：**
- URL 解析、git clone
- repo 結構驗證（`validate_repo_structure` — 檢查是否有 skills/commands/agents 目錄）
- `~/.config/ai-dev/repos.yaml` 寫入
- `--fix` 選項（自動建立缺少的目錄結構）

**v2 現狀（55 行）：**
- URL 解析 + git clone ✓
- `repos.yaml` 寫入功能存在 ✓
- 缺少：repo 結構驗證
- 缺少：`--fix` 選項

**需補齊項目（2 項）：**
- [ ] repo 結構驗證（`validate_repo_structure`）
- [ ] `--fix` 選項（自動建立缺少的目錄結構）

---

### 17. `update-custom-repo` — P2

**v1 行為（82 行）：**
- 讀取 `repos.yaml`
- 逐一 `git fetch --all` + 比較遠端
- 本地修改偵測 + `backup_dirty_files` 自動備份
- `git reset --hard origin/{branch}`
- 更新摘要（哪些 repo 有更新、哪些已是最新）

**v2 現狀（39 行）：**
- 讀取 `repos.yaml` ✓
- 使用 `git pull` 更新（而非 fetch + backup + reset）
- 缺少：本地修改偵測 + 自動備份
- 缺少：更新摘要
- 缺少：`git fetch --all` + 遠端比較

**需補齊項目（3 項）：**
- [ ] 改用 `git fetch --all` + 遠端比較 + `git reset --hard`
- [ ] 本地修改偵測 + 自動備份（`backup_dirty_files`）
- [ ] 更新摘要（顯示每個 repo 的更新狀態）

---

## 已確認缺失清單

### P0（語意錯誤或功能完全缺失）

| # | 指令 | 缺失項數 | 缺失描述 |
|---|------|---------|----------|
| 1 | install | 13 項 | 前置檢查、目錄建立、Skills 分發、Shell Completion 等 |
| 2 | update | 12 項 | Claude Code 更新、備份機制、Plugin Marketplace 等 |
| 3 | clone | 7 項 | 語意完全錯誤（v1=分發 Skills，v2=clone repos），需完全重寫 |

### P1（功能部分缺失）

| # | 指令 | 缺失項數 | 缺失描述 |
|---|------|---------|----------|
| 4 | sync | 8 項 | push/pull 只做 file copy 不做 git ops、缺 LFS、缺互動選單 |
| 5 | mem | 7 項 | push/pull 是 stub、缺 HTTP API、缺 auto 子命令 |
| 6 | project | 7 項 | 缺 .gitignore 合併、備份、反向同步、--only 選項 |
| 7 | standards | 5 項 | switch 不計算 disabled items、缺 sync 子命令 |
| 8 | add-repo | 4 項 | 缺格式偵測、sources.yaml 寫入、--analyze |

### P2（UX 退化）

| # | 指令 | 缺失項數 | 缺失描述 |
|---|------|---------|----------|
| 9 | status | 3 項 | 缺格式化表格、上游同步狀態 |
| 10 | list | 4 項 | 缺啟用/停用狀態、來源顯示、--hide-disabled |
| 11 | add-custom-repo | 2 項 | 缺 repo 結構驗證、--fix 選項 |
| 12 | update-custom-repo | 3 項 | 缺備份機制、更新摘要 |

### P3（小差異）

| # | 指令 | 缺失項數 | 缺失描述 |
|---|------|---------|----------|
| 13 | toggle | 2 項 | 缺 target/type 驗證、--list 格式化 |
| 14 | hooks | 1 項 | 缺 uninstall 確認提示 |
| 15 | test | 1 項 | 缺自動偵測測試框架（可選） |
| 16 | coverage | 1 項 | 缺 --source 選項（可選） |
| 17 | derive-tests | 0 項 | 功能一致 ✓ |

**總計：80 項缺失**（P0: 32, P1: 31, P2: 12, P3: 5）

## 共通缺失（跨指令）

| # | 缺失 | 影響指令 |
|---|------|---------|
| A | 格式化輸出（v1 用 Rich Table/Panel/Tree） | 全部 17 個 |
| B | 語言配置（v1 全中文，v2 全英文） | 全部 17 個 |
| C | 完整的 REPOS 列表（v2 只有部分） | install, update, status |
| D | 自訂儲存庫系統（`repos.yaml`） | install, update, update-custom-repo |
| E | `copy_skills` 分發機制 | install, clone |
| F | OpenCode superpowers sync/symlink | install, update |

---

## 格式化輸出方案比較

v1 使用 Python `rich` 套件提供 Table、Panel、Tree、Progress Bar 等。v2 需要在 Node.js/Bun 生態中找到對等方案。

**已存在於 v2 `package.json` 的套件：**
- `chalk@^5.6.2` — 顏色文字
- `ora@^9.3.0` — 載入動畫 (spinner)
- `inquirer@^13.3.0` — 互動式選單/提示
- `ink@^6.8.0` — React-based terminal UI（TUI 已使用）

**需要額外引入的套件比較：**

| 套件 | 用途 | 對應 v1 Rich 功能 | 優點 | 缺點 |
|------|------|------------------|------|------|
| `cli-table3` | 表格渲染 | Rich Table | 穩定、廣泛使用、支援 colSpan/rowSpan | 1 dependency (string-width) |
| `tty-table` | 表格渲染 | Rich Table | 自動調整寬度、支援 header 色彩 | 較多 dependencies |
| `columnify` | 對齊欄位 | Rich Table (簡化) | 零 dependency、輕量 | 無邊框、功能較少 |
| 自行實作 | 簡易表格 | — | 零 dependency | 維護成本高 |

**建議方案：** `chalk` + `ora` + `cli-table3`（推薦）
- chalk：已有，色彩輸出
- ora：已有，載入動畫
- cli-table3：新增，表格格式化
- inquirer：已有，互動式選單（sync pull 的 3 選項選單）

理由：三個套件覆蓋 v1 Rich 的主要功能（Table + 色彩 + Progress），且 cli-table3 是最穩定、使用最廣的 Node.js 表格套件。

---

## 語言配置

**需求：** 輸出語言可配置，預設英文。

**方案：**
- 在 `~/.config/ai-dev/config.yaml` 中新增 `locale: en` 設定
- 支援 `en`（English）和 `zh-TW`（繁體中文）
- 字串集中管理在 `src/utils/i18n.ts`
- 所有 CLI 輸出使用 `t('key')` 取代硬編碼字串
- `--lang` 全域選項可臨時切換語言

## 建議執行策略

### Phase 0：共通基礎設施
1. **格式化基礎** — 引入 `cli-table3`，建立 `src/utils/formatter.ts` 封裝表格/色彩/spinner 輸出
2. **i18n 基礎** — 建立 `src/utils/i18n.ts`，支援 `en`/`zh-TW`，預設英文
3. **共用工具** — `copy_skills` 分發機制、`backup_dirty_files` 備份機制

### Phase 1：P0 修復（最高優先）
4. **clone** — 完全重寫，恢復 v1 語意（分發 Skills 到各工具目錄）
5. **install** — 補齊 13 項缺失功能
6. **update** — 補齊 12 項缺失功能

### Phase 2：P1 修復
7. **sync** — 改用 git operations、加 LFS、加互動選單（8 項）
8. **mem** — 實作 HTTP API push/pull、加 auto 子命令（7 項）
9. **project** — 加 .gitignore 合併、備份、反向同步（7 項）
10. **standards** — 實作 compute_disabled_items、加 sync 子命令（5 項）
11. **add-repo** — 加格式偵測、sources.yaml 寫入（4 項）

### Phase 3：P2/P3 UX 對齊
12. **status/list** — 格式化表格輸出 + 額外資訊欄位
13. **add-custom-repo/update-custom-repo** — 備份機制 + 結構驗證
14. **toggle/hooks** — 小修正
15. **test/coverage** — 可選改善

## 狀態

- [x] 差異分析完成（所有 17 個指令已逐一驗證 v2 core + CLI 實作）
- [x] 格式化方案比較完成（推薦 chalk + ora + cli-table3）
- [x] 語言配置方案確認（可配置，預設英文）
- [ ] 待建立 design.md
- [ ] 待建立 specs
- [ ] 待建立 tasks
- [ ] 待實作
