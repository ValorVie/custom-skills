# tui-hooks-display Specification Delta

## MODIFIED Requirements

### Requirement: ECC Hooks Plugin Status Display (Hooks Plugin 狀態顯示)

TUI MUST (必須) 顯示 ECC Hooks Plugin 的安裝狀態，但不再提供安裝/移除功能。

**變更理由**：ECC Hooks 已改為使用者透過 `@plugins` 或 `npx skills add` 自行管理，ai-dev 不再負責 plugin 生命週期管理。

#### Scenario: 顯示已安裝狀態

給定 ECC Hooks Plugin 已安裝（`.claude/plugins/ecc-hooks/.claude-plugin` 存在）
當 TUI 已啟動時
則 Hooks 區塊應該顯示：
- 「✓ 已安裝」狀態標籤
- Plugin 安裝路徑（簡化顯示，如 `~/.claude/plugins/ecc-hooks`）
- 「View Config」按鈕（開啟 hooks.json）

#### Scenario: 顯示未安裝狀態與安裝提示

給定 ECC Hooks Plugin 未安裝
當 TUI 已啟動時
則 Hooks 區塊應該顯示：
- 「✗ 未安裝」狀態標籤
- 安裝提示：「安裝方式：npx skills add affaan-m/everything-claude-code」

#### Scenario: View Config 按鈕僅在已安裝時可用

給定 TUI 已啟動
當 ECC Hooks Plugin 狀態為「未安裝」時
則「View Config」按鈕應該被隱藏或禁用

給定 TUI 已啟動
當 ECC Hooks Plugin 狀態為「已安裝」時
則「View Config」按鈕應該可見且可點擊

## REMOVED Requirements

### Requirement: ECC Hooks Plugin Installation (Hooks Plugin 安裝功能)

~~TUI MUST (必須) 提供安裝與移除 ECC Hooks Plugin 的功能。~~

**移除理由**：使用者應透過 `npx skills add` 或 CLI 指令 `ai-dev hooks install` 手動管理 plugin，TUI 不再負責此功能。

#### Scenario: 透過 TUI 安裝 Hooks Plugin

~~給定使用者點擊「Install/Update」按鈕或按下 `i` 鍵~~
~~則應該執行 `ai-dev hooks install` 指令~~

**移除理由**：安裝功能改為由使用者透過外部指令執行。

#### Scenario: 透過 TUI 移除 Hooks Plugin

~~給定使用者點擊「Uninstall」按鈕或按下 `u` 鍵~~
~~則應該執行 `ai-dev hooks uninstall` 指令~~

**移除理由**：移除功能改為由使用者透過外部指令執行。

## ADDED Requirements

### Requirement: Hooks Installation Guidance (Hooks 安裝指引)

TUI MUST (必須) 在 Hooks Plugin 未安裝時顯示清楚的安裝指引。

#### Scenario: 顯示 npx skills add 指令

給定 ECC Hooks Plugin 未安裝
當 TUI 顯示 Hooks 區塊時
則應該顯示文字提示：
- 「安裝方式：npx skills add affaan-m/everything-claude-code」
- 提示樣式應為 dim/gray 色調（不干擾主要內容）

#### Scenario: 安裝提示在已安裝時隱藏

給定 ECC Hooks Plugin 已安裝
當 TUI 顯示 Hooks 區塊時
則安裝提示文字應該隱藏或顯示為空字串

## Impact

### 對現有功能的影響

1. **TUI 使用者介面**：
   - 移除 Install/Update 按鈕
   - 移除 Uninstall 按鈕
   - 移除快捷鍵 `i` (install_hooks)
   - 移除快捷鍵 `u` (uninstall_hooks)
   - 保留快捷鍵 `v` (view_hooks_config)

2. **CLI 指令**：
   - `ai-dev hooks install` 保持不變
   - `ai-dev hooks uninstall` 保持不變
   - `ai-dev hooks status` 保持不變

3. **共用函式**：
   - `get_ecc_hooks_status()` 不變（仍用於狀態偵測）
   - `install_ecc_hooks_plugin()` 不變（CLI 使用）
   - `uninstall_ecc_hooks_plugin()` 不變（CLI 使用）
   - `show_ecc_hooks_status()` 不變（CLI 使用）

### 向後相容性

- **破壞性變更**：TUI 不再提供圖形化安裝功能
- **緩解措施**：顯示清楚的安裝指引，引導使用者使用替代方法
- **影響範圍**：預期小，因為多數使用者應已透過其他方式安裝

### 相關 Capabilities

- 本變更與 `hook-system` spec 相關（定義 Hooks 的核心功能）
- 本變更僅影響 TUI 介面，不影響 Hooks 的實際運作機制
