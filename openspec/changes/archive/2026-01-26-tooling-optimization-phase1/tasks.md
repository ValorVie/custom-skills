## 1. 命令整合

- [x] 1.1 讀取 `commands/claude/test-coverage.md` 內容，提取測試生成相關邏輯
- [x] 1.2 修改 `commands/claude/coverage.md`，整合 `--generate` 參數支援
- [x] 1.3 更新 `coverage.md` 的 description，說明兩種模式
- [x] 1.4 刪除 `commands/claude/test-coverage.md`
- [x] 1.5 更新 CHANGELOG，記錄 breaking change 與遷移指引
- [x] 1.6 更新引用 test-coverage 的文件（README, 指南等）

## 2. ~~Git 提交群組標註~~ ❌ 已取消

> **取消原因**：經評估，Claude Code 基於 description 語意選擇 Skill，不讀取 related 欄位。效益有限。

- [ ] ~~2.1 修改 `skills/commit-standards/SKILL.md`，新增 related 欄位~~
- [ ] ~~2.2 修改 `skills/git-commit-custom/SKILL.md`，新增 related 欄位~~
- [ ] ~~2.3 修改 `skills/git-workflow-guide/SKILL.md`，新增 related 欄位~~

## 3. ~~代碼審查群組標註~~ ❌ 已取消

- [ ] ~~3.1 修改 `skills/code-review-assistant/SKILL.md`，新增 related 欄位~~
- [ ] ~~3.2 修改 `skills/checkin-assistant/SKILL.md`，新增 related 欄位~~

## 4. ~~測試群組標註~~ ❌ 已取消

- [ ] ~~4.1 修改 `skills/testing-guide/SKILL.md`，新增 related 欄位~~
- [ ] ~~4.2 修改 `skills/tdd-workflow/SKILL.md`，新增 related 欄位~~
- [ ] ~~4.3 修改 `skills/test-coverage-assistant/SKILL.md`，新增 related 欄位~~

## 5. 驗證與文件

- [x] 5.1 驗證 `/coverage` 命令配置正確
- [x] 5.2 更新分析報告，反映已完成的優化與取消的項目
- [x] 5.3 更新 `tool-overlap-analyzer` SKILL，新增 Cross-Reference Analysis 步驟
