# v1/v2 指令對齊分析報告

> **生成日期**: 2026-02-27
> **分支**: v2-bun-migration
> **分析範圍**: 全部 20 個指令 + TUI
> **注意**: v1 原始碼在 main 分支 `script/commands/`，build/lib 為舊版建置輸出

## 🔄 最新修復狀態（2026-02-27，多代理執行）

> 本段為最新執行結果。下方章節為較早盤點內容，部分狀態已過時。

| 範圍 | 最新狀態 | 備註 |
|------|----------|------|
| clone short options | ✅ 已修復 | 補齊 `-f/-s/-b` |
| add-custom-repo short options | ✅ 已修復 | 補齊 `-n/-b` |
| standards sync short options | ✅ 已修復 | 補齊 `-n/-t` |
| standards sync target/dry-run 行為 | ✅ 已修復 | `--target` 限定目標，`--dry-run` 不改檔 |
| sync init/add/remove parity | ✅ 已修復 | `--remote` 必填、add 先驗證目錄、remove 新增刪除子目錄確認 |
| project init reverse-sync 條件 | ✅ 已修復 | 僅 `--force` 才觸發反向同步 |
| toggle list/toggle-config 相容 | ✅ 已修復 | `--list` 輸出「整體啟用/停用項目」並同步 `toggle-config.yaml` |
| install/update 開頭與收尾輸出 | ✅ 已修復 | 補齊「開始安裝/更新」與完成提示 |
| TUI standards Enter / MCP e,f / source | ✅ 已修復 | Enter 切換 profile、e/f 可開啟設定、來源改為真實來源 |
| mem push/pull parity（P0-P2） | ✅ 已修復 | 四類資料、server_epoch、水位/匯入/reindex、CLI 輸出與 register 提示對齊 |
| sync push/pull parity（P0-P2） | ✅ 已修復 | force 確認、push_then_pull、`pull --rebase`、fail-fast、CLI 摘要格式對齊 |
| mem/sync 設定相容（v1→v2） | ✅ 已修復 | `sync-server.yaml` 與 `sync.yaml` snake_case 欄位可讀取 |

### 驗證摘要（本次）

- 針對 mem/sync parity 修復測試集合：`79 pass / 0 fail`
- 涵蓋：core parity（P0/P1）、CLI parity（P2）、既有回歸測試（`sync-engine`/`mem-sync`/`smoke`）全綠
- 本報告中 `mem/sync` 範圍可視為已完成 v1/v2 對齊；其餘非本次範圍差異維持既有盤點結果


## 總覽

| 狀態 | 數量 | 指令 |
|------|------|------|
| ✅ 已對齊 | 9 | test, derive-tests, coverage, add-custom-repo, update-custom-repo, mem, sync, clone, hooks |
| ⚠️ 輸出差異 | 8 | install, update, status, list, toggle, project, standards, add-repo |
| 🔧 功能缺失 | 1 | tui |

---

## 一、核心指令 (install, update, clone, status)

### 1. install

| 項目 | 狀態 | 說明 |
|------|------|------|
| 輸出格式 | ⚠️ | v1 實時逐行進度，v2 表格總結 |
| 業務邏輯 | ✅ | 核心流程一致（prerequisites → npm → repos → skills） |
| 選項 | ⚠️ | v2 新增 `--skip-bun`, `--json`（v1 無） |

**輸出差異明細：**
- v1: `[bold blue]開始安裝...[/bold blue]` → v2: 無此標題
- v1: `[bold cyan][1/6] 正在安裝 xxx...[/bold cyan]` 逐一進度 → v2: 表格彙總
- v1: `[green]正在 Clone 儲存庫...[/green]` 逐行 → v2: 表格彙總
- v1: `[yellow]⚠️ 已安裝的 Skills（建立自訂 skill 時請避免使用重複名稱）[/yellow]` → v2: 無此提示
- v1: `[bold green]安裝完成！[/bold green]` → v2: 表格

**邏輯差異：**
- v1: Node.js/Git 缺失直接 exit → v2: 記錄狀態繼續
- v2 新增: Bun 套件安裝、Shell Completion、superpowers symlink 同步

---

### 2. update

| 項目 | 狀態 | 說明 |
|------|------|------|
| 輸出格式 | ⚠️ | v1 實時逐行進度，v2 表格總結 |
| 業務邏輯 | ✅ | 核心流程一致 |
| 選項 | ⚠️ | v2 新增 `--skip-bun`, `--skip-plugins`, `--json` |

**輸出差異明細：**
- v1: `[bold blue]開始更新...[/bold blue]` → v2: 無此標題
- v1: `[bold cyan][1/6] 正在更新 xxx...[/bold cyan]` 逐一進度 → v2: 表格彙總
- v1: `[bold cyan]以下儲存庫有新更新：[/bold cyan]` + `• repo_name` → v2: 表格
- v1: `[bold green]更新完成！[/bold green]` → v2: `chalk.bold.green("更新完成！")`
- v1: `[dim]提示：如需分發 Skills...[/dim]` → v2: `chalk.dim("提示：...")`

**邏輯差異：**
- v2 新增: Plugin Marketplace 更新、superpowers symlink 刷新
- v1: Claude Code npm→native 切換建議 → v2: 簡潔記錄

---

### 3. clone

| 項目 | 狀態 | 說明 |
|------|------|------|
| 輸出格式 | ✅ | 已對齊（本次修復） |
| 業務邏輯 | ✅ | manifest 追蹤已接上 |
| 選項 | ✅ | 完全對齊 + `--json` |

**已修復項目（本次 session）：**
- ✅ 資源層級進度訊息: `skills → Claude Code` + `source → dest`
- ✅ 衝突跳過訊息: `跳過（衝突）: name`
- ✅ TARGET_NAMES 對照表
- ✅ 色彩格式: green(type) → cyan(target), dim(paths), yellow(conflict)

---

### 4. status

| 項目 | 狀態 | 說明 |
|------|------|------|
| 輸出格式 | ⚠️ | v1 Rich Table，v2 Simple Table |
| 業務邏輯 | ✅ | v2 擴展了檢測範圍 |
| 選項 | ⚠️ | v2 新增 `--json` |

**輸出差異明細：**
- v1: `[bold blue]AI 開發環境狀態檢查[/bold blue]` → v2: 相同文字
- v1: Core Tools 表格 (Node.js, Git) → v2: 擴展 (+ Bun, gh)
- v1: 3 種 repo 狀態 → v2: 6 種狀態 (含 ahead/diverged)
- v2 新增: Upstream Sync Status 表格

---

## 二、資源管理指令 (list, toggle, add-repo)

### 5. list

| 項目 | 狀態 | 說明 |
|------|------|------|
| 輸出格式 | ⚠️ | 表格欄位名差異 |
| 業務邏輯 | ✅ | 核心邏輯一致 |
| 選項 | ⚠️ | v2 缺少短選項 `-t`, `-T`, `-H` |

**輸出差異明細：**
- v1 表格欄位: 「名稱」「來源」「狀態」(中文) → v2: Name, Source, Status (英文)
- v1 狀態: `[green]✓ 啟用[/green]` → v2: `✓ Enabled` / `✓ 已啟用`
- v1 標題: `[bold blue]Claude Code - Skills[/bold blue]` → v2: `claude - skills`

---

### 6. toggle

| 項目 | 狀態 | 說明 |
|------|------|------|
| 輸出格式 | ⚠️ | v1 有視覺反饋，v2 無 |
| 業務邏輯 | ⚠️ | v2 丟棄 toggle-config.yaml 機制 |
| 選項 | ⚠️ | v2 缺少所有短選項 |

**輸出差異明細：**
- v1 啟用/停用: `[yellow]已停用 claude/skills/xxx[/yellow]` → v2: 無輸出
- v1 --list 表格: 有「整體啟用」欄位 → v2: 僅個別資源狀態
- v1 重啟提醒: `show_restart_reminder(target)` → v2: 無

**邏輯差異：**
- v1: 維護 toggle-config.yaml（全局開關） → v2: 純檔案系統 (.disabled 後綴)
- v1: 複製到 disabled 目錄 + 刪除原檔 → v2: rename 加 .disabled

---

### 7. add-repo

| 項目 | 狀態 | 說明 |
|------|------|------|
| 輸出格式 | ⚠️ | v1 有「下一步」提示 |
| 業務邏輯 | ✅ | 核心流程一致 |
| 選項 | ⚠️ | v2 缺少短選項 `-n`, `-b`, `-a` |

**輸出差異明細：**
- v1: `[bold blue]新增上游 Repo[/bold blue]` + 詳細資訊 → v2: 表格
- v1: `[bold green]✓ 完成！[/bold green]` + 下一步提示 → v2: 無下一步

---

### 8. add-custom-repo ✅

| 項目 | 狀態 | 說明 |
|------|------|------|
| 輸出格式 | ⚠️ | v1 Rich 逐步進度，v2 表格摘要 |
| 業務邏輯 | ✅ | 核心流程一致（parse URL → clone → 驗證 → 寫入 config） |
| 選項 | ✅ | v2 新增 `--no-clone`（向後相容） |

**v1 原始碼**: `script/commands/add_custom_repo.py` (main 分支)

---

### 9. update-custom-repo ✅

| 項目 | 狀態 | 說明 |
|------|------|------|
| 輸出格式 | ⚠️ | v1 逐行進度，v2 統計表格 |
| 業務邏輯 | ✅ | 核心流程一致（fetch → 備份 dirty → reset） |
| 選項 | ✅ | v2 新增 `--json` |

**v1 原始碼**: `script/commands/update_custom_repo.py` (main 分支)

---

## 三、專案/設定指令 (project, standards, hooks, sync)

### 10. project

| 項目 | 狀態 | 說明 |
|------|------|------|
| 輸出格式 | ⚠️ | v1 逐檔案進度，v2 只有摘要 |
| 業務邏輯 | ✅ | 核心流程一致（init + update） |
| 選項 | ⚠️ | v2 缺少短選項 `-f`, `-o` |

**輸出差異明細：**
- v1 init:
  ```
  [bold blue]開始初始化專案...[/bold blue]
  [dim]模板目錄：{path}[/dim]
    [green]✓[/green] filename/
    [blue]合併[/blue] filename
    [dim]無變更[/dim] filename
  [bold green]專案初始化完成！[/bold green]
  [dim]下一步：...[/dim]
  ```
- v2 init: 只輸出摘要表格

---

### 11. standards

| 項目 | 狀態 | 說明 |
|------|------|------|
| 輸出格式 | ⚠️ | v1 Rich 豐富樣式，v2 表格 |
| 業務邏輯 | ⚠️ | v2 sync 邏輯簡化（僅 .ai.yaml） |
| 選項 | ⚠️ | v2 缺少 `-n` (dry-run), `-t` (target) |

**輸出差異明細：**
- v1 switch:
  ```
  [green]✓ 成功從 'old' 切換到 'new'[/green]
    設定檔更新: 停用 N 個項目
    檔案同步: 停用 X 個, 啟用 Y 個
  [yellow]⚠️ 請重啟 Claude Code 以套用變更[/yellow]
  ```
- v2 switch: `✓ Switched to profile 'xxx'` + 計數表格

**邏輯差異：**
- v1 sync: 處理 skills/commands/agents 資源移動 → v2: 僅處理 .ai.yaml 標準文件

---

### 12. hooks

| 項目 | 狀態 | 說明 |
|------|------|------|
| 輸出格式 | ⚠️ | v1 Rich 色彩，v2 符號前綴 |
| 業務邏輯 | ✅ | 核心流程一致 |
| 選項 | ✅ | v2 新增 `--yes` 跳過確認 |

**輸出差異明細：**
- v1 install: `[bold blue]Installing ECC Hooks Plugin...[/bold blue]` → v2: `✓ Installed to: {path}`
- v1 交互: `typer.confirm()` → v2: `inquirer.prompt()` + `--yes`

---

### 13. sync ✅

| 項目 | 狀態 | 說明 |
|------|------|------|
| 輸出格式 | ✅ | `push/pull` 完成文案與摘要格式已對齊（`sync push/pull 完成` + `+X ~Y -Z`） |
| 業務邏輯 | ✅ | `push/pull` 安全流程與失敗處理已對齊（force 確認、`push_then_pull`、`pull --rebase`、fail-fast） |
| 選項 | ✅ | v2 全量新增 `--json` |

**v1 原始碼**: `script/commands/sync.py` (main 分支)

**子指令**: init, push, pull, status, add, remove（v1/v2 均為 6 個）

**最新對齊摘要（2026-02-27）：**
- ✅ `sync push/pull` 完成文案改為 `sync push 完成` / `sync pull 完成`
- ✅ 摘要格式改為 `+{added} ~{updated} -{deleted}`
- ✅ pull 衝突選項含「先 push 再 pull（推薦）」
- ✅ 關鍵 git 指令失敗改為 fail-fast，並統一使用 `git pull --rebase`

---

## 四、工具指令 (mem, test, derive-tests, coverage)

### 14. mem ✅

| 項目 | 狀態 | 說明 |
|------|------|------|
| 輸出格式 | ✅ | `push/pull` 關鍵輸出已對齊（包含 `Pull 完成 (API|SQLite)` 動態 method label） |
| 業務邏輯 | ✅ | `push/pull` 核心資料流、水位與後處理已對齊 |
| 選項 | ✅ | v2 auto 改為 `--enable/--disable`（更清晰），全量 `--json` |

**v1 原始碼**: `script/commands/mem.py` (main 分支)

**子指令**: register, push, pull, status, cleanup, reindex, auto（v1/v2 均為 7 個）

**選項變更：**
- v1 auto: `--on/--off` → v2: `--enable/--disable/--status/--interval`

**最新對齊摘要（2026-02-27）：**
- ✅ push 改為四類資料增量推送（sessions/observations/summaries/prompts）
- ✅ 未註冊時錯誤提示與 v1 對齊（含 `ai-dev mem register` 指引）
- ✅ pull 匯入路徑為 API 優先 + SQLite fallback
- ✅ pull 完成文案 method label 動態顯示 API/SQLite

---

### 15. test ✅

| 項目 | 狀態 | 說明 |
|------|------|------|
| 輸出格式 | ✅ | 直接透傳測試框架輸出 |
| 業務邏輯 | ✅ | v2 擴展多框架支援（bun, pytest, phpunit, npm） |
| 選項 | ✅ | v2 新增 `--framework`（向後相容） |

---

### 16. derive-tests ✅

| 項目 | 狀態 | 說明 |
|------|------|------|
| 輸出格式 | ✅ | 基本一致（v2 用相對路徑） |
| 業務邏輯 | ✅ | 相同 |
| 選項 | ✅ | 相同 |

---

### 17. coverage ✅

| 項目 | 狀態 | 說明 |
|------|------|------|
| 輸出格式 | ✅ | 直接透傳覆蓋率報告 |
| 業務邏輯 | ✅ | v2 擴展多框架（不僅限 pytest） |
| 選項 | ✅ | v2 新增 `--framework` |

---

## 五、TUI

### 18. tui

| 項目 | 狀態 | 說明 |
|------|------|------|
| 框架 | 🔄 | v1: Textual (Python) → v2: Ink (React) |
| 功能完整度 | 🔧 | v2 缺失多項 v1 功能 |

**v2 缺失功能：**

| 功能 | v1 | v2 | 優先級 |
|------|----|----|--------|
| Standards Profile 管理 | ✅ 完整（預覽+切換） | ❌ 未實作 | 高 |
| MCP 配置管理 | ✅ 路徑+編輯器+檔案管理 | ❌ 未實作 | 高 |
| 第三方 Skills 安裝 | ✅ AddSkillsModal | ⚠️ 僅提示 | 中 |
| CLI 命令快捷 | ✅ Install/Update/Clone/Status | ❌ 未實作 | 中 |
| Antigravity target | ✅ | ❌ 移除 | 低 |
| Source 篩選 | ✅ 7 個選項 | ⚠️ 2 個選項 | 中 |

---

## 六、跨指令共通差異

### 輸出體系

| 面向 | v1 (Python/Rich) | v2 (TypeScript/Chalk) |
|------|-------------------|------------------------|
| 色彩庫 | Rich (bold blue/cyan/yellow/green + dim) | Chalk (green/cyan/yellow/red + dim) |
| 進度展示 | 實時逐行輸出 | 收集結果後表格總結 |
| 中文訊息 | 硬編碼 | i18n 系統 (`t("key")`) |
| 表格渲染 | Rich Table (含色彩欄位) | printTable() (簡化) |
| JSON 輸出 | 無 | 全指令支援 `--json` |

### 短選項

v2 全面移除了 v1 的短選項支援：

| 短選項 | v1 指令 | 說明 |
|--------|---------|------|
| `-t` | list, toggle, standards | target |
| `-T` | list, toggle | type |
| `-n` | toggle, add-repo, standards | name / dry-run |
| `-e` | toggle | enable |
| `-d` | toggle | disable |
| `-l` | toggle | list |
| `-H` | list | hide-disabled |
| `-f` | project | force |
| `-o` | project | only |
| `-b` | add-repo | branch |
| `-a` | add-repo | analyze |

### 錯誤處理

| 面向 | v1 | v2 |
|------|----|----|
| 策略 | 即時 exit(1) | 收集錯誤到結果結構 |
| 輸出 | print(stderr) | process.stderr.write() |
| 退出 | typer.Exit(code=N) | process.exitCode = N |

---

## 七、修復建議優先級

### P0 — 必須修復（影響功能正確性）

| # | 指令 | 問題 | 說明 |
|---|------|------|------|
| 1 | toggle | toggle-config.yaml 機制丟棄 | 無法支援全局開關 |
| 2 | standards | sync 僅處理 .ai.yaml | 應同時處理 skills/commands/agents |
| 3 | toggle | 啟用/停用無視覺反饋 | 使用者不知操作是否成功 |

### P1 — 應該修復（輸出格式一致性）

| # | 指令 | 問題 |
|---|------|------|
| 4 | install | 缺少實時進度輸出 |
| 5 | update | 缺少實時進度輸出 |
| 6 | list | 表格欄位名應國際化 |
| 7 | project | init 缺少逐檔案進度 |
| 8 | hooks | 色彩格式不一致 |
| 9 | 全部 | 恢復短選項支援 |

### P2 — 可以修復（增強體驗）

| # | 指令 | 問題 |
|---|------|------|
| 10 | add-repo | 缺少「下一步」提示 |
| 11 | toggle | 缺少重啟提醒 |
| 12 | tui | Standards Profile 管理未實作 |
| 13 | tui | MCP 配置管理未實作 |
| 14 | tui | Source 篩選過度簡化 |

---

## 八、結論

v2 的核心業務邏輯大致與 v1 對齊（20 個指令中 9 個已完全對齊），主要差異集中在：

1. **輸出格式**：v2 偏向表格總結，v1 偏向實時逐行進度 — 這是架構差異（async result → render vs sync print），非錯誤
2. **短選項**：v2 全面移除，應恢復以維持向後相容
3. **toggle 機制**：v2 簡化為檔案系統操作，丟失了 toggle-config 全局開關
4. **TUI**：v2 功能不完整，需補足 Standards Profile 和 MCP 管理
5. **v2 改進**：全指令新增 `--json` 輸出、i18n 國際化、多框架測試支援
