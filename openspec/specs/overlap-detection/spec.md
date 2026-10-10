# overlap-detection Specification

## Purpose

定義功能重疊偵測機制，用於識別任一 repo（上游或新候選）與本專案之間的功能重疊，並輔助整合或排除決策。

重疊偵測由 `/custom-skills-upstream-ops overlap <target>` mode 提供（原 `/upstream-compare --new-repo` 與 `--generate-overlaps` 能力合併於此）。

## Requirements

### Requirement: 重疊偵測功能

系統 SHALL 提供功能重疊偵測能力，識別目標 repo 與本專案之間的功能重疊。

#### Scenario: 對已註冊來源偵測

- **GIVEN** 使用者執行 `/custom-skills-upstream-ops overlap <source-name>`
- **WHEN** target 存在於 `upstream/sources.yaml`
- **THEN** 讀取該來源的 `local_path`
- **AND** 比較 target 的 skills/commands/agents 與本專案對應目錄
- **AND** 輸出重疊清單（exact match / similar names / functional overlap）

#### Scenario: 對任意本地目錄偵測

- **GIVEN** 使用者執行 `/custom-skills-upstream-ops overlap <local-path>`
- **WHEN** 指定路徑是有效的本地目錄（不必為 git repo）
- **THEN** 掃描該目錄的 skills/commands/agents
- **AND** 比較本專案對應目錄
- **AND** 輸出重疊清單

#### Scenario: 重疊判斷依據

- **GIVEN** 比較兩個項目
- **WHEN** AI 判斷是否重疊
- **THEN** 考慮名稱完全相同（exact match）
- **AND** 考慮名稱相似（Levenshtein distance < 3 或縮寫／同義詞）
- **AND** 考慮功能關鍵字匹配（tdd、test、commit、review 等領域詞）
- **AND** 考慮 frontmatter description 與前 20 行的語意相似
- **AND** 不使用硬性數值門檻（由 AI 當下判斷）

### Requirement: 重疊分析報告

系統 SHALL 在 overlap mode 輸出結構化的 Markdown 報告。

#### Scenario: 報告包含重疊分類

- **GIVEN** 偵測完成
- **WHEN** 輸出報告
- **THEN** 包含「重疊清單」章節，分為 Exact Match / Similar Names / Functional Overlap 三類
- **AND** 每個重疊項包含本地 ↔ 目標對應項目與類型

#### Scenario: 報告包含全新項目

- **GIVEN** 目標 repo 有本專案無的項目
- **WHEN** 輸出報告
- **THEN** 列在「全新項目」章節
- **AND** 建議直接整合／評估後整合／跳過

#### Scenario: 報告包含下一步

- **GIVEN** 分析完成
- **WHEN** 輸出報告
- **THEN** 包含「下一步」章節
- **AND** 建議可能動作：整合（audit mode）、排除（distribution.yaml）
