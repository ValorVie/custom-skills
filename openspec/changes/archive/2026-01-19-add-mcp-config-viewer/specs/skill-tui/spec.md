# skill-tui Specification Delta

## ADDED Requirements

### Requirement: MCP Config Section (MCP 設定區塊)
TUI MUST (必須) 顯示目前選擇的 AI 工具的 MCP 設定檔資訊。

#### Scenario: 顯示 MCP 設定檔路徑
給定使用者已選擇某個 Target（如 Claude Code）
則 TUI 應該：
1. 在資源列表下方顯示「MCP Config」區塊
2. 顯示該工具對應的 MCP 設定檔完整路徑
3. 標示檔案是否存在

#### Scenario: Target 切換時更新路徑
給定使用者切換 Target 下拉選單
當選擇不同的目標工具時
則 MCP Config 區塊應該更新為新工具的設定檔路徑：
- Claude Code: `~/.claude.json`
- Antigravity: `~/.gemini/antigravity/mcp_config.json`
- OpenCode: `~/.config/opencode/opencode.json`

### Requirement: Open in Editor (在編輯器中開啟)
TUI MUST (必須) 提供功能讓使用者在外部編輯器中開啟 MCP 設定檔。

#### Scenario: 點擊按鈕開啟編輯器
給定 MCP Config 區塊已顯示
當使用者點擊「Open in Editor」按鈕
則應該：
1. 使用外部編輯器開啟設定檔
2. 若檔案不存在，顯示警告訊息

#### Scenario: 使用快捷鍵開啟編輯器
給定 TUI 已啟動
當使用者按下 `e` 鍵
則應該在編輯器中開啟目前選擇的 Target 的 MCP 設定檔。

#### Scenario: 編輯器選擇邏輯
給定使用者請求開啟設定檔
則系統應該依照以下優先順序選擇編輯器：
1. 環境變數 `EDITOR` 指定的編輯器
2. VS Code (`code` 指令)
3. 系統預設開啟方式 (`open` on macOS, `xdg-open` on Linux)

### Requirement: Open in File Manager (在檔案管理器中開啟)
TUI MUST (必須) 提供功能讓使用者在檔案管理器中開啟 MCP 設定檔所在目錄。

#### Scenario: 點擊按鈕開啟檔案管理器
給定 MCP Config 區塊已顯示
當使用者點擊「Open Folder」按鈕
則應該：
1. 在檔案管理器中開啟設定檔所在目錄並選取該檔案
2. 若檔案不存在，開啟父目錄

#### Scenario: 使用快捷鍵開啟檔案管理器
給定 TUI 已啟動
當使用者按下 `f` 鍵
則應該在檔案管理器中開啟目前選擇的 Target 的 MCP 設定檔所在目錄。

#### Scenario: 跨平台檔案管理器支援
給定使用者請求開啟檔案管理器
則系統應該依照平台選擇對應的檔案管理器：
- macOS: Finder (`open -R`)
- Linux: Nautilus 或 `xdg-open`
- Windows: Explorer (`explorer /select,`)

## MODIFIED Requirements

### Requirement: TUI Keyboard Navigation (TUI 鍵盤導航)
TUI MUST (必須) 支援完整的鍵盤操作：

#### Scenario: 基本導航（新增 MCP 快捷鍵）
給定 TUI 已啟動
則應該支援：
- Tab / Shift+Tab - 在區域間切換焦點
- 方向鍵 - 在列表項目間移動
- Enter - 確認選擇
- Q - 退出 TUI
- P - 開啟 Add Skills 對話框
- **E - 開啟 MCP 設定檔於編輯器**
- **F - 開啟 MCP 設定檔所在目錄於檔案管理器**
