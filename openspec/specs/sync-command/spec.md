# Sync Command Specification

## Purpose

`ai-dev sync` 子命令群管理 custom-skills 與外部目錄之間的雙向同步（init / push / pull / status / add / remove）。
## Requirements
### Requirement: sync init 子指令初始化同步環境

系統 SHALL 提供 `ai-dev sync init --remote <url>` 子指令，執行以下步驟：

1. 驗證 Git 已安裝
2. 若已存在 sync.yaml，詢問使用者是否覆蓋
3. 呼叫 `git_init_or_clone()` 建立/更新 sync repo
4. 建立預設同步目錄子目錄
5. **偵測 git-lfs 安裝狀態並設定 LFS**
6. 寫入 `.gitignore` 和 `.gitattributes`（含動態 LFS pattern）
7. 若為 clone（第二台機器），先還原 repo→local
8. 產生 plugin manifest
9. 執行 local→repo 同步
10. **掃描 repo 中大檔案，產生 LFS pattern**
11. **若有 LFS pattern 且為既有 repo，執行 migrate**
12. Commit、pull --rebase、push
13. 儲存 sync.yaml
14. 若為 clone，自動安裝 plugin

**LFS 行為**：
- git-lfs 已安裝：自動 `git lfs install --local`，偵測大檔案後寫入 LFS gitattributes 規則
- git-lfs 未安裝且有大檔案：顯示警告建議安裝
- git-lfs 未安裝且無大檔案：靜默不處理

#### Scenario: init 時 git-lfs 已安裝且有大檔案
- **WHEN** 系統已安裝 git-lfs 且 sync repo 中存在超過 50 MB 的 sqlite3 檔案
- **THEN** 系統 SHALL 執行 `git lfs install --local`，偵測 pattern，寫入 `.gitattributes` 含 LFS 規則，並顯示 LFS 追蹤訊息

#### Scenario: init 時 git-lfs 未安裝且有大檔案
- **WHEN** 系統未安裝 git-lfs 且 sync repo 中存在超過 50 MB 的檔案
- **THEN** 系統 SHALL 顯示黃色警告建議安裝 git-lfs，但不阻擋 init 流程

#### Scenario: init 時無大檔案
- **WHEN** sync repo 中所有檔案皆小於 50 MB
- **THEN** 系統 SHALL 不寫入 LFS 規則，行為與原有相同

### Requirement: sync push 子指令推送本機變更

系統 SHALL 提供 `ai-dev sync push` 子指令，執行以下步驟：

1. 載入 sync.yaml
2. 寫入 `.gitignore` 和 `.gitattributes`
3. 執行 local→repo 同步
4. **掃描 repo 中大檔案，產生 LFS pattern**
5. **寫入含 LFS pattern 的 `.gitattributes`**
6. 產生 plugin manifest
7. Commit、pull --rebase、push
8. 更新 sync.yaml 的 last_sync

#### Scenario: push 時偵測到新的大檔案
- **WHEN** git-lfs 已安裝且 sync 後 repo 中出現新的超過 50 MB 的檔案類型
- **THEN** `.gitattributes` SHALL 自動加入該檔案類型的 LFS track 規則，新檔案 SHALL 以 LFS 方式 commit

#### Scenario: push 時無大檔案
- **WHEN** sync 後 repo 中無超過 50 MB 的檔案
- **THEN** `.gitattributes` SHALL 不包含 LFS 規則

### Requirement: sync pull 子指令拉取遠端變更

系統 SHALL 提供 `ai-dev sync pull` 子指令，從遠端 repo 拉取變更到本機。

- 執行前 SHALL 偵測本機是否有未推送的變更
- 若有變更，SHALL 顯示變更清單與互動式選項（先 push 再 pull / 強制覆蓋 / 取消）
- 若無變更或使用者確認後，執行 `git pull --rebase`
- 對每個目錄執行檔案同步（repo 子目錄 → 本機）
- 提供 `--no-delete` 選項，防止刪除本機有但 repo 沒有的檔案
- 提供 `--force` 選項，跳過本機變更偵測直接執行 pull
- 顯示同步結果摘要

#### Scenario: 本機無異動時正常拉取

- **WHEN** 使用者執行 `ai-dev sync pull`，且本機與 repo 一致
- **THEN** 系統直接執行 pull 流程，行為與原有相同

#### Scenario: 本機有異動時顯示互動選項

- **WHEN** 使用者執行 `ai-dev sync pull`，且本機有未推送的變更
- **THEN** 系統 SHALL 顯示變更清單與三個選項，等待使用者選擇

#### Scenario: 使用 --force 跳過偵測

- **WHEN** 使用者執行 `ai-dev sync pull --force`
- **THEN** 系統 SHALL 跳過本機變更偵測，直接執行 pull 流程

#### Scenario: --force 與 --no-delete 同時使用

- **WHEN** 使用者執行 `ai-dev sync pull --force --no-delete`
- **THEN** 系統 SHALL 跳過偵測並執行 pull，且不刪除本機多出的檔案

#### Scenario: 無遠端變更

- **WHEN** 使用者執行 `ai-dev sync pull`，但遠端無新 commit
- **THEN** 系統顯示「已是最新狀態」

#### Scenario: 未初始化時拉取

- **WHEN** 使用者執行 `ai-dev sync pull`，但尚未執行 `sync init`
- **THEN** 系統顯示錯誤訊息並提示先執行 `ai-dev sync init`

### Requirement: sync status 子指令顯示同步狀態

系統 SHALL 提供 `ai-dev sync status` 子指令，以 Rich 表格顯示各同步目錄的狀態。

- 顯示每個目錄的：本機變更檔案數、遠端狀態（最新/落後 N commits）、最後同步時間
- 使用 Rich Table 格式化輸出

#### Scenario: 顯示同步狀態

- **WHEN** 使用者執行 `ai-dev sync status`
- **THEN** 系統以表格顯示所有同步目錄的本機變更數、遠端狀態和最後同步時間

#### Scenario: 未初始化時查看狀態

- **WHEN** 使用者執行 `ai-dev sync status`，但尚未初始化
- **THEN** 系統顯示「尚未初始化，請先執行 ai-dev sync init」

---

### Requirement: sync add 子指令新增同步目錄

系統 SHALL 提供 `ai-dev sync add <path>` 子指令，將新目錄加入同步清單。

- 接受目錄路徑作為參數
- 提供 `--profile` 選項指定 ignore profile（預設為 `custom`）
- 提供 `--ignore` 選項指定自訂排除模式（可多次使用）
- 驗證路徑存在且為目錄
- 新增到 `sync.yaml`
- 在 sync-repo 中建立對應子目錄
- 更新 `.gitignore`

#### Scenario: 新增自訂目錄

- **WHEN** 使用者執行 `ai-dev sync add ~/.gemini --ignore "cache/" --ignore "*.log"`
- **THEN** 系統將 `~/.gemini` 加入同步清單，建立 repo 子目錄，更新 `.gitignore`

#### Scenario: 路徑不存在

- **WHEN** 使用者執行 `ai-dev sync add /nonexistent`
- **THEN** 系統顯示錯誤「目錄不存在」

#### Scenario: 重複新增

- **WHEN** 使用者執行 `ai-dev sync add ~/.claude`，但該目錄已在同步清單中
- **THEN** 系統顯示提示「該目錄已在同步清單中」

---

### Requirement: sync remove 子指令移除同步目錄

系統 SHALL 提供 `ai-dev sync remove <path>` 子指令，從同步清單移除目錄。

- 從 `sync.yaml` 移除該目錄
- 詢問是否也從 repo 中刪除對應子目錄
- 更新 `.gitignore`
- 不可移除最後一個目錄

#### Scenario: 移除自訂目錄

- **WHEN** 使用者執行 `ai-dev sync remove ~/.gemini`
- **THEN** 系統從設定中移除，詢問是否刪除 repo 中的 `gemini/` 子目錄

#### Scenario: 移除不存在的目錄

- **WHEN** 使用者執行 `ai-dev sync remove /not-tracked`
- **THEN** 系統顯示錯誤「該目錄不在同步清單中」

