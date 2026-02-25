## MODIFIED Requirements

### Requirement: CLI 分發機制
ai-dev CLI SHALL 以 npm scoped package (`@valorvie/ai-dev`) 分發，取代 Python egg/wheel 格式。

#### Scenario: 套件包含必要檔案
- **WHEN** 套件發佈到 npm
- **THEN** 包含 `src/`、`dist/`、`skills/`、`commands/`、`agents/` 目錄

#### Scenario: 更新 CLI
- **WHEN** 使用者執行 `bun update -g @valorvie/ai-dev`
- **THEN** CLI 更新到最新版本

## REMOVED Requirements

### Requirement: Python egg 分發
**Reason**: 以 npm package 取代
**Migration**: 移除 `pyproject.toml`、`setup.cfg`、`ai_dev.egg-info/`
