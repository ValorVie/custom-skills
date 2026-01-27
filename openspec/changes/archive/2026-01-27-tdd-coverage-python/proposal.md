# Proposal: TDD Coverage Python

## Summary

建立 `/custom-skills-coverage` 命令，支援 Python 專案的測試覆蓋率分析（`pytest --cov`）。

## Motivation

目前的 `/coverage` 命令：
- 依賴 `npm test --coverage`
- 解析 `coverage/coverage-summary.json`
- 不支援 Python 專案

Python 專案（如 custom-skills 本身）無法在工作流程中進行覆蓋率驗證，這是 TDD 流程的最後一環。

## Scope

### In Scope

- `/custom-skills-coverage` 命令
- `pytest --cov` 執行和輸出解析
- 覆蓋率摘要顯示（行、分支、函數）
- 未覆蓋檔案/行數清單

### Out of Scope

- 自動生成缺失測試（與 test-generation 整合是後續）
- 其他語言支援
- HTML 報告生成

## Design

### 命令介面

```bash
# 基本用法
/custom-skills-coverage                    # 分析整個專案

# 指定模組
/custom-skills-coverage script/            # 分析特定目錄

# 選項
/custom-skills-coverage --threshold 80     # 設定門檻（預設 80%）
/custom-skills-coverage --html             # 生成 HTML 報告
/custom-skills-coverage --fail-under 80    # 低於門檻時失敗
```

### 輸出格式

```
Coverage Report
═══════════════════════════════════════════════════════════════

Overall: 75.2%  (目標: 80%) ⚠️

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┓
┃ Module                      ┃ Lines    ┃ Covered  ┃ %       ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━┩
│ script/commands/clone.py    │ 120      │ 108      │ 90.0%   │
│ script/commands/update.py   │ 85       │ 68       │ 80.0%   │
│ script/utils/git_helpers.py │ 150      │ 95       │ 63.3% ⚠️│
│ script/utils/shared.py      │ 200      │ 150      │ 75.0%   │
└─────────────────────────────┴──────────┴──────────┴─────────┘

Uncovered Lines:
  script/utils/git_helpers.py: 45-52, 78-85, 120-135
```

### 實作架構

```python
# script/commands/coverage.py

@app.command()
def coverage(
    path: str = typer.Argument(".", help="要分析的路徑"),
    threshold: int = typer.Option(80, help="覆蓋率門檻"),
    fail_under: int = typer.Option(None, help="低於此值時失敗"),
):
    """分析 Python 專案的測試覆蓋率。"""

    # 執行 pytest --cov
    result = subprocess.run([
        "pytest", "--cov=" + path,
        "--cov-report=json",
        "--cov-report=term"
    ], capture_output=True, text=True)

    # 解析 coverage.json
    report = parse_coverage_json("coverage.json")

    # 格式化輸出
    display_coverage_report(report, threshold)

    # 檢查門檻
    if fail_under and report.total < fail_under:
        raise typer.Exit(code=1)
```

## Capabilities

1. **執行覆蓋率分析** - `pytest --cov`
2. **解析報告** - JSON 格式解析
3. **格式化顯示** - Rich 表格輸出
4. **門檻檢查** - 低於門檻時警告或失敗
5. **未覆蓋清單** - 顯示需要補測試的位置

## Dependencies

- pytest
- pytest-cov
- Rich（已有）

## Related Specs

- 現有 `/coverage` 命令（JS/TS）
- testing-guide skill
- TDD workflow
