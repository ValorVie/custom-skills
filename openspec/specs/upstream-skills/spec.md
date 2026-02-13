# upstream-skills Specification

## Purpose
TBD - created by archiving change simplify-upstream-architecture. Update Purpose after archive.
## Requirements
### Requirement: upstream-sync Skill (上游同步 Skill)

`upstream-sync` MUST (必須) 專注於追蹤上游差異與提供初步建議。

#### Scenario: 檢查更新

給定執行 `/upstream-sync --check` 時
則應該：
1. 讀取 `upstream/sources.yaml` 取得上游來源清單
2. 比較 `~/.config/<repo>/` 的 HEAD 與 `last-sync.yaml` 記錄的 commit
3. 顯示有更新的 repo 列表與 commit 範圍
4. 不做任何檔案複製或同步操作

#### Scenario: 差異摘要

給定執行 `/upstream-sync --diff` 時
則應該：
1. 對有更新的 repo 執行 `git diff`
2. 生成簡潔的差異摘要（新增/修改/刪除的檔案數量）
3. 輸出到 `upstream/diff-report-YYYY-MM-DD.md`

#### Scenario: 初步整合建議

給定執行 `/upstream-sync --assess` 時
則應該：
1. 列出 repo 中有哪些資源類型（skills, agents, commands 等）
2. 與現有 `skills/` 比對，標記重疊項目
3. 給出 High/Medium/Low/Skip 的初步建議
4. 輸出到 `upstream/integration-assessment-YYYY-MM-DD.md`

#### Scenario: 職責限制

`upstream-sync` 不應該：
- 同步檔案到 `sources/` 目錄
- 執行深度品質分析
- 生成 OpenSpec 提案

### Requirement: upstream-compare Skill (上游比較 Skill)

`upstream-compare` MUST (必須) 專注於深度品質比較與分析報告生成。

#### Scenario: 報告檔案輸出

給定執行 `/upstream-compare` 時
則必須：
1. 讀取結構化報告（`upstream/reports/structured/analysis-*.yaml`）
2. 分析內容並生成 Markdown 報告
3. **使用 Write 工具儲存報告至 `upstream/reports/analysis/compare-YYYY-MM-DD.md`**
4. 在對話中輸出精簡摘要並告知報告檔案位置

#### Scenario: 品質比較

給定執行 `/upstream-compare` 時
則應該：
1. 對重疊的資源進行詳細比較
2. 提取內容特徵（雙語、程式碼範例、圖表等）
3. 計算品質評分
4. 生成詳細比較報告

#### Scenario: 特定資源比較

給定執行 `/upstream-compare --resource tdd` 時
則應該：
1. 只比較名為 `tdd` 的資源
2. 顯示本地版本與所有上游版本的差異
3. 提供 KEEP_LOCAL/USE_UPSTREAM/MERGE 建議

#### Scenario: OpenSpec 提案生成

給定執行 `/upstream-compare --proposal` 時
則應該：
1. 基於比較結果生成結構化 YAML
2. 格式符合 OpenSpec 規範
3. 包含明確的整合建議與實作步驟

#### Scenario: AI 分析報告

給定執行 `/upstream-compare --ai-analysis` 時
則應該：
1. 生成適合 AI 分析的 prompt
2. 提供結構化資料供 AI 參考
3. 輸出自然語言分析報告

### Requirement: 直接讀取上游目錄 (Direct Upstream Access)

所有 upstream skill MUST (必須) 直接從 `~/.config/<repo>/` 讀取，不使用中間 sources 目錄。

#### Scenario: 不使用 sources 目錄

給定執行任何 upstream skill 時
則不應該：
1. 建立或更新 `sources/` 目錄
2. 從 `~/.config/<repo>/` 複製到 `sources/<name>/`

比較操作應直接讀取 `~/.config/<repo>/`。

### Requirement: 設定儲存庫表完整清單與狀態

`ai-dev status` 的「設定儲存庫」表 SHALL 列出 `shared.py` 中 `REPOS` 字典定義的全部 repo，並顯示 git 版本比對狀態。

#### Scenario: 顯示全部 6 個 repo
- **WHEN** 使用者執行 `ai-dev status`
- **THEN** 設定儲存庫表 MUST 包含 `REPOS` 字典中的全部項目：custom-skills、superpowers、universal-dev-standards、obsidian-skills、anthropic-skills、everything-claude-code

#### Scenario: 本地與遠端一致
- **WHEN** 某 repo 的 `git rev-parse HEAD` 等於 `git rev-parse origin/{branch}`
- **THEN** 狀態欄顯示「✓ 最新」

#### Scenario: 本地落後於遠端
- **WHEN** 某 repo 的本地 HEAD 落後於 origin HEAD
- **THEN** 狀態欄顯示「↑ 有可用更新」

#### Scenario: 無法比對（未 fetch 或非 git 目錄）
- **WHEN** 無法取得 origin HEAD（例如未執行過 fetch 或目錄非 git repo）
- **THEN** 狀態欄顯示目錄存在狀態（維持原有降級行為）

#### Scenario: repo 目錄不存在
- **WHEN** repo 對應的本地目錄不存在
- **THEN** 狀態欄顯示「未安裝」

