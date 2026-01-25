# Tasks: 整合 everything-claude-code + 架構調整

## Phase 1: 上游追蹤系統

### 1.1 建立追蹤目錄結構

- [x] 1.1.1 建立 `upstream/` 目錄
- [x] 1.1.2 建立 `upstream/sources.yaml`（所有第三方 repo）
- [x] 1.1.3 建立 `upstream/README.md`

### 1.2 各 repo 追蹤配置

- [x] 1.2.1 建立 `upstream/ecc/mapping.yaml`
- [x] 1.2.2 建立 `upstream/ecc/last-sync.yaml`
- [x] 1.2.3 建立 `upstream/uds/mapping.yaml`
- [x] 1.2.4 建立 `upstream/uds/last-sync.yaml`
- [x] 1.2.5 建立 `upstream/obsidian-skills/mapping.yaml`
- [x] 1.2.6 建立 `upstream/anthropic-skills/mapping.yaml`
- [x] 1.2.7 建立 `upstream/superpowers/mapping.yaml`

## Phase 2: CLI 指令重構

### 2.1 修改 ai-dev project init

- [x] 2.1.1 重新命名 `project/` → `project-template/`
- [x] 2.1.2 修改 `script/commands/project.py`：改為從 project-template 複製模板
- [x] 2.1.3 實作模板複製邏輯（從 project-template/ 複製到目標專案）

### 2.2 修改 ai-dev update

- [x] 2.2.1 修改 `script/commands/update.py`
  - 預設：只拉取 custom-skills + 複製到工具目錄
  - 移除預設拉取其他第三方 repo
- [x] 2.2.2 新增 `--sync-upstream` 選項，調用 upstream-sync skill

### 2.3 upstream-sync skill/command（已完成）

- [x] 2.3.1 建立 `skills/upstream-sync/SKILL.md`
- [x] 2.3.2 建立 `skills/upstream-sync/scripts/sync_upstream.py`
- [x] 2.3.3 建立 `skills/upstream-sync/references/sources-schema.md`
- [x] 2.3.4 建立 `commands/claude/upstream-sync.md`

### 2.4 修改 shared.py

- [x] 2.4.1 新增 ecc 到 REPOS 配置
- [ ] 2.4.2 調整 `copy_sources_to_custom_skills()` 邏輯（待 ecc clone 後實作）

## Phase 3: ecc 目錄結構

### 3.1 建立 sources/ecc 目錄

- [x] 3.1.1 建立 `sources/ecc/` 目錄
- [x] 3.1.2 建立子目錄結構：
  - `sources/ecc/agents/`
  - `sources/ecc/commands/`
  - `sources/ecc/skills/`
  - `sources/ecc/hooks/`
  - `sources/ecc/contexts/`
  - `sources/ecc/rules/`
  - `sources/ecc/scripts/lib/`
  - `sources/ecc/examples/`
  - `sources/ecc/mcp-configs/`
  - `sources/ecc/.claude-plugin/`
  - `sources/ecc/tests/`

## Phase 4-11: ecc 資源複製（待上游同步）

> **注意**：Phase 4-11 的具體複製任務需要先執行 `ai-dev install` 或 `ai-dev update` 來 clone ecc repo，然後透過 `/upstream-sync` skill 來執行實際的同步操作。
>
> 目前已建立目錄結構和 README 說明檔，實際檔案將在上游同步時填入。

### 待完成項目

- [ ] Phase 4: Agents 整合（6 個 agents）
- [ ] Phase 5: Commands 整合（10 個 commands）
- [ ] Phase 6: Skills 整合（7 個 skills）
- [ ] Phase 7: Hooks 系統（Python 實作）
- [ ] Phase 8: Contexts 整合（3 個 contexts）
- [ ] Phase 9: Rules 整合（5 個 rules）
- [ ] Phase 10: Scripts/Package Manager（Python 實作）
- [ ] Phase 11: 其他資源（examples, mcp-configs, plugin, tests）

## Phase 12: 文件與驗證

### 12.1 更新文件

- [x] 12.1.1 建立 `sources/ecc/README.md`
- [x] 12.1.2 更新 `docs/dev-guide/copy-architecture.md`
- [ ] 12.1.3 更新主 `README.md`（選擇性）
- [x] 12.1.4 更新 `CHANGELOG.md`

### 12.2 驗證

- [x] 12.2.1 驗證目錄結構完整
- [ ] 12.2.2 驗證所有檔案包含 upstream 標注（待同步）
- [ ] 12.2.3 驗證 Python hooks 跨平台執行（待實作）
- [ ] 12.2.4 驗證 package_manager.py 跨平台執行（待實作）
- [ ] 12.2.5 驗證 `ai-dev update` 預設行為
- [ ] 12.2.6 驗證 `ai-dev update --sync-upstream` 行為
- [x] 12.2.7 驗證 `ai-dev project init` 新行為
- [x] 12.2.8 驗證 upstream/mapping.yaml 完整

## 驗收標準

1. ✅ 所有 ecc 資源保持 Claude Code 原生格式（不轉換為 UDS 格式）
2. ✅ 所有資源放在 `sources/ecc/` 目錄下
3. ⏳ 所有資源包含 upstream 標注（待同步）
4. ⏳ Node.js hooks/scripts 重寫為 Python，可跨平台執行（待實作）
5. ✅ UDS 資源（`.standards/`, `skills/agents/`）保持不變
6. ✅ `ai-dev update` 預設只拉取 custom-skills
7. ✅ `ai-dev update --sync-upstream` 觸發上游同步 + 審核流程
8. ✅ `ai-dev project init` 使用 project-template 而非 UDS CLI
9. ✅ upstream/ 記錄所有第三方 repo 的同步狀態
10. ✅ CHANGELOG 記錄所有變更

## 完成摘要

| 階段 | 內容 | 狀態 |
|------|------|------|
| Phase 1 | 上游追蹤系統 | ✅ 完成 |
| Phase 2 | CLI 指令重構 | ✅ 完成（部分待 ecc clone） |
| Phase 3 | ecc 目錄結構 | ✅ 完成 |
| Phase 4-11 | ecc 資源複製 | ⏳ 待上游同步 |
| Phase 12 | 文件與驗證 | ✅ 基本完成 |

**下一步**：執行 `ai-dev install` 或 `ai-dev update` 來 clone ecc repo，然後使用 `/upstream-sync` skill 執行實際的資源同步。
