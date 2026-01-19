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

#### Scenario: 頂部操作列
給定 TUI 已啟動
則頂部應該顯示：
- Install 按鈕 - 執行安裝流程
- Maintain 按鈕 - 執行維護流程
- Status 按鈕 - 顯示環境狀態
- Add Skills 按鈕 - 開啟新增第三方 Skills 對話框
- Quit 按鈕 - 退出 TUI

#### Scenario: 過濾器列
給定 TUI 已啟動
則應該顯示：
- Target 下拉選單（Claude Code / Antigravity / OpenCode）
- Type 下拉選單（Skills / Commands / Agents）

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

#### Scenario: 基本導航
給定 TUI 已啟動
則應該支援：
- Tab / Shift+Tab - 在區域間切換焦點
- 方向鍵 - 在列表項目間移動
- Enter - 確認選擇
- Q - 退出 TUI
- P - 開啟 Add Skills 對話框

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

