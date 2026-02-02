# Proposal: upstream-sync-worktree-safety

**類型**: 上游同步
**優先級**: High
**複雜度**: 中
**來源**: upstream/reports/analysis/compare-2026-02-02.md

---

## 背景

superpowers 上游 (obra/superpowers) 對 subagent 工作流進行了安全性強化，要求使用 git worktree 隔離開發，防止 subagent 直接在 main branch 操作。這是三個 skill 的連動更新，形成完整的安全鏈。

## 動機

目前本專案的 subagent 相關 skill 缺少 main branch 保護機制。若 subagent 在 main branch 上直接操作，可能造成：
- 未經審查的變更直接進入主分支
- 多個 subagent 互相衝突
- 意外破壞主分支歷史

## 變更範圍

### 安全鏈架構

```
subagent-driven-development
    │ requires
    ▼
using-git-worktrees  ◀── callers: [subagent-driven-dev, executing-plans]
    │ required by
    ▼
executing-plans
```

### 1. skills/subagent-driven-development/SKILL.md

**上游 commits**: `b63d485`, `fa3f46d`

**變更內容**:
- 新增 main branch 紅旗警告到 "Never" 清單
- 新增 `using-git-worktrees` 為必要前置 skill
- 要求使用者明確同意才能在 main branch 操作

### 2. skills/executing-plans/SKILL.md

**上游 commit**: `b323e35`

**變更內容**:
- 新增 worktree 前置要求：執行計畫前必須先建立 worktree

### 3. skills/using-git-worktrees/SKILL.md

**上游 commit**: `bb2ff5d`

**變更內容**:
- 新增 callers 資訊：標注 subagent-driven-development 和 executing-plans 為呼叫者

## 實作步驟

1. 逐一 diff 三個 skill 的本地版本與上游版本
2. 確認本專案是否有自訂修改（需 3-way diff）
3. 合併上游變更，保留本專案自訂內容
4. 確認三個 skill 的交叉引用一致
5. 更新 `upstream/last-sync.yaml` 中 superpowers 的 `last_synced_commit`

## 風險

- **衝突風險**: 中 — 本專案可能已對這三個 skill 有自訂修改
- **功能影響**: 中 — 會改變 subagent 的行為模式，要求使用 worktree
- **緩解措施**: 使用 3-way diff 合併，保留本專案自訂內容；紅旗警告設為需使用者明確同意

## 驗收標準

- [ ] subagent-driven-development 包含 main branch 紅旗警告
- [ ] subagent-driven-development 引用 using-git-worktrees 為必要 skill
- [ ] executing-plans 包含 worktree 前置要求
- [ ] using-git-worktrees 列出 callers
- [ ] 三個 skill 的交叉引用一致無矛盾
- [ ] last-sync.yaml 已更新為 `06b92f3`
