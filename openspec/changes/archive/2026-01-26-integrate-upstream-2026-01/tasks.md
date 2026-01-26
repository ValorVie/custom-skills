# Tasks: 2026-01 上游整合

## 1. 同步狀態確認（已完成）

- [x] 1.1 執行 `upstream-sync` 分析所有上游 repo
- [x] 1.2 執行 `upstream-compare` 生成分析報告
- [x] 1.3 更新 `last-sync.yaml` 標記同步狀態

## 2. upstream-compare Skill 更新（已完成）

- [x] 2.1 更新 `~/.claude/skills/custom-skills-upstream-compare/SKILL.md` 新增報告輸出規範
- [x] 2.2 同步更新 `skills/custom-skills-upstream-compare/SKILL.md`
- [x] 2.3 建立 `upstream/reports/analysis/` 目錄
- [x] 2.4 生成範例報告 `compare-2026-01-26.md`

## 3. 整合 ECC 獨特內容

- [x] 3.1 從 ECC 複製 `database-reviewer` agent 到 `agents/claude/`
- [x] 3.2 調整 agent 內容符合本專案規範（繁體中文）
- [x] 3.3 從 ECC 評估並整合 `cloud-infrastructure-security` skill
- [x] 3.4 決定其他 commands - 暫不整合，現有 commands 已足夠

## 4. 驗證與文件

- [x] 4.1 新增的 agent 與 skill 已建立
- [x] 4.2 更新 `upstream/README.md` 記錄整合決定
- [x] 4.3 執行 `openspec validate` 確認提案有效

## 5. 完成整合

- [ ] 5.1 提交變更
- [ ] 5.2 歸檔 OpenSpec 提案
