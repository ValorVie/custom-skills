# Proposal: TDD Test Execution

## Summary

建立 `/custom-skills-test` 命令，執行 pytest 測試並格式化結果輸出，支援 TDD 工作流程的 Red/Green 循環。

## Motivation

目前工作流程中無法自動執行測試：
- `/derive-tdd` 生成測試骨架後，需手動執行 pytest
- `/opsx:apply` 的驗證任務需手動執行
- 無法在 Claude Code 中直接執行測試

這導致 TDD 的 Red-Green 循環無法自動化。

## Scope

### In Scope

- `/custom-skills-test` 命令
- 執行 pytest 並格式化結果
- 支援常用選項（--verbose, --fail-fast, -k 等）
- 可擴充的 TestRunner 架構

### Out of Scope

- 覆蓋率分析（見 tdd-coverage-python 子提案）
- 其他語言支援（保留架構但不實作）
- 測試生成（見 tdd-test-generation 子提案）

## Design

### 架構設計（語言無關）

```
┌─────────────────────────────────────────────────────────────┐
│              /custom-skills-test 命令                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ TestRunner  │    │ TestRunner  │    │ TestRunner  │     │
│  │  (Python)   │    │   (Node)    │    │    (Go)     │     │
│  │   pytest    │    │ vitest/jest │    │  go test    │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│        ✓                 △                   △              │
│     Phase 1           未來               未來               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 命令流程

```
使用者執行 /custom-skills-test [path] [options]
         ↓
    偵測專案語言/框架
         ↓
    呼叫對應的 TestRunner
         ↓
    執行測試、收集結果
         ↓
    格式化輸出（Rich Table）
         ↓
    回傳 exit code（0=通過, 1=失敗）
```

### 檔案結構

```
script/
├── commands/
│   └── test.py              # ai-dev test CLI
└── utils/
    └── test_runner/
        ├── __init__.py      # 公開 API
        ├── base.py          # TestRunner 抽象基類
        ├── python.py        # Python (pytest) 實作
        └── detector.py      # 框架自動偵測

commands/claude/
└── custom-skills-test.md    # Claude Code 命令定義
```

### 命令介面

```bash
# CLI 用法
ai-dev test                      # 執行所有測試
ai-dev test tests/               # 指定目錄
ai-dev test tests/test_foo.py    # 指定檔案

# 選項
ai-dev test --verbose            # 詳細輸出
ai-dev test --fail-fast          # 失敗即停
ai-dev test -k "test_name"       # 過濾測試名稱

# Claude Code 命令
/custom-skills-test              # 執行測試
/custom-skills-test tests/       # 指定目錄
```

### 輸出格式

```
Test Results
═══════════════════════════════════════════════════════════════

✓ 15 passed, ✗ 2 failed, ○ 1 skipped  (3.2s)

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━┓
┃ Test                                    ┃ Status ┃ Time    ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━┩
│ test_is_git_repo                        │ ✓ PASS │ 0.01s   │
│ test_detect_mode_changes                │ ✓ PASS │ 0.15s   │
│ test_revert_files                       │ ✗ FAIL │ 0.02s   │
│ test_handle_metadata_changes            │ ✗ FAIL │ 0.01s   │
└─────────────────────────────────────────┴────────┴─────────┘

Failures:
─────────────────────────────────────────────────────────────
test_revert_files - AssertionError: Expected True, got False
  File: tests/test_git_helpers.py:45
```

## Capabilities

1. **測試執行** - 執行 pytest
2. **框架偵測** - 自動偵測 pytest/unittest
3. **結果格式化** - Rich 表格顯示
4. **失敗詳情** - 顯示失敗測試的錯誤訊息
5. **擴充架構** - TestRunner 抽象類別

## Dependencies

- pytest
- Rich（已有）

## Related Specs

- tdd-workflow-automation（主提案）
- tdd-coverage-python（覆蓋率子提案）
- tdd-test-generation（測試生成子提案）
