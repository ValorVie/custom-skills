## ADDED Requirements

### Requirement: Ink TUI 入口
系統 SHALL 提供 `ai-dev tui` 指令啟動 Ink TUI，使用 React 元件模型。

#### Scenario: 啟動 TUI
- **WHEN** 使用者執行 `ai-dev tui`
- **THEN** 啟動全螢幕 Ink 應用程式，顯示主畫面

#### Scenario: 退出 TUI
- **WHEN** 使用者按下 `q`
- **THEN** TUI 結束，回到終端

### Requirement: 視圖切換路由
App 根元件 SHALL 使用 `useState<Screen>` 管理當前畫面，支援 main、preview、confirm、settings 四種視圖。

#### Scenario: 從主畫面切換到預覽
- **WHEN** 使用者在主畫面按下 `p`
- **THEN** 切換到 PreviewScreen，顯示選中資源的內容

#### Scenario: 從子畫面返回
- **WHEN** 使用者在 PreviewScreen 按下 ESC 或 backspace
- **THEN** 返回 MainScreen

### Requirement: MainScreen 元件結構
MainScreen SHALL 包含 Header、TabBar、FilterBar、ResourceList、ActionBar 子元件。

#### Scenario: 顯示資源列表
- **WHEN** MainScreen 載入
- **THEN** 顯示當前目標 (claude) 的所有已安裝資源

#### Scenario: 切換目標
- **WHEN** 使用者按下 `t`
- **THEN** TabBar 切換到下一個目標 (claude → opencode → codex → gemini)

### Requirement: 鍵盤快捷鍵
TUI SHALL 使用 Ink `useInput` hook 支援以下快捷鍵：q(退出)、space(切換選取)、a(全選)、n(新增)、s(儲存)、p(預覽)、e(編輯器)、f(檔案管理器)、c(設定)、t(切換目標)。

#### Scenario: 空白鍵切換資源
- **WHEN** 使用者將游標移到某資源並按空白鍵
- **THEN** 該資源的啟用狀態切換

#### Scenario: 全選
- **WHEN** 使用者按下 `a`
- **THEN** 所有可見資源的啟用狀態切換

### Requirement: 狀態管理使用 useReducer
TUI SHALL 使用 React `useReducer` + Context 管理全域狀態，包含 target、typeFilter、sourceFilter、resources、selectedIndex。

#### Scenario: 篩選器影響列表
- **WHEN** 使用者變更 typeFilter
- **THEN** ResourceList 僅顯示符合篩選條件的資源
