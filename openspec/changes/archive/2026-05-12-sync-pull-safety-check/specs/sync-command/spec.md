## MODIFIED Requirements

### Requirement: sync pull 子指令拉取遠端變更

系統 SHALL 提供 `ai-dev sync pull` 子指令，從遠端 repo 拉取變更到本機。

- 執行前 SHALL 偵測本機是否有未推送的變更
- 若有變更，SHALL 顯示變更清單與互動式選項（先 push 再 pull / 強制覆蓋 / 取消）
- 若無變更或使用者確認後，執行 `git pull --rebase`
- 對每個目錄執行檔案同步（repo 子目錄 → 本機）
- 提供 `--no-delete` 選項，防止刪除本機有但 repo 沒有的檔案
- 提供 `--force` 選項，跳過本機變更偵測直接執行 pull
- 顯示同步結果摘要

#### Scenario: 本機無異動時正常拉取

- **WHEN** 使用者執行 `ai-dev sync pull`，且本機與 repo 一致
- **THEN** 系統直接執行 pull 流程，行為與原有相同

#### Scenario: 本機有異動時顯示互動選項

- **WHEN** 使用者執行 `ai-dev sync pull`，且本機有未推送的變更
- **THEN** 系統 SHALL 顯示變更清單與三個選項，等待使用者選擇

#### Scenario: 使用 --force 跳過偵測

- **WHEN** 使用者執行 `ai-dev sync pull --force`
- **THEN** 系統 SHALL 跳過本機變更偵測，直接執行 pull 流程

#### Scenario: --force 與 --no-delete 同時使用

- **WHEN** 使用者執行 `ai-dev sync pull --force --no-delete`
- **THEN** 系統 SHALL 跳過偵測並執行 pull，且不刪除本機多出的檔案

#### Scenario: 無遠端變更

- **WHEN** 使用者執行 `ai-dev sync pull`，但遠端無新 commit
- **THEN** 系統顯示「已是最新狀態」

#### Scenario: 未初始化時拉取

- **WHEN** 使用者執行 `ai-dev sync pull`，但尚未執行 `sync init`
- **THEN** 系統顯示錯誤訊息並提示先執行 `ai-dev sync init`
