## Context

auto-skill 系統有兩個物理位置：使用者層級（`~/.claude/skills/auto-skill/`，個人，Syncthing 同步）和專案層級（`./skills/auto-skill/`，團隊，git 提交）。目前 SessionStart hook 採用 first-match-wins，只載入使用者層級。Clone policy（`.clonepolicy.json`）處理分發時的合併，但 runtime 完全單層。

**現有架構：**
- `inject-knowledge-index.py`：`find_skill_root()` 回傳第一個找到的路徑
- `SKILL.md`：相對路徑，假設單一來源
- `_index.json` 格式：knowledge-base 用 `categories[].id`，experience 用 `skills[].skillId`

## Goals / Non-Goals

**Goals:**
- 讓 inject hook 同時載入兩個層級，合併輸出並標註來源
- 讓 SKILL.md 指引 Claude 讀取雙層內容、記錄時詢問層級選擇
- 記錄到專案層級時，若目錄不存在，從 `~/.config/custom-skills/skills/auto-skill/` 初始化

**Non-Goals:**
- 不修改 clone policy 或 `shared.py` 的合併邏輯
- 不修改 `_index.json` 的 schema（不新增欄位）
- 不做自動判斷寫入層級（每次詢問使用者）
- 不做跨層級去重（同一經驗可存在兩層）

## Decisions

### D1: inject 腳本改為掃描所有層級

`find_skill_root()` → `find_all_skill_roots()`，回傳 `dict` 而非單一路徑。

**理由：** 最小變更，保留 `load_json()` 不變，只改搜尋和輸出邏輯。

### D2: 合併策略 — 以 id/skillId 為鍵

knowledge-base 以 `categories[].id` 合併，experience 以 `skills[].skillId` 合併。同一 id 在兩層都有 count > 0 時，輸出加總並標註各層 count。

**替代方案：** 分開顯示為兩個獨立區塊（`[Auto-Skill Knowledge Base - 使用者]`、`[Auto-Skill Knowledge Base - 專案]`）。
**不選原因：** 分開顯示會讓 SKILL.md 的匹配邏輯更複雜，合併後單一列表更簡潔。

### D3: 來源標註格式

- 單層：`N entries [使用者]` 或 `N entries [專案]`
- 雙層：`N entries (X [使用者] + Y [專案])`

**理由：** 簡潔、一目了然，且 SKILL.md 可根據標註判斷要讀取哪個層級的檔案。

### D4: SKILL.md 雙層讀取 — 兩層都讀

Step 3（experience）和 Step 4（knowledge-base）讀取時，兩個層級的 `.md` 都讀取，不做 fallback。

**替代方案：** 只讀有 count > 0 的層級。
**不選原因：** inject 已過濾 count=0，所以 SKILL.md 看到的標註一定有內容，兩層都讀更完整。

### D5: 專案層級初始化來源

從 `~/.config/custom-skills/skills/auto-skill/` 複製。這是 custom-skills 的全域配置位置，包含最新的模板結構（SKILL.md、.clonepolicy.json、空的 _index.json、空的 .md 模板）。

**理由：** 與 clone 命令使用相同的來源，確保結構一致。

## Risks / Trade-offs

- [Risk] inject 腳本讀取兩倍檔案 → 影響微小（JSON 檔案都 < 2KB，一次性 startup 成本）
- [Risk] 使用者每次記錄都被問層級 → 可能感覺繁瑣，但保持明確控制權
- [Risk] 專案層級初始化後忘記 git add → SKILL.md 提醒使用者提交
- [Trade-off] 同一經驗可能在兩層重複 → 接受，不做去重，讓使用者自行管理
