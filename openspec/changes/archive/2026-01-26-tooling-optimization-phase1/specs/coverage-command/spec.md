## MODIFIED Requirements

### Requirement: 覆蓋率命令功能

`/coverage` 命令必須分析測試覆蓋率並提供建議。當使用 `--generate` 旗標時，必須同時生成缺失的測試檔案。

**預設模式（僅分析）：**
- 分析程式碼庫的測試覆蓋率
- 識別覆蓋率不足的檔案和函式
- 提供可執行的改善建議

**生成模式（`--generate` 旗標）：**
- 執行所有分析模式的功能
- 額外為覆蓋率不足的程式碼生成測試檔案骨架

#### Scenario: 預設分析模式

- **WHEN** 使用者執行 `/coverage` 不帶任何旗標
- **THEN** 命令分析覆蓋率並輸出建議，不建立任何檔案

#### Scenario: 使用旗標的生成模式

- **WHEN** 使用者執行 `/coverage --generate`
- **THEN** 命令分析覆蓋率並為覆蓋率不足的程式碼生成測試檔案骨架

#### Scenario: 生成旗標的變體形式

- **WHEN** 使用者執行 `/coverage --generate` 或 `/coverage -g`
- **THEN** 兩種形式都被接受並觸發生成模式

### Requirement: 命令描述更新

命令描述必須清楚說明兩種模式皆可使用。

#### Scenario: 更新後的描述反映兩種模式

- **WHEN** 檢視命令說明或描述
- **THEN** 描述提及分析模式（預設）和生成模式（--generate 旗標）

## REMOVED Requirements

### Requirement: 獨立的 test-coverage 命令

獨立的 `/test-coverage` 命令必須移除。

**原因**：功能已合併至 `/coverage --generate`，以減少使用者困惑並整合相關功能。

**遷移**：使用者應改用 `/coverage --generate` 取代 `/test-coverage`。

#### Scenario: test-coverage.md 檔案已移除

- **WHEN** 檢查 `commands/claude/test-coverage.md`
- **THEN** 該檔案不再存在

#### Scenario: 遷移路徑已記錄

- **WHEN** 使用者嘗試使用 `/test-coverage`
- **THEN** 應透過文件或錯誤訊息（如工具支援）引導使用者改用 `/coverage --generate`
