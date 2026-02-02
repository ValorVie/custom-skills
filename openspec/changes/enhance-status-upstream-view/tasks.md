## 1. 補齊設定儲存庫表

- [x] 1.1 擴充 `status.py` 的 repo 清單，從 `REPOS` 字典取得全部 6 個 repo（取代目前寫死的 4 個）
- [x] 1.2 改寫設定儲存庫表的狀態欄位，使用 `git rev-parse HEAD` vs `git rev-parse origin/{branch}` 比對，顯示「✓ 最新」或「↑ 有可用更新」
- [x] 1.3 處理降級情境：目錄不存在顯示「未安裝」、非 git 目錄或無法比對時維持原有行為

## 2. 新增上游同步狀態表

- [x] 2.1 新增讀取 `upstream/last-sync.yaml` 的邏輯，取得各 repo 的 commit 和 synced_at
- [x] 2.2 實作 commit 比對函式：在 `~/.config/<repo>/` 執行 `git rev-list --count <last-sync-commit>..HEAD` 計算落後數
- [x] 2.3 建立「上游同步狀態」Rich Table，欄位：名稱、同步於（MM-DD 格式）、狀態（✓ 同步 / ⚠ 落後 N / ? 無法比對 / 未安裝）
- [x] 2.4 處理 `last-sync.yaml` 不存在時不顯示此表

## 3. 驗證

- [x] 3.1 執行 `ai-dev status` 確認兩張表正確顯示
- [x] 3.2 驗證各降級情境（目錄不存在、commit 不存在、yaml 不存在）
