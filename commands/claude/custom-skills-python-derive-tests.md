---
description: 從 OpenSpec specs 生成完整 pytest 測試程式碼
allowed-tools: Bash(ai-dev derive-tests:*), Bash(uv run:*), Read, Write, Glob, Grep
argument-hint: "<specs-path> [--output <tests-dir>]"
---

# Custom Skills Derive Tests | 測試生成

從 OpenSpec specs 的 WHEN/THEN 場景生成完整可執行的 pytest 測試程式碼。

## Workflow | 工作流程

### Step 1: 讀取 Specs

執行 CLI 讀取 specs 內容：

```bash
uv run ai-dev derive-tests <specs-path>
```

取得 specs 的原始內容，包含 WHEN/THEN 場景定義。

### Step 2: 理解場景語義

分析 specs 中的 WHEN/THEN 格式：

| Spec 元素 | 語義 |
|-----------|------|
| `### Requirement:` | 功能需求，對應測試類別 |
| `#### Scenario:` | 測試場景，對應測試方法 |
| `- **WHEN**` | 前置條件（Arrange） |
| `- **AND**` | 附加條件（Arrange 續） |
| `- **THEN**` | 預期結果（Assert） |

理解場景的業務語義，將其對應到程式碼概念。

### Step 3: 讀取專案程式碼

找到被測函數/類別的位置和簽名：

1. 使用 Glob 找到相關的程式碼檔案
2. 使用 Read 讀取被測模組
3. 理解函數簽名和預期行為

### Step 4: 生成測試程式碼

根據場景生成完整的 pytest 測試程式碼（AAA 格式）：

```python
class TestRequirementName:
    """Requirement: <需求名稱>"""

    def test_scenario_name(self):
        """Scenario: <場景名稱>"""
        # Arrange
        # WHEN <前置條件>
        # AND <附加條件>
        <設置測試資料>

        # Act
        <呼叫被測函數>

        # Assert
        # THEN <預期結果>
        <驗證結果>
```

**轉換規則：**
- `### Requirement:` → `class Test{Name}:`
- `#### Scenario:` → `def test_{scenario_name}():`
- `- **WHEN**` / `- **AND**` → Arrange 區塊
- `- **THEN**` → Assert 區塊

### Step 4.1: 識別互動式場景

識別需要 mock 使用者輸入或 UI 互動的場景：

**互動式場景特徵：**
- WHEN 包含「使用者選擇」「使用者輸入」「使用者點擊」
- THEN 包含「系統顯示選單」「系統提示」「顯示對話框」

**處理方式：**
1. 為可直接測試的邏輯生成單元測試
2. 將互動式場景標記為「需手動補充」
3. 在摘要中列出這些場景並提供 mock 範例

### Step 5: 決定檔案位置並寫入

1. 檢查專案的測試目錄結構（通常為 `tests/`）
2. 參考現有測試檔案的命名慣例
3. 決定測試檔案的適當路徑
4. 使用 Write 工具寫入測試檔案

如果使用者指定 `--output <dir>`，則寫入指定目錄。

### Step 6: 顯示生成結果摘要

```
## 測試生成完成

**生成檔案:**
- tests/test_feature.py (3 tests)
- tests/test_utils.py (2 tests)

**測試數量:** 5 個測試方法

**下一步:** 執行 `/custom-skills-python-test` 驗證測試（Red Phase）
```

**如有互動式場景，額外顯示：**

```
## 需手動補充的互動式場景

以下場景涉及使用者輸入或 UI 互動，需手動補充測試：

| Requirement | Scenario | 原因 |
|-------------|----------|------|
| 提供互動式處理選項 | 顯示處理選項選單 | 需 mock `Prompt.ask` |
| 還原非內容異動 | 執行還原 | 需 mock 使用者選擇 |

### Mock 範例

```python
from unittest.mock import patch, MagicMock

class TestInteractiveFlow:
    """互動式流程測試範例"""

    @patch("script.utils.git_helpers.Prompt.ask")
    def test_user_selects_revert(self, mock_prompt):
        """測試使用者選擇還原選項"""
        # Arrange
        mock_prompt.return_value = "1"  # 模擬選擇第一個選項
        console = MagicMock()
        changes = MetadataChanges(mode_changes=["test.txt"])

        # Act
        handle_metadata_changes(changes, repo_path, console)

        # Assert
        mock_prompt.assert_called_once()
        console.print.assert_any_call("[bold green]✓ 已還原所有非內容異動[/bold green]")
```
```

## Example | 範例

### 輸入 Spec

```markdown
### Requirement: 檢測檔案權限變更

#### Scenario: 偵測 644 到 755 的權限變更
- **WHEN** 檔案在 git 記錄為 mode 100644
- **AND** 工作目錄的檔案為 mode 100755
- **THEN** 系統將該檔案分類為「權限變更」
```

### 生成的測試

```python
class TestDetectModeChanges:
    """Requirement: 檢測檔案權限變更"""

    def test_detect_644_to_755_mode_change(self, tmp_path):
        """Scenario: 偵測 644 到 755 的權限變更"""
        # Arrange
        # WHEN 檔案在 git 記錄為 mode 100644
        # AND 工作目錄的檔案為 mode 100755
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

## TDD Workflow | TDD 工作流程

此命令是 TDD 流程的第一步：

1. **生成測試** (此命令)
   ```
   /custom-skills-python-derive-tests specs/
   ```

2. **Red Phase**: 執行測試，預期失敗
   ```
   /custom-skills-python-test
   ```

3. **實作功能程式碼**

4. **Green Phase**: 執行測試，預期通過
   ```
   /custom-skills-python-test
   ```

5. **覆蓋率驗證**
   ```
   /custom-skills-python-coverage
   ```

## Limitations | 限制

- 生成的測試可能需要微調
- **互動式場景**（使用者輸入、UI 互動）會標記為「需手動補充」並提供 mock 範例
- 複雜的 mock 場景需手動補充
- 依賴 AI 理解場景語義和專案程式碼
