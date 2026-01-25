## ADDED Requirements

### Requirement: 重疊偵測功能

系統 SHALL 提供功能重疊偵測能力，識別本地資源與上游 repo 之間的功能重疊。

#### Scenario: 自動重疊偵測

- **GIVEN** 使用者執行 `/upstream-sync --new-repo` 或 `/upstream-compare`
- **WHEN** 分析 repo 內容
- **THEN** 比較 skills, commands, agents 的功能相似度
- **AND** 識別名稱相似的項目（Levenshtein distance < 3）
- **AND** 識別功能關鍵字匹配（tdd, test, commit, review 等）
- **AND** 輸出 `overlap_analysis` 欄位

#### Scenario: 重疊相似度計算

- **GIVEN** 需要比較兩個項目
- **WHEN** 計算相似度
- **THEN** 考慮名稱相似度（權重 40%）
- **AND** 考慮功能關鍵字匹配（權重 30%）
- **AND** 考慮目錄結構相似（權重 30%）
- **AND** 相似度 > 0.7 視為重疊

### Requirement: overlaps.yaml 生成

系統 SHALL 支援自動生成 overlaps.yaml 草稿。

#### Scenario: 生成重疊定義草稿

- **GIVEN** 使用者執行 `/upstream-compare --generate-overlaps`
- **WHEN** 分析完成
- **THEN** 在 `profiles/overlaps.yaml.draft` 生成草稿
- **AND** 包含偵測到的重疊群組
- **AND** 包含建議的 uds/ecc 對應
- **AND** 標記需要人工確認的項目

#### Scenario: 增量更新建議

- **GIVEN** 已存在 `profiles/overlaps.yaml`
- **WHEN** 分析發現新的重疊
- **THEN** 在報告中輸出 `suggested_overlaps_yaml_update`
- **AND** 提供可直接複製的 YAML 片段
- **AND** 不自動修改現有 overlaps.yaml

### Requirement: 重疊分析報告

系統 SHALL 在 upstream-compare 報告中包含詳細的重疊分析。

#### Scenario: 重疊項目列表

- **GIVEN** upstream-compare 分析完成
- **WHEN** 輸出報告
- **THEN** 包含 `detected_overlaps` 列表
- **AND** 每個重疊項包含 local 和 upstream 對應項目
- **AND** 包含建議的處理方式

#### Scenario: 新增非重疊項目

- **GIVEN** 上游有本地沒有的項目
- **WHEN** 該項目無重疊對應
- **THEN** 列在 `new_items_not_overlapping` 中
- **AND** 建議直接整合（無需在 overlaps.yaml 定義）

#### Scenario: 整合建議

- **GIVEN** 偵測到重疊
- **WHEN** 輸出報告
- **THEN** 提供 recommendation 欄位
- **AND** 說明哪個版本更適合哪個 profile
- **AND** 提供整合步驟建議

### Requirement: 重疊驗證

系統 SHALL 驗證 overlaps.yaml 的正確性。

#### Scenario: 項目存在性驗證

- **GIVEN** overlaps.yaml 定義了項目
- **WHEN** 執行 `ai-dev standards validate-overlaps`
- **THEN** 檢查所有列出的 skills 是否存在
- **AND** 檢查所有列出的 standards 是否存在
- **AND** 報告不存在的項目

#### Scenario: 格式驗證

- **GIVEN** overlaps.yaml 存在
- **WHEN** 載入時
- **THEN** 驗證 version 欄位存在
- **AND** 驗證 groups 結構正確
- **AND** 驗證每個體系至少有一個項目

#### Scenario: 完整性檢查

- **GIVEN** 重疊定義完成
- **WHEN** 切換 profile
- **THEN** 確保不會遺漏未定義的重疊
- **AND** 警告可能的重複功能（名稱相似但未在 overlaps.yaml）
