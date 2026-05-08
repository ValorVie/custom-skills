# Issue Tracker

本 repo 的工作項目 canonical 出口。

## Canonical 出口

- **主**：`openspec/changes/<change-id>/tasks.md`
  - 所有正式變更（功能、重構、規格修改）走 OpenSpec 流程。
  - 每筆任務的 ready 狀態以 tasks.md 內的 checkbox 與標註為準。
- **輔**：GitHub issues（`ValorVie/custom-skills`）
  - 用於對外回報的 bug、外部使用者提出的需求、尚未進入 OpenSpec 的雜項討論。
  - 一旦進入正式變更，於 issue 內附 OpenSpec change id，並以 OpenSpec 為 canonical。

## 不使用

- 不另開本地 Markdown todo 列表作為 canonical 出口。
- 不引入第三方 tracker（Jira、Linear 等）。

## 參考路徑

- OpenSpec 變更：`openspec/changes/`
- OpenSpec 規格：`openspec/specs/`
- 專案總述：`openspec/project.md`
- GitHub：`https://github.com/ValorVie/custom-skills`
