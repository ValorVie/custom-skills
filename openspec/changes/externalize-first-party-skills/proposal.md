## Why

第一方 skills 目前與 ai-dev CLI、文件、測試及其他框架資源放在同一個 `custom-skills` repository。只修改一個 skill 也必須更新整個框架來源，且 ai-dev 的 copy、ManifestTracker、toggle 與 `npx skills` 同時擁有相同目標目錄，增加發布與相容性負擔。

本變更把第一方 skills 移到獨立的公開 `ValorVie/ai-dev-skills` repository，並讓 ai-dev 使用既有 `npx-skills` phase 安裝與更新。`custom-skills` 保留框架、設定與非 skill 資源管理，兩邊可以各自發布。

## What Changes

- 建立公開的 `ValorVie/ai-dev-skills` collection repository，保存目前 `skills/` 下的第一方 skill 及其自帶 scripts、references、assets、evals 與測試。
- 清理第一方 skill 中的內部名稱、私有路徑與逃出 skill 根目錄的相對連結；新 repository 加入 metadata、內部連結及公開邊界驗證。
- 將第一方 skill 的期望清單加入 `upstream/npx-skills.yaml`，使用明確 skill 名稱與全域 agent IDs 批次執行 `npx skills add`／`npx skills update`，不使用 wildcard 自動納入新 skill 或不相關 agent。
- 以 frontmatter `name` 作為 canonical skill ID；初始遷移包含 `custom-simplify` 目錄名到 `simplify` 的一次性對照。
- **BREAKING**：`ai-dev clone` 不再從 `~/.config/custom-skills/skills/` 分發第一方 skills，也不再以 ai-dev ManifestTracker 擁有這批目標檔案。
- **BREAKING**：`ai-dev toggle`、resource-disable 與 standards profile 不再搬動 npx-managed skill 目錄；這類操作應停止並顯示對應的 `npx skills` 指引，非 npx-managed 資源維持既有行為。
- 更新 `ai-dev list`／status 的來源辨識，使 npx-managed 第一方 skill 顯示為 `ai-dev-skills`，而不是 `user`。
- 先完成 npx 安裝與讀回驗證，再移除舊 manifest ownership 與未修改的舊副本；偵測到本機修改、名稱衝突或目標路徑不一致時停止，不自動覆蓋。
- 保留 ECC 白名單 skill、custom repo skill、project-template repo-local skill，以及 commands、agents、workflows、plugins 的現行管理方式；它們不在本次遷移範圍。

## Capabilities

### New Capabilities

- `first-party-skill-distribution`: 定義第一方公開 skill collection、明確清單、npx 安裝／更新、公開邊界、遷移驗證與回復契約。

### Modified Capabilities

- `skill-npm-integration`: 從提示第三方 `npx skills` 指令，擴充為 ai-dev 依 declarative manifest 安裝與更新第一方 skills。
- `clone-command`: 移除第一方 `skills/` 的 Stage 3 copy ownership，保留其他資源與 ECC 分發。
- `cli-distribution`: 調整 Stage 3 的第一方資源映射與 manifest source ownership。
- `skill-listing`: 依 npx 管理清單辨識第一方 skill 來源及 canonical ID。
- `skill-toggle`: npx-managed skill 不再使用檔案移動切換，改為 fail-closed 指引。
- `resource-disable`: disabled 目錄不再接管 npx-managed skill；其他資源維持原流程。
- `standards-profiles`: profile 切換遇到 npx-managed skill 時不得搬動或刪除其安裝內容。

## Impact

- 新增公開 repository：`ValorVie/ai-dev-skills`。建立 repository、首次發布及任何 remote push 都是獨立外部 mutation，實作時需在操作點確認。
- `custom-skills` 受影響區域包括 `skills/`、`upstream/npx-skills.yaml`、`script/services/npx_skills/`、`script/utils/shared.py`、list／toggle／standards 流程、manifest migration、測試、README、架構文件與 CHANGELOG。
- 現有 `ecc-whitelist-distribution` change 不被取代；ECC 仍由 `ai-dev clone` 白名單分發與 ManifestTracker 管理。
- project-template 內隨專案版本控制的 skills 不改用 global npx 安裝。
- 不修改正式環境、資料庫、服務、credential 或流量。
