---
name: mp-wayfinder
description: |
  把「大到單一 session 裝不下、還寫不出 OpenSpec proposal」的模糊工作，
  規劃成 canonical tracker 上的地圖與子工作項目，每個 session 只解一個決策點。
  Use when: 使用者明確要求規劃探索期大型工作、或說「這件事太大還理不清」。
  不適用於已能撰寫 proposal 的需求（改走 /opsx:new）。
---

# mp-wayfinder

本技能處理探索期：目的地看得到方向、路徑還在迷霧裡。它產出**決策**，不產出交付物。
發現自己想動手做時，通常代表已走到地圖邊緣，該交棒了。

## 邊界（先檢查）

- 需求已清楚到能寫 proposal → 停止，改走 `/opsx:new`。本技能不重複 OpenSpec 的工作。
- 工作一個 session 就能收斂 → 停止，直接用 `mp-grill-with-docs` 對齊即可。
- 只是要拆已成形的需求 → 改用 `mp-to-issues`。

## 啟動時先讀

- `docs/agents/mp-workflow.md`
- `docs/agents/issue-tracker.md`
- `docs/agents/triage-states.md`
- 相關 `CONTEXT.md`、ADR

## 地圖結構

地圖建立在 `docs/agents/issue-tracker.md` 指定的 canonical tracker。地圖是**索引不是倉庫**：
每個決策只住在自己的子工作項目裡，地圖只留一行摘要加連結。

本專案使用 Beads：

- 地圖是一張 `epic`，加 label `wayfinder:map`。
- 決策點使用 `--parent=<epic-id>` 建立 child issue。
- 真正的阻擋關係使用 `bd dep add <blocked> <blocker>`。
- `ready-for-agent` child 使用 `open` status；`ready-for-human` child 使用
  `blocked` status。
- frontier 是無 blocking dependency 且具有 `ready-for-agent` 或
  `ready-for-human` label 的未完成 child；代理只能從 `bd ready` 認領
  `ready-for-agent`。

若儲存庫規則指定 GitHub，才使用 GitHub parent/sub-issue 與 blocking link。

```markdown
## 目的地

<這張地圖要走到哪：一份 spec、一個鎖定的決策、或一次就地完成的變更。一到兩行。>

## 備註

<領域脈絡、每個 session 應參考的技能、本次工作的固定偏好>

## 已決事項

- [<已關閉子 issue 標題>](連結) — <答案的一行摘要>

## 尚未成形

<看得到方向但還無法精確提問的區域，不預先切票>

## 範圍外

<明確排除於本次目的地之外的工作，附一行原因>
```

## 子工作項目

每個決策點是地圖的子工作項目，body 只放要解的問題。四種型別（對應 AFK/HITL）：

| 型別 | 模式 | 用途 |
| --- | --- | --- |
| research | AFK | 讀文件、外部 API、知識庫，產出引用來源的 Markdown 摘要 |
| prototype | HITL | 用 `mp-prototype` 做丟棄式原型，把討論具體化 |
| grilling | HITL | 用 `mp-grill-with-docs` 一次一題追問，預設型別 |
| task | AFK/HITL | 為了解鎖決策而必須先做的雜項（開通服務、搬資料），做完記下結果事實 |

HITL 型別只能透過與真人對答解決；agent 不得代答使用者那一側。

阻擋關係必須使用 canonical tracker 的 blocking edge。認領方式也使用 tracker 的原子認領；
Beads 執行 `bd update <id> --claim`，未認領不得開工。

## 尚未成形 vs 切票

判斷標準是**能否精確提問**，不是能否回答：

- 問題已能精確陳述（即使被阻擋）→ 切成子 issue。
- 還無法精確陳述 → 留在「尚未成形」，等前緣推進後再結晶。不預先切碎。

範圍外不是尚未成形：超出目的地的工作直接關閉並記到「範圍外」，永不結晶。

## 兩種啟動模式

### 開圖

使用者帶著模糊想法啟動：

1. 用 `mp-grill-with-docs` 釘住目的地（目的地決定範圍，最先確定）。
2. 廣度優先再追問一輪：攤開整個空間，找出所有已能提問的決策點。
   若攤開後沒有迷霧（路徑已清楚、一個 session 裝得下），不需要地圖，
   停下來問使用者要走哪條軌。
3. 建立地圖工作項目：目的地與備註填好、已決事項空白、迷霧寫進「尚未成形」。
4. 建立可提問的子工作項目，第二輪補上阻擋連結（工作項目要先有 ID 才能互相引用）。
5. 停止。開圖是一個 session 的工作，不順手解票。

### 工作

使用者帶著地圖啟動（issue 編號或連結），可指定子 issue：

1. 載入地圖（低解析度視圖，不逐張讀子工作項目）。
2. 選票：使用者指定就用指定的；否則取 frontier 第一張。**先認領再開工**。
3. 解決：需要時放大讀相關子工作項目全文，依型別呼叫對應技能。
4. 記錄：答案寫進 notes 或 resolution、關閉工作項目、地圖「已決事項」追加一行摘要加連結。
5. 更新地圖：新浮現的決策點切票（先建後連）；答案讓迷霧結晶的，從「尚未成形」
   移出成新子工作項目；答案顯示某票超出目的地的，關票記入「範圍外」。
6. 停止。**一個 session 只解一張**，其他 session 可能正在並行編輯地圖。

## 結晶轉 OpenSpec

地圖上的決策足以撰寫 proposal 時，該部分工作轉入 OpenSpec change（`/opsx:new`）：

- 地圖「已決事項」留一行指向該 change 的連結，內容不重複維護。
- 地圖剩餘部分繼續走完；全部結晶或關閉後，關閉地圖工作項目。
