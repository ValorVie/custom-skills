## Why

custom-skills 專案目前將 ECC (everything-claude-code) 的 skills、agents、commands 複製到 `sources/ecc/` 並手動同步到專案內，導致維護負擔高且版本落後。ECC 上游活躍開發（50K+ stars，每日更新），手動同步已無法跟上。應改為 `ai-dev clone` 時直接從 `~/.config/everything-claude-code/` 選擇性分發，移除專案內的 ECC 複製品。

## What Changes

- **新增** `upstream/distribution.yaml` — 定義 ECC 分發設定（來源路徑、目標平台、元件對應、排除清單）
- **新增** `copy_custom_skills_to_targets()` 中的 ECC 分發邏輯 — 從 `~/.config/everything-claude-code/` 讀取並按平台分發 skills/agents/commands
- **移除** `sources/ecc/` 整個目錄 — 不再需要本地複製品
- **移除** `upstream/ecc/` 目錄 — mapping.yaml 被 distribution.yaml 取代
- **移除** `plugins/ecc-hooks-old/` — 已棄用的舊版 hooks
- **移除** 6 個 ECC 來源的 skills — `continuous-learning`, `strategic-compact`, `eval-harness`, `security-review`, `tdd-workflow`, `coding-standards`
- **移除** 5 個 ECC 來源的 agents — `build-error-resolver`, `e2e-runner`, `doc-updater`, `security-reviewer`, `database-reviewer`（皆在 `agents/claude/`）
- **移除** 6 個 ECC 來源的 commands — `checkpoint`, `build-fix`, `e2e`, `learn`, `test-coverage`, `eval`（在 `skills/commands/`）
- **移除** `integrate_to_dev_project()` 中的 ECC 段落（`shared.py:1561-1598`）
- **修改** `upstream/sources.yaml` — ECC 的 `install_method` 從 `manual` 改為 `selective`

## Capabilities

### New Capabilities
- `ecc-selective-distribution`: 定義 ECC 選擇性分發機制 — distribution.yaml 設定檔格式、按平台分發邏輯、manifest hash 追蹤、排除清單支援

### Modified Capabilities
- `clone-command`: clone 流程新增 ECC 分發階段
- `upstream-skills`: 上游來源管理方式變更（ECC 從 manual 改為 selective）

## Impact

- **程式碼**: `script/utils/shared.py` — 新增分發函式、修改 `copy_custom_skills_to_targets()`、移除 `integrate_to_dev_project()` ECC 段落
- **設定檔**: `upstream/sources.yaml`、新增 `upstream/distribution.yaml`
- **移除檔案**: 共 20+ 個檔案/目錄
- **依賴**: 需要 `~/.config/everything-claude-code/` 已由 `ai-dev update` 拉取
- **分發目標**:

| 平台 | skills | commands | agents |
|------|:------:|:--------:|:------:|
| claude | ✅ `commands/` | ✅ `agents/` | ✅ |
| opencode | ✅ `.opencode/commands/` | ✅ `.opencode/prompts/agents/` | ✅ |
| gemini | ✅ | ❌ 格式不相容(.toml) | ✅ `agents/`(共用格式) |
| codex | ✅ | ❌ 不支援 | ❌ 不支援 |
