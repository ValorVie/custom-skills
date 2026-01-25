# setup-script Specification Delta

## MODIFIED Requirements

### Requirement: Update Logic (更新邏輯)

腳本 MUST (必須) 實作 `update` 指令以進行每日更新，簡化為只負責更新工具與拉取 repo，不再執行分發。

#### Scenario: 每日更新

給定已安裝的環境
當執行 `ai-dev update` 時
則應該只執行：
1. 更新全域 NPM 套件（除非 `--skip-npm`）
2. 在已 clone 的儲存庫中執行 `git fetch --all` 與 `git reset --hard origin/HEAD`（除非 `--skip-repos`）

且不應該執行：
- Stage 2（整合 skills）
- Stage 3（分發到目標目錄）
- `copy_skills()` 或任何分發操作

#### Scenario: 跳過特定步驟

給定已安裝的環境
當執行 `ai-dev update --skip-npm` 時
則應該只執行 repo 更新

當執行 `ai-dev update --skip-repos` 時
則應該只執行 NPM 更新

### Requirement: Project Directory Sync (專案目錄同步)

腳本 MUST (必須) 將專案目錄同步選項移至 `ai-dev clone` 指令。

#### Scenario: update 不再支援專案同步選項

給定執行 `ai-dev update --help` 時
則不應該顯示：
- `--sync-project` 選項
- `--no-sync-project` 選項

這些選項應移至 `ai-dev clone`。
