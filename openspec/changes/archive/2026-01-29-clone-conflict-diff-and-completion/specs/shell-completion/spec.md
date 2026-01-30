## ADDED Requirements

### Requirement: 安裝流程自動設定 shell completion
`ai-dev install` SHALL 在安裝流程結尾嘗試自動安裝 shell completion。透過 subprocess 呼叫 `ai-dev --install-completion`。失敗時顯示手動安裝提示，不阻擋安裝流程。

#### Scenario: 自動安裝成功
- **WHEN** 執行 `ai-dev install` 且 shell completion 尚未安裝
- **THEN** 自動執行 `ai-dev --install-completion`，顯示安裝成功訊息

#### Scenario: 已經安裝過
- **WHEN** 執行 `ai-dev install` 且 shell completion 已安裝
- **THEN** 不重複安裝，顯示已安裝提示或靜默跳過

#### Scenario: 安裝失敗
- **WHEN** `ai-dev --install-completion` 執行失敗（非互動環境或其他原因）
- **THEN** 顯示提示訊息「Shell 自動補全安裝失敗，請手動執行：ai-dev --install-completion」，安裝流程繼續不中斷
