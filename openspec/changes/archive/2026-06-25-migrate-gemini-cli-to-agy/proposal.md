## Why

Google 已於 2026-06-18 關閉舊版 Gemini CLI（`gemini` 指令、`@google/gemini-cli` 套件），由 Antigravity CLI（`agy` 指令）接手。目前 `ai-dev` 仍把 `@google/gemini-cli` 列在全域 npm 安裝清單，`ai-dev install` 會嘗試安裝已退役的套件而失敗；同時 `gemini` target、`Gemini CLI` 顯示字串、重啟提示與設定路徑全程硬編碼在程式碼中，與現況不符。文件層已先行更新，本變更處理程式碼面。

## What Changes

- 從 `NPM_PACKAGES` 移除 `@google/gemini-cli`（已退役、無法安裝）；`agy` 改以官方執行檔安裝，**不**由 `ai-dev` 自動安裝。
- **BREAKING**：將分發 target 識別碼 `gemini` 直接改名為 `agy`（不保留相容別名），顯示名稱由 `Gemini CLI` 改為 `Antigravity CLI (agy)`。對外的 `--target gemini` 與 `toggle-config.yaml` 的 `gemini` 鍵改為 `agy`，舊值不再被接受。涵蓋 `TargetType`、`COPY_TARGETS`、`platform_configs`、toggle 預設、`get_target_path`、list 的 `targets`／`type_mapping`、MCP 設定對照、`VALID_TARGETS`、`project_tracking` targets、TUI 下拉、`install.py` 匯入與相關 docstring。
- 設定目錄輔助函式 `get_gemini_cli_config_dir()` 改名為 `get_agy_config_dir()`（回傳 `~/.gemini`）。agy 的 skills 分發沿用 `~/.gemini/skills/`（agy 與所有 Antigravity 工具共用的 skills 目錄），路徑不變。
- 移除 agy target 的 `commands` 與 `agents` 分發：agy 無全域 commands/agents 目錄，slash 指令以 skill（`SKILL.md`）實作。agy target 僅分發 `skills`。
- MCP 設定對照由 `~/.gemini/settings.json` 改為 agy 的 `~/.gemini/config/mcp_config.json`。
- 更新重啟提示訊息：由「重啟 Gemini CLI、重新執行 `gemini`」改為「重啟 Antigravity CLI、重新執行 `agy`」。
- 同步更新測試夾具與 README、`docs/ai-dev指令與資料流參考.md` 中的 `--target gemini` API 說明。

## Capabilities

### New Capabilities
<!-- 無新增能力，屬既有分發能力的修正 -->

### Modified Capabilities
- `cli-distribution`: 分發目標以 `agy`（取代 `gemini`）為 Antigravity CLI 目標，僅分發 skills 至 `~/.gemini/skills/`；依賴宣告移除已退役的 `@google/gemini-cli`；移除來源 `commands/gemini/` 的對映（agy 無全域 commands 目錄）。

## Impact

- 程式碼：`script/utils/shared.py`（`TargetType`、`NPM_PACKAGES`、`COPY_TARGETS`、`platform_configs`、toggle 預設、`get_target_path`、list targets/type_mapping、MCP map、重啟提示）、`script/utils/paths.py`（`get_gemini_cli_config_dir`）、`script/commands/standards.py`（`VALID_TARGETS`）、`script/utils/project_tracking.py`、`script/tui/app.py`、`script/commands/install.py`、`script/utils/manifest.py` docstring。
- 設定／資料：`toggle-config.yaml` 的 target 鍵由 `gemini` 改 `agy`；來源目錄 `commands/gemini/`（若存在）停止對映。
- 測試：`tests/test_project_tracking.py`、`tests/test_git_exclude.py`、`tests/test_clone_policy.py`、`tests/test_smart_merge.py` 中引用 `gemini` target 的夾具與斷言改為 `agy`。
- 文件：README、`docs/ai-dev指令與資料流參考.md`（`--target` 可用值改 `agy`）。`docs/AI開發環境設定指南.md` 與 `docs/Skill-Command-Agent差異說明.md` 的安裝/使用說明已於先前變更更新。
- 相容性：**不保留**舊值 `gemini`；既有使用者需把設定與腳本中的 `--target gemini`／toggle 鍵手動改為 `agy`（於 CHANGELOG 標注遷移指引）。
- 不在範圍：歷史 `CHANGELOG.md`、歷史 plan/report 文件不改寫。
- 已實測確認：真實安裝 agy v1.0.12 + 官方文件確認共用 skills 為 `~/.gemini/skills`（與專案現有 `gemini` 路徑相同、agy 會讀取），MCP 設定為 `~/.gemini/config/mcp_config.json`（安裝即建立）。沿用現有 skills 路徑即可，無未決項。
