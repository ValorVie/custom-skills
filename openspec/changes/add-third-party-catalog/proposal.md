# Change: 建立第三方資源目錄 (Third-Party Resource Catalog)

## Why

目前專案透過 `upstream/` 系統追蹤並整合精選的第三方資源(如 ECC, superpowers 等),但使用者缺乏一個統一的地方來:
1. 探索更多可參考的第三方專案(如 wshobson/agents 提供 108 個專門代理和 129 個技能)
2. 了解這些專案的功能特色與適用場景
3. 獲得手動安裝與整合的指引

建立獨立的第三方資源目錄可以讓使用者在不影響核心系統的情況下,自主探索和選擇性採用外部資源。

## What Changes

- **新增目錄結構**: 建立 `third-party/` 作為參考資源庫,與 `upstream/` 系統分離
- **新增文件模板**: 為每個第三方專案提供標準化的資訊結構
  - 專案概述與功能清單
  - 手動安裝指南
  - 與本專案的對照表(可選)
- **新增索引文件**: 提供所有第三方資源的統一入口
- **新增評估工作流**: 建立新增第三方資源的標準流程

## Impact

- **新增 capability**: `third-party-catalog` (第三方資源目錄管理)
- **影響範圍**:
  - 新增頂層目錄 `third-party/`
  - 新增文件模板 `third-party/templates/`
  - 更新專案文件 `README.md`, `docs/` 以說明資源目錄的用途
- **與現有系統關係**:
  - 不影響 `upstream/` 的同步機制
  - 不影響 `sources/` 的整合流程
  - 作為 `upstream/` 的前置探索階段,精選資源才納入 `upstream/sources.yaml`
