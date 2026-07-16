## 1. 對齊工作流文件

- [x] 1.1 更新 `docs/agents/issue-tracker.md`，定義 Beads、OpenSpec 與 GitHub 的 canonical 權責
- [x] 1.2 更新 `docs/agents/triage-states.md`，加入 Beads label／status 映射與唯一 triage label 規則
- [x] 1.3 更新 `docs/dev-guide/workflow/DEVELOPMENT-WORKFLOW.md`，將三軌執行追蹤與輕量軌出口改為 Beads

## 2. 更新 MP 工作入口技能

- [x] 2.1 更新 `skills/mp-to-issues/SKILL.md`，加入 Beads issue graph 輸出與輸出選擇優先序
- [x] 2.2 更新 `skills/mp-wayfinder/SKILL.md`，以 tracker 無關模型及 Beads epic／child／blocking 表示地圖
- [x] 2.3 更新 `skills/mp-triage/SKILL.md`，輸出 Beads triage label／status 映射並保留寫入授權限制

## 3. 刷新 AI 工具整合

- [x] 3.1 執行 `bd setup claude`，只更新受管理的 Beads 區段
- [x] 3.2 確認 `CLAUDE.md`、`AGENTS.md` 與 SessionStart hook 的 Beads 規則一致

## 4. 驗證與收尾

- [x] 4.1 執行 OpenSpec strict validation，確認 proposal、design、delta specs 與 tasks 有效
- [x] 4.2 執行 Markdown lint 與一致性搜尋，確認文件及技能沒有殘留 GitHub-only canonical 規則
- [x] 4.3 執行 `bd where`、`bd info`、`bd lint`、`bd dep cycles` 與 Claude／Codex setup check
- [x] 4.4 更新並關閉 `custom-skills-3i6`，保留 `custom-skills-szw` 作為既有 active OpenSpec 遷移工作
