# Tasks: enhance-skill-management

## Phase 1: 基礎設施準備

### 1.1 新增 `list_installed_resources()` 工具函式
- [ ] 在 `utils/shared.py` 新增函式
- [ ] 實作掃描各目標目錄的邏輯
- [ ] 實作來源比對邏輯（UDS/Obsidian/Anthropic/Custom/User）
- **驗證**：單元測試確認能正確識別來源

### 1.2 新增 Toggle 配置檔處理
- [ ] 在 `utils/shared.py` 新增 `load_toggle_config()` 函式
- [ ] 在 `utils/shared.py` 新增 `save_toggle_config()` 函式
- [ ] 定義配置檔預設結構
- **驗證**：測試配置檔讀寫與預設值邏輯

---

## Phase 2: List 指令實作

### 2.1 建立 `list.py` 指令檔案
- [ ] 建立 `script/commands/list.py`
- [ ] 實作 `--type` 參數（skills/commands/agents）
- [ ] 實作 `--target` 參數（claude/antigravity/opencode）
- [ ] 使用 Rich Table 格式化輸出
- **驗證**：手動執行確認輸出格式正確

### 2.2 註冊指令到 CLI
- [ ] 在 `script/main.py` 引入並註冊 `list` 指令
- **驗證**：執行 `uv run script/main.py --help` 確認指令出現

---

## Phase 3: Install 後警告與 NPM 提示

### 3.1 將 `skills` 加入 NPM 套件清單
- [ ] 在 `utils/shared.py` 的 `NPM_PACKAGES` 加入 `skills`
- **驗證**：執行 `install` 確認 skills 套件被安裝

### 3.2 修改 `install.py` 顯示警告與提示
- [ ] 在安裝完成後呼叫 `list_installed_resources()`
- [ ] 顯示已安裝 skill 名稱清單
- [ ] 顯示重複名稱警告訊息
- [ ] 顯示 `npx skills` 可用指令提示
- **驗證**：執行 `install --skip-npm --skip-repos` 確認顯示

### 3.3 修改 `status.py` 顯示 skills 提示
- [ ] 新增 skills 套件狀態檢查
- [ ] 顯示 `npx skills` 可用指令提示
- **驗證**：執行 `status` 確認提示顯示

---

## Phase 4: Toggle 開關機制

### 4.1 修改 `copy_skills()` 支援開關
- [ ] 讀取 toggle 配置
- [ ] 在複製時排除 disabled 列表中的項目
- [ ] 支援整體啟用/停用（`enabled: false`）
- **驗證**：手動測試停用特定 skill 後確認未被複製

### 4.2 建立 `toggle.py` 指令檔案
- [ ] 建立 `script/commands/toggle.py`
- [ ] 實作 `--target`、`--type`、`--name` 參數
- [ ] 實作 `--enable`/`--disable` 邏輯
- [ ] 實作 `--list` 顯示目前狀態
- [ ] 操作後自動執行 `copy_skills()`
- **驗證**：測試啟用/停用/列表功能

### 4.3 註冊指令到 CLI
- [ ] 在 `script/main.py` 引入並註冊 `toggle` 指令
- **驗證**：執行 `uv run script/main.py toggle --help` 確認

---

## Phase 5: TUI 介面

### 5.1 新增 Textual 依賴
- [ ] 在 `pyproject.toml` 加入 `textual` 依賴
- [ ] 執行 `uv sync` 安裝依賴
- **驗證**：確認 `import textual` 不報錯

### 5.2 建立 TUI 目錄結構
- [ ] 建立 `script/tui/` 目錄
- [ ] 建立 `script/tui/__init__.py`
- [ ] 建立 `script/tui/app.py` - 主應用程式
- [ ] 建立 `script/tui/styles.tcss` - 樣式檔
- **驗證**：目錄結構正確

### 5.3 實作 TUI 主框架
- [ ] 實作 `SkillManagerApp` 主類別
- [ ] 實作 Header 與 Footer
- [ ] 實作基本 BINDINGS（q/space/a/n/s/p）
- **驗證**：TUI 可啟動並顯示基本框架

### 5.4 實作頂部操作列
- [ ] 實作 Install 按鈕
- [ ] 實作 Maintain 按鈕
- [ ] 實作 Status 按鈕
- [ ] 實作 Add Skills 按鈕
- [ ] 實作 Quit 按鈕
- **驗證**：按鈕可點擊並觸發對應動作

### 5.5 實作過濾器列
- [ ] 實作 Target 下拉選單（Claude/Antigravity/OpenCode）
- [ ] 實作 Type 下拉選單（Skills/Commands/Agents）
- [ ] 切換時刷新資源列表
- **驗證**：切換選單時列表正確更新

### 5.6 實作資源列表
- [ ] 使用 ListView + Checkbox 顯示資源
- [ ] 顯示資源名稱與來源
- [ ] 根據 toggle-config.yaml 設定初始狀態
- **驗證**：列表正確顯示資源與狀態

### 5.7 實作互動邏輯
- [ ] Space 切換選中項目
- [ ] A 全選
- [ ] N 全取消
- [ ] S 儲存並同步
- **驗證**：所有互動正常運作

### 5.8 實作操作按鈕功能
- [ ] Install 按鈕執行安裝流程並顯示進度
- [ ] Maintain 按鈕執行維護流程並顯示進度
- [ ] Status 按鈕顯示環境狀態
- **驗證**：按鈕功能正常

### 5.9 實作 Add Skills 對話框
- [ ] 建立 `AddSkillsModal` 類別
- [ ] 實作套件名稱輸入框
- [ ] 實作範例提示區域
- [ ] 實作 Install 按鈕
- [ ] 實作輸出日誌區域（Log widget）
- **驗證**：對話框可正常開啟與關閉

### 5.10 實作 npx skills add 執行邏輯
- [ ] 使用 `asyncio.create_subprocess_exec` 執行 `npx skills add`
- [ ] 即時串流輸出到 Log widget
- [ ] 處理成功/失敗狀態
- [ ] 成功後刷新主畫面資源列表
- **驗證**：執行 `npx skills add vercel-labs/agent-skills` 測試

### 5.11 註冊 TUI 指令到 CLI
- [ ] 在 `script/main.py` 引入並註冊 `tui` 指令
- **驗證**：執行 `uv run script/main.py tui` 可啟動 TUI

---

## Phase 6: 文件與測試

### 6.1 更新 README
- [ ] 新增 `list` 指令說明
- [ ] 新增 `toggle` 指令說明
- [ ] 新增 `tui` 指令說明
- [ ] 新增配置檔格式說明
- [ ] 新增 `npx skills` 提示說明

### 6.2 更新 setup-script spec
- [ ] 將新增的 Requirements 合併到 `openspec/specs/setup-script/spec.md`

---

## Dependencies

```
Phase 1 ──┬──> Phase 2
          │
          ├──> Phase 3
          │
          └──> Phase 4

Phase 1 + Phase 4 ──> Phase 5

Phase 2~5 ──> Phase 6
```

## Parallelizable Work

- Phase 2、Phase 3、Phase 4 可並行（在 Phase 1 完成後）
- Phase 5.4、5.5、5.6 可並行（在 5.3 完成後）
- Phase 5.9、5.10 可並行（在 5.3 完成後）
