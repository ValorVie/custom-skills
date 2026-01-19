# Proposal: enhance-skill-management

## Summary

增強 Skill 管理功能，包含：
1. 安裝後顯示重複名稱警告
2. 新增 `list` 指令顯示已安裝的 skills/commands/agents
3. 設計各工具（Claude Code、OpenCode、Antigravity）的開關機制
4. 維護 `skills` npm 套件並提示可用指令
5. 新增 TUI 介面整合安裝與開關功能

## Motivation

目前使用者自建的 skill 若與專案內建 skill 同名會被覆蓋，但使用者無法事先得知有哪些名稱需要避開。此外，缺乏查看已安裝資源的方式，也無法針對特定工具啟用/停用特定資源。TUI 可以提供更友善的互動體驗。

## Scope

### In Scope
- `install` 指令完成後顯示已安裝 skill 名稱清單與警告
- 新增 `list` 子指令，列出 skills/commands/agents
- 新增開關機制，控制各工具的資源啟用狀態
- 維護 `skills` npm 套件（安裝/更新），並在 `status` 或安裝後提示可用指令
- 新增 TUI 介面，整合安裝、維護、開關等功能

### Out of Scope
- 深度整合 `skills` npm 套件的 add/update 功能（由使用者自行操作 `npx skills`）
- 自動衝突偵測與重新命名

## Related Specs
- `setup-script`：現有安裝與維護邏輯

## Dependencies
- `skills` npm 套件 (v1.0.6)
- `textual` 或類似的 Python TUI 框架
- 現有 `utils/shared.py` 中的路徑與複製邏輯

## Risks
- TUI 框架選擇可能影響跨平台相容性
- 開關機制需要新的配置檔案格式設計
