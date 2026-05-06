# MP 工作入口層導入指南

本文件說明本專案如何導入 `mattpocock/skills` 的工作入口層改寫版。

## 定位

MP 工作入口層負責：

- 需求澄清。
- 專案語言校準。
- OpenSpec 前置摘要。
- 垂直切片。
- 任務分流。
- 架構改善候選。

它不取代：

- `openspec-*`：正式變更生命週期。
- `superpowers:*`：任務內 TDD、除錯、review、完成前驗證。

## 命名

本地技能一律採 `mp-<來源技能名>`：

- `mp-setup-matt-pocock-skills`
- `mp-grill-with-docs`
- `mp-to-issues`
- `mp-triage`
- `mp-improve-codebase-architecture`
- `mp-to-prd`

這樣可保留上游辨識度，也能在未來上游更新時用 mapping 追蹤差異。

## 上游追蹤

上游登錄在：

- `upstream/sources.yaml`
- `upstream/mattpocock-skills/last-sync.yaml`
- `upstream/mattpocock-skills/mapping.yaml`

`install_method` 必須保持 `manual`。本地 `mp-*` 是改寫版，不是直接複製版。

## 更新流程

```text
ai-dev update
  -> 拉取 ~/.config/mattpocock-skills
  -> /custom-skills-upstream-ops audit --source mattpocock-skills
  -> 依 upstream/mattpocock-skills/mapping.yaml 檢查選定技能差異
  -> 人工決定是否更新 skills/mp-*/
  -> 更新 upstream/mattpocock-skills/last-sync.yaml
```

審核時只看 `mapping.yaml` 中列為 `skills` 的來源技能。`excluded` 區塊列出的技能不應被自動導入。

## Claude / Codex 投影

canonical 來源在 `skills/mp-*`。

投影目標：

- `.claude/skills/mp-*`
- `.codex/skills/mp-*`

共同規則不放在兩個入口文件中分叉維護，而是放在 `docs/agents/`。

## 驗證

建議檢查：

```bash
openspec validate add-mp-workflow-entry-layer --strict
find skills .claude/skills .codex/skills -path '*/mp-*/SKILL.md' -print
```

並確認 `mp-*` 的 description 不會覆蓋 `openspec-*` 或 `superpowers:*` 的觸發責任。
