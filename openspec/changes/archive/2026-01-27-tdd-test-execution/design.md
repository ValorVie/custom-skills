## Context

目前專案使用 Typer 作為 CLI 框架，已有 `script/commands/` 目錄放置各種命令。需要新增測試執行命令，並建立可擴充的 TestRunner 架構。

## Goals / Non-Goals

**Goals:**
- 建立 `/custom-skills-test` Claude Code 命令
- 建立 `ai-dev test` CLI 命令
- 可擴充的 TestRunner 抽象架構
- **腳本只負責執行命令，AI 負責分析結果**

**Non-Goals:**
- ~~格式化的測試結果輸出~~（改由 AI 分析）
- 覆蓋率分析（見 tdd-coverage-python）
- 其他語言支援（架構預留但不實作）
- 測試生成（見 tdd-test-generation）

## Architecture Principle | 架構原則

```
┌─────────────────────────────────────────────────────────────┐
│                 Claude Code Command                          │
│  /custom-skills-test                                         │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Prompt 定義：                                            ││
│  │ 1. 執行什麼命令                                          ││
│  │ 2. 如何分析輸出（測試摘要、失敗分析、建議）              ││
│  │ 3. 報告格式規範                                          ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    CLI 命令 (ai-dev test)                    │
│  - 偵測測試框架                                              │
│  - 檢查依賴                                                  │
│  - 執行 pytest 並輸出原始結果                                │
└─────────────────────────────────────────────────────────────┘
```

**原則**：
- 腳本只負責「執行」和「基本檢查」
- 分析和格式化交給 AI（更有彈性、易於擴展）

## Decisions

### 1. TestRunner 抽象架構

**選擇**：使用 ABC 抽象基類 + 簡化的 CommandResult。

```python
# script/utils/test_runner/base.py
@dataclass
class CommandResult:
    output: str      # 原始輸出
    exit_code: int   # Exit code

class TestRunner(ABC):
    @abstractmethod
    def run(self, path, verbose, fail_fast, keyword) -> CommandResult:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass
```

**理由**：
- 不解析輸出，交給 AI 分析
- 保持簡單，只傳遞原始資料

### 2. Python TestRunner 實作

**選擇**：執行 `pytest --tb=short` 並回傳原始輸出。

```python
class PythonTestRunner(TestRunner):
    def run(self, ...) -> CommandResult:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return CommandResult(
            output=result.stdout + result.stderr,
            exit_code=result.returncode,
        )
```

**理由**：
- 不解析輸出格式（避免寫死）
- AI 可以處理任何格式變化

### 3. Claude Code 命令

**選擇**：在 prompt 中定義分析流程。

```markdown
### Step 2: 分析結果

#### 2.1 測試摘要
從輸出中提取 passed/failed/skipped/時間

#### 2.2 失敗分析（如有失敗）
- 識別失敗的測試
- 分析錯誤訊息
- 建議修復方向
```

**理由**：
- AI 分析更有彈性
- 可以提供智慧建議
- 易於調整格式

## Risks / Trade-offs

**[風險] pytest 未安裝**
→ 緩解：`is_available()` 檢查，提示安裝指令

**[取捨] 不在腳本中解析輸出**
→ 理由：AI 分析更有彈性，避免因格式變化需修改程式碼
