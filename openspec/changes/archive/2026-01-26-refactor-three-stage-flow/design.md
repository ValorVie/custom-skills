# Design: 三階段分發流程重構

## Context

目前的三階段複製流程：
1. **Stage 1 (Clone/Pull)**：由 `install`/`update` 執行，拉取外部 repos 到 `~/.config/`
2. **Stage 2 (整合)**：由 `clone` 執行，將外部來源整合到 `~/.config/custom-skills`
3. **Stage 3 (分發)**：由 `clone` 執行，分發到各工具目錄

問題：Stage 2 會覆蓋 `~/.config/custom-skills` 的 git 控制內容。

### 使用者角色

| 角色 | 執行位置 | 目標 |
|------|----------|------|
| 一般使用者 | 任意目錄 | 工具穩定運作 |
| 開發者 | `$dev/custom-skills`（開發目錄） | 追蹤上游更新、測試變更 |

### 判斷開發者的條件

現有 `_is_custom_skills_project()` 檢測邏輯：
- 檢查 `pyproject.toml` 中是否有 `name = "ai-dev"`
- 這是充分且必要的條件，因為只有本專案會使用這個名稱

額外的防護：
- `project_root.resolve() != get_custom_skills_dir().resolve()`
- 確保開發目錄不是 `~/.config/custom-skills` 本身

## Goals / Non-Goals

### Goals
- 移除對 `~/.config/custom-skills` 的自動整合（Stage 2）
- 保留開發者在開發目錄整合外部來源的能力
- 確保工具目錄的穩定性（只從 git 控制的 `~/.config/custom-skills` 分發）

### Non-Goals
- 不改變 `install`/`update` 的行為（Stage 1 維持不變）
- 不改變分發目標（Stage 3 的目標目錄不變）
- 不新增額外的命令

## Decisions

### Decision 1: 移除預設的 Stage 2

**選擇**：`copy_skills()` 不再呼叫 `copy_sources_to_custom_skills()`

**原因**：
- `~/.config/custom-skills` 應由 git 版本控制
- 外部來源整合應是開發者的選擇，不是預設行為

### Decision 2: 保留 `--sync-project` 選項用於開發者整合

**選擇**：當同時滿足以下條件時執行整合：
1. `--sync-project` 為 True
2. 當前目錄是 custom-skills 專案（`_is_custom_skills_project()` 回傳 True）
3. 當前目錄不是 `~/.config/custom-skills`

**原因**：
- 開發者需要追蹤上游更新
- 整合方向是從 `~/.config/<repos>` 到開發目錄
- 分發方向仍是從 `~/.config/custom-skills` 到工具目錄

### Decision 3: 整合來源

整合到開發目錄時，來源與現有 Stage 2 相同：
- `~/.config/universal-dev-standards/skills/claude-code/` → skills, agents, workflows, commands
- `~/.config/obsidian-skills/skills/` → skills
- `~/.config/anthropic-skills/skills/skill-creator/` → skills
- `sources/ecc/` → skills, agents, commands（專案內的 ECC 資源）

## Risks / Trade-offs

### Risk 1: 開發者忘記使用 `--sync-project`
- **影響**：開發目錄不會收到上游更新
- **緩解**：輸出提示訊息提醒開發者

### Risk 2: 判斷開發者的邏輯誤判
- **影響**：非開發者被誤認為開發者，或反之
- **緩解**：現有 `_is_custom_skills_project()` 已經足夠嚴謹（檢查 `pyproject.toml` 中的 `name = "ai-dev"`）

## Migration Plan

1. 修改 `copy_skills()` 移除自動 Stage 2
2. 新增開發者整合邏輯到 `clone` 指令
3. 更新文件說明新流程

### 向後相容
- 使用者不受影響（分發仍正常運作）
- 開發者需使用 `--sync-project` 來整合外部來源

## Open Questions

無
