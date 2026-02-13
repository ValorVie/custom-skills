# ai-dev sync 跨裝置同步教學

> 使用 `ai-dev sync` 指令透過 Git 同步 Claude Code 配置、記憶資料庫與自訂目錄。

---

## 前置條件

- **Git** 已安裝且可用
- **私有 Git 遠端倉庫**（GitHub / GitLab / 自架）— 同步內容可能包含敏感資訊
- **SSH Key 認證**（建議）— 避免每次 push/pull 輸入密碼

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
4. 執行首次同步並推送到遠端

### 第二台機器：加入同步

```bash
# 同樣初始化，指向相同遠端倉庫
ai-dev sync init --remote git@github.com:<user>/claude-sync.git

# 拉取遠端內容到本機
ai-dev sync pull
```

---

## 日常使用

### 離開前：推送變更

```bash
ai-dev sync push
```

將本機所有同步目錄的變更推送到遠端。

### 換到另一台機器：拉取變更

```bash
ai-dev sync pull
```

從遠端拉取最新變更，同步到本機目錄。

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
| `pull` | 拉取遠端變更到本機 | `ai-dev sync pull --no-delete` |
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

## 預設 Ignore Profile

### claude

排除 `~/.claude` 中不需同步的檔案：

```
debug/  cache/  paste-cache/  downloads/  shell-snapshots/
session-env/  ide/  statsig/  telemetry/  stats-cache.json
plugins/cache/  plugins/marketplaces/  plugins/repos/
plugins/install-counts-cache.json
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

### SQLite 資料庫安全

`claude-mem.db` 為 SQLite 資料庫，同步期間若正在寫入可能損壞。

**建議**：同步前先確認 claude-mem worker 已停止（或至少沒有活躍的寫入操作）。

### 大型檔案與倉庫膨脹

`~/.claude/projects/` 可能累積到數百 MB。長期使用建議：

- 定期執行 `git gc --aggressive`（在 sync-repo 目錄內）
- 評估是否使用 Git LFS 處理大型 JSONL 檔案

### 跨平台路徑差異

`~/.claude/projects/` 下的子目錄名稱包含機器路徑（如 `-Users-arlen-Documents-project`）。不同機器若專案路徑不同，Claude Code 不會自動關聯。

**解決方式**：統一各機器的專案路徑，或手動重新命名目錄。

### 合併衝突

- 使用 `git pull --rebase` 減少衝突機率
- `.gitattributes` 已設定 `*.jsonl merge=union` 自動合併 JSONL 檔案
- JSON 檔案若發生衝突需手動解決

### 拉取後重裝外掛

外掛的實際程式碼（`plugins/marketplaces/`、`plugins/repos/`）已排除同步。拉取到新機器後需重新安裝：

```bash
claude plugins install
```

---

## 相關文件

- [Claude Code 跨裝置同步指南](../ai-tools/CLAUDE-CODE-SYNC.md) — Syncthing / Git 兩種方案的完整比較
- [ai-dev CLI 框架技術架構](ai-dev-framework-architecture.md) — ai-dev 整體架構說明
