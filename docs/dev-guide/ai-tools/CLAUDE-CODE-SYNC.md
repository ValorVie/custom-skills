# Claude Code 跨裝置同步指南

跨裝置同步 Claude Code 的配置、會話、記憶與狀態，實現一致的開發體驗。

提供兩種同步方案：**Syncthing**（即時雙向同步）和 **Git**（版本控制同步）。

---

## 跨平台路徑對照

需要同步的目錄有兩個：Claude Code 本體配置和 claude-mem 記憶資料庫。

### ~/.claude（Claude Code 配置）

| 平台 | 路徑 | 範例 |
|------|------|------|
| macOS | `~/.claude` | `/Users/arlen/.claude` |
| Linux | `~/.claude` | `/home/arlen/.claude` |
| Windows | `%USERPROFILE%\.claude` | `C:\Users\arlen\.claude` |

> **注意**：部分 Linux 版本可能使用 `~/.config/claude`，請以實際安裝為準。

### ~/.claude-mem（claude-mem 記憶資料庫）

| 平台 | 路徑 | 範例 |
|------|------|------|
| macOS | `~/.claude-mem` | `/Users/arlen/.claude-mem` |
| Linux | `~/.claude-mem` | `/home/arlen/.claude-mem` |
| Windows | `%USERPROFILE%\.claude-mem` | `C:\Users\arlen\.claude-mem` |

> 路徑由 `~/.claude-mem/settings.json` 中的 `CLAUDE_MEM_DATA_DIR` 定義。

---

## ~/.claude 目錄結構分析

> 基於 2026-02-13 實際目錄調查。總計約 1.2GB。

### 同步（保留）

| 路徑 | 大小 | 說明 | 同步理由 |
|------|------|------|----------|
| `CLAUDE.md` | 4KB | 全域 AI 指令 | 核心配置，跨裝置必須一致 |
| `DISABLE-CLAUDE.md` | 8KB | 停用指令 | 配對 CLAUDE.md |
| `settings.json` | 4KB | Claude Code 設定 | 偏好設定跨裝置一致 |
| `session-aliases.json` | 4KB | 會話別名 | 方便跨裝置找回會話 |
| `history.jsonl` | 668KB | 操作歷史 | 跨裝置保留完整歷史紀錄 |
| `commands/` | 300KB | 自訂 slash commands | 自訂指令跨裝置可用 |
| `skills/` | 1.4MB | 已安裝的技能 | 技能與知識庫跨裝置一致 |
| `agents/` | 88KB | 自訂 agent 定義 | agent 配置跨裝置一致 |
| `plans/` | 84KB | 實作計畫 | 計畫可在另一台機器繼續 |
| `workflows/` | 8KB | 工作流程定義 | 自動化流程跨裝置可用 |
| `sessions/` | 68KB | 會話元資料 | 會話可跨裝置接續 |
| `tasks/` | 152KB | 任務清單 | 任務狀態跨裝置一致 |
| `todos/` | 5.6MB | 待辦事項（per session） | 跨裝置看到一致的待辦狀態 |
| `transcripts/` | 17MB | 會話完整逐字稿 | 可在任何裝置回顧對話 |
| `projects/` | 407MB | 各專案會話與設定 | 專案上下文跨裝置接續 |
| `file-history/` | 29MB | 檔案編輯歷史 | 編輯紀錄跨裝置完整 |
| `usage-data/` | 2MB | 用量統計報告 | 統計資料合併可用 |
| `plugins/config.json` | <1KB | 外掛設定 | 外掛配置一致 |

### 排除（不同步）

| 路徑 | 大小 | 說明 | 排除理由 |
|------|------|------|----------|
| `debug/` | 413MB | Debug log 檔案 | 1,879 個檔案，本機除錯用，高頻寫入易衝突，可重建 |
| `plugins/cache/` | 11MB | 外掛快取 | 可重建的暫存資料 |
| `plugins/marketplaces/` | 355MB | Marketplace git repos | 含 node_modules（254MB），可 reinstall 重建 |
| `plugins/repos/` | 0 | 外掛 repo clone | 可重新 clone |
| `plugins/installed_plugins.json` | 4KB | 已安裝外掛清單 | 含機器專屬絕對路徑，跨平台會導致 plugin 載入失敗 |
| `plugins/known_marketplaces.json` | 2KB | Marketplace 清單 | 含機器專屬絕對路徑，同上 |
| `shell-snapshots/` | 24MB | Shell 環境快照 | 包含本機 shell 變數與路徑，跨機器不適用 |
| `session-env/` | ~0 | 會話環境變數 | 449 個目錄，本機環境專屬 |
| `ide/` | 48KB | IDE 連線 lock 檔 | PID lock 檔案，跨機器必定衝突 |
| `cache/` | 92KB | 一般快取 | 可重建 |
| `paste-cache/` | 372KB | 剪貼簿暫存 | 本機剪貼簿行為 |
| `statsig/` | 36KB | Feature flag 狀態 | 裝置層級的 A/B 測試狀態 |
| `stats-cache.json` | 12KB | 統計快取 | 可重建的暫存 |
| `telemetry/` | 0 | 遙測資料 | 本機裝置專屬 |
| `downloads/` | 0 | 下載暫存 | 本機暫存 |
| `.DS_Store` | — | macOS 系統檔案 | OS 專屬 |
| `Thumbs.db` | — | Windows 系統檔案 | OS 專屬 |
| `desktop.ini` | — | Windows 系統檔案 | OS 專屬 |

### 空間影響

| 類別 | 大小 | 佔比 |
|------|------|------|
| 同步 | ~462MB | 37% |
| 排除 | ~804MB | 63% |
| **總計** | ~1.2GB | 100% |

排除後同步量約 462MB，其中 `projects/` (407MB) 佔大宗。

### ecc-hooks 記憶儲存

ecc-hooks 外掛的記憶資料儲存在 `~/.claude` 內，**已包含在上方同步清單**：

| 路徑 | 說明 | 用途 |
|------|------|------|
| `sessions/` | 會話摘要檔（`.tmp`） | 每日會話的 git 變更、commit 記錄、工作目錄狀態 |
| `sessions/compaction-log.txt` | 壓縮紀錄 | 追蹤每次 context compaction 事件 |
| `skills/learned/` | 學習到的模式 | 從長會話（10+ 訊息）自動萃取的可重用模式 |
| `session-aliases.json` | 會話別名 | 會話命名與快速查找 |

---

## ~/.claude-mem 目錄結構分析

> claude-mem MCP Server 的持久化記憶資料庫。總計約 124MB。

### 同步（保留）

| 路徑 | 大小 | 說明 | 同步理由 |
|------|------|------|----------|
| `claude-mem.db` | 12MB | 主資料庫（SQLite） | 所有觀察紀錄、元資料、會話資料，**核心記憶** |
| `vector-db/chroma.sqlite3` | 57MB | 向量資料庫（Chroma） | 語意搜尋的 embedding 向量，**語意記憶** |
| `vector-db/*/` | 29MB | HNSW 索引檔 | Chroma 的近鄰搜尋索引，配合向量 DB 使用 |
| `settings.json` | <1KB | 配置檔 | 模型、日誌、上下文等設定 |

### 排除（不同步）

| 路徑 | 大小 | 說明 | 排除理由 |
|------|------|------|----------|
| `logs/` | 22MB | 每日日誌檔 | 本機除錯用，可重建 |
| `worker.pid` | <1KB | Worker 程序 PID | 包含本機 PID 和 port，跨機器無意義 |
| `claude-mem.db-wal` | ~4MB | SQLite WAL 日誌 | 交易暫存檔，重啟後合併回主 DB |
| `claude-mem.db-shm` | 32KB | SQLite 共享記憶體 | 程序間通訊用，本機專屬 |

### SQLite 同步注意事項

SQLite 資料庫同步有特殊風險：

- **寫入中同步**：如果 claude-mem 正在寫入時 Syncthing 同步 `.db` 檔案，可能導致資料庫損毀
- **WAL 模式**：claude-mem 使用 WAL 模式，未提交的變更在 `-wal` 檔案中，主 `.db` 檔案相對穩定
- **建議**：同步前確保 claude-mem worker 已停止，或接受極低機率的損毀風險（SQLite 有自動修復機制）

---

## 跨平台注意事項

### projects/ 路徑問題

`projects/` 使用本機絕對路徑作為目錄名，路徑分隔符號用 `-` 取代：

| 平台 | 目錄名範例 |
|------|-----------|
| macOS | `-Users-arlen-Documents-myproject` |
| Linux | `-home-arlen-Documents-myproject` |
| Windows | `-Users-arlen-Documents-myproject` |

**同平台同路徑結構**：直接同步，路徑完全匹配。

**跨平台或不同路徑**：目錄名不匹配，Claude Code 無法自動關聯到本機專案。資料仍存在，可手動重命名目錄來對應。

**建議**：統一各裝置的專案路徑結構。例如都使用：
- macOS/Linux: `~/Projects/...`
- Windows: `C:\Users\<user>\Projects\...`

這樣 macOS 和 Windows 的 projects 目錄名會一致（都是 `-Users-<user>-Projects-...`）。

### 換行符號

- `history.jsonl`、`*.json` — 不受換行符號影響（JSON 規範）
- `CLAUDE.md`、`commands/*.md` — 需注意 LF vs CRLF
- **建議**：Git 方案設定 `core.autocrlf=input`；Syncthing 不處理換行轉換，建議所有裝置統一使用 LF

### 符號連結

- Syncthing 預設**不跟隨**符號連結（需在進階設定中啟用）
- `skills/` 目錄內可能包含 symlink（由 ai-dev clone 建立）
- Windows 建立 symlink 需要開發者模式或管理員權限

### 檔案權限

- macOS/Linux 有 POSIX 權限，Windows 沒有
- Syncthing 跨平台同步時建議啟用「忽略權限」
- Git 方案預設只追蹤執行位元（`core.fileMode`）

---

## 方案一：Syncthing 同步

即時雙向同步，適合需要**自動、無感同步**的場景。

### .stignore

將以下內容寫入 `~/.claude/.stignore`：

```
// === 本機暫存（可重建） ===
/debug
/cache
/paste-cache
/downloads
/stats-cache.json

// === OS 系統檔案 ===
.DS_Store
Thumbs.db
desktop.ini

// === 本機環境（跨機器無意義） ===
/shell-snapshots
/session-env
/ide
/statsig
/telemetry

// === 外掛（可 reinstall 重建） ===
/plugins/cache
/plugins/marketplaces
/plugins/repos
/plugins/install-counts-cache.json
// 保留 plugins/*.json（設定檔）
```

### ~/.claude-mem/.stignore

將以下內容寫入 `~/.claude-mem/.stignore`：

```
// === 本機暫存 ===
/logs
/worker.pid

// === SQLite 暫存檔（由主 DB 重建） ===
*.db-wal
*.db-shm
```

### 設定步驟

1. **各裝置安裝 Syncthing**
   - macOS: `brew install syncthing`
   - Linux: `sudo apt install syncthing` 或 `sudo pacman -S syncthing`
   - Windows: `winget install Syncthing.Syncthing` 或 `scoop install syncthing`

2. **新增共享資料夾 — ~/.claude**（在 Syncthing Web UI `http://localhost:8384`）
   - 路徑：`~/.claude`（Windows 填 `%USERPROFILE%\.claude`）
   - 資料夾 ID：`claude-config`（各裝置統一）
   - 資料夾標籤：`Claude Code Config`

3. **新增共享資料夾 — ~/.claude-mem**
   - 路徑：`~/.claude-mem`（Windows 填 `%USERPROFILE%\.claude-mem`）
   - 資料夾 ID：`claude-mem-db`（各裝置統一）
   - 資料夾標籤：`Claude Memory DB`

4. **建立 .stignore**
   - 將對應內容分別寫入 `~/.claude/.stignore` 和 `~/.claude-mem/.stignore`
   - `.stignore` 本身會被同步，所有裝置共享相同的排除規則

5. **連接對端裝置**
   - 交換 Device ID 並共享兩個資料夾

6. **建議的資料夾選項**
   - **檔案版本控制**：Staggered File Versioning（保留歷史版本，方便救回誤改）
   - **忽略權限**：啟用（跨平台必備）
   - **掃描間隔**：60 秒
   - **Watch for Changes**：啟用（即時偵測檔案變更）

### 衝突處理

| 情境 | 處理方式 |
|------|---------|
| 兩台同時編輯 `settings.json` | Syncthing 產生 `.sync-conflict` 檔案，手動合併後刪除衝突檔 |
| `history.jsonl` 同時追加 | 保留較大的檔案（append-only 特性） |
| `todos/` 同一 session 同時寫入 | 避免同時操作同一 session，衝突時保留較新版本 |
| lock 檔案衝突 | 已在 .stignore 排除 `ide/`，不會發生 |
| `claude-mem.db` SQLite 衝突 | 同步前停止 claude-mem worker；若已衝突，保留較大的 `.db` 檔案 |

**最佳實踐**：
- 避免在兩台裝置同時開啟 Claude Code 操作同一個 session
- 切換裝置前，確保 claude-mem worker 已停止（讓 WAL 回寫到主 DB）

---

## 方案二：Git 同步

版本控制同步，適合需要**變更歷史追蹤、手動控制同步時機**的場景。

### ai-dev sync 指令（推薦）

`ai-dev` 已內建 `sync` 指令群組，可用單一 repo 一次同步 `~/.claude` 與 `~/.claude-mem`。

```bash
# 1) 首次初始化（建立/clone ~/.config/ai-dev/sync-repo）
ai-dev sync init --remote git@github.com:<user>/claude-sync.git

# 2) 查看狀態（本機變更、遠端落後、最後同步時間）
ai-dev sync status

# 3) 離開目前裝置前推送
ai-dev sync push

# 4) 到新裝置後拉取（--no-delete 可避免刪除本機多出的檔案）
ai-dev sync pull --no-delete
```

新增或移除自訂同步目錄：

```bash
# 加入新目錄（預設 profile=custom）
ai-dev sync add ~/.gemini --ignore "cache/" --ignore "*.log"

# 指定內建 profile
ai-dev sync add ~/.claude --profile claude

# 從同步清單移除
ai-dev sync remove ~/.gemini
```

`sync` 會使用以下路徑：

- 設定檔：`~/.config/ai-dev/sync.yaml`
- 本機同步 repo：`~/.config/ai-dev/sync-repo/`

> **安全提醒**：remote 必須使用**私有 repo**，因為會話與記憶資料可能包含敏感內容。

### ~/.claude/.gitignore

```gitignore
# === 本機暫存（可重建） ===
debug/
cache/
paste-cache/
downloads/
stats-cache.json

# === OS 系統檔案 ===
.DS_Store
Thumbs.db
desktop.ini

# === 本機環境（跨機器無意義） ===
shell-snapshots/
session-env/
ide/
statsig/
telemetry/

# === 外掛（可 reinstall 重建） ===
plugins/cache/
plugins/marketplaces/
plugins/repos/
plugins/install-counts-cache.json
```

### ~/.claude-mem/.gitignore

```gitignore
# === 本機暫存 ===
logs/
worker.pid

# === SQLite 暫存檔 ===
*.db-wal
*.db-shm
```

### 初始化步驟

可以用兩個獨立 repo 或一個 repo 搭配 git submodule。以下示範獨立 repo：

**~/.claude**:
```bash
cd ~/.claude
git init && git branch -M main
# 建立 .gitignore（內容如上）
git config core.autocrlf input
git config core.ignoreCase false
git add .
git commit -m "初始化: Claude Code 配置同步"
git remote add origin git@github.com:<user>/claude-config.git
git push -u origin main
```

**~/.claude-mem**:
```bash
cd ~/.claude-mem
git init && git branch -M main
# 建立 .gitignore（內容如上）
git config core.autocrlf input
git add .
git commit -m "初始化: claude-mem 記憶資料庫同步"
git remote add origin git@github.com:<user>/claude-mem-db.git
git push -u origin main
```

> **安全提醒**：兩個 repo 都**必須使用私有 repo**。記憶資料庫包含程式碼片段和對話內容。

### 同步工作流程

#### 手動同步

```bash
# 離開時推送（兩個目錄）
for dir in ~/.claude ~/.claude-mem; do
  cd "$dir" && git add -A && git diff --cached --quiet || git commit -m "sync: $(hostname) $(date +%Y-%m-%d)" && git push
done

# 到新機器時拉取
for dir in ~/.claude ~/.claude-mem; do
  cd "$dir" && git pull --rebase
done
```

#### 自動同步（推薦）

使用 cron / systemd timer / Windows Task Scheduler 定時同步：

**macOS / Linux** — 建立 `~/.claude/sync.sh`：
```bash
#!/bin/bash
for dir in "$HOME/.claude" "$HOME/.claude-mem"; do
  cd "$dir" || continue
  git add -A
  git diff --cached --quiet && continue
  git commit -m "auto-sync: $(hostname) $(date +%Y-%m-%d-%H%M)"
  git pull --rebase
  git push
done
```

```bash
chmod +x ~/.claude/sync.sh
# cron: 每 10 分鐘執行
*/10 * * * * ~/.claude/sync.sh >> /tmp/claude-sync.log 2>&1
```

**Windows (Task Scheduler)** — 建立 `%USERPROFILE%\.claude\sync.ps1`：
```powershell
$dirs = @("$env:USERPROFILE\.claude", "$env:USERPROFILE\.claude-mem")
foreach ($dir in $dirs) {
    if (-not (Test-Path "$dir\.git")) { continue }
    Set-Location $dir
    git add -A
    $changes = git diff --cached --name-only
    if ($changes) {
        git commit -m "auto-sync: $env:COMPUTERNAME $(Get-Date -Format 'yyyy-MM-dd-HHmm')"
    }
    git pull --rebase
    git push
}
```

排程每 10 分鐘執行此腳本。

### Git 方案注意事項

| 考量 | 說明 |
|------|------|
| 大型 projects/ | 407MB+ 的 JSONL 會話紀錄，repo 會快速膨脹。考慮定期 `git gc --aggressive` 或使用 Git LFS |
| 二進位差異 | JSONL 檔案逐行追加，git diff 效率尚可。但 `projects/` 內的大型 session 檔案可能效率差 |
| 安全性 | **必須使用私有 repo**，會話紀錄可能包含敏感程式碼片段 |
| 合併衝突 | `git pull --rebase` 減少衝突，但 JSON 檔案衝突需手動解決 |
| `.gitattributes` | 建議加入 `*.jsonl merge=union` 讓 JSONL 自動合併 |

### 建議的 .gitattributes

```gitattributes
# JSONL 檔案使用 union merge（各行獨立，自動合併）
*.jsonl merge=union

# JSON 設定檔使用預設 merge（衝突時手動解決）
*.json merge=ort

# Markdown 使用 LF
*.md text eol=lf
```

---

## 方案比較

| 面向 | Syncthing | Git |
|------|-----------|-----|
| 同步方式 | 即時自動雙向 | 手動或定時 push/pull |
| 變更歷史 | 靠版本控制（有限保留） | 完整 git log |
| 衝突處理 | 自動偵測，產生 conflict 檔案 | rebase / merge |
| 離線使用 | 上線後自動追上 | 需手動 pull |
| 儲存空間 | 只佔同步檔案大小 | repo 歷史會累積膨脹 |
| 設定難度 | GUI 設定，較簡單 | 需 git 操作經驗 |
| 安全性 | P2P 加密，不經第三方 | 依賴 git host 安全性 |
| 大檔案 | 原生支援 | 需 Git LFS 或定期清理 |
| 跨平台 | 原生支援三平台 | 原生支援三平台 |
| **推薦場景** | 日常使用，多台機器即時同步 | 需要精確版本控制或團隊共享配置 |

**推薦**：日常個人使用選 Syncthing；需要版本歷史追蹤或在受限環境（無法安裝 Syncthing）時用 Git。

---

## 新裝置首次設定

不論使用哪種方案，同步完成後在新裝置執行：

```bash
# 1. 重新安裝 Claude Code 外掛（根據 installed_plugins.json 自動安裝）
claude plugins install
# 外掛 marketplace 會在首次使用時自動 clone

# 2. 啟動 claude-mem worker（記憶資料庫已同步，只需啟動服務）
# claude-mem 會自動讀取 ~/.claude-mem/settings.json 並使用既有資料庫

# 3. 其餘排除項目（debug, cache 等）會在 Claude Code 執行時自動產生
```

如果 `projects/` 路徑不匹配，手動重命名：

```bash
# 範例：macOS 路徑轉 Linux 路徑
cd ~/.claude/projects
mv -- "-Users-arlen-Documents-myproject" "-home-arlen-Documents-myproject"
```

如果 `~/.claude-mem/settings.json` 中的 `CLAUDE_MEM_DATA_DIR` 路徑不匹配，更新為本機路徑：

```bash
# 確認路徑指向正確位置
cat ~/.claude-mem/settings.json | grep CLAUDE_MEM_DATA_DIR
# 如需修改，更新為本機的絕對路徑
```
