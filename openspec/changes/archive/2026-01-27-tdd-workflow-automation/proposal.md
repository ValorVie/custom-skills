# Proposal: TDD Workflow Automation

## Summary

完整自動化 TDD（Test-Driven Development）工作流程，從規格到測試執行到覆蓋率驗證，消除目前流程中的手動步驟。

## Motivation

目前的 TDD 流程存在多個斷點：

```
Best Practice TDD 流程          現有工具支援          缺口
─────────────────────────────────────────────────────────────
specs 定義需求                  ✓ OpenSpec specs
         ↓
/derive-tdd 生成測試骨架        ✓ 有（但只生成 [TODO]）
         ↓
填寫測試邏輯                    ✗ 缺少（需手動）       ← 缺口 1
         ↓
執行測試（應失敗 - Red）        ✗ 缺少 /run-tests      ← 缺口 2
         ↓
實作功能程式碼                  ✓ /opsx:apply
         ↓
執行測試（應通過 - Green）      ✗ 缺少 /run-tests      ← 缺口 2
         ↓
覆蓋率驗證                      △ /coverage（僅 JS/TS） ← 缺口 3
```

這導致：
- 開發者需手動填寫測試邏輯
- 無法在工作流程中自動執行測試
- Python 專案無覆蓋率分析支援
- TDD 的 Red-Green-Refactor 循環無法自動化

## Scope

### In Scope

完整 TDD 工作流自動化，包含三個子提案：

| 子提案 | 解決缺口 | 說明 |
|--------|----------|------|
| **tdd-test-generation** | 缺口 1 | 從骨架生成完整測試邏輯 |
| **tdd-test-execution** | 缺口 2 | 執行測試（Red/Green） |
| **tdd-coverage-python** | 缺口 3 | Python 覆蓋率分析 |

### Out of Scope（Phase 1）

- OpenSpec TDD schema（test-first artifact 順序）
- 非 Python 語言支援
- CI/CD 整合

## Design

### 目標流程

```
┌─────────────────────────────────────────────────────────────┐
│  /opsx:continue                                             │
│  建立 specs (WHEN/THEN 場景)                                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  /custom-skills-derive-tests                                │
│  從 specs 生成完整測試程式碼（非骨架）                        │
│  - 解析 WHEN/THEN 場景                                      │
│  - 生成 pytest 測試函數                                     │
│  - 填寫 Arrange/Act/Assert                                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  /custom-skills-test                                        │
│  執行測試（應失敗 - Red Phase）                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  /opsx:apply                                                │
│  實作功能程式碼                                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  /custom-skills-test                                        │
│  執行測試（應通過 - Green Phase）                            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  /custom-skills-coverage                                    │
│  覆蓋率驗證（≥80%）                                         │
└─────────────────────────────────────────────────────────────┘
```

### 子提案關係

```
tdd-workflow-automation (主提案)
├── tdd-test-generation      # 缺口 1: 生成完整測試
├── tdd-test-execution       # 缺口 2: 執行測試
└── tdd-coverage-python      # 缺口 3: 覆蓋率分析
```

## Capabilities

### 1. 測試生成 (tdd-test-generation)
- `/custom-skills-derive-tests` 命令
- 從 OpenSpec specs 的 WHEN/THEN 場景生成測試
- 輸出完整可執行的 pytest 測試程式碼

### 2. 測試執行 (tdd-test-execution)
- `/custom-skills-test` 命令
- 執行 pytest 並格式化結果
- 支援 `--verbose`, `--fail-fast` 等選項

### 3. 覆蓋率分析 (tdd-coverage-python)
- `/custom-skills-coverage` 命令
- `pytest --cov` 整合
- 顯示未覆蓋的檔案和行數

## Success Criteria

- [ ] 從 specs 到測試執行的完整自動化流程
- [ ] Red-Green 循環可在工作流程中執行
- [ ] Python 專案覆蓋率分析支援
- [ ] 所有新命令使用 `custom-skills-*` 前綴

## Dependencies

- pytest
- pytest-cov
- 現有 OpenSpec 基礎設施

## Related Specs

- 現有 `/derive-tdd` 命令
- 現有 `/coverage` 命令
- testing-guide skill
- forward-derivation skill
