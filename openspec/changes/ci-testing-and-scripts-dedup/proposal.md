# Proposal: CI 測試流程與 Scripts 去重

## Problem

1. CI/CD 未執行任何測試（Jest、pytest），無法自動驗證程式碼品質
2. Python `script/` 目錄缺少單元測試
3. Python `shell=True` 使用需安全審查
4. `ecc-hooks` 與 `ecc-hooks-opencode` 維護兩份相同 scripts，容易不同步
5. Markdown 文件缺少格式驗證

## Proposed Solution

### Phase 1: CI 測試 Workflow
- 新增 `.github/workflows/test.yml`
- 執行 Jest（plugins/ecc-hooks）與 pytest（tests/）

### Phase 2: Python 安全改善
- 審查 `shell=True` 使用點，改為安全替代方案
- 為 `script/utils/custom_repos.py` 與 `script/commands/add_custom_repo.py` 補充測試

### Phase 3: Scripts 去重
- 評估 symlink vs CI diff-check 方案
- 實作選定方案

### Phase 4: Markdown 驗證（可選）
- 加入 markdownlint 與 YAML front matter 驗證

## Scope

- 不涉及功能變更
- 聚焦於品質基礎設施與維護性改善
