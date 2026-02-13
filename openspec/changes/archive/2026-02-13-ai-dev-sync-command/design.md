## Context

開發者跨裝置使用 Claude Code 時，`~/.claude`（配置、會話、技能）和 `~/.claude-mem`（記憶資料庫）無法共享。已完成目錄結構分析與排除規則文件（`docs/dev-guide/ai-tools/CLAUDE-CODE-SYNC.md`），現在要將 Git 同步方案內建到 ai-dev CLI。

現有架構中，ai-dev 已有：
- `script/commands/` 下的 Typer 指令模式（standalone function 或 Typer app subgroup）
- `script/utils/paths.py` 統一管理所有 AI 工具路徑
- `script/utils/system.py` 提供 `run_command()`、`get_os()` 等跨平台工具
- `script/utils/git_helpers.py` 提供 `is_git_repo()` 等 Git 操作
- `~/.config/ai-dev/repos.yaml` 作為設定檔先例

## Goals / Non-Goals

**Goals:**
- 提供 `ai-dev sync` 指令群組，用 Git 同步多個 AI 工具配置目錄
- 單一 repo 管理所有目錄，一次 push/pull 完成同步
- 內建 ignore profiles 自動排除不需同步的檔案
- 可配置：預設 `~/.claude` + `~/.claude-mem`，使用者可新增其他目錄
- 跨平台：macOS、Linux、Windows

**Non-Goals:**
- 不做 Syncthing 整合
- 不內建自動同步排程（cron/launchd/Task Scheduler）
- 不處理 `projects/` 路徑重新映射（留給使用者手動）
- 不做 Git LFS 整合（未來可擴充）

## Decisions

### D1: 單 repo 多子目錄 vs 多獨立 repo

**選擇**：單一 repo，每個同步目錄對應 repo 中的一個子目錄。

```
~/.config/ai-dev/sync-repo/
├── .gitignore
├── .gitattributes
├── claude/          ← ~/.claude 的內容
└── claude-mem/      ← ~/.claude-mem 的內容
```

**替代方案**：每個目錄獨立 git repo（各有各的 remote）。
**理由**：單 repo 只需設定一個 remote URL，一次操作同步所有目錄，不需管理多組 credentials。

### D2: rsync + shutil 雙軌策略

**選擇**：macOS/Linux 使用 `rsync`，Windows 使用 Python `shutil` + `fnmatch` exclude。

封裝為 `sync_directory(src, dst, excludes, delete=True)` 函數。

**替代方案**：全部用 Python shutil（跨平台一致）。
**理由**：rsync 在 Unix 上效能遠優於 shutil（增量傳輸、硬連結），Windows 無原生 rsync，fallback 到 shutil 是合理的折衷。

### D3: 設定檔格式與位置

**選擇**：`~/.config/ai-dev/sync.yaml`，YAML 格式。

**替代方案**：JSON 或存在 `~/.claude/` 內。
**理由**：與現有 `repos.yaml` 同層，YAML 可讀性高且支援註解。存在 `~/.config/ai-dev/` 而非被同步目錄內，避免循環依賴。

### D4: .gitignore 生成策略

**選擇**：依據各目錄的 ignore profile 產生帶有路徑前綴的合併 `.gitignore`。

```gitignore
# claude/ profile
claude/debug/
claude/cache/
...
# claude-mem/ profile
claude-mem/logs/
claude-mem/worker.pid
...
```

**理由**：單一 repo 需要用路徑前綴區分各目錄的排除規則，合併到一個 `.gitignore` 比 nested `.gitignore` 簡單。

### D5: 指令群組結構

**選擇**：使用 Typer app subgroup（如同 `hooks.py` 模式），註冊為 `ai-dev sync`。

子指令：`init`、`push`、`pull`、`status`、`add`、`remove`。

## Risks / Trade-offs

- **[Risk] SQLite DB 同步可能損毀** → claude-mem 的 `.db` 在寫入中被同步可能損毀。Mitigation：排除 WAL/SHM 檔案，文件提醒使用者同步前停止 worker。
- **[Risk] Repo 膨脹** → `projects/` 有 407MB JSONL 檔案，頻繁 commit 會讓 repo 快速膨脹。Mitigation：commit message 包含 `--no-gpg-sign` 減少開銷，未來可加 Git LFS 支援。
- **[Risk] rsync --delete 誤刪** → pull 時 rsync `--delete` 可能刪除本機新增但尚未 push 的檔案。Mitigation：pull 前先做 push，或提供 `--no-delete` 選項。
- **[Trade-off] 不做自動同步** → 使用者需手動 push/pull。接受此限制以降低複雜度，文件中提供 cron 設定範例。
