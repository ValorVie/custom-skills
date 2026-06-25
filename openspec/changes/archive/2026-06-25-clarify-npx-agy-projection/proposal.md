## Why

承接 `migrate-gemini-cli-to-agy`（已封存）。該變更把使用者層級分發 target `gemini` 改名為 `agy`，但刻意未動「專案層級 npx skills 投影層」：`script/services/tools/update.py` 的 `_NPX_PROJECT_AGENTS` 仍含外部 `npx skills` 工具的 `gemini-cli` agent，`project_projection.py` 與 `project-template` 仍管理 `.gemini/`。本變更釐清這一層的正確處置，避免日後誤把它一起改名而破壞 npx 整合。

## What Changes

- 確認並記錄調查結論（依 `npx skills` v1.5.1 官方 README 與實測）：
  - `npx skills` **沒有** `agy`／`antigravity-cli` agent。
  - `gemini-cli` agent 的路徑為 project `.agents/skills/`、global `~/.gemini/skills/`，**正是 agy 實際讀取的 skills 目錄**。
  - 故 `_NPX_PROJECT_AGENTS` 保留 `gemini-cli` 即可正確餵給 agy；**不可改名為 `agy`**（npx skills 不認得，會使 `npx skills add -a` 失敗）。
- 在 `script/services/tools/update.py` 的 `_NPX_PROJECT_AGENTS` 加上澄清註解：說明 `gemini-cli` 是外部 npx agent，其路徑對應 agy 的共用 skills 目錄，待 npx skills 推出 `agy` agent 前不得改名。
- 不變更行為、不改 `.gemini` 投影與 `project-template`（見 Non-Goals 與後續）。

## Capabilities

### New Capabilities
<!-- 無 -->

### Modified Capabilities
- `cli-distribution`: 新增不變量需求，明訂專案層級 npx skills 以 `gemini-cli` agent 餵給 agy（路徑對應 `~/.gemini/skills` / `.agents/skills`），在 npx skills 提供 `agy` agent 前不得改名。

## Impact

- 程式碼：`script/services/tools/update.py`（僅新增註解）。
- 不改：`_NPX_PROJECT_AGENTS` 內容、`project_projection.py` 的 `.gemini`、`project-template.manifest.yaml` 的 `.gemini/`、任何測試行為。
- 後續（不在本變更）：`.gemini/commands/opsx/*.toml`（為已退役 Gemini CLI 投影的 OpenSpec slash 指令）是否改用 agy 的 skill 機制，屬專案模板內容遷移，另案處理。
