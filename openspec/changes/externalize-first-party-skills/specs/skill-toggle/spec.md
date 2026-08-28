## MODIFIED Requirements

### Requirement: toggle 指令整合檔案移動機制 (MUST)

`toggle` 指令 MUST 只對非 npx-managed 資源使用檔案移動機制。當 canonical skill ID 出現在 npx declarative manifest 時，`toggle` MUST fail closed，不得呼叫 `disable_resource()`、`enable_resource()` 或直接操作 npx canonical copy／symlink。

#### Scenario: toggle --disable 觸發檔案移動

- **WHEN** 使用者對非 npx-managed resource 執行 `toggle --disable`
- **THEN** 系統 SHALL 呼叫 `disable_resource()` 移動檔案
- **THEN** 不再呼叫 `copy_skills()` 進行全量同步

#### Scenario: toggle --enable 觸發檔案還原

- **WHEN** 使用者對非 npx-managed resource 執行 `toggle --enable`
- **THEN** 系統 SHALL 呼叫 `enable_resource()` 還原檔案
- **THEN** 不再呼叫 `copy_skills()` 進行全量同步

#### Scenario: 停用 npx-managed skill

- **WHEN** 使用者對 npx-managed skill 執行 `toggle --disable`
- **THEN** 指令 SHALL 以 exit code 1 停止
- **THEN** SHALL 顯示 canonical ID、來源 repository 與對應的 `npx skills remove --global --agent <agent> <skill>` 指引
- **THEN** SHALL 不修改 skill 路徑、disabled 目錄或 toggle config

#### Scenario: 啟用 npx-managed skill

- **WHEN** 使用者對 npx-managed skill 執行 `toggle --enable`
- **THEN** 指令 SHALL 以 exit code 1 停止
- **THEN** SHALL 顯示由 declarative manifest 重裝該 skill 的 `npx skills add <repo> --skill <skill> --global --agent <agent> --yes` 指引
- **THEN** SHALL 不修改 skill 路徑、disabled 目錄或 toggle config

#### Scenario: target 無可靠 npx agent 對照

- **WHEN** ai-dev target 無法對應到目前 npx CLI 支援的 agent ID 或實際讀取路徑
- **THEN** 指引 SHALL 標示此 mapping 尚未驗證
- **THEN** SHALL 不猜測 agent 名稱或執行 remove／add
