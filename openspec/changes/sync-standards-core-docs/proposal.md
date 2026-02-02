## Why

universal-dev-standards 上游在 `9e4403c` 對 29 個 core 文件新增了 `Industry Standards` 和 `References` metadata 欄位，將 UDS 各規範對應到業界標準（ISO 12207、WCAG、OWASP 等）。本專案的 `.standards/` 目錄是由 UDS CLI 轉換產生的 `.ai.yaml` 格式，目前停留在上游 `a6412d7` 版本，落後 19 個 commit。需要同步以取得最新的標準對照資訊。

## What Changes

- 更新 `.standards/` 目錄至上游最新版本，透過 `uds update` 重新生成 `.ai.yaml` 檔案
- 驗證 `.standards/manifest.json` 的版本資訊正確更新
- 更新 `upstream/last-sync.yaml` 中 `universal-dev-standards` 的同步狀態

## Capabilities

### New Capabilities

（無新功能）

### Modified Capabilities

- `standards-sync`: `.standards/` 目錄內容更新，新增 Industry Standards / References metadata

## Impact

- `.standards/*.ai.yaml` — 多數檔案會新增 industry_standards 相關欄位
- `.standards/manifest.json` — 版本號更新
- `upstream/last-sync.yaml` — 同步 commit 更新
- 不影響 skills、commands、agents 等其他目錄
- 不影響 CLAUDE.md（其引用的 .standards 路徑不變）
