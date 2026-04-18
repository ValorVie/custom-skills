## MODIFIED Requirements

### Requirement: 直接讀取上游目錄 (Direct Upstream Access)

所有 upstream skill MUST (必須) 直接從 `~/.config/<repo>/` 讀取，不使用中間 sources 目錄。

> **變更說明**：ECC 的 `install_method` 從 `manual` 改為 `selective`，表示其分發規則由 `upstream/distribution.yaml` 定義。`upstream/ecc/mapping.yaml` 由 `upstream/distribution.yaml` 取代。

#### Scenario: 不使用 sources 目錄

給定執行任何 upstream skill 時
則不應該：
1. 建立或更新 `sources/` 目錄
2. 從 `~/.config/<repo>/` 複製到 `sources/<name>/`

比較操作應直接讀取 `~/.config/<repo>/`。

#### Scenario: sources.yaml install_method 語意

- **WHEN** 某來源的 `install_method` 為 `selective`
- **THEN** 表示該來源的分發規則定義在 `upstream/distribution.yaml`
- **THEN** `ai-dev clone` SHALL 讀取 distribution.yaml 執行選擇性分發
- **THEN** /custom-skills-upstream-ops audit 仍 SHALL 正常追蹤該來源的 commit 差異
