## MODIFIED Requirements

### Requirement: List Command (列表指令)

腳本 MUST (必須) 實作 `list` 指令以顯示已安裝的資源，並從 ai-dev declarative manifests 與現有來源目錄辨識來源。list 為唯讀操作，不得為了補來源資訊執行 add、update、remove 或重新分發。

#### Scenario: 列出所有 Skills

給定使用者執行 `ai-dev list`
當未指定 `--type` 參數時
則應該顯示所有類型的資源（skills、commands、agents）並標示來源。

#### Scenario: 列出特定類型的資源

給定使用者執行 `ai-dev list --type skills`
當指定 `--type` 參數時
則應該只顯示該類型的資源。

#### Scenario: 列出特定工具的資源

給定使用者執行 `ai-dev list --target <target>` 指令
當 target 為 `claude`、`antigravity`、`opencode`、`codex` 或 `agy` 時
則應該列出該工具安裝的所有資源。

#### Scenario: 標示資源來源

給定使用者執行 `list` 指令
當顯示資源清單時
則每個項目應該標示其來源：
- `ai-dev-skills`：由 `upstream/npx-skills.yaml` 宣告、來源為 `ValorVie/ai-dev-skills` 的第一方 skill
- `universal-dev-standards`：來自 UDS
- `obsidian-skills`：來自 Obsidian Skills
- `anthropic-skills`：來自 Anthropic Skills
- `everything-claude-code`：來自 ECC
- `custom-skills`：仍由本 framework repository 管理的非 npx 資源
- `user`：使用者自建，且不在任何已知來源或 declarative manifest 中
- 其他 npx package：顯示 manifest 的 `source` 或 repository 名稱

#### Scenario: 第一方 skill 有 local overlay

- **WHEN** `npx-first-party.yaml` schema v2 顯示 canonical skill 有一個以上 active overlay 或 tombstone
- **THEN** list SHALL 保留來源 `ai-dev-skills`
- **THEN** SHALL 另標示 `local overlay` 與受影響檔案數，不得把它誤標為 user-only 或 pure upstream

#### Scenario: overlay state 無法讀取

- **WHEN** 第一方 overlay manifest 損壞或 active overlay path 不可讀
- **THEN** list SHALL 維持 read-only 並標示 `overlay state unknown`
- **THEN** SHALL 不自動修復、刪除或重裝該 skill

#### Scenario: canonical ID 與舊目錄名不同

- **WHEN** list 遇到已安裝的 `simplify` 與待清理的舊目錄 `custom-simplify`
- **THEN** 遷移摘要 SHALL 將兩者顯示為同一 canonical skill 的新舊路徑
- **THEN** 一般安裝清單 SHALL 以 `simplify` 為名稱

#### Scenario: npx manifest 暫時不可讀

- **WHEN** `upstream/npx-skills.yaml` 不存在或無法解析
- **THEN** list SHALL 繼續列出檔案系統中可見的資源
- **THEN** 無法證明來源的項目 SHALL 標示為 `unknown`，不得誤標為 `user`
