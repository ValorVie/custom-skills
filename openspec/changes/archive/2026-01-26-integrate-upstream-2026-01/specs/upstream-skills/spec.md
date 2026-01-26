## MODIFIED Requirements

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
