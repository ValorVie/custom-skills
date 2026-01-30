## MODIFIED Requirements

### Requirement: Install Logic (安裝邏輯)

腳本 MUST 實作 `install` 指令以執行初始設定，使用三階段複製流程。

> **變更說明**：重構為三階段流程、新增 OpenCode skills/commands 支援、新增 Claude Code native 安裝檢查。
> **新增**：install 指令 MUST 同時 clone 已註冊的 custom repos。

#### Scenario: macOS 全新安裝

給定已安裝 Homebrew 的全新 macOS 環境
當執行 `ai-dev install` 時
則應該：
1. 檢查 Node.js 與 Git
2. 檢查 Claude Code CLI 是否已安裝，若未安裝則顯示 native 安裝指引
3. 建立所有必要目錄
4. 安裝全域 NPM 套件（不包含 `@anthropic-ai/claude-code`）
5. Clone 外部儲存庫到 `~/.config/`（Stage 1）
6. Clone 已註冊的 custom repos 到對應目錄
7. 複製 skills 到所有目標目錄（Stage 3）

#### Scenario: Clone custom repos

給定 `~/.config/ai-dev/repos.yaml` 存在已註冊的 custom repos
當執行 `ai-dev install` 時
則 MUST：
1. 讀取 `repos.yaml` 取得 custom repos 清單
2. 對每個 repo，若本地目錄不存在則執行 clone
3. 若本地目錄已存在則跳過
4. Clone 失敗時顯示警告並繼續（不中斷安裝流程）

#### Scenario: 無 custom repos 設定檔

給定 `~/.config/ai-dev/repos.yaml` 不存在
當執行 `ai-dev install` 時
則 MUST 正常執行所有步驟，跳過 custom repos clone 階段

### Requirement: Update Logic (更新邏輯)

腳本 MUST 實作 `update` 指令以進行每日更新，簡化為只負責更新工具與拉取 repo，不再執行分發。

> **變更說明**：update 指令 MUST 同時拉取已註冊的 custom repos。

#### Scenario: 每日更新（含 custom repos）

給定已安裝的環境且 `repos.yaml` 存在已註冊的 custom repos
當執行 `ai-dev update` 時
則應該執行：
1. 更新全域 NPM 套件（除非 `--skip-npm`）
2. 在已 clone 的內建儲存庫中執行 `git fetch --all` 與 `git reset --hard origin/<branch>`（除非 `--skip-repos`）
3. 對每個 custom repo 執行相同的 fetch 與 reset 操作（除非 `--skip-repos`）

且不應該執行：
- Stage 2（整合 skills）
- Stage 3（分發到目標目錄）

#### Scenario: Custom repo 更新失敗

給定某 custom repo 的本地目錄不存在或 git 操作失敗
當執行 `ai-dev update` 時
則 MUST：
1. 顯示警告訊息
2. 繼續更新其他 repos（不中斷整體流程）

#### Scenario: Custom repo 更新通知

給定 custom repos 有新的 commits
當 update 完成後顯示更新摘要時
則 MUST 將有更新的 custom repos 一併列入摘要清單
