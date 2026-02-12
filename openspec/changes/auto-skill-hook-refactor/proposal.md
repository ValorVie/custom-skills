## Why

auto-skill 設計為每次對話自動載入知識庫與經驗的自進化系統，但在 Claude Code 中從未運作。根本原因是 skill 機制不支援自動觸發——SKILL.md 的 description 欄位中的「CRITICAL PROTOCOL」文字無法迫使 Claude 主動讀取並執行完整協議。知識庫 5 個分類幾乎全空、經驗索引是無效模板、全局 CLAUDE.md 不存在，均證實此系統從安裝以來處於完全失效狀態。

現在需要將核心功能從「依賴 AI 自覺觸發」重構為「Hook 注入 + CLAUDE.md 指令」的混合架構，建立獨立的 `auto-skill-hooks` 插件（與 ecc-hooks 分離），讓知識庫與經驗系統真正生效。

## What Changes

- 新增獨立插件 `plugins/auto-skill-hooks/`，與 ecc-hooks 職責分離
- 在插件中建立 SessionStart hook 腳本，每次對話開始時自動注入 knowledge-base 和 experience 的索引摘要到 context
- 在 `~/.claude/CLAUDE.md` 新增「知識庫與經驗協議」行為指令，告訴 Claude 如何使用索引、何時讀取詳情、何時記錄經驗
- 精簡 `skills/auto-skill/SKILL.md`，移除無法在 Claude Code 中運作的機制（自動加固、關鍵詞匹配、話題切換偵測），保留條目格式規範與記錄判斷準則

## Capabilities

### New Capabilities

- `knowledge-injection`: SessionStart hook 自動注入知識庫與經驗索引到對話 context，讓 Claude 在無需手動呼叫 /auto-skill 的情況下感知可用知識

### Modified Capabilities

（無——知識注入作為獨立插件，不修改 ecc-hooks 的 hook-system）

## Impact

- **檔案變更**：
  - `plugins/auto-skill-hooks/.claude-plugin/plugin.json` — 新增插件定義
  - `plugins/auto-skill-hooks/hooks/hooks.json` — SessionStart hook 配置
  - `plugins/auto-skill-hooks/scripts/inject-knowledge-index.py` — 注入腳本
  - `~/.claude/CLAUDE.md` — 新增全域行為指令（此檔案目前不存在）
  - `skills/auto-skill/SKILL.md` — 精簡內容
- **依賴**：Python 3
- **插件註冊**：`~/.claude/settings.json` 新增 `"auto-skill-hooks@custom-skills": true`
- **向下相容**：knowledge-base 和 experience 的資料格式不變；`/auto-skill` 仍可手動呼叫
