# Proposal: upstream-sync-standards

**類型**: 上游同步
**優先級**: Medium
**複雜度**: 中高
**來源**: upstream/reports/analysis/compare-2026-02-02.md

---

## 背景

universal-dev-standards 上游 (AsiaOstrich/universal-dev-standards) 發布 V5 架構升級，包含大量標準文件更新。本專案的 `.standards/` 目錄需要同步這些變更，但**不跟進目錄結構重組**（保持現有 `.standards/*.ai.yaml` 結構）。

## 結構決策

UDS V5 新增了 `core/`、`ai/`、`methodologies/` 頂層目錄，但本專案：
- `.standards/*.ai.yaml` 等同 UDS 的 `ai/standards/`，直接可比對
- `core/` 的 markdown 版本由 skill 覆蓋，不需要
- `methodologies/` 對應 `skills/methodology-system/`，不需要

**決策: 只同步 `.standards/` 下的 `.ai.yaml` 檔案內容，不動目錄結構。**

## 變更範圍

### 子任務 C1: 小幅更新（7 檔）

直接從上游覆蓋，diff 行數均 < 15 行：

| 檔案 | Diff 行數 | 變更摘要 |
|------|----------|---------|
| acceptance-test-driven-development.ai.yaml | +10 | 小幅調整 |
| behavior-driven-development.ai.yaml | +10 | 小幅調整 |
| git-workflow.ai.yaml | +11 | 小幅調整 |
| refactoring-standards.ai.yaml | +5 | 小幅調整 |
| spec-driven-development.ai.yaml | +8 | 小幅調整 |
| test-driven-development.ai.yaml | +4 | 小幅調整 |
| testing.ai.yaml | +2 | 小幅調整 |

### 子任務 C2: 大幅更新（2 檔）

需審查後合併：

#### anti-hallucination.ai.yaml (+78 diff lines)

**重要新增**:
- **Derivation Tags 系統**: 新增 `[Source]`, `[Derived]`, `[Generated]`, `[TODO]` 標記
- **Workflow-Tag 對應表**: Code analysis 和 Reverse engineering 用 Certainty Tags; Forward derivation 和 Spec generation 用 Derivation Tags
- 版本號差異：本地 1.4.0 vs 上游 1.3.1（本地可能有超前自訂修改，需確認）

**影響評估**: 新增的 Derivation Tags 會影響 `forward-derivation` 和 `spec-driven-dev` skill 的工作流標記

#### test-completeness-dimensions.ai.yaml (+80 diff lines)

**重要新增**:
- **第 8 維度**: AI Test Generation Quality（AI 生成測試品質）
- 每種 feature type mapping 新增 `with_ai` 欄位
- 新增 `review-ai-tests` 規則
- checklist 模板新增 AI 生成品質檢查項

**影響評估**: 直接強化日常 AI 生成測試的品質管控

### 子任務 C3: 新增標準（選擇性採用）

| 新標準 | 決策 | 理由 |
|--------|------|------|
| requirement-engineering.ai.yaml | **採用** | 本專案有 `requirement-assistant` skill，需配套標準 |
| security-standards.ai.yaml | **採用** | 本專案有 `security-review` skill，需配套標準 |
| ai-agreement-standards.ai.yaml | **評估** | AI 協作標準，待審查內容後決定 |
| performance-standards.ai.yaml | 跳過 | 無對應 skill |
| accessibility-standards.ai.yaml | 跳過 | 與本專案類型無關 |
| virtual-organization-standards.ai.yaml | 跳過 | 組織管理標準，非技術性 |

### 子任務 C4: manifest.json 更新

更新 `.standards/manifest.json` 反映新增與變更的標準檔案。

### 附帶: options/ 同步

| 檔案 | 狀態 |
|------|------|
| options/github-flow.ai.yaml | SAME |
| options/integration-testing.ai.yaml | SAME |
| options/squash-merge.ai.yaml | SAME |
| options/unit-testing.ai.yaml | SAME |
| options/traditional-chinese.ai.yaml | LOCAL_ONLY（保留） |
| options/english.ai.yaml | NEW — 評估是否需要 |

## 實作步驟

1. **C1**: 逐一覆蓋 7 個小幅變更檔案
2. **C2**: 審查 anti-hallucination 和 test-completeness-dimensions 的大幅變更，合併
3. **C3**: 從上游複製 requirement-engineering 和 security-standards；審查 ai-agreement-standards
4. **C4**: 更新 manifest.json
5. 確認 CLAUDE.md 中 `.standards/` 引用路徑無需調整
6. 更新 `upstream/last-sync.yaml` 中 universal-dev-standards 的 `last_synced_commit`

## 風險

- **衝突風險**: 中 — anti-hallucination 版本號不一致（本地 1.4.0 vs 上游 1.3.1），可能有超前修改需保留
- **影響範圍**: 高 — 標準檔案影響所有 AI 行為（尤其 anti-hallucination 和 test-completeness）
- **緩解措施**: C2 大幅變更逐段審查；合併後驗證 CLAUDE.md 引用

## 驗收標準

- [ ] C1: 7 個小幅更新檔案已同步
- [ ] C2: anti-hallucination 包含 Derivation Tags 系統
- [ ] C2: test-completeness-dimensions 包含第 8 維度（AI Test Generation Quality）
- [ ] C3: requirement-engineering.ai.yaml 已新增
- [ ] C3: security-standards.ai.yaml 已新增
- [ ] C4: manifest.json 已更新
- [ ] CLAUDE.md 引用路徑正確
- [ ] last-sync.yaml 已更新為 `a6412d7`
