# Beads 工作脈絡

## 啟動

- 執行 `bd prime --memories-only --export`，略過本覆寫並讀取目前專案的持久記憶。
- 執行 `bd ready`，確認可接續的工作。

## Git 權限

- 使用者明確要求 `commit`，即構成本機 Git commit 的清楚授權。
- 提交前檢查工作樹，只 stage 本輪相關檔案，不夾帶其他變更。
- 除非使用者明確要求 `push`，否則不得推送遠端。

