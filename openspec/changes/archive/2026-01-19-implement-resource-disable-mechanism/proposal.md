# Proposal: implement-resource-disable-mechanism

## Summary

實作資源停用機制，當使用者透過 toggle 指令停用 skill、command 或 agent 時，實際將對應檔案從目標工具目錄移動到 `~/.config/custom-skills/disabled/` 目錄，並提醒使用者重啟對應的 AI 工具。

## Problem Statement

目前的 toggle 機制只在 `toggle-config.yaml` 中記錄 disabled 列表，但：

1. **檔案仍存在**：Claude Code 等工具仍會載入已標記為 disabled 的檔案
2. **需要重新同步**：必須執行 `copy_skills()` 才能生效，但即使如此也只是「下次複製時跳過」
3. **無法立即生效**：使用者必須手動重啟工具才能看到變化，但沒有提示

## Proposed Solution

### 核心機制

1. **停用資源時**：
   - 將檔案從目標工具目錄移動到 `~/.config/custom-skills/disabled/<target>/<type>/`
   - 保留原始目錄結構，方便重新啟用時還原
   - 顯示提醒訊息，告知使用者需重啟對應工具

2. **啟用資源時**：
   - 從 disabled 目錄移回目標工具目錄
   - 若 disabled 目錄中不存在，則從來源重新複製
   - 同樣提醒使用者重啟

3. **目錄結構**：
   ```
   ~/.config/custom-skills/
   ├── disabled/
   │   ├── claude/
   │   │   ├── skills/
   │   │   │   └── skill-creator/     # 被停用的 skill
   │   │   └── commands/
   │   │       └── git-commit.md      # 被停用的 command
   │   ├── antigravity/
   │   │   ├── skills/
   │   │   └── workflows/
   │   └── opencode/
   │       └── agents/
   └── toggle-config.yaml              # 保留作為狀態記錄
   ```

## Capabilities

### C1: Resource Disable Mechanism
實作檔案移動式的資源停用機制。

### C2: Restart Reminder
停用/啟用後顯示重啟提醒訊息。

## Success Criteria

1. 停用 skill 後，檔案確實從 `~/.claude/skills/` 移除
2. 啟用 skill 後，檔案確實還原到 `~/.claude/skills/`
3. 停用/啟用後顯示明確的重啟提醒
4. TUI 介面同步更新，支援新機制
5. 使用者自建的資源不會因停用而遺失

## Out of Scope

- 自動重啟 AI 工具（需使用者手動操作）
- 跨機器同步 disabled 狀態
- 批次停用/啟用多個資源

## Risks & Mitigations

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| 移動過程中斷導致檔案遺失 | 高 | 先複製再刪除，確保完整性 |
| 使用者自建資源被誤刪 | 高 | 移動而非刪除，保留在 disabled 目錄 |
| 權限問題導致移動失敗 | 中 | 捕獲例外並顯示明確錯誤訊息 |
