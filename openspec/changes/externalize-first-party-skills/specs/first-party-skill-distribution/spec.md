## Purpose

定義 ai-dev 第一方 skills 的公開來源、可攜式內容、明確安裝清單、npx 生命週期，以及從舊 copy ownership 遷移時必須保留的相容性與停止條件。

## ADDED Requirements

### Requirement: 第一方 skill collection 為獨立公開來源

系統 SHALL 以獨立公開 repository `ValorVie/ai-dev-skills` 作為 ai-dev 第一方 skills 的 canonical source。該 repository SHALL 允許 `npx skills add <source> --list` 找到所有宣告的第一方 skills，且每個 skill SHALL 以其 frontmatter `name` 作為 canonical ID。

#### Scenario: collection 可被 npx 探索

- **WHEN** 維護者對公開來源執行 `npx skills add ValorVie/ai-dev-skills --list`
- **THEN** 指令 SHALL 成功列出 `upstream/npx-skills.yaml` 宣告的全部第一方 skill 名稱
- **THEN** 不得出現同名、空名稱或只靠目錄名稱才能辨識的 skill

#### Scenario: collection 可在互動 picker 整組選取

- **WHEN** 使用者以互動模式執行 `npx skills add ValorVie/ai-dev-skills`
- **THEN** repository SHALL 透過 `.claude-plugin/plugin.json` 將全部第一方 skills 宣告為單一 `Ai Dev Skills` group
- **THEN** plugin manifest 的 skills 清單 SHALL 與 repository 的 canonical inventory 完全一致，不得漏列、重複或加入未發布 ID
- **THEN** 使用者 SHALL 可由 group row 整組選取，且在支援的 CLI 版本可使用頂層 `Select All`
- **THEN** 單一 `--skill <canonical-id>` 安裝語意與 ai-dev 的明確 baseline 清單 SHALL 維持不變

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

### Requirement: 第一方使用 base + persistent overlay 分層 ownership

ai-dev SHALL 使用 `npx skills add` materialize 第一方 upstream base，並使用獨立的 persistent overlay 保存 local intent。npx SHALL NOT 管理 overlay；ai-dev SHALL NOT 使用 clone ManifestTracker、toggle、disabled directory 或 orphan cleanup 改寫 upstream base。installed skill 是 base + overlay 的 materialized view。

#### Scenario: 新工作站安裝

- **WHEN** 使用者在尚未安裝第一方 skills 的工作站執行 `ai-dev install`
- **THEN** npx-skills phase SHALL 依明確清單安裝第一方 base
- **THEN** SHALL 驗證 base、建立 per-file state，且 overlay 為空
- **THEN** 成功摘要 SHALL 列出來源、skill 數量與目標 agents

#### Scenario: local-only 修改成為 persistent overlay

- **WHEN** upstream file 與 base 相同，但 installed local file 不同
- **THEN** file SHALL 分類為 `local-only`
- **THEN** 沒有相同 decision pair 時，TTY SHALL 要求 keep-local、use-upstream 或 abort
- **THEN** keep-local SHALL 保存 local bytes 或 deletion marker 為 overlay
- **THEN** 後續 npx install／update 或直接原生 npx 覆蓋 installed tree 後，ai-dev SHALL 能重新套用 overlay

### Requirement: conflict decision 以 per-file hash pair 記憶

ai-dev SHALL 以 accepted upstream `src_hash`、effective-local `dst_hash_at_sync` 與 `decision` 記錄每個 file 的 conflict answer。decision memory SHALL 與 persistent overlay 配合；hash 只控制是否重新詢問，不得取代 local bytes 或 deletion tombstone。

#### Scenario: remote 與 effective-local 都未改變

- **WHEN** current source hash 等於 stored `src_hash`
- **AND** current effective-local hash 等於 stored `dst_hash_at_sync`
- **AND** stored decision 是 keep-local 或 use-upstream
- **THEN** reconcile SHALL 沿用 stored decision，不重複詢問

#### Scenario: remote 或 local 任一邊改變

- **WHEN** file 仍有 local divergence
- **AND** current source hash 或 current effective-local hash 與 stored decision pair 不同
- **THEN** TTY SHALL 重新詢問 keep-local、use-upstream 或 abort
- **THEN** non-interactive SHALL 跳過整個受影響 skill，保留舊 state／overlay，並使 phase 最後 exit 1

#### Scenario: source-only clean update

- **WHEN** source hash 改變，但 local 沒有 override 或 remembered overlay
- **THEN** file SHALL 維持 clean source-only，不要求 decision

#### Scenario: 原生 npx wipe installed overlay

- **WHEN** stored keep-local overlay 與 decision pair 未變
- **AND** installed local 暫時等於 pure upstream source
- **THEN** effective-local SHALL 使用 persistent overlay hash
- **THEN** reconcile SHALL 重新 materialize overlay，不重複詢問

#### Scenario: 使用者修改已 materialize 的 overlay 內容

- **WHEN** installed local 同時不同於 stored overlay 與 current source
- **THEN** installed local SHALL 成為新的 local candidate
- **THEN** effective-local hash 改變 SHALL 使舊 decision 失效並重新詢問

#### Scenario: 強制重審 remembered overlay

- **WHEN** 使用者執行 `ai-dev install-npx-skills --review-first-party-overlays`
- **THEN** remembered keep-local overlay files SHALL 重新進入 interactive decision menu，即使 hash pair 未變
- **THEN** 使用者選擇 use-upstream 時 SHALL 先保留 transaction backup，再移除 overlay 並採用 upstream
- **THEN** non-interactive 使用此 flag SHALL fail closed，不得自動清除 overlay

#### Scenario: 上游與 local overlay 同時改變

- **WHEN** upstream file 與 base 不同
- **AND** 該 file 有 persistent overlay 或新的 local edit
- **THEN** file SHALL 分類為 `both-changed`
- **THEN** TTY SHALL 提供 upstream-vs-base、local-vs-base、upstream-vs-local diff，以及 keep-local、use-upstream、abort 選擇

#### Scenario: no-base 檔案

- **WHEN** file 沒有可信 base，且 source 與 local 內容不同
- **THEN** file SHALL 分類為 `no-base` 並要求 keep-local、use-upstream 或 abort
- **WHEN** base 不存在且 source 與 local 相同
- **THEN** SHALL 自動 bootstrap
- **WHEN** base 不存在且只有 source 存在
- **THEN** SHALL 視為 clean source-only
- **WHEN** base 不存在且只有 local 存在
- **THEN** SHALL 視為 local-only new file 並保存 overlay

### Requirement: per-file planner 支援新增、刪除與 binary

reconcile SHALL 對 base、source、local、overlay 的 path union 分類。missing SHALL 是明確狀態；local deletion SHALL 以 tombstone 保存，不得與空檔案混淆。

#### Scenario: upstream 刪除且 local 未修改

- **WHEN** base 有 file、upstream 已刪除，local 等於 base
- **THEN** file SHALL 視為 clean source-only deletion
- **THEN** npx 完成後 final materialized view SHALL 不含該 file

#### Scenario: upstream 刪除但 local 已修改

- **WHEN** base 有 file、upstream 已刪除，local 與 base 不同
- **THEN** file SHALL 分類為 `both-changed`
- **THEN** keep-local SHALL 以 overlay resurrect file；use-upstream SHALL 接受刪除

#### Scenario: local 刪除而 upstream 未修改

- **WHEN** source 等於 base，local file 已刪除
- **THEN** file SHALL 分類為 `local-only`
- **THEN** overlay SHALL 保存 deletion tombstone，後續 npx 寫入後重新刪除該 file

#### Scenario: 平台 metadata 不屬於 skill 內容

- **WHEN** 任一 installed root 只多出 `.DS_Store` 或明確排除的 runtime metadata
- **THEN** file map、directory hash、local tree comparison 與 overlay snapshot SHALL 忽略該檔案
- **THEN** 不得把內容相同的 roots 誤判為不同 local modifications

#### Scenario: binary 或 unsupported file type

- **WHEN** conflict file 無法顯示文字 diff
- **THEN** 系統 SHALL 顯示 path、hash、size 與存在狀態
- **THEN** 仍 SHALL 提供 keep-local、use-upstream、abort；skill tree 內無法安全保存的 symlink 或特殊型態 SHALL fail closed

### Requirement: conflict decision 在 mutation 前完成

FirstPartyReconciler SHALL 先規劃所有第一方 files，再執行任何 npx command。第一次出現或 per-file hash pair 已改變的 `local-only`、`both-changed` 與內容不同的 `no-base` 必須先完成 decision resolution；hash pair 相同時 SHALL 沿用原 decision。

#### Scenario: interactive menu 說明每個選項的影響

- **WHEN** TTY 需要使用者處理 `local-only`、`both-changed` 或 `no-base` file
- **THEN** menu SHALL 先顯示 file path 與狀態的中文說明，再等待輸入
- **THEN** `Ds`、`Dl`、`Dc` SHALL 分別說明比較的兩個版本
- **THEN** `K` SHALL 說明本機內容或刪除狀態會保存成持久 overlay，後續更新仍會套用
- **THEN** `O` SHALL 說明系統會先備份目前本機內容，再採用 upstream 內容或刪除狀態
- **THEN** `A` SHALL 說明整個第一方更新會在任何 mutation 前停止
- **WHEN** file 是 `no-base`
- **THEN** `Ds` 與 `Dl` SHALL 顯示為不可用，input prompt SHALL 只列 `Dc/K/O/A`

#### Scenario: interactive keep local

- **WHEN** 使用者對 conflict file 選擇 keep-local
- **THEN** local bytes 或 tombstone SHALL 成為 persistent overlay
- **THEN** current upstream SHALL 成為新 base；下次 upstream 未變時顯示 local-only，不重複詢問
- **THEN** upstream 再次修改該 file 時 SHALL 重新進入 both-changed

#### Scenario: interactive use upstream

- **WHEN** 使用者選擇 use-upstream
- **THEN** 系統 SHALL 自動備份原 local content
- **THEN** SHALL 移除該 file overlay，並以 current upstream 作為 base 與 final content

#### Scenario: interactive abort

- **WHEN** 使用者在任一 conflict 選擇 abort
- **THEN** 整個第一方 reconcile SHALL 在 npx、overlay、manifest 或 legacy mutation 前停止

#### Scenario: non-interactive unresolved conflicts

- **WHEN** stdin 非 TTY 且存在 both-changed 或內容不同的 no-base
- **THEN** 系統 SHALL 跳過整個受影響 skill，不自動 keep-local 或 overwrite
- **THEN** 其他已完整決策的安全 skills MAY 繼續
- **THEN** phase SHALL 最後 exit 1

### Requirement: transaction 保護 npx whole-directory replace

每個要更新的第一方 skill SHALL 在 npx 前建立完整 installed-root backup 與 transaction journal。apply 順序 SHALL 是 capture overlay candidates、npx base、base verification、overlay materialization、effective verification、atomic state commit、legacy detach。

#### Scenario: safe skills 使用一次 grouped npx add

- **WHEN** 同一第一方 repository 有多個已完成 decision resolution 的 safe skills
- **THEN** reconcile SHALL 先讓每個 safe skill 的 transaction 到達 `BACKED_UP`
- **THEN** SHALL 只執行一次 npx add command，並以多個明確 `--skill <canonical-id>` 傳入 safe inventory
- **THEN** SHALL NOT 使用 wildcard，也不得為每個 safe skill 重複 clone 或顯示獨立 installation summary
- **THEN** unresolved skills SHALL 不出現在 grouped command

#### Scenario: npx partial success 或回傳 0 但內容錯誤

- **WHEN** grouped npx command 非零
- **THEN** transaction SHALL 還原所有參與該 command 的 skills
- **WHEN** npx 回傳 0，但部分 skills 的 lock、frontmatter、base hash、canonical path 或 agent-visible root 不符合 plan
- **THEN** transaction SHALL 只還原驗證失敗 skill 的所有 pre-update roots
- **THEN** 驗證成功的 skills MAY 共同提交 schema v2 state
- **THEN** 失敗項 SHALL 保留舊 manifest 與 active overlay，不 detach ownership

#### Scenario: overlay 或 state commit 失敗

- **WHEN** overlay materialization、effective verification 或 atomic state commit 失敗
- **THEN** transaction SHALL 還原 pre-update roots 與舊 active overlay／manifest
- **THEN** phase SHALL exit 1 並保留 recovery evidence

#### Scenario: 發現未完成 transaction

- **WHEN** 下次執行發現 journal 尚未 committed
- **THEN** 系統 SHALL 先依 backup 恢復，或在無法證明 rollback 前提時停止
- **THEN** SHALL NOT 直接開始新的 npx transaction

#### Scenario: grouped state write 後 finalize 中斷

- **WHEN** successful skills 已共同寫入 schema v2 state，但只有部分 journals 到達 `COMMITTED`
- **THEN** 每個 `VERIFIED` journal SHALL 以事前保存的 expected SkillState fingerprint 比對 active manifest
- **THEN** fingerprint 吻合時 SHALL 完成 commit cleanup，不得 rollback 已提交 skill
- **THEN** fingerprint 不吻合或 state 無法證明時 SHALL rollback 或停止，不得猜測完成

### Requirement: 單一 canonical overlay

同一 canonical skill SHALL 只有一份所有 agents 共用的 overlay。canonical 與 agent-visible roots SHALL 依 real path 去重；獨立 copy roots 仍需 materialize 並驗證相同 effective tree。

#### Scenario: npx projection symlink 指向 canonical root

- **WHEN** agent-visible root 是 symlink，且 real path 等於已知 canonical active root
- **THEN** reconcile SHALL 將兩者去重，不得視為不安全 legacy symlink
- **WHEN** root symlink 指向 canonical active roots 以外的位置
- **THEN** migration SHALL fail closed，且不得跟隨或改寫該 symlink

#### Scenario: 舊 target copies 完全相同

- **WHEN** 多個 legacy target copies 的 local content 完全相同
- **THEN** migration MAY 合併成單一 canonical overlay
- **THEN** verified 後 SHALL 安全清理不再使用的 legacy copies

#### Scenario: 舊 target copies 有不同修改

- **WHEN** legacy targets 對同一 canonical skill 有不同 local content
- **THEN** migration SHALL 停止該 skill 並顯示各 target hashes／changed files
- **THEN** SHALL 要求選擇 canonical 版本或另建不同 canonical skill ID
- **THEN** SHALL NOT 建立 per-agent overlay 或猜測合併

### Requirement: schema v1 可遷移到 per-file schema v2

現有 directory-level `npx-first-party.yaml` SHALL 使用其 source commit 取得 base tree，並展開為 per-file entries。overlay bytes／tombstones SHALL 保存於 user-only overlay directory。

#### Scenario: v1 directory baseline 仍 clean

- **WHEN** v1 source commit 可取得，且 directory source／local hashes 仍符合 v1 baseline
- **THEN** migration SHALL 自動產生 per-file state，overlay 為空
- **THEN** SHALL 備份舊 schema v1 manifest後原子切換

#### Scenario: v1 baseline 已有 local drift

- **WHEN** v1 directory hash 不吻合，但 source commit 可取得
- **THEN** migration SHALL 以該 commit 作為 base 逐檔分類，不把整個 skill 降級成單一 no-base
- **WHEN** base commit 無法取得
- **THEN** 受影響 files SHALL fail closed 為 no-base

#### Scenario: schema v2 file entry 語意

- **WHEN** reconcile 寫入一個有 overlay 的 file entry
- **THEN** `src_hash` SHALL 是本輪接受的 upstream base hash
- **THEN** `dst_hash_at_sync` SHALL 是 overlay materialize 後的 expected effective hash
- **THEN** overlay metadata SHALL 記錄 `file` 或 `deleted`、hash 與 safe relative path
- **THEN** missing source／local SHALL 使用固定 sentinel，不得與空檔案 hash 相同

### Requirement: overlay 與 transaction state 為 user-only

manifest、overlay bytes、deletion metadata、transaction journal 與 backups SHALL 留在 user config directory，使用 user-only permissions，且不得被 project sync、Git、public report 或一般 log 收集。

#### Scenario: 顯示 conflict diff

- **WHEN** 使用者在本機 TTY 主動要求 `Ds`、`Dl` 或 `Dc`
- **THEN** 系統 MAY 顯示檔案內容差異
- **THEN** 非互動 log、summary 與 audit SHALL 只顯示 canonical ID、safe relative path、hash、size、state 與 decision，不得輸出 overlay bytes

#### Scenario: transaction 成功與失敗的 retention

- **WHEN** pure clean transaction 成功且沒有使用者內容被 overwrite
- **THEN** 暫存 backup MAY 清除
- **WHEN** use-upstream 覆蓋 local content，或 transaction／rollback 失敗
- **THEN** timestamped backup 與 recovery evidence SHALL 保留並回報位置

### Requirement: npx phase 失敗不得遺失 local intent

任何第一方 add、overlay、verification、state 或 rollback 失敗都 SHALL 保留可恢復的 local intent，且不得宣稱完成該 skill migration。

#### Scenario: npx 或 transaction 失敗

- **WHEN** 任何第一方 add、overlay、verification、state 或 rollback 步驟失敗
- **THEN** phase SHALL 以非零結果或明確失敗摘要結束
- **THEN** active overlay 或 transaction backup SHALL 保留 local intent
- **THEN** ai-dev SHALL 不宣稱完成該 skill migration

### Requirement: 舊 copy ownership 安全遷移

首次遷移 SHALL 先盤點舊 manifest、目標內容與 canonical IDs，再安裝 npx 版本。只有舊項目可證明由 ai-dev 管理、未被使用者修改，且 npx 安裝已讀回驗證時，才可移除舊 manifest ownership 與舊副本。

#### Scenario: 未修改的同名舊副本

- **WHEN** 舊 manifest 證明目標 skill 由 `custom-skills` 管理，且目標 hash 與已知 base 相同
- **THEN** 遷移 SHALL 安裝並驗證 npx 版本
- **THEN** 驗證成功後才可移除舊 manifest entry 與不再使用的舊副本

#### Scenario: 使用者修改過舊副本

- **WHEN** 舊目標內容與 manifest base 不同，或無法證明 ownership
- **THEN** base 可取得時 SHALL 將舊副本送入 per-file planner；base 不可取得時 SHALL 分類為 no-base
- **THEN** local-only SHALL 轉為 persistent overlay；both-changed／no-base SHALL 完成 keep-local、use-upstream 或 abort decision
- **THEN** SHALL 不以 `--yes`、force 或 orphan cleanup 繞過 decision 或 transaction backup

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
