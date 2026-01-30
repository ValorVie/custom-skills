## Context

`script/commands/project.py` 實作了 `ai-dev project init` 指令，其中 `--force` 在 custom-skills 專案中會觸發反向同步（專案 → project-template）。目前有兩個問題需要修正。

## Goals / Non-Goals

**Goals:**
- 反向同步目標指向 `cwd/project-template/`（repo 內）
- 排除 `settings.local.json` 不被複製進模板
- 移除 repo 中已存在的 `project-template/.claude/settings.local.json`

**Non-Goals:**
- 不修改正向 init 的邏輯（從模板複製到目標專案）
- 不引入 `.templateignore` 配置檔

## Decisions

### Decision 1: 反向同步目標改為 `project_root / "project-template"`

**選擇**：在 `init()` 函式中，反向同步時直接用 `project_root / "project-template"` 取代 `get_project_template_dir()`。

**理由**：`get_project_template_dir()` 優先返回 `~/.config/custom-skills/project-template/`，這在正向 init 時是正確的（安裝後的模板），但反向同步的意圖是更新 repo 內的範本。

**替代方案**：修改 `get_project_template_dir()` 加入參數切換——但會增加函式複雜度，不如直接在呼叫端處理。

### Decision 2: 排除清單使用 `shutil.copytree` 的 `ignore` 參數

**選擇**：新增 `EXCLUDE_FROM_TEMPLATE` 常數和 `_template_ignore()` 函式，傳入 `shutil.copytree(ignore=...)` 參數。

**理由**：`shutil.copytree` 原生支援 `ignore` 回調，不需要額外框架。排除清單以相對路徑儲存，便於維護。

**替代方案**：
- `.templateignore` 檔案：過度設計，目前只需排除一個檔案
- 複製後刪除：不夠乾淨，且有時序問題

### Decision 3: 排除清單同時應用於正向和反向

**選擇**：`init()` 正向複製的 `copytree` 也加入相同的 `ignore` 參數。

**理由**：`settings.local.json` 在任何方向都不應被複製——它是個人設定，不屬於模板。

## Risks / Trade-offs

- **[風險] 排除清單擴展** → 目前只有一個項目，若未來增加，常數清單即可維護
- **[風險] 已存在的 settings.local.json** → 需要在此 PR 中移除 `project-template/.claude/settings.local.json`
