# Proposal: TDD Test Generation

## Summary

建立 `/custom-skills-derive-tests` 命令和 `ai-dev derive-tests` CLI，從 OpenSpec specs 的 WHEN/THEN 場景生成完整可執行的測試程式碼，而非只是 `[TODO]` 標記的骨架。

## Motivation

目前的 `/derive-tdd` 命令只生成測試骨架：

```python
def test_should_expected_behavior(self):
    # Arrange
    # [TODO] Set up test data

    # Act
    # [TODO] Call method under test

    # Assert
    # [TODO] Add assertions
    assert True  # Placeholder
```

開發者仍需手動：
1. 理解 specs 中的場景
2. 撰寫 Arrange（測試資料準備）
3. 撰寫 Act（呼叫被測函數）
4. 撰寫 Assert（驗證結果）

這違反了 TDD 的自動化精神，且容易遺漏場景。

## Scope

### In Scope

- `/custom-skills-derive-tests` Claude Code 命令
- `ai-dev derive-tests` CLI 命令
- 讀取 OpenSpec specs 檔案
- AI 生成完整 pytest 測試程式碼
- 支援 Python 專案

### Out of Scope

- 其他語言的測試生成
- 複雜的 mock 自動生成
- 與 CI/CD 整合

## Design

### 架構原則（與其他子提案一致）

```
┌─────────────────────────────────────────────────────────────┐
│                 Claude Code Command                          │
│  /custom-skills-derive-tests                                 │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Prompt 定義：                                            ││
│  │ 1. 執行 CLI 讀取 specs 內容                              ││
│  │ 2. AI 理解 WHEN/THEN 場景語義                           ││
│  │ 3. AI 生成完整測試程式碼                                 ││
│  │ 4. AI 決定測試檔案位置並寫入                            ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 CLI 命令 (ai-dev derive-tests)              │
│  - 找到指定路徑的 specs 檔案                                │
│  - 讀取並輸出 specs 內容                                    │
│  - 不做解析或生成（交給 AI）                                │
└─────────────────────────────────────────────────────────────┘
```

**原則**：
- 腳本只負責「讀取」specs 檔案
- 語義理解和程式碼生成交給 AI（更有彈性、能理解上下文）

### 輸入：OpenSpec Spec 格式

```markdown
### Requirement: 檢測檔案權限變更

#### Scenario: 偵測 644 到 755 的權限變更
- **WHEN** 檔案在 git 記錄為 mode 100644
- **AND** 工作目錄的檔案為 mode 100755
- **AND** 檔案內容未變更
- **THEN** 系統將該檔案分類為「權限變更」
```

### 輸出：完整 pytest 測試（由 AI 生成）

```python
class TestDetectModeChanges:
    """Requirement: 檢測檔案權限變更"""

    def test_detect_644_to_755_mode_change(self, tmp_path):
        """Scenario: 偵測 644 到 755 的權限變更"""
        # Arrange
        # WHEN 檔案在 git 記錄為 mode 100644
        # AND 工作目錄的檔案為 mode 100755
        # AND 檔案內容未變更
        repo = setup_git_repo(tmp_path)
        test_file = repo / "test.txt"
        test_file.write_text("content")
        subprocess.run(["git", "add", "."], cwd=repo)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo)
        test_file.chmod(0o755)

        # Act
        changes = detect_metadata_changes(repo)

        # Assert
        # THEN 系統將該檔案分類為「權限變更」
        assert "test.txt" in changes.mode_changes
```

### AI 轉換指引

AI 在生成測試時參考以下對應關係：

| Spec 元素 | 測試元素 |
|-----------|----------|
| `### Requirement:` | `class Test{Name}:` |
| `#### Scenario:` | `def test_{scenario_name}():` |
| `- **WHEN**` | Arrange 區塊 |
| `- **AND**` | Arrange 區塊（續） |
| `- **THEN**` | Assert 區塊 |

### 檔案結構

```
script/
├── commands/
│   └── derive_tests.py      # ai-dev derive-tests CLI
└── utils/
    └── spec_reader.py       # Spec 檔案讀取工具

commands/claude/
└── custom-skills-derive-tests.md    # Claude Code 命令定義
```

### 命令介面

```bash
# CLI 用法
ai-dev derive-tests specs/                    # 讀取 specs 內容
ai-dev derive-tests openspec/changes/xxx/specs/  # 指定路徑

# Claude Code 命令
/custom-skills-derive-tests specs/            # 讀取 specs 並生成測試
/custom-skills-derive-tests --output tests/   # 指定輸出目錄
```

## Capabilities

1. **讀取 specs 檔案** - CLI 找到並輸出 specs 內容
2. **AI 理解場景語義** - 理解 WHEN/THEN 的業務含義
3. **AI 生成測試類別** - Requirement → TestClass
4. **AI 生成測試方法** - Scenario → test method
5. **AI 填寫 AAA 區塊** - 根據場景語義和專案程式碼生成實作
6. **AI 決定檔案位置** - 根據專案結構決定測試檔案路徑

## Dependencies

- OpenSpec specs 結構
- pytest
- 專案程式碼結構（用於 import）

## Limitations

- 生成的測試可能需要微調
- 複雜的 mock 場景需手動補充
- 依賴 AI 理解場景語義和專案程式碼

## Related Specs

- tdd-workflow-automation（主提案）
- tdd-test-execution（測試執行子提案）
- tdd-coverage-python（覆蓋率子提案）
- 現有 `/derive-tdd` 命令
- forward-derivation skill
