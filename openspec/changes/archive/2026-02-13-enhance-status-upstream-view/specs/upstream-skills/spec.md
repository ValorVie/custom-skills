## MODIFIED Requirements

### Requirement: 設定儲存庫表完整清單與狀態

`ai-dev status` 的「設定儲存庫」表 SHALL 列出 `shared.py` 中 `REPOS` 字典定義的全部 repo，並顯示 git 版本比對狀態。

#### Scenario: 顯示全部 6 個 repo
- **WHEN** 使用者執行 `ai-dev status`
- **THEN** 設定儲存庫表 MUST 包含 `REPOS` 字典中的全部項目：custom-skills、superpowers、universal-dev-standards、obsidian-skills、anthropic-skills、everything-claude-code

#### Scenario: 本地與遠端一致
- **WHEN** 某 repo 的 `git rev-parse HEAD` 等於 `git rev-parse origin/{branch}`
- **THEN** 狀態欄顯示「✓ 最新」

#### Scenario: 本地落後於遠端
- **WHEN** 某 repo 的本地 HEAD 落後於 origin HEAD
- **THEN** 狀態欄顯示「↑ 有可用更新」

#### Scenario: 無法比對（未 fetch 或非 git 目錄）
- **WHEN** 無法取得 origin HEAD（例如未執行過 fetch 或目錄非 git repo）
- **THEN** 狀態欄顯示目錄存在狀態（維持原有降級行為）

#### Scenario: repo 目錄不存在
- **WHEN** repo 對應的本地目錄不存在
- **THEN** 狀態欄顯示「未安裝」
