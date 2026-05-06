## 0. 準備與邊界確認

- [x] 0.1 確認上游參考快照 `mattpocock/skills@b843cb5` 仍可取得，並記錄來源連結
- [x] 0.2 確認本 change 不直接安裝整包上游技能
- [x] 0.3 確認 `superpowers` 與 `openspec` 的既有技能名稱不會被覆寫
- [x] 0.4 確認 `docs/report/2026050612-01-mattpocock-skills-workflow-positioning.md` 中的導入判斷仍適用

## 1. 上游追蹤

- [x] 1.1 在 `upstream/sources.yaml` 新增 `mattpocock-skills`，`install_method` 設為 `manual`
- [x] 1.2 建立 `upstream/mattpocock-skills/last-sync.yaml`，記錄目前採用的 commit
- [x] 1.3 建立 `upstream/mattpocock-skills/mapping.yaml`，以 `skills` 區塊記錄來源技能到本地 `mp-*` 技能的對照
- [x] 1.4 在 mapping 中記錄排除的上游技能與原因（例如 `tdd`、`diagnose`）
- [x] 1.5 在 mapping 中為每個採用技能記錄 `local_skill`、`priority`、`adaptation`
- [x] 1.6 文件化上游更新流程：audit、diff、人工合併、更新 last-sync

## 2. P0：工作入口層核心技能

- [x] 2.1 建立 `skills/mp-setup-matt-pocock-skills/SKILL.md`
- [x] 2.2 建立 `skills/mp-grill-with-docs/SKILL.md`
- [x] 2.3 建立 `skills/mp-to-issues/SKILL.md`
- [x] 2.4 確認三個 P0 skill 全文使用繁體中文，英文僅保留必要識別
- [x] 2.5 為三個 P0 skill 加入清楚的觸發條件，避免與 `openspec-*`、`superpowers:*` 誤觸

## 3. P0：共同工作規則文件

- [x] 3.1 建立 `docs/agents/issue-tracker.md`
- [x] 3.2 建立 `docs/agents/triage-states.md`
- [x] 3.3 建立 `docs/agents/domain.md`
- [x] 3.4 建立 `docs/agents/mp-workflow.md`
- [x] 3.5 文件中明確定義 MP 工作入口層、OpenSpec、Superpowers 的分工

## 4. P0：Claude / Codex 入口整合

- [x] 4.1 更新 `CLAUDE.md`，加入 MP 工作入口層讀取規則
- [x] 4.2 更新 `AGENTS.md`，加入 MP 工作入口層讀取規則
- [x] 4.3 確認兩個入口都指向 `docs/agents/`，不各自維護重複內容
- [x] 4.4 確認 `ai-dev clone` 後能分發 P0 skills 到 `.claude/skills/` 與 `.codex/skills/`

## 5. P1：任務分流與架構回看

- [x] 5.1 建立 `skills/mp-triage/SKILL.md`
- [x] 5.2 建立 `skills/mp-improve-codebase-architecture/SKILL.md`
- [x] 5.3 `mp-triage` 支援 `needs-triage`、`needs-info`、`ready-for-agent`、`ready-for-human`、`wontfix`
- [x] 5.4 `mp-triage` 支援 OpenSpec tasks、GitHub issue、本地 Markdown 三種出口
- [x] 5.5 `mp-improve-codebase-architecture` 僅輸出候選，不直接實作或重構

## 6. P2：需求摘要技能

- [x] 6.1 建立 `skills/mp-to-prd/SKILL.md`
- [x] 6.2 `mp-to-prd` 支援輸出 OpenSpec proposal 前置素材
- [x] 6.3 `mp-to-prd` 支援輸出 PRD 風格摘要，但不強制每個需求都建立 PRD
- [x] 6.4 確認 `mp-to-prd` 不重新訪談使用者，只整理既有脈絡

## 7. 投影與分發驗證

- [x] 7.1 執行或模擬 `ai-dev clone --target claude`，確認 `.claude/skills/mp-*` 存在
- [x] 7.2 執行或模擬 `ai-dev clone --target codex`，確認 `.codex/skills/mp-*` 存在
- [x] 7.3 檢查 `skills/mp-*`、`.claude/skills/mp-*`、`.codex/skills/mp-*` 的技能清單一致
- [x] 7.4 確認 `auto-skill` 任務啟動協議仍優先於 MP 技能

## 8. 驗證與文件

- [x] 8.1 執行 `openspec validate add-mp-workflow-entry-layer --strict`
- [x] 8.2 檢查所有新增 skill 的 frontmatter 與 `description` 觸發語
- [x] 8.3 新增或更新 `docs/dev-guide/workflow/` 中的 MP 工作入口層說明
- [x] 8.4 增加觸發案例檢查，確認 `mp-*` 不覆蓋 `superpowers` TDD / 除錯技能
- [x] 8.5 執行儲存庫既有測試或最接近的文件/技能檢查命令
