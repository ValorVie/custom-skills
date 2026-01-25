# third-party-catalog Specification

## Purpose

提供第三方 AI 輔助開發資源的探索、評估和參考功能,讓使用者能自主選擇並手動整合外部專案到自己的環境。

## ADDED Requirements

### Requirement: 第三方資源目錄結構

本專案 MUST (必須) 提供 `third-party/` 目錄結構,用於存放第三方專案的參考資訊。

#### Scenario: 目錄結構符合規範

給定專案根目錄存在時
- **WHEN** 檢查專案目錄結構
- **THEN** 應存在以下目錄和檔案:
  - `third-party/README.md` (索引入口)
  - `third-party/templates/` (文件模板目錄)
  - `third-party/catalog/` (專案資訊目錄)

#### Scenario: 與現有系統隔離

給定 `third-party/` 和 `upstream/` 並存時
- **WHEN** 使用者瀏覽專案結構
- **THEN** 兩者應明確區隔:
  - `upstream/` 追蹤已整合資源
  - `third-party/` 提供待評估資源參考
  - 不應有內容重複或功能混淆

### Requirement: 專案資訊模板

本專案 MUST (必須) 提供標準化的專案資訊模板,確保所有第三方資源描述格式一致。

#### Scenario: 專案資訊模板完整

給定 `third-party/templates/project-entry.md` 存在時
- **WHEN** 讀取模板內容
- **THEN** 應包含以下章節:
  - 專案基本資訊(名稱、GitHub 連結、授權、維護狀態)
  - 功能概述與特色清單
  - 適用場景與目標使用者
  - 手動安裝指南(步驟化說明)
  - 與 custom-skills 的整合建議
  - 最後更新日期與來源版本

#### Scenario: 模板易於使用

給定新增專案資訊需求時
- **WHEN** 使用者複製模板並填寫內容
- **THEN** 應能在 30 分鐘內完成基本資訊填寫
- **AND** 所有必填欄位應有清晰的說明或範例

### Requirement: 專案資訊檔案

本專案 MUST (必須) 為每個收錄的第三方專案提供獨立的資訊檔案。

#### Scenario: wshobson/agents 專案資訊完整

給定 `third-party/catalog/wshobson-agents.md` 存在時
- **WHEN** 讀取檔案內容
- **THEN** 應包含:
  - 專案概述(108 代理、129 技能、72 工具)
  - 主要功能分類(Agents, Commands, Skills, Workflows, Languages, Infrastructure)
  - GitHub 連結與授權資訊
  - 手動安裝指南(如何從 GitHub 獲取並配置)
- **AND** 所有章節應使用繁體中文撰寫(技術術語保留英文)

#### Scenario: 專案資訊檔案命名規範

給定新增第三方專案時
- **WHEN** 建立專案資訊檔案
- **THEN** 檔名應遵循 `{owner}-{repo}.md` 格式
- **AND** 使用小寫字母和連字號(kebab-case)
- **例如**: `wshobson-agents.md`, `obra-superpowers.md`

### Requirement: 索引文件

本專案 MUST (必須) 提供統一的索引文件,列出所有已收錄的第三方資源。

#### Scenario: 索引文件結構清晰

給定 `third-party/README.md` 存在時
- **WHEN** 讀取索引文件
- **THEN** 應包含:
  - 第三方目錄的用途說明
  - 與 `upstream/` 系統的關係
  - 所有已收錄專案的摘要表格(名稱、簡介、功能規模、連結)
  - 如何提交新專案的指引

#### Scenario: 索引文件易於導航

給定使用者需要探索第三方資源時
- **WHEN** 開啟 `third-party/README.md`
- **THEN** 應能在 5 分鐘內:
  - 理解第三方目錄的定位
  - 瀏覽所有可用資源
  - 點擊連結查看特定專案詳情

### Requirement: 評估檢查清單

本專案 MUST (必須) 提供評估檢查清單,幫助使用者判斷是否採用特定第三方資源。

#### Scenario: 評估檢查清單涵蓋關鍵面向

給定 `third-party/templates/evaluation-checklist.md` 存在時
- **WHEN** 讀取檢查清單
- **THEN** 應包含以下評估維度:
  - 功能適配性(是否解決實際需求)
  - 授權相容性(是否與專案授權相容)
  - 維護狀態(最後更新時間、活躍度)
  - 與現有功能的重疊度
  - 學習成本與複雜度

#### Scenario: 使用者可依據檢查清單做決策

給定使用者評估 wshobson/agents 專案時
- **WHEN** 依照檢查清單逐項評估
- **THEN** 應能明確判斷:
  - 是否值得花時間學習此專案
  - 是否應整合到自己的環境
  - 是否應提議納入 `upstream/` 系統

### Requirement: 專案文件整合

本專案 MUST (必須) 在主要文件中說明第三方資源目錄的存在與用途。

#### Scenario: README 提及第三方目錄

給定 `README.md` 更新後
- **WHEN** 讀取 README 的「功能特色」或「專案結構」章節
- **THEN** 應包含:
  - 第三方資源目錄的簡介(1-2 句話)
  - 連結到 `third-party/README.md`
  - 與 `upstream/` 的差異說明

#### Scenario: project.md 反映新目錄

給定 `openspec/project.md` 更新後
- **WHEN** 檢查「目錄結構原則」章節
- **THEN** 應包含:
  - **`third-party/`**: 第三方專案參考資訊(待評估資源)
  - 說明其與 `upstream/` 的關係

### Requirement: 版本控制與協作

本專案 MUST (必須) 將第三方資源目錄納入版本控制,並支援社群貢獻。

#### Scenario: 目錄內容受版本控制

給定 `.gitignore` 檔案存在時
- **WHEN** 檢查忽略規則
- **THEN** `third-party/` 目錄不應被排除
- **AND** 所有 `.md` 檔案應被追蹤

#### Scenario: 社群可提交新專案

給定使用者發現新的優質第三方專案時
- **WHEN** 依照 `third-party/README.md` 的指引
- **THEN** 應能:
  - 複製專案資訊模板
  - 填寫完整資訊
  - 提交 Pull Request
- **AND** 維護者應在 7 天內審核並合併或提出修改建議
