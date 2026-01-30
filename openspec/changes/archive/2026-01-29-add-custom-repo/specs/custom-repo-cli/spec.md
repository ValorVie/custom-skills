## ADDED Requirements

### Requirement: add-custom-repo 指令介面 (CLI Interface)

系統 MUST 提供 `ai-dev add-custom-repo` 指令，接受以下參數：

- **必要參數**: `remote_path` — 遠端 repo 路徑（支援 `owner/repo`、完整 HTTPS URL、SSH URL）
- **選用參數**:
  - `--name` / `-n`: 自訂名稱（預設使用 repo 名稱）
  - `--branch` / `-b`: 追蹤的分支（預設 `main`）

#### Scenario: 使用簡寫格式新增

- **WHEN** 執行 `ai-dev add-custom-repo mycompany/ai-tools`
- **THEN** 解析為 repo URL `https://github.com/mycompany/ai-tools.git`
- **THEN** 使用 `ai-tools` 作為預設名稱
- **THEN** Clone 到 `~/.config/ai-tools/`
- **THEN** 寫入 `~/.config/ai-dev/repos.yaml`

#### Scenario: 使用完整 URL 和自訂名稱

- **WHEN** 執行 `ai-dev add-custom-repo https://github.com/mycompany/ai-tools.git --name company-tools --branch develop`
- **THEN** Clone 到 `~/.config/company-tools/`
- **THEN** 追蹤 `develop` 分支
- **THEN** 寫入設定檔時使用 `company-tools` 作為 key

#### Scenario: 使用 SSH URL

- **WHEN** 執行 `ai-dev add-custom-repo git@github.com:mycompany/ai-tools.git`
- **THEN** 正確解析 owner 和 repo 名稱
- **THEN** 使用原始 SSH URL 進行 clone

### Requirement: add-custom-repo 執行流程 (Execution Flow)

指令 MUST 依序執行以下步驟：
1. 解析 repo URL
2. Clone repo 到本地目錄
3. 驗證 repo 結構
4. 寫入設定檔

#### Scenario: 完整成功流程

- **WHEN** 執行 `ai-dev add-custom-repo owner/repo` 且 clone 成功
- **THEN** 顯示解析結果（Repo、名稱、分支、目錄）
- **THEN** 執行 clone
- **THEN** 執行結構驗證並顯示結果
- **THEN** 寫入設定檔
- **THEN** 顯示完成訊息與後續步驟提示

#### Scenario: 目標目錄已存在

- **WHEN** 執行指令且本地目錄已存在
- **THEN** 跳過 clone 步驟
- **THEN** 顯示警告並繼續執行後續步驟（驗證結構、寫入設定檔）

#### Scenario: Clone 失敗

- **WHEN** clone 過程失敗（如網路錯誤或無權限）
- **THEN** 顯示錯誤訊息
- **THEN** 終止執行，不寫入設定檔

#### Scenario: URL 解析失敗

- **WHEN** 傳入無法解析的 remote_path
- **THEN** 顯示「無法解析 URL」錯誤訊息
- **THEN** 以非零 exit code 終止
