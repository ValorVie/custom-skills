## 1. 排除機制

- [x] 1.1 在 `script/commands/project.py` 新增 `EXCLUDE_FROM_TEMPLATE` 常數（包含 `settings.local.json`）
- [x] 1.2 新增 `_template_ignore()` 函式，返回 `shutil.copytree` 可用的 ignore 回調

## 2. 修正反向同步目標

- [x] 2.1 修改 `init()` 函式：反向同步時使用 `project_root / "project-template"` 取代 `get_project_template_dir()`
- [x] 2.2 修改 `_sync_to_project_template()` 中的 `shutil.copytree` 呼叫加入 `ignore` 參數

## 3. 正向同步排除

- [x] 3.1 修改 `init()` 正向複製中的 `shutil.copytree` 呼叫加入相同的 `ignore` 參數

## 4. 清理

- [x] 4.1 刪除 `project-template/.claude/settings.local.json`

## 5. 驗證

- [x] 5.1 確認 `project-template/.claude/` 目錄不包含 `settings.local.json`
- [x] 5.2 確認 `_template_ignore()` 正確排除指定檔案
