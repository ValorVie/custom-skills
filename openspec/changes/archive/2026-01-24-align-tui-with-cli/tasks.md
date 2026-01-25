# Tasks: align-tui-with-cli

## 概覽

對齊 TUI 與 CLI 功能，新增 Clone 按鈕和 Standards Profile 管理。

---

## 任務列表

### Phase 1: Clone 功能整合

- [x] **T1.1**: 在頂部操作列新增 Clone 按鈕
  - 位置：Update 按鈕之後
  - 樣式：variant="default"
  - 驗證：點擊後執行 `ai-dev clone`

- [x] **T1.2**: 實作 Clone 按鈕事件處理
  - 呼叫 `run_cli_command("clone", self._get_sync_project_args())`
  - 完成後刷新資源列表

### Phase 2: Standards Profile 管理

- [x] **T2.1**: 新增 Standards Profile 區塊
  - 位置：MCP Config 區塊上方
  - 顯示目前啟用的 profile
  - 顯示可用 profiles 下拉選單

- [x] **T2.2**: 實作 profile 切換功能
  - 使用 `script/commands/standards.py` 的邏輯
  - 切換後顯示通知

- [x] **T2.3**: 新增快捷鍵
  - `c` - 執行 Clone 功能
  - `t` - 切換 Standards Profile（循環）
  - 更新 Footer 顯示

### Phase 3: 更新規格文件

- [x] **T3.1**: 更新 `openspec/specs/skill-tui/spec.md`
  - 新增 Clone 按鈕相關 Requirements
  - 新增 Standards Profile Section Requirements

---

## 驗證步驟

1. 執行 `ai-dev tui`
2. 確認 Clone 按鈕存在且可點擊
3. 確認 Standards Profile 區塊顯示正確
4. 確認 profile 切換功能正常
5. 確認快捷鍵 `t` 正常運作
