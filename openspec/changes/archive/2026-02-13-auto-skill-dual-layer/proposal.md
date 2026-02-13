## Why

目前 auto-skill 的 SessionStart hook 採用 first-match-wins 策略，只載入一個層級（使用者優先）。專案層級的知識庫和經驗在執行時期完全不可見，導致專案特定的經驗無法與團隊共享（透過 git），所有經驗混在使用者層級無法區分通用 vs 專案特定。

## What Changes

- inject-knowledge-index.py 改為同時載入使用者層級（`~/.claude/skills/auto-skill/`）和專案層級（`./skills/auto-skill/`），合併輸出並標註來源 `[使用者]` / `[專案]`
- SKILL.md 核心循環更新：讀取時合併雙層內容，記錄時詢問使用者要存到哪一層
- 記錄到專案層級時，若 `./skills/auto-skill/` 不存在，詢問使用者是否從 `~/.config/custom-skills/skills/auto-skill/` 初始化

## Capabilities

### New Capabilities

_無新增獨立能力_

### Modified Capabilities

- `knowledge-injection`: 從 first-match-wins 單層載入改為雙層合併載入，輸出增加來源標註，搜尋順序從「找到第一個就停」改為「兩個都找」。SKILL.md 的讀取步驟（Step 3/4）改為雙層讀取，記錄步驟（Step 5）增加層級選擇詢問與專案層級目錄初始化流程。

## Impact

- **腳本**: `plugins/auto-skill-hooks/scripts/inject-knowledge-index.py` — 重寫搜尋與輸出邏輯
- **Skill 定義**: `skills/auto-skill/SKILL.md` — 更新 Step 0/3/4/5 與存儲路徑章節
- **輸出格式變更**: SessionStart 注入的文字格式改變（增加 `[使用者]` / `[專案]` 標註），依賴此格式的下游邏輯需確認相容
- **無 breaking change**: 單層環境（只有使用者層級或只有專案層級）行為與現有一致
