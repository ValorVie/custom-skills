# tui-standards-profile Specification

## Purpose

在 TUI 中新增 Standards Profile 管理區塊，讓使用者可以查看和切換標準體系配置。

## ADDED Requirements

### Requirement: Standards Profile Section (Standards Profile 區塊)

TUI MUST (必須) 顯示 Standards Profile 區塊。

#### Scenario: 顯示 Standards Profile 區塊

給定 TUI 已啟動
當 `.standards/profiles/` 目錄存在時
則應該在 MCP Config 區塊上方顯示：
- 標題「Standards Profile」
- 目前啟用的 profile 名稱
- 可用 profiles 下拉選單

#### Scenario: 專案未初始化標準時

給定 TUI 已啟動
當 `.standards/profiles/` 目錄不存在時
則 Standards Profile 區塊應該顯示：
- 「未初始化」狀態提示
- 「執行 `ai-dev project init`」建議

### Requirement: Profile Switching (Profile 切換)

TUI MUST (必須) 允許使用者切換 Standards Profile。

#### Scenario: 透過下拉選單切換 Profile

給定 Standards Profile 區塊已顯示
當使用者在下拉選單選擇不同的 profile
則應該：
1. 執行 `ai-dev standards switch <profile>` 邏輯
2. 更新 `.standards/active-profile.yaml`
3. 顯示切換成功通知

#### Scenario: 使用快捷鍵循環切換 Profile

給定 TUI 已啟動
當使用者按下 `t` 鍵
則應該循環切換到下一個可用的 profile。

### Requirement: Profile Display (Profile 顯示)

TUI MUST (必須) 顯示目前 profile 的基本資訊。

#### Scenario: 顯示 Profile 資訊

給定使用者選擇了某個 profile
則應該顯示：
- Profile 名稱
- Profile 描述（如有）
- 啟用的標準數量

## Related Specifications

- `skill-tui` - 主 TUI 規格
