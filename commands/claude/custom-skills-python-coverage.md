---
description: 執行 Python 覆蓋率分析並提供改善建議
allowed-tools: Bash(pytest:*), Bash(python:*), Bash(ai-dev coverage:*), Bash(uv run:*)
argument-hint: "[path] [--source dir]"
---

# Custom Skills Coverage | 覆蓋率分析

執行 Python 測試覆蓋率分析並由 AI 分析結果、提供改善建議。

## Workflow | 工作流程

### Step 1: 執行覆蓋率分析

```bash
uv run ai-dev coverage [--source <path>]
```

**Options:**
- `--source`, `-s`: 原始碼路徑（預設為當前目錄）

### Step 2: 分析結果

根據 pytest-cov 輸出（`--cov-report=term-missing` 格式），分析並回報：

#### 2.1 整體摘要
從輸出中提取：
- 整體覆蓋率百分比
- 總行數 vs 已覆蓋行數

格式範例：
```
## 覆蓋率報告

**整體覆蓋率**: 75% (150/200 行)
```

#### 2.2 各檔案覆蓋率
以表格呈現各檔案狀態：

```markdown
| 檔案 | 覆蓋率 | 未覆蓋行數 |
|------|--------|-----------|
| script/main.py | 85% | 45-52, 78 |
| script/utils.py | 60% | 12-20, 35-40 |
```

標示規則：
- ≥ 80%: 良好
- 60-79%: 需改善
- < 60%: 警告

#### 2.3 改善建議
針對低覆蓋率檔案：
1. 識別未覆蓋的程式碼區塊
2. 分析這些區塊的功能
3. 建議應撰寫的測試類型

格式範例：
```
### 改善建議

#### `script/utils.py` (60%)
**未覆蓋區塊**:
- 行 12-20: `parse_config()` 函式的錯誤處理
- 行 35-40: `validate_input()` 的邊界條件

**建議測試**:
1. 測試 `parse_config()` 處理無效 JSON
2. 測試 `parse_config()` 處理缺失欄位
3. 測試 `validate_input()` 的空值和邊界值
```

#### 2.4 優先順序
根據以下因素排序改善優先級：
1. 檔案的重要性（核心邏輯 > 工具函式）
2. 覆蓋率差距
3. 未覆蓋程式碼的風險程度

## 覆蓋率門檻參考

| 等級 | 覆蓋率 | 說明 |
|------|--------|------|
| 優秀 | ≥ 90% | 高品質測試覆蓋 |
| 良好 | 80-89% | 符合一般標準 |
| 及格 | 70-79% | 最低可接受 |
| 不足 | < 70% | 需要改善 |

## Prerequisites | 前置需求

需要安裝 pytest-cov：
```bash
pip install pytest-cov
```
