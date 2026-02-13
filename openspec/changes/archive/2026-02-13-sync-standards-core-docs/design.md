## Context

本專案的 `.standards/` 目錄由 UDS CLI 從 `core/*.md` 轉換為 `.ai.yaml` 格式，目前版本為 UDS 4.3.0-alpha.1（安裝於 2026-01-29）。上游已更新至 `9e4403c`，主要變更為 29 個 core 文件新增 `Industry Standards` 和 `References` metadata。

`.standards/` 的更新機制是透過 `uds update` 指令重新生成，而非手動 diff 合併 markdown 檔案。

## Goals / Non-Goals

**Goals:**
- 將 `.standards/` 更新至上游最新版本
- 驗證更新後的 `.ai.yaml` 檔案包含新的 industry standards metadata
- 更新 `upstream/last-sync.yaml` 記錄同步狀態

**Non-Goals:**
- 不修改 `.standards/` 的檔案格式或結構
- 不自訂或覆寫上游的 metadata 內容
- 不更新 CLAUDE.md 中的 .standards 引用（路徑不變）

## Decisions

### 1. 同步方式：使用 `uds update` 指令

**選擇**：執行 `uds update` 讓 UDS CLI 自動重新生成 `.ai.yaml` 檔案，而非手動複製 `core/*.md`。

**理由**：`.standards/` 是 UDS CLI 的產出物，格式為 `.ai.yaml`（經過結構化轉換）。手動複製 markdown 會破壞格式一致性。`uds update` 是官方支援的更新路徑。

**替代方案**：手動 diff 合併 — 但 `.ai.yaml` 格式與 `core/*.md` 不同，手動合併容易出錯。

### 2. 驗證方式：抽樣檢查 + manifest 版本

**選擇**：更新後抽樣檢查 2-3 個 `.ai.yaml` 檔案確認包含新 metadata，並確認 `manifest.json` 版本號已更新。

**理由**：29 個檔案逐一比對成本過高，且 UDS CLI 的轉換邏輯已由上游測試覆蓋。抽樣驗證足以確認同步成功。

### 3. 同步狀態更新：手動執行 analyze_upstream.py --update-sync

**選擇**：驗證完成後執行 `python skills/custom-skills-upstream-sync/scripts/analyze_upstream.py --source universal-dev-standards --update-sync`。

**理由**：這是現有的同步狀態管理機制，保持一致。

## Risks / Trade-offs

- **[Risk] `uds update` 可能引入非預期變更** → 透過 `git diff` 檢查更新後的差異，確認只有 metadata 新增
- **[Risk] UDS CLI 版本不匹配** → 先執行 `npm update -g universal-dev-standards` 確保 CLI 為最新
- **[Trade-off] 無法只更新 metadata 欄位** → `uds update` 是全量更新，可能連帶更新其他小幅修正。可接受，因為保持與上游一致是目標
