---
description: "Multi-agent orchestration - 依序呼叫多個 agent 完成複雜任務"
allowed-tools: "Task, Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion"
argument-hint: "<workflow-type> <task-description>"
---

# Orchestrate | 多 Agent 協調

依序呼叫多個 agent 完成複雜任務，每個 agent 之間透過結構化 handoff 文件傳遞上下文。

## 用法

```
/orchestrate <workflow-type> <task-description>
```

## 工作流類型

### feature — 完整功能實作

```
code-architect → test-specialist → 實作 → reviewer → security-reviewer
```

1. **code-architect**：分析需求、建立實作計畫、識別依賴
2. **test-specialist**：根據計畫撰寫測試骨架（TDD）
3. **實作**：實作程式碼使測試通過
4. **reviewer**：Code review、檢查問題、建議改善
5. **security-reviewer**：安全稽核、弱點檢查、最終核准

### bugfix — 除錯與修復

```
診斷 → test-specialist → 修復 → reviewer
```

1. **診斷**：調查問題根因
2. **test-specialist**：撰寫重現測試
3. **修復**：修正問題使測試通過
4. **reviewer**：驗證修復正確性

### refactor — 安全重構

```
code-architect → 重構計畫 → 實作 → reviewer → test-specialist
```

1. **code-architect**：分析現有架構、規劃重構方向
2. **重構計畫**：詳細步驟與影響範圍
3. **實作**：執行重構
4. **reviewer**：Code review
5. **test-specialist**：回歸測試驗證

### security — 安全審查

```
security-reviewer → 修復計畫 → 實作 → security-reviewer → reviewer
```

1. **security-reviewer**：全面安全掃描
2. **修復計畫**：列出修復項目與優先順序
3. **實作**：修復安全問題
4. **security-reviewer**：驗證修復
5. **reviewer**：Code review

## 執行模式

### 依序執行

對每個 agent：

1. 使用 **Task** 工具啟動對應的子代理
2. 傳入前一個 agent 的 handoff 文件作為上下文
3. 收集輸出為結構化 handoff 文件
4. 傳遞給下一個 agent

### 並行執行

獨立檢查可同時執行：

```
並行階段：
- reviewer（品質）
- security-reviewer（安全）
- code-architect（設計）

合併結果 → 統整報告
```

## Handoff 文件格式

每個 agent 之間傳遞的結構化文件：

```markdown
## HANDOFF: [前一 agent] → [下一 agent]

### 上下文
[已完成工作的摘要]

### 發現
[關鍵發現或決策]

### 已修改檔案
[變更的檔案清單]

### 待處理事項
[未解決的項目，供下一 agent 處理]

### 建議
[建議的下一步]
```

## 最終報告格式

```
協調報告
========
工作流：feature
任務：[任務描述]
Agent 序列：code-architect → test-specialist → reviewer → security-reviewer

摘要
----
[一段摘要]

各 Agent 輸出
-------------
code-architect: [摘要]
test-specialist: [摘要]
reviewer: [摘要]
security-reviewer: [摘要]

變更檔案
--------
[所有修改的檔案]

測試結果
--------
[測試通過/失敗摘要]

安全狀態
--------
[安全發現]

建議
----
[可上線 / 需修改 / 阻塞]
```

## 自訂工作流

指定任意 agent 序列：

```
/orchestrate custom "code-architect,test-specialist,reviewer" "重新設計快取層"
```

## Agent 對映表

| Agent 名稱 | 子代理類型 | 說明 |
|------------|-----------|------|
| code-architect | code-architect | 架構規劃與設計 |
| test-specialist | test-specialist | TDD 測試撰寫 |
| reviewer | reviewer | Code review |
| security-reviewer | security-reviewer | 安全審查 |
| doc-writer | doc-writer | 文件撰寫 |
| spec-analyst | spec-analyst | 規格分析 |

## 提示

1. 複雜功能**從 code-architect 開始**規劃
2. 合併前**務必包含 reviewer**
3. 涉及認證/支付/PII 時**使用 security-reviewer**
4. Handoff 文件**保持精簡**，聚焦下一 agent 所需的資訊
5. 需要時可在 agent 之間**插入驗證步驟**
