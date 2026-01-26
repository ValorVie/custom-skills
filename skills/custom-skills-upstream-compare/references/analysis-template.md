# AI Analysis Report Template

## Input: Structured Report (YAML)

AI 讀取 `upstream/reports/structured/analysis-YYYY-MM-DD.yaml`，格式如下：

```yaml
generated_at: '2026-01-24T18:09:43'
summary:
  total_repos: 5
  repos_with_updates: 3
  recommendations:
    High: 2
    Medium: 1
    Low: 0
    Skip: 2
repos:
  repo-name:
    local_path: ~/.config/repo-name
    last_synced_commit: abc1234
    current_commit: def5678
    recommendation: High
    reasoning: "2 個新功能、5 個 skill 變更。建議優先整合。"
    summary:
      total_commits: 8
      by_type:
        feat: 2
        fix: 3
        refactor: 1
        docs: 2
      by_category:
        skills: 5
        agents: 1
        commands: 2
      files_added: 10
      files_modified: 5
      files_deleted: 0
      total_insertions: 500
      total_deletions: 100
    commits:
      - hash: abc1234
        subject: "feat: add new debugging skill"
        author: Developer Name
        date: 2026-01-23 10:00:00
        type: feat
        files_count: 3
    file_changes:
      - path: skills/debugging/SKILL.md
        status: A
        category: skills
```

## Output: Natural Language Report

### 報告結構

```markdown
# 上游整合分析報告

**分析日期**: YYYY-MM-DD
**報告來源**: custom-skills-upstream-sync 結構化報告

---

## 執行摘要

本次分析了 **N** 個上游 repository，其中 **M** 個有新的變更。

### 整合建議總覽

| Repository | 建議等級 | 主要原因 |
|------------|----------|----------|
| repo-a | High | 多個新功能、重要修復 |
| repo-b | Medium | 有價值的改進 |
| repo-c | Skip | 無新變更 |

### 關鍵發現

1. **[最重要的發現]**
2. **[次要發現]**
3. **[其他觀察]**

---

## 詳細分析

### [Repository Name]

**整合建議**: 🔴 High / 🟡 Medium / 🟢 Low / ⚪ Skip

**變更統計**:
- 總 commit 數: X
- 新功能 (feat): Y
- 修復 (fix): Z
- 影響 skills: A 個
- 影響 agents: B 個

#### 重要變更分析

1. **[commit subject]** (`hash`)
   - 類型: feat/fix/refactor
   - 影響: [說明這個變更的影響]
   - 建議: [是否需要整合及原因]

2. **[commit subject]** (`hash`)
   - ...

#### 檔案變更摘要

| 分類 | 新增 | 修改 | 刪除 |
|------|------|------|------|
| Skills | X | Y | Z |
| Agents | A | B | C |
| Commands | D | E | F |

#### 整合建議

**建議動作**: [整合 / 部分整合 / 觀望 / 跳過]

**理由**:
- [原因 1]
- [原因 2]

**注意事項**:
- [需要注意的相容性問題]
- [可能的風險]

**實作步驟**:
1. [具體步驟]
2. [具體步驟]

---

## 整合路線圖

### 優先整合 (High Priority)

1. **[Repo A]**: [原因簡述]
   - 預計影響: [影響範圍]
   - 建議時程: 立即處理

2. **[Repo B]**: [原因簡述]
   - ...

### 建議評估 (Medium Priority)

1. **[Repo C]**: [原因簡述]
   - 需要進一步評估: [評估重點]

### 可選整合 (Low Priority)

1. **[Repo D]**: 小幅改進，可視需要整合

---

## 風險評估

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|----------|
| [風險描述] | 高/中/低 | 高/中/低 | [緩解措施] |

---

## 下一步行動

1. **立即**: 建立 OpenSpec proposal 處理 High 優先級項目
2. **短期**: 評估 Medium 優先級項目的整合價值
3. **持續**: 更新 last-sync.yaml 追蹤同步狀態

### 建議指令

```bash
# 建立整合提案
/openspec:proposal upstream-integration-[repo-name]

# 完成整合後更新同步狀態
python skills/custom-skills-upstream-sync/scripts/analyze_upstream.py --update-sync
```

---

*此報告由 upstream-compare skill 生成，基於 custom-skills-upstream-sync 結構化數據*
```

## Analysis Guidelines

### 評估重點

1. **變更類型優先級**
   - `feat` > `fix` > `refactor` > `docs` > `chore`
   - 新功能和修復通常需要優先評估

2. **影響範圍**
   - Skills 變更：直接影響 AI 行為
   - Agents 變更：影響子代理能力
   - Commands 變更：影響使用者體驗

3. **相容性考量**
   - 是否與現有 skills 衝突
   - 是否需要調整配置
   - 是否有破壞性變更

### 建議措辭

| 情境 | 建議用語 |
|------|----------|
| 明確需要整合 | "建議優先整合" |
| 有價值但需評估 | "值得評估整合價值" |
| 可選但有好處 | "可視需要選擇性整合" |
| 無需處理 | "無需處理，保持現狀" |

### 風險評估標準

- **高風險**: 可能影響核心功能、破壞性變更
- **中風險**: 需要調整配置、部分功能改變
- **低風險**: 純新增功能、文件更新
