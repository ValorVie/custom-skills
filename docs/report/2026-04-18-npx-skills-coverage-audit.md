# npx skills registry 覆蓋率盤點報告

**日期**：2026-04-18
**範圍**：`skills/` 下 53 個本地 skill
**目的**：判斷哪些本地 skill 可改由 `npx skills` registry 維護，以精簡本地維護量
**工具**：`npx skills find <name>` 對 [skills.sh](https://skills.sh) registry 查詢

---

## 摘要

| 類別 | 數量 | 行動 |
|------|------|------|
| ✅ 可改用 npx（官方/權威來源） | 7 | 可移除本地、改用 `npx skills add` |
| 🟡 需人工判斷（僅非官方聚合 repo） | 5 | diff 後決定 |
| 🔒 保留本地（UDS 上游鏡像） | 24 | 由 `ai-dev clone` 維護 |
| 🔒 保留本地（custom-* 專屬） | 12 | 本專案客製 |
| 🔒 保留本地（無對應/語意不符） | 5 | 無替代方案 |

---

## A 組：可安全改用 npx（7 個）

來源為官方（Anthropic）或權威作者（kepano = Obsidian 官方），下載量高。

| 本地 skill | npx 對應 | 權威來源 | 下載量 |
|-----------|---------|---------|-------|
| `claude-api` | `anthropics/skills@claude-api` | Anthropic 官方 | 13.9K |
| `skill-creator` | `anthropics/skills@skill-creator` | Anthropic 官方 | 154.4K |
| `defuddle` | `kepano/obsidian-skills@defuddle` | kepano | 12.9K |
| `obsidian-markdown` | `kepano/obsidian-skills@obsidian-markdown` | kepano | 20.3K |
| `obsidian-cli` | `kepano/obsidian-skills@obsidian-cli` | kepano | 18.1K |
| `obsidian-bases` | `kepano/obsidian-skills@obsidian-bases` | kepano | 18.9K |
| `json-canvas` | `kepano/obsidian-skills@json-canvas` | kepano | 14.1K |

**安裝指令範例**：
```bash
npx skills add anthropics/skills@claude-api
npx skills add anthropics/skills@skill-creator
npx skills add kepano/obsidian-skills@defuddle
npx skills add kepano/obsidian-skills@obsidian-markdown
npx skills add kepano/obsidian-skills@obsidian-cli
npx skills add kepano/obsidian-skills@obsidian-bases
npx skills add kepano/obsidian-skills@json-canvas
```

---

## B 組：需人工判斷（5 個）

僅 `affaan-m/everything-claude-code` 這種非官方聚合 repo 提供，來源可信度不足。建議先 diff 本地版與 npx 版再決定。

| 本地 skill | npx 對應 | 下載量 | 備註 |
|-----------|---------|-------|------|
| `codebase-onboarding` | `affaan-m/everything-claude-code@codebase-onboarding` | 1.7K | — |
| `context-budget` | `affaan-m/everything-claude-code@context-budget` | 1.5K | 本地版定位較明確（審計整體 context 消耗），可能與 npx 版不同 |
| `mcp-server-patterns` | `affaan-m/everything-claude-code@mcp-server-patterns` | 1.7K | 本地版已含內部約定（Context7），建議保留 |
| `safety-guard` | `affaan-m/everything-claude-code@safety-guard` | 997 | — |
| `security-scan` | `affaan-m/everything-claude-code@security-scan` | 2.7K | — |

**行動**：逐個 `npx skills add --dry-run` 或 clone 後 diff 本地版，比對差異後決定。

---

## C 組：保留本地 — UDS 上游鏡像（24 個）

由 `universal-dev-standards` 上游維護，透過 `ai-dev clone` 同步到本地。這些 skill 在 npx registry 無對等權威版本。

```
ai-collaboration-standards, ai-friendly-architecture, ai-instruction-standards,
atdd-assistant, bdd-assistant, changelog-guide, checkin-assistant,
code-review-assistant, commit-standards, docs-generator, documentation-guide,
error-code-guide, forward-derivation, git-workflow-guide, logging-guide,
methodology-system, project-structure-guide, refactoring-assistant,
release-standards, requirement-assistant, reverse-engineer, spec-driven-dev,
test-coverage-assistant, testing-guide
```

**維護方式**：`ai-dev update --only repos` + `ai-dev clone`

---

## D 組：保留本地 — custom-* 專屬（12 個）

本專案客製 skill，不對外發布。

```
custom-simplify, custom-skill-creator, custom-skills-dev,
custom-skills-doc-updater, custom-skills-doc-writer,
custom-skills-git-commit, custom-skills-notify,
custom-skills-plan-analyze, custom-skills-threads-research,
custom-skills-tool-overlap-analyzer, custom-skills-upstream-ops
```

---

## E 組：保留本地 — 無對應或語意不符（5 個）

| 本地 skill | 狀況 |
|-----------|------|
| `wiki` | npx 僅有 `larksuite/lark-wiki`（飛書 Wiki），語意不同 |
| `auto-skill` | npx 有 `toolsai/auto-skill@auto-skill`（293 installs），語意不符本地（任務啟動協議） |
| `cloud-infrastructure-security` | 無結果 |
| `discuss-multi-ai` | 無結果 |
| `work-log-claude` | 無結果 |

---

## 建議行動順序

1. **A 組 7 個**：先移除本地，改用 `npx skills add` 安裝官方版
   - 風險低，官方維護
   - 節省本地維護負擔

2. **B 組 5 個**：逐一 diff
   - 若本地無特殊客製 → 改用 npx
   - 若本地有客製（如 `mcp-server-patterns` 的 Context7 約定）→ 保留

3. **C/D/E 組 41 個**：現狀不變

---

## 備註

- `npx skills` 是 https://skills.sh 的 CLI，支援 `add/remove/list/find/update`
- 支援專案層級（`./node_modules` 或 `skills-lock.json`）與全域層級（`-g`）
- 若改用 npx，需更新 `ai-dev` 相關流程（例如 `ai-dev clone` 是否涵蓋 npx skills）

---

## 執行結果（2026-04-18）

本盤點的遷移建議已完整執行：

- **A 組 7 個 + B 組 5 個共 12 個 skill** 已改用 npx 維護
  - 見 `upstream/npx-skills.yaml`
  - 安裝指令：`ai-dev install-npx-skills`
- **C 組 24 個 UDS 鏡像**已移至 `skills/uds/` 子目錄（commit `e472d92`）
- 本地 12 個鏡像已移除（commit `8d14135`）

### 相關文件
- 設計稿：`docs/plans/2026-04-18-npx-skills-migration-design.md`
- 實作計畫：`docs/plans/2026-04-18-npx-skills-migration-impl.md`
