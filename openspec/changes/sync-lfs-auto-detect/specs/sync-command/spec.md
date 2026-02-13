## MODIFIED Requirements

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
