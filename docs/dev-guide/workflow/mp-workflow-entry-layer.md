# MP 工作入口層定位指南

本文件說明 ai-dev 如何看待 `mattpocock/skills` 的 MP 工作入口層改寫版。MP 是通用工具，不是 ai-dev 框架專案自己的專案層級 skill，也不是 `project-template` 的預載內容。

日常操作與情境示範請看 [MP 使用指南](MP-USAGE-GUIDE.md)。

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

通用工具命名一律採 `mp-<來源技能名>`：

- `mp-setup-matt-pocock-skills`
- `mp-grill-with-docs`
- `mp-to-issues`
- `mp-triage`
- `mp-improve-codebase-architecture`
- `mp-to-prd`

這樣可保留上游辨識度，也能在未來上游更新時用 mapping 追蹤差異。這些名稱描述的是工具本身，不代表每個使用 ai-dev 的目標專案都必須建立同名 project-level skill。

## 上游追蹤

上游登錄在：

- `upstream/sources.yaml`
- `upstream/mattpocock-skills/last-sync.yaml`
- `upstream/mattpocock-skills/mapping.yaml`

`install_method` 必須保持 `manual`。`mp-*` 是人工審核後的通用工具改寫版，不是直接複製版。

## 更新流程

```text
ai-dev update
  -> 拉取 ~/.config/mattpocock-skills
  -> /custom-skills-upstream-ops audit --source mattpocock-skills
  -> 依 upstream/mattpocock-skills/mapping.yaml 檢查選定技能差異
  -> 人工決定是否更新通用 mp-* 工具
  -> 更新 upstream/mattpocock-skills/last-sync.yaml
```

審核時只看 `mapping.yaml` 中列為 `skills` 的來源技能。`excluded` 區塊列出的技能不應被自動導入。

## 目標專案導入

目標專案需要 MP 時，透過 `mp-setup-matt-pocock-skills` opt-in 建立自己的工作流文件：

- `docs/agents/mp-workflow.md`
- `docs/agents/issue-tracker.md`
- `docs/agents/triage-states.md`
- `docs/agents/domain.md`

若目標專案有 `CLAUDE.md` 或 `AGENTS.md`，只加入 MP 入口提示，不在入口文件中維護完整規則。ai-dev 的 `project-template` 不預載這些 MP 文件，避免把可選工具變成所有專案的預設立場。

## 驗證

建議檢查文件邊界：

- [MP 使用指南](MP-USAGE-GUIDE.md) 明確說明 MP 是通用工具。
- [DEVELOPMENT-WORKFLOW.md](DEVELOPMENT-WORKFLOW.md) 只描述日常開發流程，不要求本專案存在 `docs/agents/`。
- `project-template/` 不包含 MP 專案工作流文件。
- `mp-*` 的 description 不覆蓋 `openspec-*` 或 `superpowers:*` 的觸發責任。
