# custom-repo-management Specification

## Purpose

提供使用者自訂 repo 的設定檔管理與結構驗證功能。

## Requirements

### Requirement: Custom Repos 設定檔管理 (Config File Management)

系統 MUST 提供 `~/.config/ai-dev/repos.yaml` 設定檔來儲存使用者自訂的 repo 清單。設定檔格式如下：

```yaml
repos:
  <repo-name>:
    url: <git-clone-url>
    branch: <branch-name>
    local_path: ~/.config/<repo-name>/
    added_at: "<ISO-8601-timestamp>"
```

#### Scenario: 設定檔不存在時讀取

- **WHEN** `load_custom_repos()` 被呼叫且 `~/.config/ai-dev/repos.yaml` 不存在
- **THEN** 回傳空結構 `{"repos": {}}`，不拋出錯誤

#### Scenario: 設定檔存在時讀取

- **WHEN** `load_custom_repos()` 被呼叫且設定檔存在
- **THEN** 回傳解析後的 YAML 結構，包含所有已註冊的 repos

#### Scenario: 新增 repo 到設定檔

- **WHEN** `add_custom_repo(name, url, branch, local_path)` 被呼叫
- **THEN** 將新 repo 條目寫入 `repos.yaml`，包含 `url`、`branch`、`local_path`、`added_at` 欄位
- **THEN** `added_at` MUST 為呼叫時的 ISO 8601 時間戳記

#### Scenario: 新增已存在的 repo 名稱

- **WHEN** `add_custom_repo()` 被呼叫且名稱已存在於設定檔
- **THEN** 不覆蓋既有條目
- **THEN** 顯示警告訊息告知使用者該名稱已存在

#### Scenario: 移除 repo

- **WHEN** `remove_custom_repo(name)` 被呼叫且名稱存在
- **THEN** 從 `repos.yaml` 移除該條目並寫回檔案

#### Scenario: 列出所有 custom repos

- **WHEN** `list_custom_repos()` 被呼叫
- **THEN** 回傳設定檔中所有 repos 的名稱與資訊

### Requirement: Repo 結構驗證 (Structure Validation)

系統 MUST 驗證 custom repo 根目錄是否包含規範的五個目錄：`agents/`、`skills/`、`commands/`、`hooks/`、`plugins/`。

#### Scenario: 所有目錄皆存在

- **WHEN** `validate_repo_structure(repo_dir)` 被呼叫且五個目錄皆存在
- **THEN** 回傳驗證通過，無警告

#### Scenario: 部分目錄缺少

- **WHEN** `validate_repo_structure(repo_dir)` 被呼叫且缺少部分目錄
- **THEN** 對缺少的目錄發出警告訊息
- **THEN** 不阻擋後續操作（驗證仍視為通過）

#### Scenario: 目錄存在但為空

- **WHEN** 規範目錄存在但內部沒有檔案
- **THEN** 視為結構合規，不發出警告

### Requirement: 設定檔目錄自動建立 (Config Directory Auto-creation)

系統 MUST 在寫入設定檔前確保 `~/.config/ai-dev/` 目錄存在。

#### Scenario: 目錄不存在時自動建立

- **WHEN** 寫入 `repos.yaml` 時 `~/.config/ai-dev/` 目錄不存在
- **THEN** 自動建立該目錄（含父目錄）後再寫入檔案

### Requirement: Add-custom-repo validates repository structure
The add-custom-repo command SHALL validate that the cloned repository has the expected directory structure.

#### Scenario: Valid repository structure
- **WHEN** user runs `ai-dev add-custom-repo <url>` and repo has skills/ or commands/ directory
- **THEN** system clones repo and writes entry to repos.yaml

#### Scenario: Invalid repository structure
- **WHEN** cloned repo has no skills/, commands/, agents/, or workflows/ directory
- **THEN** system warns about invalid structure

#### Scenario: Fix option creates missing directories
- **WHEN** user runs `ai-dev add-custom-repo <url> --fix`
- **THEN** system creates missing directory structure in the cloned repo

### Requirement: Update-custom-repo with safe update mechanism
The update-custom-repo command SHALL use fetch + backup + reset instead of simple git pull.

#### Scenario: Update with local changes
- **WHEN** a custom repo has local modifications
- **THEN** system backs up dirty files before `git reset --hard origin/{branch}`

#### Scenario: Update without local changes
- **WHEN** a custom repo has no local modifications
- **THEN** system performs `git fetch --all` then `git reset --hard origin/{branch}`

#### Scenario: Update summary
- **WHEN** update completes
- **THEN** system displays summary showing which repos were updated, which were already up-to-date, and any errors
