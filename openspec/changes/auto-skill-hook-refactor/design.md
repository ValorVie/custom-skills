## Context

auto-skill 是 custom-skills 專案中的自進化知識系統，設計目標是在每次 AI 對話中自動載入領域知識與跨技能經驗。然而自安裝以來從未實際運作，因為 Claude Code 的 skill 需要明確呼叫（`/auto-skill`）才會載入完整 SKILL.md 內容。

現有基礎設施：
- **ecc-hooks 插件**（`plugins/ecc-hooks/`）：已提供 SessionStart、SessionEnd、PreCompact 等 hook，使用 Python 3 腳本實作。Claude Code 支援同一 repo 下多個獨立插件（以 `{plugin-name}@{repo-name}` 格式區分）
- **knowledge-base 目錄結構**：`skills/auto-skill/knowledge-base/` 含 `_index.json` 和 5 個分類 `.md` 檔（幾乎全空）
- **experience 目錄結構**：`skills/auto-skill/experience/` 含 `_index.json`（空模板）
- **claude-mem MCP 插件**：提供跨 session 記憶搜尋，與 auto-skill 的知識庫部分重疊但定位不同

## Goals / Non-Goals

**Goals:**
- 讓 auto-skill 的知識庫與經驗索引在每次對話開始時自動出現在 Claude 的 context 中
- 透過 CLAUDE.md 指令讓 Claude 知道如何使用索引、何時讀取詳情、何時記錄經驗
- 建立獨立插件，與 ecc-hooks 職責分離，可獨立啟用/停用
- 保持 knowledge-base 和 experience 的資料格式向下相容

**Non-Goals:**
- 不重建逐回合關鍵詞匹配或話題切換偵測機制（讓 Claude 自行判斷）
- 不整合或取代 claude-mem MCP（兩者共存）
- 不在此次變更中填充知識庫內容（內容隨日常使用累積）
- 不支援 Claude Code 以外的 AI 工具（Antigravity、OpenCode 等的支援留待未來）

## Decisions

### Decision 1: Hook 注入 + CLAUDE.md 指令混合架構

**選擇**：SessionStart hook 注入動態索引資料，`~/.claude/CLAUDE.md` 提供靜態行為指令。

**替代方案**：
- 純 CLAUDE.md（靜態索引 + 指令）：分類增長時 token 膨脹，每次修改需手動同步
- 純 Hook（動態資料 + 內嵌指令）：hook 輸出太長會被截斷，行為指令不穩定
- 遷移至 claude-mem：失去分類結構，依賴第三方

**理由**：職責分離——動態資料用 hook 注入，穩定指令用 CLAUDE.md。兩者各自可獨立演進。

### Decision 2: 獨立插件而非擴展 ecc-hooks

**選擇**：建立 `plugins/auto-skill-hooks/` 獨立插件，不修改 ecc-hooks。

**替代方案**：在 ecc-hooks 的 hooks.json 新增 SessionStart 條目。

**理由**：
- 職責不同：ecc-hooks 負責記憶持久化 + 程式碼品質，auto-skill-hooks 負責知識注入
- 可獨立啟用/停用：不需要知識庫的使用者不受影響
- 不汙染 ecc-hooks 的上游同步：ecc-hooks 有 upstream 來源，混入 auto-skill 邏輯會造成同步困難

### Decision 3: Hook 腳本使用 Python 3

**選擇**：與 ecc-hooks 的慣例一致，使用 Python 3。

**理由**：腳本邏輯簡單（讀 JSON、過濾、輸出），Python 標準庫即可完成，不引入額外依賴。

### Decision 4: 只輸出有內容的分類

**選擇**：hook 腳本只輸出 `count > 0` 的知識庫分類和有效的經驗條目。

**理由**：避免空索引佔用 context token。知識庫初期幾乎全空，全部輸出反而是噪音。

### Decision 5: CLAUDE.md 指令放在全局 `~/.claude/CLAUDE.md`

**選擇**：全局而非專案層級。

**替代方案**：專案 CLAUDE.md（只在 custom-skills 專案生效）。

**理由**：auto-skill 的知識庫是跨專案的（前端、後端、寫作等通用知識），全局設定讓所有專案都能受益。

### Decision 6: 保留 /auto-skill 手動入口

**選擇**：精簡 SKILL.md 但保留為手動管理知識庫的入口。

**理由**：使用者可能需要手動查看、新增、清理知識庫條目。`/auto-skill` 作為管理介面仍有價值。

## Risks / Trade-offs

- **[Hook 輸出被忽略]** → CLAUDE.md 明確指示 Claude 關注 `[Auto-Skill Knowledge Base]` 標記；與 ecc-hooks 的 session-start.py 輸出模式一致，Claude 已習慣處理 hook 輸出
- **[全局 CLAUDE.md 衝突]** → `~/.claude/CLAUDE.md` 目前不存在，首次建立無衝突；未來若有其他全局指令，以區塊化（`## 知識庫與經驗協議`）方式追加即可
- **[知識庫長期膨脹]** → 腳本只輸出摘要（分類名 + count + keywords），不輸出完整內容；即使 50+ 分類也只佔數十行
- **[auto-skill 上游更新衝突]** → auto-skill 來自 upstream，精簡 SKILL.md 後可能與上游版本分歧；需在 upstream/sources.yaml 標記為 local fork

## Migration Plan

1. 建立 `plugins/auto-skill-hooks/` 插件目錄結構（`.claude-plugin/plugin.json`、`hooks/hooks.json`、`scripts/`）
2. 建立 `inject-knowledge-index.py` 注入腳本
3. 在 `~/.claude/settings.json` 啟用 `"auto-skill-hooks@custom-skills": true`
4. 建立 `~/.claude/CLAUDE.md` 並寫入知識庫協議指令
5. 精簡 `skills/auto-skill/SKILL.md`（移除 Step 0.5, 1, 2，簡化 3, 4）
6. 驗證：啟動新對話，確認索引注入和行為指令生效

**回滾**：在 settings.json 中停用 `auto-skill-hooks` 插件 + 刪除 CLAUDE.md 協議區塊。原有資料完全不受影響。
