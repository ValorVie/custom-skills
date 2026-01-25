# setup-script Spec Delta

## MODIFIED Requirements

### Requirement: Update Logic (更新邏輯)

腳本 MUST (必須) 實作 `update` 指令以進行每日更新。

> **變更說明**：將原本的 `maintain` 指令重新命名為 `update`，使指令名稱更符合其「更新」的語意。

#### Scenario: 每日更新

給定已安裝的環境
當執行 `ai-dev update` 時
則應該：
1. 更新全域 NPM 套件
2. 在已 clone 的儲存庫中執行 `git fetch --all` 與 `git reset --hard origin/HEAD`
3. 重新複製 skills 到目標目錄，覆寫舊檔

#### Scenario: 跳過特定步驟

給定已安裝的環境
當執行 `ai-dev update --skip-npm --skip-repos` 時
則應該只執行 skills 同步，跳過 NPM 與 Git 更新

