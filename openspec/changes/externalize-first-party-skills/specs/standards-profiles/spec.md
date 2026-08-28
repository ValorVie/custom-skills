## ADDED Requirements

### Requirement: Profile 切換不得接管 npx-managed skill

standards profile 計算 SHALL 辨識 npx declarative manifest 中的 canonical skill IDs。profile 可以顯示這些 skills 的重疊關係，但 SHALL NOT 透過 disabled 目錄、直接刪除或 copy 來切換其安裝狀態。

#### Scenario: dry-run 包含 npx-managed skill

- **WHEN** `ai-dev standards switch <profile> --dry-run` 的計算結果包含 npx-managed skill
- **THEN** 預覽 SHALL 將該項標示為 `npx-managed`
- **THEN** SHALL 顯示需要使用原生 npx 操作或調整 baseline manifest
- **THEN** SHALL 不把它列為即將移動的檔案

#### Scenario: apply 遇到 npx-managed skill

- **WHEN** standards profile 實際切換需要停用或啟用 npx-managed skill
- **THEN** 切換 SHALL 在修改任何該 skill 路徑前停止
- **THEN** SHALL 回報 canonical ID、來源與未執行的動作
- **THEN** 其他已完成計算不得被宣稱為完整 profile 切換成功

#### Scenario: profile 只影響非 npx-managed 資源

- **WHEN** profile 的變更清單不包含任何 npx-managed skill
- **THEN** 現有 non-destructive profile 切換行為 SHALL 維持不變
