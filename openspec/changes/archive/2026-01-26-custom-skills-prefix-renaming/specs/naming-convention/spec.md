# Naming Convention Spec

本規格定義專案專屬工具的命名慣例。

---

## ADDED Requirements

### Requirement: 專案專屬工具前綴命名

專案專屬的 Skills 和 Commands **必須 (SHALL)** 使用 `custom-skills-` 前綴命名。

命名格式：`custom-skills-<function>`

其中 `<function>` 為工具的功能描述，使用 kebab-case。

#### Scenario: Skill 目錄命名

- **WHEN** 檢視 `skills/` 目錄下的專案專屬工具
- **THEN** 目錄名稱以 `custom-skills-` 開頭

#### Scenario: Skill YAML frontmatter 命名

- **WHEN** 檢視專案專屬 Skill 的 SKILL.md
- **THEN** frontmatter 中的 `name` 欄位以 `custom-skills-` 開頭

#### Scenario: Command 檔案命名

- **WHEN** 檢視 `commands/*/` 目錄下的專案專屬命令
- **THEN** 檔案名稱以 `custom-skills-` 開頭

---

## RENAMED Requirements

### Requirement: git-commit-custom → custom-skills-git-commit

- **FROM**: `git-commit-custom`
- **TO**: `custom-skills-git-commit`

涉及檔案：
- `skills/git-commit-custom/` → `skills/custom-skills-git-commit/`
- `skills/git-commit-custom/SKILL.md` name 欄位
- `commands/claude/git-commit.md` → `commands/claude/custom-skills-git-commit.md`
- `commands/antigravity/git-commit.md` → `commands/antigravity/custom-skills-git-commit.md`

#### Scenario: Skill 目錄已重命名

- **WHEN** 執行 `ls skills/ | grep git-commit`
- **THEN** 結果為 `custom-skills-git-commit`，不包含 `git-commit-custom`

#### Scenario: Command 檔案已重命名

- **WHEN** 執行 `ls commands/claude/ | grep git-commit`
- **THEN** 結果為 `custom-skills-git-commit.md`，不包含 `git-commit.md`

### Requirement: tool-overlap-analyzer → custom-skills-tool-overlap-analyzer

- **FROM**: `tool-overlap-analyzer`
- **TO**: `custom-skills-tool-overlap-analyzer`

涉及檔案：
- `skills/tool-overlap-analyzer/` → `skills/custom-skills-tool-overlap-analyzer/`
- `skills/tool-overlap-analyzer/SKILL.md` name 欄位

#### Scenario: Skill 目錄已重命名

- **WHEN** 執行 `ls skills/ | grep overlap`
- **THEN** 結果為 `custom-skills-tool-overlap-analyzer`，不包含 `tool-overlap-analyzer`

### Requirement: upstream-sync command → custom-skills-upstream-sync

- **FROM**: `commands/claude/upstream-sync.md`
- **TO**: `commands/claude/custom-skills-upstream-sync.md`

#### Scenario: Command 檔案已重命名

- **WHEN** 執行 `ls commands/claude/ | grep upstream`
- **THEN** 結果為 `custom-skills-upstream-sync.md`，不包含 `upstream-sync.md`

---

## Cross-Reference Update Requirements

### Requirement: 所有引用必須更新

重命名後，所有功能性引用 **必須 (SHALL)** 更新為新名稱。

排除範圍：
- `CHANGELOG.md`（歷史記錄）
- `openspec/changes/archive/*`（歸檔文件）

#### Scenario: 無殘留舊名引用

- **WHEN** 執行 grep 搜尋舊名（排除 archive 和 CHANGELOG）
- **THEN** 搜尋結果為空

```bash
grep -r "git-commit-custom" --include="*.md" | grep -v "archive/" | grep -v "CHANGELOG"
grep -r "tool-overlap-analyzer" --include="*.md" | grep -v "archive/" | grep -v "CHANGELOG"
grep -r "/git-commit[^-]" --include="*.md" | grep -v "archive/" | grep -v "CHANGELOG"
grep -r "/upstream-sync[^-]" --include="*.md" | grep -v "archive/" | grep -v "CHANGELOG"
```

#### Scenario: 命令調用更新

- **WHEN** 檢視 `commands/claude/custom-skills-git-commit.md` 內容
- **THEN** 調用的 skill 名稱為 `custom-skills-git-commit`
