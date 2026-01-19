# skill-listing Specification

## Purpose
TBD - created by archiving change enhance-skill-management. Update Purpose after archive.
## Requirements
### Requirement: Post-Install Warning (安裝後警告)
腳本 MUST (必須) 在 `install` 指令完成後顯示已安裝的 skill 名稱清單與重複名稱警告。

#### Scenario: 首次安裝完成後顯示警告
給定使用者執行 `install` 指令
當所有安裝步驟完成時
則應該：
1. 列出所有已安裝的 skill 名稱
2. 顯示警告訊息提醒使用者避免使用重複名稱
3. 建議使用獨特前綴（如 `user-`、`local-`）

### Requirement: List Command (列表指令)
腳本 MUST (必須) 實作 `list` 指令以顯示已安裝的資源。

#### Scenario: 列出所有 Skills
給定使用者執行 `uv run script/main.py list`
當未指定 `--type` 參數時
則應該顯示所有類型的資源（skills、commands、agents）並標示來源。

#### Scenario: 列出特定類型的資源
給定使用者執行 `uv run script/main.py list --type skills`
當指定 `--type` 參數時
則應該只顯示該類型的資源。

#### Scenario: 列出特定工具的資源
給定使用者執行 `uv run script/main.py list --target claude`
當指定 `--target` 參數時
則應該只顯示該工具目錄中的資源。

#### Scenario: 標示資源來源
給定使用者執行 `list` 指令
當顯示資源清單時
則每個項目應該標示其來源：
- `universal-dev-standards`：來自 UDS
- `obsidian-skills`：來自 Obsidian Skills
- `anthropic-skills`：來自 Anthropic Skills
- `custom-skills`：來自本專案
- `user`：使用者自建（不在任何來源中）
- `npm:<package>`：來自第三方 npm 套件

