# Tasks: add-pr-workflow

## Phase 1: 核心模組建立

- [x] **Task 1.1**: 建立 `pr.md` 主控制模組
  - 定義參數解析邏輯
  - 建立流程控制結構
  - 實作前置檢查（分支檢查、gh CLI 檢查）
  - **驗證**: 文件結構完整，參數定義清晰

- [x] **Task 1.2**: 建立 `pr-analyze.md` 分析模組
  - 實作 commit 範圍讀取
  - 實作 diff 統計
  - 實作 PR 標題/內文生成邏輯
  - **驗證**: 生成的摘要格式正確

## Phase 2: 路由整合

- [x] **Task 2.1**: 更新 `SKILL.md` 路由邏輯
  - 新增 `pr` 子指令路由
  - 保持與現有路由的一致性
  - **驗證**: 路由邏輯完整，無遺漏情境

- [x] **Task 2.2**: 更新 `git-commit.md` 指令定義
  - 新增 `pr` 相關參數說明
  - 新增常用組合範例
  - **驗證**: 文件格式一致，範例可執行

## Phase 3: 測試與文件

- [ ] **Task 3.1**: 手動測試驗證
  - 測試基本 `git-commit pr` 流程
  - 測試 `--from` 和 `--range` 參數
  - 測試 `--no-squash` 參數
  - 測試 `--direct` 參數
  - **驗證**: 所有情境正常運作
  - **備註**: 需要在實際 Git 環境中執行測試

- [x] **Task 3.2**: 更新 CHANGELOG
  - 記錄新功能
  - **驗證**: CHANGELOG 格式正確

## Dependencies

```
Task 1.1 ─┬─► Task 2.1 ─► Task 2.2 ─► Task 3.1 ─► Task 3.2
Task 1.2 ─┘
```

Task 1.1 和 1.2 可並行執行。

## Notes

- 所有模組使用 Markdown 格式
- 遵循現有 `git-commit-custom` 的風格
- PR 建立依賴 `gh` CLI
