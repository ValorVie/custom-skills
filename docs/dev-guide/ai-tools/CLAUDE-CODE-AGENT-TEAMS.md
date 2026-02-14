# Claude Code Agent Teams 指南

> 協調多個 Claude Code 實例作為團隊協作，具備共享任務、代理間訊息傳遞與集中管理能力。

**狀態**：實驗性功能，預設停用
**來源**：[官方文件](https://code.claude.com/docs/zh-TW/agent-teams)

---

## 目錄

- [Agent Teams vs Subagents](#agent-teams-vs-subagents)
- [架構](#架構)
- [啟用方式](#啟用方式)
- [使用方式](#使用方式)
- [顯示模式](#顯示模式)
- [任務協調](#任務協調)
- [最佳使用場景](#最佳使用場景)
- [最佳實踐](#最佳實踐)
- [已知限制](#已知限制)
- [故障排除](#故障排除)

---

## Agent Teams vs Subagents

### 核心差異

|  | **Subagents** | **Agent Teams** |
|---|---|---|
| **Context** | 自己的 context window，結果返回給呼叫者 | 自己的 context window，完全獨立 |
| **通訊** | 只能向主代理回報結果（單向） | 隊友之間可以直接互傳訊息（雙向） |
| **協調** | 主代理管理所有工作 | 共享任務清單，隊友可自我認領任務 |
| **互動** | 使用者無法直接與 subagent 對話 | 使用者可以直接與任一隊友溝通 |
| **最適合** | 只需要結果的專注任務 | 需要討論、協作、互相質疑的複雜工作 |
| **Token 成本** | 較低（結果摘要返回主 context） | 較高（每個隊友是獨立的 Claude 實例） |
| **生命週期** | 任務完成即結束 | 持續存在，可被關閉或重新指派 |

### 簡單類比

- **Subagent** = 派出去跑腿的助手，完成後回報結果
- **Agent Team** = 會議室裡的團隊，各自分工但可以互相討論、質疑、協調

### 如何選擇？

- 工作人員**不需要互相溝通** → 用 Subagents
- 工作人員**需要分享發現、互相質疑** → 用 Agent Teams
- **順序任務**或有很多依賴關係 → 用單一工作階段或 Subagents
- **Token 預算有限** → 用 Subagents

---

## 架構

Agent Team 由以下元件組成：

| 元件 | 角色 |
|------|------|
| **Team Lead** | 建立團隊、生成隊友並協調工作的主要 Claude Code 工作階段 |
| **Teammates** | 各自處理分配任務的獨立 Claude Code 實例 |
| **Task List** | 隊友認領和完成的共享工作項目清單 |
| **Mailbox** | 代理間通訊的訊息系統 |

### 資料儲存

- **Team config**：`~/.claude/teams/{team-name}/config.json`
- **Task list**：`~/.claude/tasks/{team-name}/`

隊友可以讀取 team config 來發現其他團隊成員。

### Context 與通訊

每個隊友生成時會載入與常規工作階段相同的專案 context（CLAUDE.md、MCP servers、skills），但**不繼承**主管的對話歷史。

通訊方式：

- **自動訊息傳遞**：隊友發送的訊息自動傳遞給收件人
- **閒置通知**：隊友完成時自動通知主管
- **共享任務清單**：所有代理都可以看到任務狀態並認領工作
- **message**：向特定隊友發送訊息
- **broadcast**：同時發送給所有隊友（成本隨團隊規模增加）

### 權限

隊友以主管的權限設定啟動。生成後可個別更改，但生成時無法設定每個隊友的模式。

---

## 啟用方式

在 `settings.json` 中加入：

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

或在 shell 環境中設定：

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

---

## 使用方式

### 啟動團隊

用自然語言描述任務和團隊結構：

```
I'm designing a CLI tool that helps developers track TODO comments across
their codebase. Create an agent team to explore this from different angles: one
teammate on UX, one on technical architecture, one playing devil's advocate.
```

### 指定隊友數量和模型

```
Create a team with 4 teammates to refactor these modules in parallel.
Use Sonnet for each teammate.
```

### 要求計畫批准

```
Spawn an architect teammate to refactor the authentication module.
Require plan approval before they make any changes.
```

隊友在唯讀計畫模式下工作，直到主管批准其方法。

### 使用委派模式

按 **Shift+Tab** 循環進入委派模式，將主管限制為僅協調工具（生成、傳訊、關閉隊友、管理任務），防止主管自己動手實作。

### 直接與隊友交談

- **In-process 模式**：Shift+Up/Down 選擇隊友，輸入訊息
- **Split-pane 模式**：點擊隊友的窗格直接互動

### 關閉與清理

```
Ask the researcher teammate to shut down
Clean up the team
```

> 始終使用主管進行清理，隊友不應執行清理操作。

---

## 顯示模式

| 模式 | 說明 | 需求 |
|------|------|------|
| **In-process** | 所有隊友在主終端內運行，Shift+Up/Down 切換 | 任何終端 |
| **Split panes** | 每個隊友獨立窗格，可同時檢視 | tmux 或 iTerm2 |
| **Auto**（預設） | 在 tmux 內自動用分割窗格，否則 in-process | - |

設定方式：

```json
{
  "teammateMode": "in-process"
}
```

或單次工作階段：

```bash
claude --teammate-mode in-process
```

---

## 任務協調

### 任務狀態

待處理 → 進行中 → 已完成

任務可以設定依賴關係，有未解決依賴的任務無法被認領。

### 分配方式

- **主管分配**：告訴主管將任務分配給特定隊友
- **自我認領**：隊友完成任務後自動選擇下一個未分配、未阻止的任務

任務認領使用檔案鎖定防止競爭條件。

---

## 最佳使用場景

### 適合 Agent Teams

| 場景 | 說明 |
|------|------|
| **並行程式碼審查** | 安全、效能、測試覆蓋各由不同隊友負責 |
| **競爭假設除錯** | 多個隊友平行測試不同理論，互相反駁 |
| **新模組開發** | 各自負責獨立部分，互不干擾 |
| **跨層協調** | 前端、後端、測試各由不同隊友負責 |
| **研究與調查** | 同時從不同角度調查問題 |

### 適合 Subagents

| 場景 | 說明 |
|------|------|
| **快速搜尋/驗證** | 只需要結果，不需要討論 |
| **單一檔案修改** | 範圍明確的專注任務 |
| **順序工作流** | 步驟有先後依賴 |
| **Token 敏感場景** | 需要控制成本 |

### 使用案例範例

**並行程式碼審查：**

```
Create an agent team to review PR #142. Spawn three reviewers:
- One focused on security implications
- One checking performance impact
- One validating test coverage
Have them each review and report findings.
```

**競爭假設除錯：**

```
Users report the app exits after one message instead of staying connected.
Spawn 5 agent teammates to investigate different hypotheses. Have them talk to
each other to try to disprove each other's theories, like a scientific
debate. Update the findings doc with whatever consensus emerges.
```

---

## 最佳實踐

### 給隊友足夠的 context

隊友不繼承主管對話歷史，需在生成提示中包含任務特定詳情：

```
Spawn a security reviewer teammate with the prompt: "Review the authentication
module at src/auth/ for security vulnerabilities. Focus on token handling,
session management, and input validation. The app uses JWT tokens stored in
httpOnly cookies. Report any issues with severity ratings."
```

### 適當調整任務大小

- **太小**：協調開銷超過好處
- **太大**：隊友工作過久沒有檢查點，浪費風險高
- **恰到好處**：自包含的單位，產生清晰可交付成果（函數、測試檔案、審查）
- 每個隊友 5-6 個任務可保持生產力

### 等待隊友完成

主管有時會自行開始實作，可以提醒：

```
Wait for your teammates to complete their tasks before proceeding
```

### 避免檔案衝突

兩個隊友編輯同一檔案會導致覆蓋。分解工作時確保每個隊友擁有不同的檔案集。

### 監控和引導

定期檢查進度，重新定向不起作用的方法。讓團隊無人值守運行太長時間會增加浪費風險。

### 從研究和審查開始

新手建議先從不需要寫程式碼的任務開始：審查 PR、研究庫或調查錯誤。

---

## 已知限制

| 限制 | 說明 |
|------|------|
| **無工作階段恢復** | In-process 隊友不支援 `/resume` 和 `/rewind` |
| **任務狀態滯後** | 隊友有時無法將任務標記為已完成 |
| **關閉較慢** | 隊友需完成當前請求才能關閉 |
| **每個工作階段一個團隊** | 啟動新團隊前需清理當前團隊 |
| **無嵌套團隊** | 隊友無法生成自己的團隊 |
| **主管固定** | 無法轉移領導權或提升隊友為主管 |
| **權限在生成時設定** | 生成時無法個別設定隊友權限 |
| **分割窗格限制** | 不支援 VS Code 整合終端、Windows Terminal、Ghostty |

---

## 故障排除

### 隊友未出現

- In-process 模式：按 Shift+Down 循環瀏覽活躍隊友
- 確認任務足夠複雜以保證建立團隊
- 分割窗格模式：確認 `tmux` 已安裝（`which tmux`）
- iTerm2：確認 `it2` CLI 已安裝且 Python API 已啟用

### 過多權限提示

隊友權限請求會冒泡到主管。在權限設定中預批准常見操作以減少中斷。

### 隊友在錯誤時停止

使用 Shift+Up/Down（in-process）或點擊窗格（split）檢查輸出，給予額外指示或生成替換隊友。

### 主管過早結束

告訴主管繼續，或要求它等待隊友完成：

```
Wait for your teammates to complete their tasks before proceeding
```

### 孤立的 tmux 工作階段

```bash
tmux ls
tmux kill-session -t <session-name>
```
