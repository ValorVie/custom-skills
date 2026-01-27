## Context

已完成 `tdd-test-execution`，建立了 TestRunner 架構。現在需要擴充覆蓋率分析功能，使用 `pytest-cov` 執行覆蓋率測試。

## Goals / Non-Goals

**Goals:**
- 建立 `/custom-skills-coverage` Claude Code 命令
- 建立 `ai-dev coverage` CLI 命令
- **腳本只負責執行命令，AI 負責分析報告和提供建議**

**Non-Goals:**
- ~~解析 pytest-cov 報告~~（改由 AI 分析）
- ~~格式化輸出~~（改由 AI 分析）
- HTML 報告生成（用戶可自行使用 pytest-cov）
- 自動生成缺失測試（見 tdd-test-generation）
- 其他語言支援

## Architecture Principle | 架構原則

```
┌─────────────────────────────────────────────────────────────┐
│                 Claude Code Command                          │
│  /custom-skills-coverage                                     │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Prompt 定義：                                            ││
│  │ 1. 執行什麼命令                                          ││
│  │ 2. 如何分析覆蓋率報告                                    ││
│  │ 3. 如何提供改善建議                                      ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 CLI 命令 (ai-dev coverage)                   │
│  - 偵測測試框架                                              │
│  - 檢查依賴 (pytest-cov)                                     │
│  - 執行 pytest --cov 並輸出原始結果                          │
└─────────────────────────────────────────────────────────────┘
```

**原則**：
- 腳本只負責「執行」和「基本檢查」
- 分析和建議交給 AI（更有彈性、可提供智慧建議）

## Decisions

### 1. 擴充 TestRunner

**選擇**：在 `TestRunner` 新增 `run_with_coverage()` 方法。

```python
class TestRunner(ABC):
    @abstractmethod
    def run_with_coverage(
        self,
        path: str | None = None,
        source: str | None = None,
    ) -> CommandResult:
        pass

    @abstractmethod
    def is_coverage_available(self) -> bool:
        pass
```

**理由**：
- 覆蓋率是測試執行的擴充功能
- 保持架構一致性

### 2. 使用 term-missing 格式

**選擇**：使用 `--cov-report=term-missing`。

```python
cmd = [
    "pytest",
    f"--cov={source}",
    "--cov-report=term-missing",
]
```

**理由**：
- 文字格式，AI 容易解析
- 包含未覆蓋行號，方便分析

### 3. Claude Code 命令

**選擇**：在 prompt 中定義分析流程。

```markdown
### Step 2: 分析結果

#### 2.1 整體摘要
從輸出中提取整體覆蓋率

#### 2.2 各檔案覆蓋率
以表格呈現各檔案狀態

#### 2.3 改善建議
針對低覆蓋率檔案提供建議
```

**理由**：
- AI 可以理解程式碼並提供有意義的建議
- 不需要寫死分析邏輯

## Risks / Trade-offs

**[風險] pytest-cov 未安裝**
→ 緩解：`is_coverage_available()` 檢查並提示安裝

**[取捨] 不在腳本中解析報告**
→ 理由：AI 分析更有彈性，可提供智慧化改善建議
