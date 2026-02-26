# v2 Full Parity Design

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make v2 ai-dev CLI (TypeScript/Bun) output and behavior identical to v1 (Python/Typer/Rich)

**Architecture:** Approach 1 — Full alignment of language, data output format, data correctness, and Claude Code lifecycle. Commander.js help format accepted as-is (no Rich panel emulation).

**Tech Stack:** Bun, Commander.js, chalk, cli-table3, ora

---

## Verified Differences (from actual command output comparison)

### Category A: Language (~60 places)

All CLI text is in English, must be zh-TW by default.

| Location | v1 (zh-TW) | v2 (English) |
|----------|------------|--------------|
| Program description | AI Development Environment Setup CLI | AI development workflow CLI toolkit |
| install description | 首次安裝 AI 開發環境 | Install AI development environment |
| update description | 更新工具與拉取儲存庫 | Update packages and repositories |
| clone description | 分發 Skills 到各工具目錄 | Distribute resources to configured AI tool directories |
| status table headers | 工具/狀態/版本 | Core Tool/Status/Version |
| list table headers | 名稱/來源/狀態 | Name/Source/Status |
| status values | 已安裝/✓ 啟用/⚠ 落後 N 個 commit | OK/✓ Enabled/⚠ behind N |
| All option help text | 跳過 NPM 套件安裝 | Skip global NPM package installation |
| All error messages | 專案尚未初始化標準體系 | (English equivalents) |

**Fix:** Change `DEFAULT_LOCALE` from `"en"` to `"zh-TW"`. Add ~150 i18n keys for all CLI descriptions, option help text, table headers, and status messages.

### Category B: Data Output Format (~10 commands)

| Command | v1 Format | v2 Format |
|---------|-----------|-----------|
| `status` | 4 separate Rich tables with Chinese titles (核心工具/全域NPM套件/設定儲存庫/上游同步狀態) | 4 cli-table3 tables but English headers, no group titles |
| `list` | Grouped by Target+Type, each group has title like "Claude Code - Skills" | One flat table with Target/Type/Name/Status/Source columns |
| `list` columns | 名稱/來源/狀態 | Target/Type/Name/Status/Source |
| `sync status` | Rich table (Path/Local Changes/Remote/Last Sync) | Plain text bullet points |
| `mem status` | Rich table (項目/值) with real server data | Plain text "unregistered, 0 observations" |
| `standards overlaps` | Rich panel + detailed group listings (6 groups) | "! No overlaps detected." |
| `standards status` | Warning "專案尚未初始化標準體系" | Table showing Initialized=true |
| Help descriptions | v1 update --help shows 4-step numbered description | v2 shows one-line description |
| Table style | Rich thick borders (━┃┏┓) with colored titles | cli-table3 thin borders (─│┌┐) |

**Fix:**
- `printTable()` add `title` parameter for group headers
- cli-table3 `chars` option to use thick borders matching Rich style
- `status` output: split into 4 named tables
- `list` output: group by Target+Type, one table per group
- `sync status`: use table format
- `mem status`: use table format + fix data source

### Category C: Data Correctness (3-4 commands)

| Command | Issue | Root Cause |
|---------|-------|------------|
| `mem status` | Shows "unregistered", 0 observations | Not reading actual server/local data |
| `standards overlaps` | "No overlaps detected" | Not reading overlaps.yaml correctly |
| `standards status` | Shows Initialized=true when v1 shows "未初始化" | Wrong initialization detection logic |

**Fix:** Fix core modules: `mem-sync.ts`, `standards-manager.ts`

### Category D: Help Format (accepted difference)

v1 uses Rich panels (╭─ Options ─╮), v2 uses Commander.js plain format.
This is an **accepted difference** — not worth the custom renderer effort.
All help text will be in zh-TW though.

### Category E: Claude Code Lifecycle (NEW — missing entirely)

#### E1: install — Claude Code detection (v1 step 1.5)

v1 `show_claude_status()`:
- `get_claude_install_type()` → detects npm / native / not-installed
  - Checks `which claude`
  - If found, checks `npm list -g @anthropic-ai/claude-code`
  - npm found → "npm", not found → "native", no claude → None
- Not installed → shows install instructions (curl / Homebrew / WinGet)
- npm installed → warns to switch to native
- native installed → shows ✓

v2 currently: **Does nothing about Claude Code in install**

#### E2: update — Claude Code update (v1 step 1)

v1 `update_claude_code()`:
- npm install → `npm install -g @anthropic-ai/claude-code@latest` + migration hint
- native install → `claude update`
- not installed → show install instructions

v2 currently: **Does nothing about Claude Code in update**

#### E3: update — Additional missing steps

| v1 Step | Description | v2 Status |
|---------|-------------|-----------|
| `uds update` | Update project standards if initialized | Missing |
| `npx skills update` | Update third-party skills | Missing |
| Plugin Marketplace | Scan ~/.claude/plugins/marketplaces/ and update each | Missing |
| Shell completion | Auto-install shell completion in install | Missing |
| Missing repos warning | List un-cloned repos with remediation hint | Missing |
| Update summary | List which repos updated vs already current | Partial |

---

## Design Decisions

### D1: Default locale → zh-TW
- Change `DEFAULT_LOCALE` from `"en"` to `"zh-TW"`
- All Commander.js `.description()` and `.option()` text use `t()` function
- ~150 new i18n keys (both en and zh-TW)

### D2: Table formatting improvements
- `printTable(headers, rows, { title?, style? })` — add optional title above table
- Rich-style thick borders via cli-table3 `chars` config
- Colored title headers (chalk.bold)

### D3: status output restructure
- 4 separate tables: 核心工具, 全域 NPM 套件, 設定儲存庫, 上游同步狀態
- Chinese column headers matching v1 exactly
- Status values in Chinese (已安裝, ✓ 最新, ↑ 有可用更新, ⚠ 落後 N 個 commit)

### D4: list output restructure
- Group by Target+Type, each group as separate table with title (e.g., "Claude Code - Skills")
- Columns: 名稱/來源/狀態 (matching v1)
- Remove Target/Type columns from individual rows

### D5: Claude Code lifecycle management
- New module: `src/core/claude-code-manager.ts`
  - `getClaudeInstallType(): "npm" | "native" | null`
  - `showClaudeStatus(onProgress)`: for install flow
  - `updateClaudeCode(onProgress)`: for update flow
  - `showInstallInstructions(onProgress)`: installation guide
- Integrate into install (step 1.5) and update (step 1)

### D6: update complete flow
- Add `uds update` call (when project initialized)
- Add `npx skills update` call
- Add Plugin Marketplace scan and update
- Add missing repos warning with remediation hint
- Add update summary (which repos updated/current/missing)

---

## Files to Modify

| Category | File | Changes |
|----------|------|---------|
| i18n | `src/utils/i18n.ts` | DEFAULT_LOCALE → zh-TW, +150 keys |
| formatter | `src/utils/formatter.ts` | Table title, thick borders, Rich style |
| CLI entry | `src/cli/index.ts` | Description i18n |
| install | `src/cli/install.ts` | i18n + Claude Code check |
| update | `src/cli/update.ts` | i18n + Claude Code update + full flow |
| status | `src/cli/status.ts` | 4 grouped tables, Chinese headers |
| list | `src/cli/list.ts` | Target+Type grouping |
| clone | `src/cli/clone.ts` | i18n |
| toggle | `src/cli/toggle.ts` | i18n |
| add-repo | `src/cli/add-repo.ts` | i18n |
| add-custom-repo | `src/cli/add-custom-repo.ts` | i18n |
| update-custom-repo | `src/cli/update-custom-repo.ts` | i18n |
| test | `src/cli/test.ts` | i18n |
| coverage | `src/cli/coverage.ts` | i18n |
| derive-tests | `src/cli/derive-tests.ts` | i18n |
| project | `src/cli/project/index.ts` | i18n |
| standards | `src/cli/standards/index.ts` | i18n + fix overlaps/status |
| hooks | `src/cli/hooks/index.ts` | i18n |
| sync | `src/cli/sync/index.ts` | i18n + table format |
| mem | `src/cli/mem/index.ts` | i18n + table format + fix data |
| tui | `src/cli/tui.ts` | i18n |
| NEW | `src/core/claude-code-manager.ts` | Claude Code lifecycle |
| core | `src/core/installer.ts` | Integrate Claude Code check |
| core | `src/core/updater.ts` | Integrate Claude Code update + full flow |
| core | `src/core/standards-manager.ts` | Fix overlaps + status logic |
| core | `src/core/mem-sync.ts` | Fix status data reading |
| tests | `tests/cli/smoke.test.ts` | Update expected values |
| tests | Various | Update for new behavior |

## What We're NOT Doing

- Not emulating Rich panels (╭─╮) for Commander.js help
- Not removing v2 extras that v1 doesn't have (--json, --lang)
- Not rewriting core business logic
- Not changing the Bun runtime or build system
