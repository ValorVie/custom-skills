## 1. Skills 目錄重命名

- [x] 1.1 重命名 `skills/git-commit-custom/` → `skills/custom-skills-git-commit/`
- [x] 1.2 更新 `skills/custom-skills-git-commit/SKILL.md` 的 name 欄位為 `custom-skills-git-commit`
- [x] 1.3 重命名 `skills/tool-overlap-analyzer/` → `skills/custom-skills-tool-overlap-analyzer/`
- [x] 1.4 更新 `skills/custom-skills-tool-overlap-analyzer/SKILL.md` 的 name 欄位為 `custom-skills-tool-overlap-analyzer`

## 2. Commands 檔案重命名

- [x] 2.1 重命名 `commands/claude/git-commit.md` → `commands/claude/custom-skills-git-commit.md`
- [x] 2.2 重命名 `commands/antigravity/git-commit.md` → `commands/antigravity/custom-skills-git-commit.md`
- [x] 2.3 重命名 `commands/claude/upstream-sync.md` → `commands/claude/custom-skills-upstream-sync.md`

## 3. Commands 內部引用更新

- [x] 3.1 更新 `commands/claude/custom-skills-git-commit.md` 調用的 skill 名稱為 `custom-skills-git-commit`
- [x] 3.2 更新 `commands/antigravity/custom-skills-git-commit.md` 調用的 skill 名稱為 `custom-skills-git-commit`

## 4. Skills 內部引用更新

- [x] 4.1 更新 `skills/custom-skills-git-commit/pr-analyze.md` 的路徑引用
- [x] 4.2 更新 `skills/custom-skills-upstream-sync/SKILL.md` 的 name 欄位與腳本路徑
- [x] 4.3 更新 `skills/custom-skills-upstream-compare/SKILL.md` 的 `/upstream-sync` 引用
- [x] 4.4 更新 `skills/custom-skills-dev/SKILL.md` 的 `/upstream-sync` 引用

## 5. 文檔引用更新

- [x] 5.1 更新 `README.md` 的命令列表
- [x] 5.2 更新 `commands/claude/README.md` 的命令列表
- [x] 5.3 更新 `upstream/README.md` 的所有 `/upstream-sync` 引用
- [x] 5.4 更新 `docs/AI開發環境設定指南.md` 的命令列表
- [x] 5.5 更新 `docs/dev-guide/copy-architecture.md` 的 `/upstream-sync` 引用
- [x] 5.6 更新 `docs/report/tool-overlap-analysis-2026-01-26.md` 的工具名稱引用

## 6. CHANGELOG 更新

- [x] 6.1 更新 CHANGELOG.md，記錄 breaking change 與遷移指引

## 7. 驗證

- [x] 7.1 執行 grep 驗證無殘留舊名引用（排除 archive 和 CHANGELOG）
- [x] 7.2 確認所有重命名的工具可正常調用

## 8. 額外更新（驗證時發現）

- [x] 8.1 更新 `.standards/profiles/overlaps.yaml`
- [x] 8.2 更新 `project-template/.standards/profiles/overlaps.yaml`
- [x] 8.3 更新 `skills/custom-skills-tool-overlap-analyzer/SKILL.md` 中的範例
- [x] 8.4 更新 `script/commands/add_repo.py` 中的引用
- [x] 8.5 更新 `build/lib/script/commands/add_repo.py` 中的引用
