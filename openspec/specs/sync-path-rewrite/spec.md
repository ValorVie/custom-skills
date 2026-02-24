## ADDED Requirements

### Requirement: 路徑變數 Registry

系統 SHALL 提供 `PATH_VARIABLES` 字典，定義佔位符名稱與對應的系統路徑值。

- 預設包含 `{"HOME": str(Path.home())}`
- 佔位符格式為 `{{NAME}}`（雙花括號包裹變數名）

#### Scenario: 取得 HOME 變數

- **WHEN** 系統讀取 `PATH_VARIABLES`
- **THEN** `PATH_VARIABLES["HOME"]` 等於 `str(Path.home())`

---

### Requirement: JSON 路徑標準化（Normalize）

系統 SHALL 提供 `normalize_paths_in_file(file_path)` 函數，將 JSON 檔案中以系統路徑開頭的 string value 替換為對應的佔位符。

- 遞迴掃描所有 JSON string value
- 對每個 `PATH_VARIABLES` 條目，將值中以該路徑開頭的部分替換為 `{{NAME}}`
- 只修改 string value，不修改 key 或非 string 型別
- 有變更時寫回檔案，無變更時不寫入
- 回傳 `bool` 表示是否有變更
- 檔案不存在時靜默回傳 `False`

#### Scenario: 標準化包含 HOME 路徑的值

- **WHEN** JSON 檔案包含 `{"DATA_DIR": "/Users/arlen/.claude-mem"}`
- **AND** `Path.home()` 為 `/Users/arlen`
- **THEN** 標準化後檔案內容為 `{"DATA_DIR": "{{HOME}}/.claude-mem"}`

#### Scenario: 值不包含系統路徑

- **WHEN** JSON 檔案包含 `{"MODE": "code"}`
- **THEN** 標準化後檔案內容不變，函數回傳 `False`

#### Scenario: 巢狀 JSON 結構

- **WHEN** JSON 檔案包含 `{"config": {"path": "/Users/arlen/data"}}`
- **THEN** 標準化後為 `{"config": {"path": "{{HOME}}/data"}}`

#### Scenario: 檔案不存在

- **WHEN** 指定的檔案路徑不存在
- **THEN** 函數回傳 `False`，不拋出例外

---

### Requirement: JSON 路徑展開（Expand）

系統 SHALL 提供 `expand_paths_in_file(file_path)` 函數，將 JSON 檔案中的佔位符展開為當前系統的實際路徑。

- 遞迴掃描所有 JSON string value
- 對每個 `PATH_VARIABLES` 條目，將值中的 `{{NAME}}` 替換為對應的系統路徑
- 只修改 string value，不修改 key 或非 string 型別
- 有變更時寫回檔案，無變更時不寫入
- 回傳 `bool` 表示是否有變更
- 檔案不存在時靜默回傳 `False`

#### Scenario: 展開 HOME 佔位符

- **WHEN** JSON 檔案包含 `{"DATA_DIR": "{{HOME}}/.claude-mem"}`
- **AND** `Path.home()` 為 `/home/bob`
- **THEN** 展開後檔案內容為 `{"DATA_DIR": "/home/bob/.claude-mem"}`

#### Scenario: 無佔位符的值

- **WHEN** JSON 檔案包含 `{"MODE": "code"}`
- **THEN** 展開後檔案內容不變，函數回傳 `False`

#### Scenario: 檔案不存在

- **WHEN** 指定的檔案路徑不存在
- **THEN** 函數回傳 `False`，不拋出例外

---

### Requirement: 批次路徑處理

系統 SHALL 提供批次函數，根據 sync config 的 directories 列表處理所有 `settings.json`。

- `normalize_paths_in_repo(config)`: 掃描 repo 中各 `{repo_dir}/{repo_subdir}/settings.json`
- `expand_paths_in_local(config)`: 掃描本機各 `{local_path}/settings.json`
- 兩個函數皆回傳處理結果摘要（哪些檔案有變更）

#### Scenario: Push 時批次標準化

- **WHEN** sync config 包含 `[{"path": "~/.claude-mem", "repo_subdir": "claude-mem"}]`
- **THEN** `normalize_paths_in_repo(config)` 處理 `{repo_dir}/claude-mem/settings.json`

#### Scenario: Pull 時批次展開

- **WHEN** sync config 包含 `[{"path": "~/.claude-mem", "repo_subdir": "claude-mem"}]`
- **THEN** `expand_paths_in_local(config)` 處理 `~/.claude-mem/settings.json`

#### Scenario: 目錄無 settings.json

- **WHEN** 某同步目錄下不存在 `settings.json`
- **THEN** 該目錄被靜默跳過，不影響其他目錄的處理
