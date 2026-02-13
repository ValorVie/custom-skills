## 1. OpenCode Plugin Hooks 擴充

- [x] 1.1 讀取 ECC 上游 `ecc-hooks.ts` 並提取 file.edited / session.idle / file.watcher.updated / permission.asked / todo.updated 事件處理邏輯
- [x] 1.2 擴充 `plugins/ecc-hooks-opencode/plugin.ts`，新增 5 個 OpenCode 獨有事件的處理函式
- [x] 1.3 實作 file.edited 的條件式格式化（檢查 Prettier 是否安裝後才執行）
- [x] 1.4 實作 session 級別的編輯追蹤狀態管理（記錄已編輯檔案清單）
- [x] 1.5 實作 session.idle 的彙總稽核報告輸出
- [x] 1.6 實作 file.watcher.updated 的外部變更偵測與通知
- [x] 1.7 實作 permission.asked 的非侵入式稽核記錄
- [x] 1.8 實作 todo.updated 的任務進度追蹤
- [x] 1.9 驗證擴充後的 plugin 可正常載入，不影響現有 tool.execute / session 事件處理

## 2. OpenCode 自訂工具

- [x] 2.1 移植 ECC `run-tests.ts` 到 `.opencode/tools/run-tests.ts`，適配本專案結構
- [x] 2.2 移植 ECC `check-coverage.ts` 到 `.opencode/tools/check-coverage.ts`
- [x] 2.3 移植 ECC `security-audit.ts` 到 `.opencode/tools/security-audit.ts`
- [x] 2.4 更新 `.opencode/tools/index.ts` 匯出新工具
- [x] 2.5 更新 `.opencode/package.json` 加入必要依賴

## 3. Orchestrate 命令

- [x] 3.1 建立 agent 名稱對映表（ECC → Custom-Skills），確認所有引用的 agent 在本專案中存在
- [x] 3.2 建立 `commands/claude/orchestrate.md`，包含 feature / bugfix / refactor / security 四種工作流模板
- [x] 3.3 建立 `commands/opencode/orchestrate.md`，功能等效 Claude 版本
- [x] 3.4 定義 handoff 文件格式（任務摘要、變更清單、待處理事項、檔案路徑）
- [x] 3.5 在命令中加入自訂工作流支援（使用者可指定任意 agent 序列）

## 4. PM2 命令

- [x] 4.1 移植 ECC `pm2.md` 到 `commands/claude/pm2.md`，替換 `.claude/` 路徑為本專案結構
- [x] 4.2 建立 `commands/opencode/pm2.md`，功能等效 Claude 版本
- [x] 4.3 驗證自動偵測邏輯涵蓋 Node.js（Vite / Next.js / Express）和 Python（Django / FastAPI）框架
- [x] 4.4 驗證 ecosystem.config.cjs 生成格式正確且可被 pm2 直接使用

## 5. 整合驗證與文件

- [x] 5.1 更新 `.opencode/index.ts` 匯出 hooks 和 tools
- [x] 5.2 執行 `ai-dev clone` 驗證 OpenCode plugin 可正確分發到 `~/.config/opencode/plugins/`（需先 commit 並同步至 ~/.config/custom-skills/）
- [x] 5.3 更新 upstream `last-sync.yaml` 中 everything-claude-code 的同步狀態
- [x] 5.4 更新 CHANGELOG.md 記錄新增的 hooks、tools、commands
