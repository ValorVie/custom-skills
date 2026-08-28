## Purpose

定義 ai-dev 第一方 skills 的公開來源、可攜式內容、明確安裝清單、npx 生命週期，以及從舊 copy ownership 遷移時必須保留的相容性與停止條件。

## ADDED Requirements

### Requirement: 第一方 skill collection 為獨立公開來源

系統 SHALL 以獨立公開 repository `ValorVie/ai-dev-skills` 作為 ai-dev 第一方 skills 的 canonical source。該 repository SHALL 允許 `npx skills add <source> --list` 找到所有宣告的第一方 skills，且每個 skill SHALL 以其 frontmatter `name` 作為 canonical ID。

#### Scenario: collection 可被 npx 探索

- **WHEN** 維護者對公開來源執行 `npx skills add ValorVie/ai-dev-skills --list`
- **THEN** 指令 SHALL 成功列出 `upstream/npx-skills.yaml` 宣告的全部第一方 skill 名稱
- **THEN** 不得出現同名、空名稱或只靠目錄名稱才能辨識的 skill

#### Scenario: canonical ID 與目錄名不一致

- **WHEN** 舊來源目錄名與 frontmatter `name` 不一致
- **THEN** 新 repository SHALL 以 frontmatter `name` 作為安裝、更新、來源辨識與衝突檢查的 ID
- **THEN** 初始遷移 SHALL 將舊目錄名 `custom-simplify` 對照到 canonical ID `simplify`

### Requirement: 第一方 skill 內容可獨立安裝

每個第一方 skill SHALL 把執行所需的 scripts、references、assets、templates、evals 與直接測試保留在自己的 skill 目錄內。skill 內部連結 SHALL 留在該 skill 目錄，或指向可公開存取的正式來源。

#### Scenario: 安裝單一 skill

- **WHEN** 使用者只安裝 collection 中的一個 skill
- **THEN** 該 skill 的必要支援檔 SHALL 隨 skill 目錄一起安裝
- **THEN** skill SHALL 不依賴逃出自身根目錄的相對連結才能完成主要流程

#### Scenario: companion integration 不由 npx 安裝

- **WHEN** skill 另有 plugin、hook、command 或其他 agent-native integration
- **THEN** skill 文件 SHALL 明確標示該 integration 不由 `npx skills` 安裝
- **THEN** 文件 SHALL 指向公開且可驗證的獨立安裝入口

### Requirement: 公開內容不得包含內部識別資訊

第一方 skill repository SHALL 不包含任何內部品牌、repository、host、帳號、project ID、credential 位置、私有維運路徑或組織專用範例。一般化測試路徑如 `/home/user/app` 不在此限，但不得間接指向真實內部環境。

#### Scenario: 發布前公開邊界檢查

- **WHEN** 維護者準備提交或發布第一方 skill 變更
- **THEN** 自動檢查 SHALL 對本次公開檔案執行不分大小寫的受限關鍵字掃描
- **THEN** staged diff SHALL 接受人工檢查，以排除路徑、帳號與營運細節的間接識別資訊
- **THEN** 發現受限內容時 SHALL 阻止完成聲明

### Requirement: ai-dev 使用明確清單管理第一方 skills

`upstream/npx-skills.yaml` SHALL 明確列出 ai-dev 預設管理的第一方 skill canonical IDs。ai-dev SHALL NOT 使用 wildcard 自動採用新加入 collection 的 skill。

#### Scenario: 新 skill 尚未加入 ai-dev baseline

- **WHEN** `ValorVie/ai-dev-skills` 新增一個 skill，但 `upstream/npx-skills.yaml` 尚未列出該名稱
- **THEN** `ai-dev install` 與 `ai-dev update` SHALL 不自動安裝該 skill
- **THEN** 維護者 SHALL 先完成審查並更新明確清單，才讓它進入 baseline

#### Scenario: 宣告名稱在來源不存在

- **WHEN** ai-dev manifest 宣告的第一方 skill 無法從公開來源解析
- **THEN** npx-skills phase SHALL 回報缺少的 canonical ID 與來源
- **THEN** 整個第一方遷移 SHALL 不得進入舊副本清理階段

### Requirement: 安裝與更新由 npx 擁有

ai-dev SHALL 使用受 conflict guard 保護的 `npx skills add` 安裝或更新第一方 skills。npx 是唯一 writer；ai-dev guard 只保存衝突分類所需的 base，不得用 copy、ManifestTracker ownership、disabled 目錄或 orphan cleanup 覆蓋目標內容。

#### Scenario: 新工作站安裝

- **WHEN** 使用者在尚未安裝第一方 skills 的工作站執行 `ai-dev install`
- **THEN** npx-skills phase SHALL 依明確清單安裝第一方 skills
- **THEN** 成功摘要 SHALL 列出來源、skill 數量與目標 agents

#### Scenario: 更新單一第一方 skill

- **WHEN** 公開來源只修改一個已安裝的第一方 skill，且使用者執行 `ai-dev update`
- **THEN** npx-skills phase SHALL 讓該 skill 取得新版本
- **THEN** 使用者 SHALL 不需要重新發布或重新安裝整個 ai-dev framework 才能取得該變更

#### Scenario: 本機手動修改第一方 skill

- **WHEN** canonical install directory 或任一 configured agent-visible path 與 guard base 不同
- **AND** 上游 source 與 guard base 相同
- **THEN** skill SHALL 分類為 `local-only` 並保留本機內容
- **THEN** ai-dev SHALL 不執行 npx add 或 update

#### Scenario: 上游與本機都改變

- **WHEN** upstream source 與 guard base 不同
- **AND** canonical install directory 或任一 configured agent-visible path 也與 guard base 不同
- **THEN** skill SHALL 分類為 `both-changed`
- **THEN** ai-dev SHALL 停止該 skill 並回報 source、local 與 base hashes

#### Scenario: guard 無可信 base

- **WHEN** guard 沒有該 skill 的可信 base，且任一目標已有內容
- **THEN** skill SHALL 分類為 `no-base` 並停止，不得把現有內容當成可覆蓋的 generated output
- **WHEN** guard 沒有 base 且所有必要目標都不存在
- **THEN** SHALL 視為 fresh install；驗證成功後建立第一份 guard base

### Requirement: 第一方 conflict guard 與 npx ownership 解耦

guard SHALL 使用獨立的 `npx-first-party.yaml` 保存既有 `FileEntry` schema 的 directory-level base。該檔案 SHALL 不進入 target ManifestTracker，不列舉第三方 packages，也不提供 copy、merge、toggle、remove 或 orphan cleanup 能力。

#### Scenario: guard baseline 成功更新

- **WHEN** npx 安裝完成，canonical path、frontmatter、lock source 與五個 configured agent paths 都與 source snapshot 相符
- **THEN** guard SHALL 原子寫入新的 source hash、destination hash、source commit 與 source identifier
- **THEN** 後續 reconcile SHALL 以該 entry 作為四態分類 base

#### Scenario: 已由舊版本 npx 遷移但沒有 guard

- **WHEN** npx lock source 正確、現有所有必要 paths 與目前 source snapshot 完全相同，但 guard entry 不存在
- **THEN** reconcile MAY 安全建立 baseline，不需重裝
- **WHEN** 現有內容與 source snapshot 不同
- **THEN** SHALL 分類為 `no-base` 並保留內容

#### Scenario: npx phase 失敗

- **WHEN** 任何第一方 skill 的 add 或 update 失敗
- **THEN** phase SHALL 以非零結果或明確失敗摘要結束
- **THEN** ai-dev SHALL 保留可用的舊安裝與舊 ownership 紀錄，不得繼續清理

### Requirement: 舊 copy ownership 安全遷移

首次遷移 SHALL 先盤點舊 manifest、目標內容與 canonical IDs，再安裝 npx 版本。只有舊項目可證明由 ai-dev 管理、未被使用者修改，且 npx 安裝已讀回驗證時，才可移除舊 manifest ownership 與舊副本。

#### Scenario: 未修改的同名舊副本

- **WHEN** 舊 manifest 證明目標 skill 由 `custom-skills` 管理，且目標 hash 與已知 base 相同
- **THEN** 遷移 SHALL 安裝並驗證 npx 版本
- **THEN** 驗證成功後才可移除舊 manifest entry 與不再使用的舊副本

#### Scenario: 使用者修改過舊副本

- **WHEN** 舊目標內容與 manifest base 不同，或無法證明 ownership
- **THEN** 遷移 SHALL 停止處理該 skill
- **THEN** SHALL 顯示衝突檔案、備份建議與人工決定入口
- **THEN** SHALL 不以 `--yes`、force 或 orphan cleanup 覆蓋該內容

#### Scenario: 舊名稱轉換

- **WHEN** 遷移遇到舊路徑 `custom-simplify`，且 npx 已成功安裝 canonical ID `simplify`
- **THEN** 系統 SHALL 將兩者顯示為一次性名稱轉換，而不是兩個獨立 skills
- **THEN** 只有舊路徑未修改時才可清理

### Requirement: 遷移可回復

實作 SHALL 保留能回到上一個 ai-dev release 與上一個第一方 skill source revision 的回復方式。回復不得依賴刪除使用者自訂內容。

#### Scenario: npx 版本需回退

- **WHEN** 新第一方 skill release 驗證失敗
- **THEN** 維護者 SHALL 能將 ai-dev manifest 指回已驗證的來源 revision，或發布修復 revision
- **THEN** 回復後 SHALL 重新驗證 skill discovery、目標 agent 可見性與來源標記

#### Scenario: framework 遷移需撤回

- **WHEN** ai-dev 移除 copy ownership 後發現無法接受的相容性問題
- **THEN** 維護者 SHALL 能回復 framework 變更並重新啟用上一版 copy 流程
- **THEN** 已保存的使用者自訂副本 SHALL 不被刪除
