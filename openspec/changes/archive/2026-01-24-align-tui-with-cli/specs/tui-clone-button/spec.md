# tui-clone-button Specification

## Purpose

在 TUI 中新增 Clone 按鈕，讓使用者可以直接分發 Skills 到各工具目錄。

## ADDED Requirements

### Requirement: Clone Button in TUI (TUI 中的 Clone 按鈕)

TUI MUST (必須) 在頂部操作列提供 Clone 按鈕。

#### Scenario: 頂部操作列新增 Clone 按鈕

給定 TUI 已啟動
當顯示頂部操作列時
則應該顯示：
- Install 按鈕
- Update 按鈕
- **Clone 按鈕（新增）**
- Status 按鈕
- Add Skills 按鈕
- Quit 按鈕

#### Scenario: Clone 按鈕功能

給定使用者點擊 Clone 按鈕
則應該：
1. 執行 `ai-dev clone` 指令
2. 根據 Sync to Project checkbox 狀態傳入對應參數
3. 在終端機顯示執行進度
4. 完成後刷新資源列表

### Requirement: Clone Keyboard Shortcut (Clone 快捷鍵)

TUI MUST (必須) 提供快捷鍵執行 Clone 功能。

#### Scenario: 使用快捷鍵執行 Clone

給定 TUI 已啟動
當使用者按下 `c` 鍵
則應該執行與點擊 Clone 按鈕相同的功能。

## Related Specifications

- `skill-tui` - 主 TUI 規格
- `clone-command` - Clone 指令規格
