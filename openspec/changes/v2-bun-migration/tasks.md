## 0. Git 分支與專案初始化

- [ ] 0.1 建立 `v1` 分支保存現有程式碼，建立 `v2` 開發分支
- [ ] 0.2 移除 Python 檔案 (script/, pyproject.toml, uv.lock, ai_dev.egg-info/, tests/)
- [ ] 0.3 建立 package.json (@valorvie/ai-dev, bin, scripts, files)
- [ ] 0.4 建立 tsconfig.json, bunfig.toml, biome.json
- [ ] 0.5 建立目錄結構 (src/cli/, src/core/, src/utils/, src/tui/, tests/)
- [ ] 0.6 建立入口點 src/cli.ts 與 src/cli/index.ts (Commander.js 骨架)
- [ ] 0.7 安裝依賴 (commander, chalk, yaml, ora, inquirer, typescript, biome)
- [ ] 0.8 驗證 `bun run src/cli.ts --version` 輸出 2.0.0

## 1. Utils 工具層

- [ ] 1.1 實作 src/utils/paths.ts — 所有配置路徑常數
- [ ] 1.2 撰寫 tests/utils/paths.test.ts 並驗證通過
- [ ] 1.3 實作 src/utils/system.ts — getOS, commandExists, runCommand, getBunVersion
- [ ] 1.4 撰寫 tests/utils/system.test.ts 並驗證通過
- [ ] 1.5 實作 src/utils/config.ts — readYaml, writeYaml
- [ ] 1.6 撰寫 tests/utils/config.test.ts 並驗證通過
- [ ] 1.7 實作 src/utils/git.ts — isGitRepo, gitInit, gitClone, gitPull, gitAddCommit, gitPullRebase, gitPush, detectLocalChanges
- [ ] 1.8 撰寫 tests/utils/git.test.ts 並驗證通過
- [ ] 1.9 實作 src/utils/manifest.ts — computeFileHash, computeDirHash
- [ ] 1.10 撰寫 tests/utils/manifest.test.ts 並驗證通過
- [ ] 1.11 實作 src/utils/shared.ts — NPM_PACKAGES, BUN_PACKAGES, REPOS, COPY_TARGETS, types
- [ ] 1.12 撰寫 tests/utils/shared.test.ts 並驗證通過

## 2. CLI 核心指令

- [ ] 2.1 實作 src/core/status-checker.ts + src/cli/status.ts — status 指令
- [ ] 2.2 撰寫 tests/core/status-checker.test.ts 並驗證通過
- [ ] 2.3 實作 src/core/installer.ts + src/cli/install.ts — install 指令
- [ ] 2.4 撰寫 tests/core/installer.test.ts 並驗證通過
- [ ] 2.5 實作 src/core/updater.ts + src/cli/update.ts — update 指令
- [ ] 2.6 實作 src/cli/clone.ts — clone 指令
- [ ] 2.7 實作 src/cli/list.ts — list 指令
- [ ] 2.8 實作 src/cli/toggle.ts — toggle 指令
- [ ] 2.9 實作 src/cli/add-repo.ts + src/utils/custom-repos.ts — add-repo 指令
- [ ] 2.10 實作 src/cli/add-custom-repo.ts — add-custom-repo 指令
- [ ] 2.11 實作 src/cli/update-custom-repo.ts — update-custom-repo 指令
- [ ] 2.12 實作 src/cli/test.ts, src/cli/coverage.ts, src/cli/derive-tests.ts — 測試指令群

## 3. 子命令組

- [ ] 3.1 實作 src/core/project-manager.ts + src/cli/project/ — project init, update
- [ ] 3.2 撰寫 tests/core/project-manager.test.ts 並驗證通過
- [ ] 3.3 實作 src/core/standards-manager.ts + src/cli/standards/ — standards status, list, switch, show, overlaps
- [ ] 3.4 撰寫 tests/core/standards-manager.test.ts 並驗證通過
- [ ] 3.5 實作 src/cli/hooks/ — hooks install, uninstall, status
- [ ] 3.6 實作 src/core/sync-engine.ts + src/cli/sync/ — sync init, push, pull, status, add, remove
- [ ] 3.7 撰寫 tests/core/sync-engine.test.ts 並驗證通過
- [ ] 3.8 安裝 better-sqlite3，實作 src/core/mem-sync.ts + src/cli/mem/ — mem register, push, pull, status, reindex
- [ ] 3.9 撰寫 tests/core/mem-sync.test.ts 並驗證通過

## 4. Manifest 與 Skill 複製系統

- [ ] 4.1 擴充 src/utils/manifest.ts — ManifestTracker, detect_conflicts, find_orphans, cleanup_orphans, backup_file
- [ ] 4.2 撰寫 tests/utils/manifest-tracker.test.ts 並驗證通過
- [ ] 4.3 在 src/utils/shared.ts 加入 copySkills, getAllSkillNames 函式
- [ ] 4.4 撰寫 tests/utils/copy-skills.test.ts 並驗證通過

## 5. TUI (Ink)

- [ ] 5.1 安裝 Ink 依賴 (ink, ink-select-input, ink-text-input, ink-spinner, react, @types/react)
- [ ] 5.2 建立 src/tui/index.tsx + src/tui/App.tsx — TUI 骨架與視圖路由
- [ ] 5.3 實作 src/tui/components/ — Header, TabBar, FilterBar, ActionBar
- [ ] 5.4 實作 src/tui/components/ResourceList.tsx + ResourceItem.tsx — 資源列表
- [ ] 5.5 實作 src/tui/hooks/useResources.ts + useKeyBindings.ts — 狀態管理與鍵盤快捷鍵
- [ ] 5.6 實作 src/tui/screens/MainScreen.tsx — 組合所有子元件
- [ ] 5.7 實作 src/tui/screens/PreviewScreen.tsx, ConfirmScreen.tsx, SettingsScreen.tsx — 輔助畫面
- [ ] 5.8 註冊 `ai-dev tui` 指令到 CLI

## 6. 整合測試與收尾

- [ ] 6.1 撰寫 tests/cli/smoke.test.ts — CLI 冒煙測試 (--version, --help, status)
- [ ] 6.2 執行全部測試 `bun test` 確認通過
- [ ] 6.3 執行 lint `bun run lint` 確認通過
- [ ] 6.4 執行型別檢查 `bunx tsc --noEmit` 確認通過
- [ ] 6.5 執行建置 `bun run build` 確認 dist/cli.js 產生
- [ ] 6.6 更新 README.md 安裝指南（npm/bun 全域安裝方式）
- [ ] 6.7 更新 CHANGELOG.md 加入 v2.0.0 變更記錄
- [ ] 6.8 合併 v2 → main，打 v2.0.0 tag
