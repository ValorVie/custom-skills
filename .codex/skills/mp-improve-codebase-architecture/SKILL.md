---
name: mp-improve-codebase-architecture
description: |
  找出架構摩擦與 deep module 候選，但不直接修改實作程式碼。
  Use when: 使用者要架構回看、找重構候選、改善可測性、
  或把實作中暴露的架構摩擦整理成 OpenSpec 候選。
---

# mp-improve-codebase-architecture

本技能只輸出架構改善候選，不直接改程式碼。若使用者選定候選，應另開 OpenSpec change 或明確納入既有 change。

## 啟動時先讀

- `docs/agents/mp-workflow.md`
- `docs/agents/domain.md`
- `CONTEXT.md`
- `CONTEXT-MAP.md`
- `docs/adr/`
- 相關程式碼、測試與文件

若沒有 `CONTEXT.md` 或 ADR，不要硬建立；只有在使用者確認新術語或決策時才建立。

## 架構語言

輸出中使用固定術語：

- module：有 interface 與 implementation 的單位。
- interface：呼叫者必須知道的全部契約，不只是型別簽名。
- implementation：module 內部實作。
- depth：interface 背後包住多少行為與複雜度。
- seam：能替換行為而不原地修改的地方。
- adapter：在 seam 上滿足 interface 的具體實作。
- leverage：呼叫者從 depth 得到的簡化效果。
- locality：維護者從 depth 得到的變更集中性。

## 探查方向

尋找下列摩擦：

- 理解一個概念需要跳很多檔案。
- module 很淺，interface 幾乎和 implementation 一樣複雜。
- 為了測試抽出函式，但真正錯誤藏在呼叫關係裡。
- seam 洩漏，呼叫者仍需知道太多 implementation。
- 缺少可由 public behavior 驗證的測試面。

使用 deletion test：想像刪掉該 module。若複雜度只是分散到更多呼叫者，它可能仍有價值；若複雜度消失，它可能只是 pass-through。

## 輸出格式

先列候選，不先設計 interface。

```markdown
## 架構改善候選

### 1. <候選名稱>

**Files：**
- `path/to/file`

**Problem：**
目前的摩擦與證據。

**Direction：**
建議方向，以自然語言描述，不寫實作細節。

**Benefit：**
用 leverage、locality、test surface 說明。

**Testing implication：**
若未來實作，應如何驗證。
```

## 邊界

- 不直接修改實作程式碼。
- 不在同一輪把候選變成重構。
- 不重新爭論已被 ADR 明確決定且沒有新摩擦證據的事項。
- 若候選與 ADR 衝突，標明衝突與重新討論的理由。
