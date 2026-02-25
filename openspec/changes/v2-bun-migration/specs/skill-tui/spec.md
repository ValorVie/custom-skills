## MODIFIED Requirements

### Requirement: TUI 框架
TUI SHALL 使用 Ink (React for CLI) 取代 Python Textual，保持相同的功能集。

#### Scenario: 啟動 TUI
- **WHEN** 使用者執行 `ai-dev tui`
- **THEN** 啟動 Ink 應用程式，顯示資源管理介面

#### Scenario: 資源列表顯示
- **WHEN** TUI 載入完成
- **THEN** 顯示 Header、TabBar、FilterBar、ResourceList、ActionBar

### Requirement: Modal 改為視圖切換
TUI SHALL 使用視圖切換（`useState<Screen>`）取代 Textual 的 ModalScreen 疊加。

#### Scenario: 預覽資源
- **WHEN** 使用者在主畫面按 `p`
- **THEN** 整個畫面切換到 PreviewScreen（非疊加 Modal）

#### Scenario: 返回主畫面
- **WHEN** 使用者在子畫面按 ESC
- **THEN** 整個畫面切換回 MainScreen

### Requirement: 鍵盤快捷鍵保持相容
TUI SHALL 保持 v1 的所有鍵盤快捷鍵：q、space、a、n、s、p、e、f、c、t。

#### Scenario: 快捷鍵行為一致
- **WHEN** 使用者按下 `s`
- **THEN** 儲存當前資源啟用狀態（與 v1 行為相同）

## REMOVED Requirements

### Requirement: Textual TCSS 樣式系統
**Reason**: Ink 不支援 TCSS，改用 Ink 的 JSX style props
**Migration**: 移除 `*.tcss` 檔案，樣式改為 Ink Box/Text 的 inline props
