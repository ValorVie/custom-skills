---
description: "Multi-agent orchestration - 依序呼叫多個 agent 完成複雜任務"
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

### refactor — 安全重構

```
code-architect → 重構計畫 → 實作 → reviewer → test-specialist
```

### security — 安全審查

```
security-reviewer → 修復計畫 → 實作 → security-reviewer → reviewer
```

## 執行模式

對每個 agent：

1. 啟動對應的子代理
2. 傳入前一個 agent 的 handoff 文件作為上下文
3. 收集輸出為結構化 handoff 文件
4. 傳遞給下一個 agent

獨立檢查可同時執行（並行階段）。

## Handoff 文件格式

```markdown
## HANDOFF: [前一 agent] → [下一 agent]

### 上下文
[已完成工作的摘要]

### 發現
[關鍵發現或決策]

### 已修改檔案
[變更的檔案清單]

### 待處理事項
[未解決的項目]

### 建議
[建議的下一步]
```

## 最終報告格式

```
協調報告
========
工作流：[type]
任務：[description]
Agent 序列：[agents]

摘要 / 各 Agent 輸出 / 變更檔案 / 測試結果 / 安全狀態 / 建議
```

## 自訂工作流

```
/orchestrate custom "code-architect,test-specialist,reviewer" "重新設計快取層"
```

## Agent 對映表

| Agent 名稱 | 說明 |
|------------|------|
| code-architect | 架構規劃與設計 |
| test-specialist | TDD 測試撰寫 |
| reviewer | Code review |
| security-reviewer | 安全審查 |
| doc-writer | 文件撰寫 |
| spec-analyst | 規格分析 |
