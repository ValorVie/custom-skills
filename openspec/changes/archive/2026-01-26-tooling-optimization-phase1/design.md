## Context

本專案是一個 AI 輔助開發工具生態系統，包含 Skills、Commands、Agents 和 Workflows 四種工具類型。工具重疊性分析報告指出部分工具存在功能重疊或關係不明確的問題，需要進行優化。

**現狀**：
- `coverage.md` 和 `test-coverage.md` 是兩個獨立命令，功能高度重疊
- Skills 之間的互補關係沒有在檔案中明確標註，使用者需要自行理解

**約束**：
- Skills 使用 YAML frontmatter + Markdown body 格式
- Commands 使用純 Markdown 格式，frontmatter 包含 description 和 allowed-tools
- 變更需向後相容現有工具載入機制

## Goals / Non-Goals

**Goals:**
- 合併 `coverage.md` 與 `test-coverage.md` 為單一命令，使用參數區分模式
- 定義 `related` 欄位規範，供 Skills 標註互補工具
- 為報告中識別的 8 個 Skills 新增 `related` 標註

**Non-Goals:**
- 不修改 Skill 載入機制或驗證邏輯（`related` 僅為文件性標註）
- 不處理報告中其他低優先級建議（如 commit vs git-commit 的整合）
- 不修改 Agents 或 Workflows

## Decisions

### Decision 1: `related` 欄位格式

**選擇**：使用物件陣列格式，每個物件包含 `name` 和 `relationship` 欄位

```yaml
related:
  - name: git-commit-custom
    relationship: 實作模組
  - name: git-workflow-guide
    relationship: 分支策略
```

**理由**：
- 比簡單的 key-value 格式更具可讀性
- `relationship` 欄位說明關係類型，幫助使用者理解
- 未來可擴展其他屬性（如 `priority`、`url`）

**替代方案**：
- 簡單字串陣列 `related: [git-commit-custom, git-workflow-guide]` — 缺少關係說明
- Key-value 格式 `related: { git-commit-custom: "實作模組" }` — 不夠直觀

### Decision 2: 命令參數設計

**選擇**：使用 `--generate` 旗標啟用測試生成功能

```bash
/coverage              # 分析模式（預設）
/coverage --generate   # 分析 + 生成測試
```

**理由**：
- 預設行為保持簡單（僅分析）
- 旗標名稱直觀，表明會「生成」檔案
- 與現有 `/coverage` 使用方式相容

**替代方案**：
- 子命令 `/coverage analyze` vs `/coverage generate` — 增加使用複雜度
- 不同命令名稱 `/coverage-analyze` vs `/coverage-generate` — 與合併目標矛盾

### Decision 3: `related` 欄位放置位置

**選擇**：放在 YAML frontmatter 中，與 `name`、`description` 同層級

```yaml
---
name: commit-standards
description: ...
related:
  - name: git-commit-custom
    relationship: 實作模組
---
```

**理由**：
- Frontmatter 是元資料的標準位置
- 工具可以程式化讀取（如未來的 Skill 瀏覽器）
- 不影響 Markdown body 的內容結構

## Risks / Trade-offs

### Risk 1: Breaking Change 影響

**風險**：移除 `/test-coverage` 可能影響現有使用者的習慣或自動化腳本

**緩解**：
- 在 CHANGELOG 中明確記錄遷移指引
- 考慮在 `test-coverage.md` 中保留一個重定向提示（而非完全刪除）

### Risk 2: `related` 欄位維護負擔

**風險**：新增的 `related` 欄位需要手動維護，可能隨時間變得過時

**緩解**：
- 僅標註報告中識別的高度相關群組
- 在 Skill 開發指南中說明何時應新增 `related` 標註

### Trade-off: 標註完整性 vs 維護成本

**取捨**：僅標註分析報告中識別的 3 個群組（8 個 Skills），而非全部 41 個 Skills

**理由**：
- 報告識別的群組有明確的互補關係
- 全面標註會大幅增加工作量且價值有限
- 可在未來根據使用者回饋逐步擴展

## Open Questions

1. **重定向方案**：是否需要在移除的 `test-coverage.md` 位置保留一個提示檔案，引導使用者到新命令？
2. **驗證機制**：未來是否需要在 Skill 載入時驗證 `related` 欄位中引用的 Skill 是否存在？
