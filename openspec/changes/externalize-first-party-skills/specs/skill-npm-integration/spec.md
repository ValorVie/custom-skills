## ADDED Requirements

### Requirement: Declarative npx skill maintenance

ai-dev SHALL 以 `upstream/npx-skills.yaml` 作為 baseline skills 的 declarative manifest，並在 `install`、`update` 與 `install-npx-skills` 的 npx-skills phase 執行對應的 `npx skills` 操作。全域 npx lock 只代表目前工作站狀態，不得取代 repository manifest。

#### Scenario: install 安裝 manifest 宣告的 skills

- **WHEN** 使用者執行包含 npx-skills phase 的 `ai-dev install`
- **THEN** 系統 SHALL 對每個 manifest package 執行 add 語意
- **THEN** SHALL 明確傳入 scope、agents、skills 與 non-interactive 選項

#### Scenario: global install 只指定 ai-dev 支援的 agents

- **WHEN** manifest 使用 global scope 執行 add
- **THEN** `-a` SHALL 明確列出 `claude-code`、`codex`、`gemini-cli`、`opencode` 與 `antigravity`
- **THEN** SHALL NOT 使用 `'*'`，也不得把只支援 project scope 的 Eve 或 PromptScript 當成 global target
- **THEN** Eve 與 PromptScript 的使用者仍可在各自專案內手動執行原生 `npx skills add`

#### Scenario: update 更新已安裝 skills

- **WHEN** 使用者執行包含 npx-skills phase 的 `ai-dev update`
- **THEN** 非第一方 package SHALL 維持原生 `npx skills update` 行為
- **THEN** 第一方 package SHALL 以 reconcile 流程自動安裝缺少項目並更新安全項目
- **THEN** 使用者 SHALL 不需要另行執行 `ai-dev install-npx-skills` 才能完成第一方遷移

#### Scenario: 第一方 reconcile 保留四態判斷

- **WHEN** canonical ID 的 `source` 是 `ai-dev-first-party`
- **THEN** ai-dev SHALL 在呼叫 npx 前以 source、base、local directory hashes 分類 `clean`、`local-only`、`both-changed` 或 `no-base`
- **THEN** source-only change SHALL 維持 `clean` 分類並允許更新
- **THEN** `local-only`、`both-changed` 與有既存內容的 `no-base` SHALL 停止該 skill，不呼叫 npx

#### Scenario: 其他 npx 來源保持直通

- **WHEN** package source 不是 `ai-dev-first-party`
- **THEN** ai-dev SHALL 不建立 guard baseline、不執行四態分類，也不改變其 add／update command semantics

#### Scenario: 同一 package 含多個 skills

- **WHEN** 同一 package 宣告多個 skill canonical IDs
- **THEN** add 操作 SHALL 在同一個 package command 中傳入多個 `--skill` 選項
- **THEN** 系統 SHALL NOT 為同一 package 的每個 skill 重複解析來源

#### Scenario: dry-run 顯示完整命令

- **WHEN** npx-skills phase 以 dry-run 執行
- **THEN** 系統 SHALL 顯示 package、skills、scope、agents 與 non-interactive 參數
- **THEN** SHALL 不執行 npx、不寫 lock、不清理 manifest ownership

#### Scenario: package 部分失敗

- **WHEN** 任一 package command 回傳非零退出碼
- **THEN** phase SHALL 保存該 package 的失敗結果並顯示失敗摘要
- **THEN** SHALL 不把失敗 package 的 skills 標記為完成遷移

#### Scenario: npx 回傳成功但 agent path 不完整

- **WHEN** 第一方 npx command 回傳 0，但任一 configured agent path 缺少 skill 或內容與 source snapshot 不同
- **THEN** reconcile SHALL 將該 skill 視為失敗
- **THEN** SHALL 不更新 guard baseline，也不得 detach legacy ownership

### Requirement: Manifest schema validates canonical skill IDs

npx-skills manifest loader SHALL 拒絕重複 canonical ID、空 skill 清單、無 repo 的 package，以及同一 canonical ID 由多個來源宣告的衝突。

#### Scenario: canonical ID 重複來源

- **WHEN** 兩個 packages 宣告相同的 canonical skill ID
- **THEN** manifest validation SHALL 失敗並列出名稱與兩個來源
- **THEN** npx command SHALL 不執行

#### Scenario: package 無 skills

- **WHEN** package 沒有任何明確 skill 名稱
- **THEN** manifest validation SHALL 失敗
- **THEN** 系統 SHALL NOT 將空清單解讀為安裝全部 skills
