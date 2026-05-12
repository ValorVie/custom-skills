## ADDED Requirements

### Requirement: gitattributes 支援 LFS pattern

`generate_gitattributes()` SHALL 接受 `lfs_patterns` 參數（`list[str] | None`），當提供非空清單時，在現有規則後附加 Git LFS track 規則。`write_gitattributes()` SHALL 同步接受並傳遞 `lfs_patterns` 參數。

#### Scenario: 無 LFS pattern 時維持原有行為
- **WHEN** 呼叫 `generate_gitattributes()` 或 `generate_gitattributes(lfs_patterns=None)`
- **THEN** 輸出 SHALL 僅包含 `*.jsonl merge=union` 和 `*.md text eol=lf`，與原有行為相同

#### Scenario: 有 LFS pattern 時附加規則
- **WHEN** 呼叫 `generate_gitattributes(lfs_patterns=["*.sqlite3", "*.db"])`
- **THEN** 輸出 SHALL 在原有規則後附加 `*.sqlite3 filter=lfs diff=lfs merge=lfs -text` 和 `*.db filter=lfs diff=lfs merge=lfs -text`

#### Scenario: write_gitattributes 傳遞 lfs_patterns
- **WHEN** 呼叫 `write_gitattributes(repo_dir, lfs_patterns=["*.sqlite3"])`
- **THEN** 寫入的 `.gitattributes` SHALL 包含 LFS track 規則
