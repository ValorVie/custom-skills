---
description: 生成測試報告供人工審閱（結構化資料 + AI 分析）
allowed-tools: Bash(uv run:*), Bash(ai-dev:*), Bash(openspec:*), Bash(./vendor/bin/phpunit:*), Bash(composer:*), Read, Write, Glob, Grep
argument-hint: "[change-name] [--output <path>]"
---

# Custom Skills Report | 測試報告生成

生成結構化測試報告供人工審閱，包含測試結果、覆蓋率、任務完成狀態和 AI 分析。

## Workflow | 工作流程

### Step 0: 偵測專案語言與檢查前置需求

自動偵測專案使用的程式語言：

| 偵測條件 | 語言 | 測試命令 |
|----------|------|----------|
| 存在 `composer.json` | PHP | `./vendor/bin/phpunit` |
| 存在 `pyproject.toml` 或 `requirements.txt` | Python | `uv run ai-dev test` |

如果兩者都存在，預設使用 Python。可透過專案結構或使用者指定覆蓋。

**偵測到 PHP 時，檢查 PHPUnit：**

```bash
test -f ./vendor/bin/phpunit && echo "PHPUnit OK" || echo "PHPUnit not found"
```

如果 PHPUnit 未安裝，提示使用者：

```
⚠️ PHPUnit 未安裝。請執行以下命令安裝：

composer require --dev phpunit/phpunit

安裝完成後再次執行此命令。
```

### Step 1: 收集資料

根據偵測到的語言執行對應命令：

**Python:**
```bash
# 1. 執行測試並取得結果
uv run ai-dev test -v

# 2. 執行覆蓋率分析
uv run ai-dev coverage

# 3. 讀取 OpenSpec change 狀態（如有指定）
openspec status --change <change-name>
```

**PHP:**
```bash
# 1. 執行測試並取得結果
./vendor/bin/phpunit --verbose

# 2. 執行覆蓋率分析
./vendor/bin/phpunit --coverage-text

# 3. 讀取 OpenSpec change 狀態（如有指定）
openspec status --change <change-name>
```

### Step 2: 讀取相關檔案

如果有指定 change-name：
1. 讀取 `openspec/changes/<change-name>/tasks.md` - 任務完成狀態
2. 讀取 `openspec/changes/<change-name>/specs/*.md` - Specs 場景
3. 讀取測試檔案 - 對照 Specs 覆蓋情況

### Step 3: 生成結構化報告

建立結構化資料區塊：

```yaml
# report-data.yaml
report:
  generated_at: "2024-01-27T10:30:00+08:00"
  change_name: "<change-name>"  # 如有

test_summary:
  total: 33
  passed: 33
  failed: 0
  skipped: 0
  duration: "1.24s"

coverage:
  overall: 73
  target: 70
  status: "pass"  # pass | fail
  files:
    - path: "script/utils/git_helpers.py"
      coverage: 73
      missing_lines: "269-313"

tasks:
  total: 8
  completed: 8
  status: "complete"  # complete | in_progress | blocked

specs_coverage:
  total_scenarios: 10
  covered_by_tests: 10
  uncovered: []
```

### Step 4: 生成 AI 分析報告

根據收集的資料，生成自然語言分析報告：

```markdown
## AI 分析報告

### 整體評估

[根據資料綜合評估，例如：]
本次開發已完成所有任務，測試全數通過，覆蓋率達標。
程式碼品質良好，可進入人工審閱階段。

### 測試結果分析

- **通過率**: 100% (33/33)
- **執行時間**: 1.24s
- **評估**: 所有測試通過，無異常

### 覆蓋率分析

- **整體覆蓋率**: 73% (目標: 70%)
- **未覆蓋區塊**: `handle_metadata_changes` 互動式流程 (行 269-313)
- **評估**: 覆蓋率達標，未覆蓋部分為互動式 UI 邏輯，已標記為手動補充

### 任務完成狀態

- **完成率**: 100% (8/8)
- **評估**: 所有任務已完成

### Specs 對照

| Requirement | Scenarios | 測試覆蓋 |
|-------------|-----------|----------|
| 檢測檔案權限變更 | 2 | ✓ 2/2 |
| 檢測換行符變更 | 2 | ✓ 2/2 |
| ... | ... | ... |

### 發現的問題

[如有問題列出，例如：]
- 無重大問題

### 建議

[後續建議，例如：]
1. 可考慮補充互動式流程的整合測試
2. 建議在 PR 中說明未覆蓋區塊的原因
```

### Step 5: 輸出報告檔案

將報告寫入檔案：

**預設輸出路徑：**
- 如有 change-name: `openspec/changes/<change-name>/report.md`
- 無 change-name: `tests/report.md`

**可用 `--output <path>` 指定自訂路徑**

### Step 6: 顯示摘要

```
## 報告生成完成

**輸出檔案**: openspec/changes/my-feature/report.md

**快速摘要**:
- 測試: ✓ 33/33 通過
- 覆蓋率: ✓ 73% (目標 70%)
- 任務: ✓ 8/8 完成

**下一步**: 人工審閱報告後執行 `/opsx:archive`
```

## 報告結構

完整報告包含以下區塊：

```markdown
# Test Report: <change-name>

Generated: 2024-01-27 10:30:00

---

## 結構化資料

\`\`\`yaml
<結構化 YAML 資料>
\`\`\`

---

## AI 分析報告

### 整體評估
...

### 測試結果分析
...

### 覆蓋率分析
...

### 任務完成狀態
...

### Specs 對照
...

### 發現的問題
...

### 建議
...

---

## 審閱確認

- [ ] 已審閱測試結果
- [ ] 已審閱覆蓋率
- [ ] 已審閱未覆蓋區塊說明
- [ ] 確認可進入歸檔階段

審閱者: _______________
日期: _______________
```

## 使用情境

### 情境 1: 開發完成後生成報告

```
# 完成實作和測試後
/custom-skills-report my-feature

# 人工審閱報告
# 確認後歸檔
/opsx:archive my-feature
```

### 情境 2: 中途檢查進度

```
# 實作進行中，想看目前狀態
/custom-skills-report my-feature

# 根據報告調整實作方向
```

### 情境 3: 無 OpenSpec change

```
# 一般專案的測試報告
/custom-skills-report

# 輸出到 tests/report.md
```

## 與工作流程整合

```
Phase 5: 測試
    ↓
/custom-skills-report  ← 生成報告
    ↓
人工審閱報告
    ↓
Phase 6: /opsx:verify
    ↓
Phase 7: /opsx:archive
```

## 語言特定命令參考

如需單獨執行測試或覆蓋率分析，請使用對應語言的命令：

**Python:**
- `/custom-skills-python-test` - 執行 pytest 測試
- `/custom-skills-python-coverage` - 執行覆蓋率分析
- `/custom-skills-python-derive-tests` - 從 specs 生成測試

**PHP:**
- `/custom-skills-php-test` - 執行 PHPUnit 測試
- `/custom-skills-php-coverage` - 執行覆蓋率分析
- `/custom-skills-php-derive-tests` - 從 specs 生成測試

## Limitations | 限制

- 需要先執行測試和覆蓋率分析才能生成完整報告
- OpenSpec change 相關資訊需要 change 目錄存在
- AI 分析基於收集的資料，可能需要人工補充判斷
- 多語言專案需確認偵測結果是否正確
