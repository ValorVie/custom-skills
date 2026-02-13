## 1. 更新 UDS CLI

- [x] 1.1 執行 `npm update -g universal-dev-standards` 確保 CLI 為最新版本
- [x] 1.2 執行 `uds --version` 確認版本號（v4.2.0）

## 2. 備份與更新 .standards/

- [x] 2.1 記錄更新前的 `.standards/` 檔案數量與 `manifest.json` 版本（25 個 .ai.yaml, upstream 4.3.0-alpha.1）
- [N/A] 2.2 ~~執行 `uds update` 更新 `.standards/` 目錄~~ — 上游變更（Industry Standards metadata）僅存在於 core/*.md，UDS CLI 未轉換至 ai/standards/*.ai.yaml，.standards/ 實質上不需更新
- [N/A] 2.3 ~~執行 `git diff --stat .standards/` 確認變更範圍~~ — 同上

## 3. 驗證

- [N/A] 3.1 ~~確認 `manifest.json` 的 upstream 版本號已更新~~ — .standards/ 無變更
- [N/A] 3.2 ~~抽樣檢查 .ai.yaml 檔案包含新的 industry standards metadata~~ — 上游 ai/standards/ 亦無此 metadata
- [N/A] 3.3 ~~確認 `.ai.yaml` 檔案數量未減少~~ — 無變更

## 4. 更新同步狀態

- [x] 4.1 執行 `python skills/custom-skills-upstream-sync/scripts/analyze_upstream.py --source universal-dev-standards --update-sync`
- [x] 4.2 確認 `upstream/last-sync.yaml` 中 commit 已更新為 `9e4403c`（synced_at: 2026-02-03）
