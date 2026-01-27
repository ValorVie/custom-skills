# Spec: Metadata Detection

## ADDED Requirements

### Requirement: Clone 完成後自動檢測非內容異動
系統 SHALL 在 `ai-dev clone` 於開發目錄執行完成後，自動檢測非內容異動。

#### Scenario: 開發目錄執行 clone 後觸發檢測
- **WHEN** 使用者在開發目錄執行 `ai-dev clone`
- **AND** clone 流程完成
- **THEN** 系統自動執行非內容異動檢測

#### Scenario: 非開發目錄不觸發檢測
- **WHEN** 使用者在非開發目錄執行 `ai-dev clone`
- **THEN** 系統不執行非內容異動檢測

#### Scenario: 非 git 目錄不觸發檢測
- **WHEN** 使用者在無 `.git` 目錄的位置執行 `ai-dev clone`
- **THEN** 系統不執行非內容異動檢測
- **AND** 不顯示錯誤訊息

### Requirement: 檢測檔案權限變更
系統 SHALL 識別僅有檔案權限變更（mode change）的檔案。

#### Scenario: 偵測 644 到 755 的權限變更
- **WHEN** 檔案在 git 記錄為 mode 100644
- **AND** 工作目錄的檔案為 mode 100755
- **AND** 檔案內容未變更
- **THEN** 系統將該檔案分類為「權限變更」

#### Scenario: 偵測 755 到 644 的權限變更
- **WHEN** 檔案在 git 記錄為 mode 100755
- **AND** 工作目錄的檔案為 mode 100644
- **AND** 檔案內容未變更
- **THEN** 系統將該檔案分類為「權限變更」

### Requirement: 檢測換行符變更
系統 SHALL 識別僅有換行符變更（CRLF/LF）的檔案。

#### Scenario: 偵測 LF 到 CRLF 的變更
- **WHEN** 檔案在 git 記錄使用 LF 換行符
- **AND** 工作目錄的檔案使用 CRLF 換行符
- **AND** 正規化換行符後內容相同
- **THEN** 系統將該檔案分類為「換行符變更」

#### Scenario: 偵測 CRLF 到 LF 的變更
- **WHEN** 檔案在 git 記錄使用 CRLF 換行符
- **AND** 工作目錄的檔案使用 LF 換行符
- **AND** 正規化換行符後內容相同
- **THEN** 系統將該檔案分類為「換行符變更」

### Requirement: 區分內容變更與非內容異動
系統 SHALL 將有實際內容變更的檔案與僅有 metadata 變更的檔案區分開。

#### Scenario: 檔案有實際內容變更
- **WHEN** 檔案內容（排除換行符差異後）與 git 記錄不同
- **THEN** 系統將該檔案分類為「內容變更」
- **AND** 不納入非內容異動清單

#### Scenario: 檔案同時有權限和內容變更
- **WHEN** 檔案有權限變更
- **AND** 檔案有實際內容變更
- **THEN** 系統將該檔案分類為「內容變更」

### Requirement: 顯示檢測摘要
系統 SHALL 在檢測到非內容異動時顯示摘要資訊。

#### Scenario: 顯示異動統計
- **WHEN** 系統檢測到非內容異動
- **THEN** 系統顯示權限變更檔案數量
- **AND** 系統顯示換行符變更檔案數量

#### Scenario: 無非內容異動時不顯示
- **WHEN** 系統未檢測到任何非內容異動
- **THEN** 系統不顯示任何提示
- **AND** clone 流程正常結束

### Requirement: 提供互動式處理選項
系統 SHALL 在檢測到非內容異動時，提供使用者選擇處理方式。

#### Scenario: 顯示處理選項選單
- **WHEN** 系統檢測到非內容異動
- **THEN** 系統顯示以下選項：
  - 還原這些變更
  - 設定 git 忽略權限
  - 忽略，保留變更
  - 顯示詳細清單

### Requirement: 還原非內容異動
系統 SHALL 支援將非內容異動檔案還原到 git 記錄狀態。

#### Scenario: 執行還原
- **WHEN** 使用者選擇「還原這些變更」
- **THEN** 系統對所有非內容異動檔案執行 `git checkout`
- **AND** 系統顯示還原完成訊息

#### Scenario: 還原失敗處理
- **WHEN** 使用者選擇「還原這些變更」
- **AND** git checkout 執行失敗
- **THEN** 系統顯示錯誤訊息
- **AND** 不中斷程式執行

### Requirement: 設定 git 忽略權限
系統 SHALL 支援設定 `core.fileMode=false` 讓 git 忽略權限差異。

#### Scenario: 設定 fileMode
- **WHEN** 使用者選擇「設定 git 忽略權限」
- **THEN** 系統執行 `git config core.fileMode false`
- **AND** 系統顯示設定完成訊息

### Requirement: 顯示詳細清單
系統 SHALL 支援顯示所有非內容異動檔案的詳細清單。

#### Scenario: 列出檔案清單
- **WHEN** 使用者選擇「顯示詳細清單」
- **THEN** 系統以表格形式顯示所有非內容異動檔案
- **AND** 每個檔案顯示異動類型（權限/換行符）
- **AND** 顯示完成後再次顯示處理選項
