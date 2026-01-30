## Why

`ai-dev project init --force` 的反向同步功能有兩個問題：
1. **同步目標錯誤**：透過 `get_project_template_dir()` 取得目標，會優先指向 `~/.config/custom-skills/project-template/` 而非 repo 內的 `project-template/`，導致 repo 內的模板不會被更新。
2. **缺少排除機制**：使用 `shutil.copytree` 複製目錄時，會把 `.claude/settings.local.json`（包含個人授權設定）也複製進模板，不應出現在共享範本中。

## What Changes

- 修正反向同步目標：改為 `project_root / "project-template"`，確保更新 repo 內的模板
- 新增排除清單 `EXCLUDE_FROM_TEMPLATE`，在 `shutil.copytree` 中排除 `settings.local.json`
- 移除 `project-template/.claude/settings.local.json`（目前已存在於 repo 中）

## Capabilities

### New Capabilities

（無）

### Modified Capabilities

- `cli-distribution`: 修正 project init --force 的反向同步目標路徑與排除機制

## Impact

- 影響檔案：`script/commands/project.py`
- 影響指令：`ai-dev project init --force`
- 需刪除：`project-template/.claude/settings.local.json`
