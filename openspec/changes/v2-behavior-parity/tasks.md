# Tasks: v2 行為對齊 v1

## 1. Phase 0 — 共通基礎設施

- [ ] 1.1 安裝 cli-table3 dependency (`bun add cli-table3`)
- [ ] 1.2 建立 `src/utils/formatter.ts` — printTable, printSuccess, printError, printWarning, createSpinner, printPanel
- [ ] 1.3 為 formatter.ts 撰寫單元測試
- [ ] 1.4 建立 `src/utils/i18n.ts` — t(), setLocale(), getLocale(), en/zh-TW 字典框架
- [ ] 1.5 為 i18n.ts 撰寫單元測試
- [ ] 1.6 建立 `src/utils/backup.ts` — hasLocalChanges(), backupDirtyFiles(), restoreBackup()
- [ ] 1.7 為 backup.ts 撰寫單元測試
- [ ] 1.8 建立 `src/core/skill-distributor.ts` — distributeSkills(), 衝突偵測, developer mode symlink
- [ ] 1.9 為 skill-distributor.ts 撰寫單元測試
- [ ] 1.10 在 Commander.js program 加入 `--lang` 全域選項
- [ ] 1.11 跑全部測試確認無破壞

## 2. Phase 1 — P0 修復：clone

- [ ] 2.1 完全重寫 `src/cli/clone.ts` — 改為呼叫 skill-distributor 分發語意
- [ ] 2.2 加入 `--force`, `--skip-conflicts`, `--backup` 選項
- [ ] 2.3 加入 developer mode 偵測（在 custom-skills 目錄中使用 symlink）
- [ ] 2.4 加入 `--sync-project` / `--no-sync-project` 選項
- [ ] 2.5 加入 metadata 變更偵測
- [ ] 2.6 為 clone 命令撰寫整合測試
- [ ] 2.7 更新 smoke test 驗證新的 clone 行為

## 3. Phase 1 — P0 修復：install

- [ ] 3.1 加入前置需求檢查（Node.js >= 20, Git, gh, Bun）+ 安裝指引
- [ ] 3.2 加入 Claude Code 安裝狀態顯示
- [ ] 3.3 加入 `[i/total]` 進度計數器
- [ ] 3.4 加入已安裝套件版本偵測
- [ ] 3.5 加入建立所有 16 個目標目錄
- [ ] 3.6 補齊完整 REPOS 列表（obsidian-skills, anthropic-skills, everything-claude-code, auto-skill）
- [ ] 3.7 加入 OpenCode superpowers sync + symlink
- [ ] 3.8 加入自訂儲存庫 clone（讀取 repos.yaml）
- [ ] 3.9 整合 skill-distributor（copy_skills 分發）
- [ ] 3.10 加入已安裝 Skills 列表 + 命名衝突警告
- [ ] 3.11 加入 show_skills_npm_hint
- [ ] 3.12 加入 Shell Completion 安裝
- [ ] 3.13 加入 `--skip-skills`, `--sync-project` 選項
- [ ] 3.14 為 install 所有新功能撰寫測試
- [ ] 3.15 跑全部測試確認無破壞

## 4. Phase 1 — P0 修復：update

- [ ] 4.1 加入 Claude Code 更新
- [ ] 4.2 加入 `uds update` 和 `npx skills update`
- [ ] 4.3 加入 `[i/total]` 進度計數器
- [ ] 4.4 補齊完整 REPOS 列表
- [ ] 4.5 改用 `git fetch --all` + 遠端比較
- [ ] 4.6 加入本地修改偵測 + 自動備份（使用 backup.ts）
- [ ] 4.7 改用 `git reset --hard origin/{branch}` 取代 `git pull --ff-only`
- [ ] 4.8 加入自訂儲存庫更新
- [ ] 4.9 加入 OpenCode superpowers symlink 刷新
- [ ] 4.10 加入 Plugin Marketplace 更新 + `--skip-plugins` 選項
- [ ] 4.11 加入更新摘要 + 缺失儲存庫警告
- [ ] 4.12 為 update 所有新功能撰寫測試
- [ ] 4.13 跑全部測試確認無破壞

## 5. Phase 2 — P1 修復：sync

- [ ] 5.1 重寫 SyncEngine.init() — 加入 git clone/init + LFS 偵測 + .gitignore 寫入
- [ ] 5.2 重寫 SyncEngine.push() — 改用 git add/commit/push + LFS + plugin manifest
- [ ] 5.3 重寫 SyncEngine.pull() — 加入本地變更偵測 + inquirer 3 選項互動選單
- [ ] 5.4 加入 push `--force` 和 pull `--no-delete`, `--force` 選項
- [ ] 5.5 重寫 SyncEngine.status() — 加入本地變更統計 + 遠端 commit 落後數
- [ ] 5.6 CLI 層加入格式化輸出（非 JSON 模式）
- [ ] 5.7 為所有 sync 子命令撰寫測試
- [ ] 5.8 跑全部測試確認無破壞

## 6. Phase 2 — P1 修復：mem

- [ ] 6.1 實作 MemSync.push() — HTTP API 上傳 + hash dedup + 分批上傳
- [ ] 6.2 實作 MemSync.pull() — HTTP API 拉取 + paginated pull + merge
- [ ] 6.3 新增 `auto` 子命令 — launchd/cron/systemd 排程
- [ ] 6.4 加強 MemSync.status() — 加入遠端同步狀態 + 待推送數量
- [ ] 6.5 CLI 層加入格式化輸出（非 JSON 模式）
- [ ] 6.6 為所有 mem 子命令撰寫測試
- [ ] 6.7 跑全部測試確認無破壞

## 7. Phase 2 — P1 修復：project

- [ ] 7.1 加入 .gitignore / .gitattributes 智慧合併（逐行比對）
- [ ] 7.2 加入備份機制（覆蓋前自動備份）
- [ ] 7.3 加入 `--force` 選項
- [ ] 7.4 加入開發者反向同步（sync_project_to_template）
- [ ] 7.5 加入 `openspec update` 整合
- [ ] 7.6 加入 `--only` 選項過濾
- [ ] 7.7 CLI 層加入格式化輸出
- [ ] 7.8 為所有 project 子命令撰寫測試
- [ ] 7.9 跑全部測試確認無破壞

## 8. Phase 2 — P1 修復：standards

- [ ] 8.1 實作 compute_disabled_items() 差集計算
- [ ] 8.2 switch 時自動生成 disabled.yaml + 搬移檔案到 .disabled/
- [ ] 8.3 新增 `sync` 子命令
- [ ] 8.4 overlaps 加入格式化表格輸出
- [ ] 8.5 所有子命令加入格式化輸出
- [ ] 8.6 為 standards 所有修改撰寫測試
- [ ] 8.7 跑全部測試確認無破壞

## 9. Phase 2 — P1 修復：add-repo

- [ ] 9.1 加入格式偵測（UDS / claude-code-native / skills-repo）
- [ ] 9.2 加入 upstream/sources.yaml 寫入
- [ ] 9.3 加入 `--analyze` 選項
- [ ] 9.4 加入已存在 repo 重複檢查
- [ ] 9.5 為 add-repo 撰寫測試
- [ ] 9.6 跑全部測試確認無破壞

## 10. Phase 3 — P2/P3 UX 對齊

- [ ] 10.1 status 命令：格式化表格輸出 + 上游同步狀態 + 儲存庫遠端比較
- [ ] 10.2 list 命令：格式化表格 + 啟用/停用狀態 + 來源 + `--hide-disabled`
- [ ] 10.3 add-custom-repo：加入 repo 結構驗證 + `--fix` 選項
- [ ] 10.4 update-custom-repo：改用 fetch + backup + reset + 更新摘要
- [ ] 10.5 toggle：加入 target/type 有效組合驗證 + `--list` 格式化
- [ ] 10.6 hooks：加入 uninstall 確認提示 + 實際 plugin 複製
- [ ] 10.7 test/coverage：可選改善（自動偵測框架、--source）
- [ ] 10.8 為所有 P2/P3 修改撰寫測試
- [ ] 10.9 跑全部測試確認無破壞

## 11. 收尾

- [ ] 11.1 補充所有 i18n 字串（en + zh-TW）
- [ ] 11.2 全部測試通過 + lint clean + tsc clean
- [ ] 11.3 更新 smoke test 覆蓋所有新選項
- [ ] 11.4 手動測試所有 17 個指令
- [ ] 11.5 更新 CHANGELOG.md
