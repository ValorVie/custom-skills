# standards-sync Specification

## Purpose
TBD

## Requirements

### Requirement: .standards/ 目錄內容與上游同步

`.standards/` 目錄 SHALL 反映 universal-dev-standards 上游 core/ 的最新內容。

#### Scenario: 執行 uds update 後 .ai.yaml 包含新 metadata
- **WHEN** 執行 `uds update` 更新 `.standards/`
- **THEN** `.ai.yaml` 檔案 MUST 包含上游新增的 `industry_standards` 相關欄位
- **AND** `manifest.json` 的 upstream 版本號 MUST 更新

#### Scenario: 更新後檔案數量不減少
- **WHEN** 更新完成
- **THEN** `.standards/` 目錄的 `.ai.yaml` 檔案數量 MUST 大於或等於更新前的數量

#### Scenario: 更新後 last-sync.yaml 記錄正確
- **WHEN** 驗證通過並執行 `--update-sync`
- **THEN** `upstream/last-sync.yaml` 中 `universal-dev-standards` 的 commit MUST 等於上游 HEAD (`9e4403c`)
- **AND** `synced_at` MUST 更新為當前日期
