## Why

`ai-dev sync pull` 目前是單向覆蓋（repo → local），不會偵測本機是否有未 push 的變更。若使用者忘記在上一台機器 push 就在另一台 pull，本機異動會被靜默覆蓋，造成資料遺失。這是跨裝置同步最常見的資料遺失場景，需要在 pull 前加入安全檢查。

## What Changes

- 新增 pull 前本機異動偵測：比較本機目錄與 sync repo 的差異，列出變更檔案
- 偵測到異動時提供互動式選項：先 push 再 pull（推薦）、強制覆蓋、取消
- 新增 `--force` flag：跳過偵測直接 pull，供腳本自動化使用
- 無異動時行為不變，不影響現有工作流

## Capabilities

### New Capabilities

- `sync-pull-safety`: pull 前偵測本機未推送變更並提供安全選項，防止靜默覆蓋資料遺失

### Modified Capabilities

- `sync-command`: pull 子指令新增 `--force` flag 與互動式安全檢查流程

## Impact

- **程式碼**：`script/commands/sync.py`（修改 `pull` 指令）、`script/utils/sync_config.py`（新增變更偵測函式）
- **依賴**：無新依賴
- **文件**：`docs/dev-guide/workflow/AI-DEV-SYNC-GUIDE.md`（更新 pull 行為說明）
- **測試**：新增 pull safety check 相關測試
