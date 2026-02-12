## ADDED Requirements

### Requirement: Auto-Skill Hooks 獨立插件

系統 SHALL 提供獨立的 `auto-skill-hooks` 插件，負責在 SessionStart 時注入知識庫與經驗索引。此插件與 ecc-hooks 職責分離，可獨立啟用/停用。

#### Scenario: 插件獨立運作

- **WHEN** 啟用 `auto-skill-hooks@custom-skills` 插件
- **THEN** 插件的 SessionStart hook 獨立於 ecc-hooks 的 SessionStart hook 執行
- **AND** 停用 auto-skill-hooks 不影響 ecc-hooks 的記憶持久化功能
- **AND** 停用 ecc-hooks 不影響 auto-skill-hooks 的知識注入功能

#### Scenario: 插件註冊

- **WHEN** 安裝 auto-skill-hooks 插件
- **THEN** 在 `~/.claude/settings.json` 的 `enabledPlugins` 新增 `"auto-skill-hooks@custom-skills": true`
