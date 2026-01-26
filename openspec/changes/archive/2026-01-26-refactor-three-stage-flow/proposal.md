# Change: 重構三階段分發流程

## Why

目前的三階段流程存在架構問題：
- Stage 2 會將外部來源整合到 `~/.config/custom-skills`，但這應該由 git repo 控制
- 使用者的工具穩定性可能受開發中程式碼影響
- 開發者追蹤上游 repo 更新的流程不夠清晰

新架構目標：
1. **使用者穩定性**：工具目錄只從 `~/.config/custom-skills` 分發，內容由 git repo 控制
2. **開發者彈性**：在開發目錄執行時，可選擇整合外部來源到開發目錄

## What Changes

### 移除 Stage 2 整合流程
- `ai-dev clone` 不再執行 Stage 2（整合外部來源到 `~/.config/custom-skills`）
- `~/.config/custom-skills` 的內容完全由 git repo 管理

### 新增開發者模式整合
- 當在開發目錄（`$dev/custom-skills`，非 `~/.config/custom-skills`）執行 `ai-dev clone --sync-project` 時
- 將外部來源整合到該開發目錄
- 分發仍從 `~/.config/custom-skills` 執行，確保工具穩定性

### 流程簡化
- **使用者流程**：`ai-dev update` 拉取 repos → `ai-dev clone` 分發到工具
- **開發者流程**：`ai-dev update` 拉取 repos → `ai-dev clone --sync-project` 分發 + 整合到開發目錄

## Impact

- Affected specs: `setup-script`, `clone-command`
- Affected code: `script/utils/shared.py`, `script/commands/clone.py`
- **BREAKING**: `ai-dev clone` 不再執行 Stage 2 整合，開發者需明確使用 `--sync-project`
