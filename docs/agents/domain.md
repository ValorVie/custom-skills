# Domain Docs 規則

本文件定義 MP 工作入口層如何讀取與更新專案語言、上下文與 ADR。

## 預設佈局

本專案預設採 single-context：

```text
CONTEXT.md
docs/adr/
```

若根目錄存在 `CONTEXT-MAP.md`，則改採 multi-context，由 `CONTEXT-MAP.md` 指向各子 context。

## 讀取規則

MP 技能在需求對齊、切片、分流或架構回看前，應依序檢查：

- `docs/agents/domain.md`
- `CONTEXT-MAP.md`
- `CONTEXT.md`
- `docs/adr/`
- 與任務相關的文件與程式碼

能從本地文件或程式碼查到的資訊，不應要求使用者憑記憶回答。

## `CONTEXT.md` 寫入規則

只有符合以下條件時才建立或更新 `CONTEXT.md`：

- 術語是領域語言，不只是單一程式實作細節。
- 未來人類或 agent 會重複使用。
- 使用者已確認定義。

建議格式：

```markdown
## Glossary

### <Term>

定義、邊界、常見誤用。
```

## ADR 寫入規則

只有三個條件都成立時才建立 ADR：

- 反悔成本高。
- 沒有背景會讓未來讀者困惑。
- 曾經有真實取捨。

若缺少任一條件，不建立 ADR；可留在 OpenSpec artifact、工作紀錄或對話摘要。

## 架構回看規則

`mp-improve-codebase-architecture` 必須先讀相關 context 與 ADR，再提出候選。候選只能是建議，不直接修改實作程式碼。
