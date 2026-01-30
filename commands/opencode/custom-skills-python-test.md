---
description: 執行 Python 測試並分析結果
allowed-tools: Bash(pytest:*), Bash(python:*), Bash(ai-dev test:*), Bash(uv run:*)
argument-hint: "[path] [--verbose] [--fail-fast] [-k keyword]"
---

# Custom Skills Test | 測試執行與分析

執行 Python 測試並由 AI 分析結果。

## Workflow | 工作流程

### Step 1: 執行測試

```bash
uv run ai-dev test [options]
```

**Options:**
- `--verbose`, `-v`: 顯示詳細輸出
- `--fail-fast`, `-x`: 失敗時立即停止
- `-k <keyword>`: 過濾測試名稱

### Step 2: 分析結果

根據 pytest 輸出，分析並回報：

#### 2.1 測試摘要
從輸出中提取：
- 通過數量（passed）
- 失敗數量（failed）
- 跳過數量（skipped）
- 執行時間

格式範例：
```
## 測試結果

✓ **通過**: 15  ✗ **失敗**: 2  ○ **跳過**: 1  ⏱ **時間**: 1.23s
```

#### 2.2 失敗分析（如有失敗）
對每個失敗的測試：
1. 識別失敗的測試名稱和檔案位置
2. 分析錯誤訊息和 traceback
3. 推測可能的失敗原因
4. 建議修復方向

格式範例：
```
### 失敗測試分析

#### `test_user_login` (tests/test_auth.py:45)
**錯誤**: AssertionError: expected 200, got 401
**原因**: 認證 token 可能已過期或格式錯誤
**建議**: 檢查 token 生成邏輯，確認 expiry 設定
```

#### 2.3 整體評估
- 測試是否全部通過
- 如有失敗，優先處理建議

## TDD Workflow | TDD 工作流程

此命令支援 Red-Green 循環：

1. **Red Phase**: 執行測試，預期失敗
   ```
   /custom-skills-python-test
   ```
   → 分析哪些測試失敗，確認是預期的失敗

2. **實作功能程式碼**

3. **Green Phase**: 執行測試，預期通過
   ```
   /custom-skills-python-test
   ```
   → 確認所有測試通過

## Prerequisites | 前置需求

需要安裝 pytest：
```bash
pip install pytest
```
