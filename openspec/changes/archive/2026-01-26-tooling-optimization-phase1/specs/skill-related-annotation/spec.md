## ADDED Requirements

### Requirement: related 欄位格式

Skill 的 YAML frontmatter 必須支援 `related` 欄位，該欄位包含一個相關工具物件的陣列。

陣列中的每個物件必須包含：
- `name`：相關 Skill 的名稱（字串，必填）
- `relationship`：描述工具之間關係的簡短說明（字串，必填）

#### Scenario: 有效的 related 欄位含多個項目

- **WHEN** Skill 包含：
  ```yaml
  related:
    - name: git-commit-custom
      relationship: Implementation module
    - name: git-workflow-guide
      relationship: Branching strategy guide
  ```
- **THEN** 該 Skill 有效，related 欄位被保留

#### Scenario: related 欄位為選填

- **WHEN** Skill 沒有包含 `related` 欄位
- **THEN** 該 Skill 仍然有效（related 欄位非必填）

#### Scenario: 空的 related 陣列

- **WHEN** Skill 包含 `related: []`
- **THEN** 該 Skill 有效（允許空陣列）

### Requirement: related 欄位放置位置

`related` 欄位必須放置在 YAML frontmatter 區段中，與 `name` 和 `description` 同層級。

#### Scenario: 正確放置於 frontmatter

- **WHEN** Skill 結構如下：
  ```yaml
  ---
  name: commit-standards
  description: Format commit messages...
  related:
    - name: git-commit-custom
      relationship: Implementation module
  ---
  ```
- **THEN** 結構有效

### Requirement: Git 提交群組標註

以下 Skills 必須包含相互連結的 `related` 標註：
- `commit-standards`
- `git-commit-custom`
- `git-workflow-guide`

#### Scenario: commit-standards 包含 related 標註

- **WHEN** 檢視 `skills/commit-standards/SKILL.md`
- **THEN** frontmatter 包含 `git-commit-custom` 和 `git-workflow-guide` 的 related 項目

#### Scenario: git-commit-custom 包含 related 標註

- **WHEN** 檢視 `skills/git-commit-custom/SKILL.md`
- **THEN** frontmatter 包含 `commit-standards` 和 `git-workflow-guide` 的 related 項目

#### Scenario: git-workflow-guide 包含 related 標註

- **WHEN** 檢視 `skills/git-workflow-guide/SKILL.md`
- **THEN** frontmatter 包含 `commit-standards` 和 `git-commit-custom` 的 related 項目

### Requirement: 代碼審查群組標註

以下 Skills 必須包含相互連結的 `related` 標註：
- `code-review-assistant`
- `checkin-assistant`

#### Scenario: code-review-assistant 包含 related 標註

- **WHEN** 檢視 `skills/code-review-assistant/SKILL.md`
- **THEN** frontmatter 包含 `checkin-assistant` 的 related 項目

#### Scenario: checkin-assistant 包含 related 標註

- **WHEN** 檢視 `skills/checkin-assistant/SKILL.md`
- **THEN** frontmatter 包含 `code-review-assistant` 的 related 項目

### Requirement: 測試群組標註

以下 Skills 必須包含相互連結的 `related` 標註：
- `testing-guide`
- `tdd-workflow`
- `test-coverage-assistant`

#### Scenario: testing-guide 包含 related 標註

- **WHEN** 檢視 `skills/testing-guide/SKILL.md`
- **THEN** frontmatter 包含 `tdd-workflow` 和 `test-coverage-assistant` 的 related 項目

#### Scenario: tdd-workflow 包含 related 標註

- **WHEN** 檢視 `skills/tdd-workflow/SKILL.md`
- **THEN** frontmatter 包含 `testing-guide` 和 `test-coverage-assistant` 的 related 項目

#### Scenario: test-coverage-assistant 包含 related 標註

- **WHEN** 檢視 `skills/test-coverage-assistant/SKILL.md`
- **THEN** frontmatter 包含 `testing-guide` 和 `tdd-workflow` 的 related 項目
