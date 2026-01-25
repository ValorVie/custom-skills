# skill-tui Specification

## Purpose
TBD - created by archiving change enhance-skill-management. Update Purpose after archive.
## Requirements
### Requirement: TUI Command (TUI 指令)
腳本 MUST (必須) 實作 `tui` 指令以啟動互動式介面。

#### Scenario: 啟動 TUI
給定使用者執行 `uv run script/main.py tui`
當指令執行時
則應該：
1. 載入 toggle 配置
2. 掃描各目標目錄的資源
3. 顯示互動式終端機介面

### Requirement: TUI Layout (TUI 佈局)

TUI MUST (必須) 包含以下區域：

> **變更說明**：Target 下拉選單新增 Codex 和 Gemini CLI 選項。

#### Scenario: 頂部操作列
給定 TUI 已啟動
則頂部應該顯示：
- Install 按鈕 - 執行安裝流程
- Update 按鈕 - 執行更新流程
- Clone 按鈕 - 分發 Skills 到各工具目錄
- Status 按鈕 - 顯示環境狀態
- Add Skills 按鈕 - 開啟新增第三方 Skills 對話框
- Quit 按鈕 - 退出 TUI

#### Scenario: 過濾器列
給定 TUI 已啟動
當顯示過濾器列時
則應該包含：
- Target 下拉選單：Claude Code / Antigravity / OpenCode / Codex / Gemini CLI
- Type 下拉選單：Skills / Commands / Agents / Workflows（依據 Target 動態變更）

#### Scenario: 資源列表
給定使用者選擇了 Target 與 Type
則應該顯示該組合下的所有資源：
- Checkbox 顯示啟用/停用狀態
- 資源名稱
- 資源來源（uds/obsidian/anthropic/custom/user）

#### Scenario: 底部快捷鍵列
給定 TUI 已啟動
則底部應該顯示可用的快捷鍵提示。

### Requirement: TUI Interactions (TUI 互動)
TUI MUST (必須) 支援以下互動操作：

#### Scenario: 切換單一資源
給定使用者在資源列表中選中某項目
當按下 Space 鍵或點擊 Checkbox 時
則該資源的啟用狀態應該切換。

#### Scenario: 全選資源
給定使用者按下 A 鍵
則當前列表中的所有資源應該被勾選為啟用。

#### Scenario: 全取消資源
給定使用者按下 N 鍵
則當前列表中的所有資源應該被取消勾選（停用）。

#### Scenario: 儲存變更
給定使用者按下 S 鍵或點擊 Save 按鈕
則應該：
1. 將變更寫入 toggle-config.yaml
2. 執行 copy_skills() 重新同步
3. 顯示儲存成功訊息

#### Scenario: 執行 Install
給定使用者點擊 Install 按鈕
則應該：
1. 在 TUI 中顯示安裝進度
2. 執行安裝流程
3. 完成後刷新資源列表

#### Scenario: 執行 Maintain
給定使用者點擊 Maintain 按鈕
則應該：
1. 在 TUI 中顯示維護進度
2. 執行維護流程
3. 完成後刷新資源列表

#### Scenario: 執行 Status
給定使用者點擊 Status 按鈕
則應該在 TUI 中顯示環境狀態資訊。

### Requirement: Add Skills Modal (新增 Skills 對話框)
TUI MUST (必須) 提供對話框讓使用者直接執行 `npx skills add`。

#### Scenario: 開啟 Add Skills 對話框
給定使用者點擊 Add Skills 按鈕或按下 P 鍵
則應該開啟模態對話框，包含：
- 套件名稱輸入框（placeholder: `vercel-labs/agent-skills`）
- 範例套件清單提示
- Install 按鈕
- 輸出日誌區域

#### Scenario: 執行 npx skills add
給定使用者在對話框輸入套件名稱並點擊 Install
則應該：
1. 在輸出區域顯示執行的指令（`$ npx skills add <package>`）
2. 即時串流顯示 `npx skills add` 的輸出
3. 完成後顯示成功或失敗訊息
4. 成功時自動刷新主畫面的資源列表

#### Scenario: 取消 Add Skills 對話框
給定 Add Skills 對話框已開啟
當使用者按下 Escape 或點擊關閉按鈕
則應該關閉對話框並返回主畫面。

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
- **C - 執行 Clone 功能**
- **T - 循環切換 Standards Profile**

### Requirement: TUI Cross-Platform (TUI 跨平台)
TUI MUST (必須) 在支援的作業系統上正常運作。

#### Scenario: macOS/Linux 支援
給定使用者在 macOS 或 Linux 環境
當執行 `tui` 指令時
則 TUI 應該正常顯示並運作。

#### Scenario: Windows 支援
給定使用者在 Windows 環境
當執行 `tui` 指令時
則 TUI 應該正常顯示並運作。

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

### Requirement: Codex Target in TUI (TUI 中的 Codex 目標)

TUI MUST (必須) 支援 Codex 作為目標工具。

#### Scenario: 選擇 Codex 目標

給定使用者在 Target 下拉選單選擇 "Codex"
當選擇完成時
則 Type 下拉選單應該只顯示 "Skills" 選項
且資源列表應該顯示 `~/.codex/skills` 目錄下的 skills

### Requirement: Gemini CLI Target in TUI (TUI 中的 Gemini CLI 目標)

TUI MUST (必須) 支援 Gemini CLI 作為目標工具。

#### Scenario: 選擇 Gemini CLI 目標

給定使用者在 Target 下拉選單選擇 "Gemini CLI"
當選擇完成時
則 Type 下拉選單應該顯示 "Skills" 和 "Commands" 選項
且資源列表應該根據選擇的類型顯示對應目錄的資源

### Requirement: MCP Config for New Targets (新目標的 MCP 設定)

TUI MUST (必須) 在 MCP Config 區塊顯示新目標的設定檔路徑。

#### Scenario: Codex MCP 設定檔路徑

給定使用者選擇 Codex 目標
當顯示 MCP Config 區塊時
則應該顯示 Codex 的設定檔路徑（如 `~/.codex/config.json`）

#### Scenario: Gemini CLI MCP 設定檔路徑

給定使用者選擇 Gemini CLI 目標
當顯示 MCP Config 區塊時
則應該顯示 Gemini CLI 的設定檔路徑（如 `~/.gemini/settings.json`）

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

