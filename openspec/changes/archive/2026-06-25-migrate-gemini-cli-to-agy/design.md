## Context

`ai-dev` 將統一來源的 skills/commands/agents 分發到多個 AI 工具 target：`claude`、`antigravity`、`opencode`、`codex`、`gemini`。其中 `gemini` 對應 Google Gemini CLI（`gemini` 指令、`~/.gemini/` 設定、`@google/gemini-cli` npm 套件）。

Google 已於 2026-06-18 關閉 Gemini CLI，繼任者為 Antigravity CLI（`agy`），以單一執行檔發行、不經 npm。現況問題：

1. `NPM_PACKAGES` 仍含 `@google/gemini-cli`（`shared.py:57`），`ai-dev install` 會嘗試安裝退役套件。
2. `gemini` 作為 target 識別碼與 `Gemini CLI` 顯示字串硬編碼於多處（`shared.py`、`paths.py`、`standards.py`、`project_tracking.py`、`tui/app.py`）。

注意：專案另有獨立的 `antigravity` target，對應 Antigravity 的 IDE/VSCode 版本，設定落在 `~/.gemini/antigravity/`。`agy` 是 Antigravity 的「終端 CLI」版本，與 IDE 屬同一產品家族但介面不同；本變更不合併這兩個 target。

文件層（`docs/AI開發環境設定指南.md`、`docs/Skill-Command-Agent差異說明.md`）的安裝/使用說明已於前一變更更新為 agy，本變更僅處理程式碼面。

### agy 設定路徑（已以真實安裝 v1.0.12 + 官方文件確認）

實測安裝（`curl ... install.sh | bash`，binary 落在 `~/.local/bin/agy`）後的檔案系統證據，並對照官方 `antigravity.google/docs/cli-settings`、`/docs/skills` 與 Google Cloud Community 實測文章：

- CLI 設定：`~/.gemini/antigravity-cli/settings.json`（實測存在）、keybindings：`~/.gemini/antigravity-cli/keybindings.json`
- builtin skills：`~/.gemini/antigravity-cli/builtin/skills/`（實測存在）
- **共用 skills（所有 Antigravity 工具，含 agy）：`~/.gemini/skills/`** ← **與專案現有 `gemini` skills 路徑相同，確認 agy 會讀取**
- CLI 專屬全域 skills：`~/.gemini/antigravity-cli/skills/`
- 共用 MCP 設定：`~/.gemini/config/mcp_config.json`（實測：安裝即建立此檔）
- 工作區層級：`.agents/skills/`、`.agents/mcp_config.json`；skill 格式 `{name}/SKILL.md`
- agy 無獨立全域 commands 目錄；slash 指令以 skill 實作
- 重要更正：官方一度稱全域 skills 在 `~/.gemini/antigravity/skills/`，**實測無效**（工具不會讀取該處）；正解為共用 `~/.gemini/skills/`，故沿用現有路徑即正確

## Goals / Non-Goals

**Goals:**
- 移除已退役的 `@google/gemini-cli` npm 安裝，讓 `ai-dev install` 不再嘗試安裝死套件。
- 將 `gemini` target 直接改名為 `agy`（不留別名），顯示名稱為 `Antigravity CLI (agy)`。
- agy target 僅分發 skills 至 `~/.gemini/skills/`（共用路徑、與現況一致）；移除 commands/agents 分發。
- MCP 設定對照改指向 agy 的 `~/.gemini/config/mcp_config.json`。
- 程式碼、測試、README 與資料流文件同步更新。

**Non-Goals:**
- 不合併或改動既有 `antigravity`（IDE）target。
- 不由 `ai-dev` 自動安裝 `agy`（官方為執行檔安裝，無 npm/Homebrew）。
- 不改寫歷史 `CHANGELOG.md` 與歷史 plan/report。
- 不保留 `gemini` 相容別名（依使用者指示）。
- 不處理專案層級 npx skills 投影層（`_NPX_PROJECT_AGENTS` 的外部 `gemini-cli` agent、`.gemini` 投影目錄、`project-template` 的 `.gemini/`）。此層耦合外部 `npx skills` 工具的 agent 命名，是否支援 `agy` 未確認，留待另一變更。

## Decisions

### 決策 1：直接改名 `gemini` → `agy`，不保留別名
採硬改名。`--target gemini`、`toggle-config.yaml` 的 `gemini` 鍵改為 `agy`，舊值不再接受。
- 理由：使用者明確要求不需別名；工具已更名，保留舊值徒增雙套命名與維護負擔。
- 替代方案：保留 `gemini→agy` 別名以平滑遷移。已被使用者否決。
- 後果：屬 BREAKING，既有使用者需手動更新設定/腳本中的 target 值；於 CHANGELOG 提供遷移指引。

### 決策 2：移除 npm 自動安裝，不改為 curl 自動安裝
從 `NPM_PACKAGES` 移除 `@google/gemini-cli`，且**不**新增 agy 的 curl 自動安裝。
- 理由：`ai-dev install` 目前安裝管線為 npm/bun 套件；把 `curl | bash` 外部安裝塞進管線會引入跨平台與權限的新風險，超出本變更範圍。agy 安裝改由文件指引使用者自行執行。
- 替代方案：在 install 階段執行官方 install.sh/ps1。屬另一階段工作，本變更不納入。

### 決策 3：agy target 僅分發 skills，路徑沿用 `~/.gemini/skills`（已實測確認）
`get_gemini_cli_config_dir()` 改名 `get_agy_config_dir()`，回傳維持 `~/.gemini`；skills 分發目錄維持 `~/.gemini/skills`（agy 的共用 skills 位置）。移除 `commands`、`agents` 分發。
- 理由：真實安裝 v1.0.12 + 官方文件確認 `~/.gemini/skills` 為 agy 讀取的共用 skills 目錄，故沿用現有路徑變動最小且正確；agy 無全域 commands/agents 目錄，續留會分發到 agy 不讀取的位置。
- 替代方案 A：改用 agy 專屬 `~/.gemini/antigravity-cli/skills`。僅 agy 讀取、不與 IDE 共用；本變更採共用路徑即可，無需切換。
- 替代方案 B：保留 commands 分發。agy 不讀取，等同無效分發，否決。

### 決策 4：MCP 設定對照改指向 agy 的 mcp_config.json
`get_mcp_config_path`（`shared.py:3304`）的 `agy` 項由 `~/.gemini/settings.json` 改為 `~/.gemini/config/mcp_config.json`。
- 理由：agy 的 MCP 設定在 `~/.gemini/config/mcp_config.json`，TUI 顯示與「Open in Editor」才會指到正確檔案。

## Risks / Trade-offs

- [硬改名造成既有設定中斷] → 於 CHANGELOG 明確標注遷移指引（`gemini` → `agy`）；改名涉及處以 grep 全覆蓋確保無遺漏。
- [漏改某處硬編碼 `gemini` 導致分發或 toggle 失效] → grep 全覆蓋盤點 + 測試夾具更新 + 跑既有測試套件驗證。
- [共用 vs 專屬 skills 路徑判斷錯誤] → 先採 `~/.gemini/skills`（與現況一致），安裝 agy 後實測 `/config` 與實際讀取位置再決定是否切換到 `~/.gemini/antigravity-cli/skills`。
- [移除 commands 分發影響既有 gemini commands 使用者] → 來源 `commands/gemini/` 目前無實質內容；於 CHANGELOG 說明 agy 改用 skills 機制。

## Migration Plan

1. 先移除退役 npm 套件與改 `TargetType`，再逐處改名對照表，最後改測試與文件。
2. 修改 `NPM_PACKAGES`、`TargetType`、各 target 對照表、顯示字串、重啟提示、MCP map；移除 agy 的 commands/agents 分發。
3. 更新測試夾具與斷言，跑 `pytest` 全綠。
4. 更新 README 與 `docs/ai-dev指令與資料流參考.md` 的 `--target` 可用值（`gemini` → `agy`）。
5. CHANGELOG 記錄 target 改名（BREAKING、含遷移指引）與移除退役 npm 套件。
- 回滾：純程式碼/設定改名，git revert 即可。

## Open Questions

- （已解決）全域 skills 讀取位置：真實安裝 v1.0.12 + 官方文件確認為共用 `~/.gemini/skills`，與專案現有路徑相同，沿用即可，無未決項。
