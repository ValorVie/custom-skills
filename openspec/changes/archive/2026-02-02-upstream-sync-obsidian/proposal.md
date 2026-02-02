# Proposal: upstream-sync-obsidian

**類型**: 上游同步
**優先級**: Low
**複雜度**: 低
**來源**: upstream/reports/analysis/compare-2026-02-02.md

---

## 背景

obsidian-skills 上游 (kepano/obsidian-skills) 有 2 個新 commit，包含 2 個 skill 的小幅更新。
變更量小（+58/-11 行），風險極低，可直接同步。

## 變更範圍

### 1. json-canvas/SKILL.md

**上游 commit**: `1fe3a85` — Add instructions about JSON newline escaping to avoid common mistakes

**變更內容**: 新增 JSON 中換行符號跳脫的說明，避免使用者在建立 JSON Canvas 時常犯的 newline 錯誤。

**同步方式**: 從上游 `skills/json-canvas/SKILL.md` 複製對應段落到本專案 `skills/json-canvas/SKILL.md`

### 2. obsidian-bases/SKILL.md

**上游 commit**: `41909ae` — docs(obsidian-bases): add Duration type documentation and fix date formulas

**變更內容**:
- 新增 Duration 類型的文件說明
- 修正日期公式（bug fix）

**同步方式**: 從上游 `skills/obsidian-bases/SKILL.md` 複製對應段落到本專案 `skills/obsidian-bases/SKILL.md`

## 實作步驟

1. Diff 本地與上游的 `skills/json-canvas/SKILL.md`，合併新增內容
2. Diff 本地與上游的 `skills/obsidian-bases/SKILL.md`，合併新增內容
3. 驗證 markdown 格式正確
4. 更新 `upstream/last-sync.yaml` 中 obsidian-skills 的 `last_synced_commit`

## 風險

- **衝突風險**: 極低 — 上游為純新增內容，不修改既有段落
- **影響範圍**: 僅 Obsidian 相關 skill，不影響其他功能

## 驗收標準

- [ ] json-canvas SKILL.md 包含 JSON newline escaping 說明
- [ ] obsidian-bases SKILL.md 包含 Duration type 文件
- [ ] obsidian-bases SKILL.md 日期公式已修正
- [ ] last-sync.yaml 已更新為 `34c2cda`
