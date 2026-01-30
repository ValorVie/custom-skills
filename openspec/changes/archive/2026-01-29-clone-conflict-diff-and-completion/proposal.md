## Why

`ai-dev clone` 偵測到衝突時只顯示 hash 值，使用者無法得知實際內容改了什麼，難以判斷該覆蓋還是保留。此外，`ai-dev` CLI 安裝後缺少 shell 自動補全，使用體驗不夠流暢。

## What Changes

- 在 clone 衝突互動選單中新增「查看差異」選項，顯示來源（新版）與目標（被修改版）的 diff
- `ConflictInfo` 與 `FileRecord` 擴充路徑欄位，讓衝突偵測階段即攜帶來源/目標路徑
- 互動選單順序調整：查看差異排在「備份後覆蓋」之後、「取消分發」之前
- 查看差異後重新顯示選單，讓使用者繼續選擇處理方式
- `ai-dev install` 流程自動安裝 shell completion（Typer 內建）

## Capabilities

### New Capabilities
- `conflict-diff-view`: clone 衝突時查看來源與目標之間的差異
- `shell-completion`: 安裝流程自動設定 shell 自動補全

### Modified Capabilities

（無既有 spec 需要修改）

## Impact

- `script/utils/manifest.py`：擴充 `FileRecord`、`ConflictInfo` dataclass，修改 `detect_conflicts()`、`prompt_conflict_action()`，新增 `show_conflict_diff()`
- `script/utils/shared.py`：衝突處理迴圈改為支援 diff 後重新選擇
- `script/commands/install.py`：安裝流程新增 shell completion 安裝步驟
