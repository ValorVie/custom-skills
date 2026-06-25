## 1. 移除退役 npm 套件

- [x] 1.1 從 `script/utils/shared.py` 的 `NPM_PACKAGES` 移除 `@google/gemini-cli`
- [x] 1.2 確認 `ai-dev install` 安裝流程不再引用該套件（另移除 `status.py` 的 npm 顯示清單與 binary_map）

## 2. 改名 target：gemini → agy（程式碼，硬改名不留別名）

- [x] 2.1 `shared.py` `TargetType` Literal：`"gemini"` → `"agy"`
- [x] 2.2 `shared.py` `COPY_TARGETS`：改 `"agy"`，僅保留 `skills`（`get_agy_config_dir() / "skills"`）
- [x] 2.3 `shared.py` `platform_configs`：鍵 `"agy"`、`name` `"Antigravity CLI (agy)"`、僅 skills；移除 `src_cmd_gemini`
- [x] 2.4 `shared.py` 重啟提示：改為「重啟 Antigravity CLI、重新執行 `agy`」
- [x] 2.5 `shared.py` `DEFAULT_TOGGLE_CONFIG`：`"agy"`，僅 skills
- [x] 2.6 `shared.py` `get_target_path`：僅 `("agy", "skills")`
- [x] 2.7 `shared.py` list `targets` 與 `type_mapping["agy"] = ["skills"]`
- [x] 2.8 `shared.py` MCP 對照：`"agy"` → `~/.gemini/config/mcp_config.json`
- [x] 2.9 `paths.py`：`get_gemini_cli_config_dir()` → `get_agy_config_dir()`（回傳 `~/.gemini`），更新所有 import/呼叫（`shared.py`、`install.py`、`refresh.py`）
- [x] 2.10 `standards.py` `VALID_TARGETS`：`"agy"`
- [x] 2.11 `project_tracking.py` `targets`：`"agy"`
- [x] 2.12 `tui/app.py`：下拉項 `("Antigravity CLI (agy)", "agy")`、type 對照 `"agy": [("Skills","skills")]`
- [x] 2.13 docstring 的 target 列舉（`shared.py`、`manifest.py`）`gemini` → `agy`
- [x] 2.14 （apply 時發現）`toggle.py`、`list.py` 的第二組驗證清單/顯示名/typer help；`command_manifest.py` `TARGETS`；`npx_skills/manifest_sync.py` `_ALL_TARGETS`

## 3. 設定與目錄建立

- [x] 3.1 `install.py`、`refresh.py` 的目錄建立：agy 僅留 `~/.gemini/skills`，移除 commands 建立
- [x] 3.2 來源 `commands/gemini/` 不再對映（platform_configs 已移除 `src_cmd_gemini`）

## 4. 測試

- [x] 4.1 更新 `tests/test_clone_policy.py`（COPY_TARGETS fixture）、`tests/test_project_tracking.py`（DEFAULT_PROJECTION targets）為 `agy`
- [x] 4.2 新增 `tests/test_agy_target.py`：agy 有效且僅 skills、`gemini` 失效、npm 套件已移除
- [x] 4.3 `pytest` 全套通過（426 passed）

## 5. 文件與紀錄

- [x] 5.1 `README.md`：`--target` 值、npm 清單、相容性表、命令樹、toggle-config 範例、TUI、MCP 表
- [x] 5.2 `docs/ai-dev指令與資料流參考.md`：`--target` 可用值 `gemini` → `agy`
- [x] 5.3 `CHANGELOG.md`：BREAKING 條目 + 遷移指引

## 6. 驗收

- [x] 6.1 `openspec validate migrate-gemini-cli-to-agy --strict` 通過
- [x] 6.2 grep 確認：`@google/gemini-cli` 僅剩文件；`script/` 無殘留 `gemini` 分發 target（剩餘皆為合法 `~/.gemini` 路徑、agy MCP、或 npx 層 `gemini-cli`）
- [x] 6.3 （已完成）實測 agy v1.0.12：共用 skills `~/.gemini/skills`、MCP `~/.gemini/config/mcp_config.json`、安裝路徑 `~/.local/bin/agy`

## 範圍外（移交後續變更）

專案層級 npx skills 投影（`_NPX_PROJECT_AGENTS` 的 `gemini-cli`、`project_projection.py` 的 `.gemini`、`project-template` 的 `.gemini/`）耦合外部 `npx skills` 工具的 agent 命名，不在本提案 `cli-distribution` 範圍，已移交獨立變更 `clarify-npx-agy-projection` 處理。
