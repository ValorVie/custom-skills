## ADDED Requirements

### Requirement: 反向同步排除機制

`ai-dev project init --force` 的反向同步 SHALL 排除不屬於共享範本的檔案，並將同步目標固定為 repo 內的 `project-template/`。

#### Scenario: 反向同步目標為 repo 內的 project-template

- **WHEN** 在 custom-skills 專案中執行 `ai-dev project init --force`
- **THEN** 同步目標 SHALL 為 `cwd/project-template/`
- **AND** 不使用 `get_project_template_dir()`（避免指向 `~/.config`）

#### Scenario: 排除個人設定檔

- **WHEN** 反向同步複製目錄（如 `.claude/`）到 `project-template/`
- **THEN** SHALL 排除 `settings.local.json`
- **AND** 排除清單定義於 `EXCLUDE_FROM_TEMPLATE` 常數

#### Scenario: 正向 init 也排除個人設定檔

- **WHEN** 從 project-template 複製到目標專案
- **THEN** SHALL 同樣排除 `settings.local.json`
- **AND** 使用相同的排除機制
