# Change: 2026-01 上游整合

## Why

根據 `upstream/reports/analysis/compare-2026-01-26.md` 分析報告，5 個上游 repo 共有 647 個新 commits。
本提案旨在完成以下整合工作：

1. 確認同步狀態已更新（已完成）
2. 整合 everything-claude-code (ECC) 的獨特內容
3. 記錄新框架採用決定

## What Changes

### 1. 整合 ECC 獨特內容

- **新增 Agent**：`database-reviewer`（Supabase patterns）
- **新增 Skill**：`cloud-infrastructure-security`
- **評估 Commands**：`orchestrate`, `setup-pm`, `verify` 等

### 2. 新框架採用決定

| 框架 | 決定 | 理由 |
|------|------|------|
| Claude Plugin System | ✅ 維持 | 已有支援 |
| OpenCode Support | ⏸️ 暫緩 | 需求不明確 |
| Codex Support | ⏸️ 暫緩 | 需求不明確 |
| Hook System | 📖 參考 | 現有機制足夠 |
| MCP Integration | 📖 參考 | 按需整合 |

### 3. 更新 upstream-compare Skill

- **MODIFIED**：新增報告檔案輸出規範（已在本次對話完成）

## Impact

- Affected specs: `upstream-skills`
- Affected directories:
  - `agents/claude/` - 新增 database-reviewer
  - `skills/` - 新增 cloud-infrastructure-security
  - `upstream/last-sync.yaml` - 已更新
  - `skills/custom-skills-upstream-compare/SKILL.md` - 已更新

## 來源報告

- 分析報告：`upstream/reports/analysis/compare-2026-01-26.md`
- 結構化資料：`upstream/reports/structured/analysis-2026-01-26.yaml`
