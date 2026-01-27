# Proposal: clone-metadata-check

## Summary

在 `ai-dev clone` 執行後，檢測非內容異動（如檔案權限、換行符），並提示使用者是否要忽略這些變更，避免 git status 顯示大量無意義的差異。

## Motivation

當 `ai-dev clone` 從上游來源（UDS、ECC、Obsidian 等）複製檔案到專案時，可能會引入非內容層面的變更：

1. **檔案權限差異**：上游檔案可能是 755，而 git 記錄為 644（或反之）
2. **換行符差異**：Windows (CRLF) vs Unix (LF) 的差異
3. **其他 metadata**：檔案時間戳記等

這些變更會導致：
- `git status` 顯示大量「已修改」的檔案
- VSCode Source Control 面板充滿噪音
- 使用者困惑，不確定是否有實際內容變更

## Scope

### In Scope

- 檢測 clone 後的非內容異動
  - 檔案權限變更（mode change）
  - 換行符變更（line ending）
- 提供互動式提示，讓使用者選擇處理方式
- 支援自動修復選項

### Out of Scope

- 修改上游來源的權限/換行符
- 在 clone 過程中預防（只做事後檢測）
- 處理二進位檔案差異

## Design

### 檢測流程

```
┌─────────────────────────────────────────────────────────────────────┐
│  ai-dev clone 完成後                                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. 執行 git diff --name-only --diff-filter=M                       │
│     取得所有「已修改」的檔案                                        │
│                                                                     │
│  2. 對每個檔案分析差異類型：                                        │
│     ├── git diff --summary (檢測 mode change)                       │
│     └── git diff (檢測內容是否只有換行符差異)                       │
│                                                                     │
│  3. 分類結果：                                                      │
│     ├── metadata_only: 只有權限/換行符變更                          │
│     └── content_changed: 有實際內容變更                             │
│                                                                     │
│  4. 若有 metadata_only 檔案，提示使用者                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 使用者提示

```
ai-dev clone 完成

⚠️  偵測到 23 個檔案有非內容異動：
   - 檔案權限變更: 18 個
   - 換行符變更: 5 個

這些變更不影響實際內容。如何處理？

  [1] 還原這些變更 (git checkout)     ← 建議
  [2] 設定 git 忽略權限 (core.fileMode=false)
  [3] 忽略，保留變更
  [4] 顯示詳細清單

選擇 [1-4]:
```

### 處理選項

| 選項 | 動作 | 說明 |
|------|------|------|
| 還原變更 | `git checkout -- <files>` | 將檔案還原到 git 記錄的狀態 |
| 忽略權限 | `git config core.fileMode false` | 讓 git 忽略權限差異 |
| 保留變更 | 不處理 | 使用者自行決定 |
| 顯示清單 | 列出所有檔案 | 讓使用者審查後再決定 |

### 實作位置

修改 `script/commands/clone.py` 的 `clone()` 函數：

```python
@app.command()
def clone(...):
    # ... existing clone logic ...

    # 新增：檢測非內容異動
    if is_dev_dir:
        metadata_changes = detect_metadata_changes()
        if metadata_changes:
            handle_metadata_changes(metadata_changes)
```

新增 `script/utils/git_helpers.py`：

```python
def detect_metadata_changes() -> dict:
    """檢測非內容異動。"""
    ...

def handle_metadata_changes(changes: dict) -> None:
    """互動式處理非內容異動。"""
    ...
```

### 配置選項

可在 `toggle-config.yaml` 新增設定，記住使用者偏好：

```yaml
clone:
  auto_fix_metadata: true  # 自動還原非內容異動
  ignore_file_mode: false  # 是否自動設定 core.fileMode=false
```

## Related Specs

- `ai-dev-clone`: 現有的 clone 功能規格

## Dependencies

- Git CLI
- 現有的 clone 流程
