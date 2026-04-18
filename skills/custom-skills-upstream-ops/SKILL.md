---
name: custom-skills-upstream-ops
description: |
  Unified upstream repo operations: audit commit drift, check UDS file-level drift, detect repo overlap with local project, and perform sync maintenance.
  Use when: reviewing upstream updates, auditing standards drift, evaluating a new repo for integration, updating last-sync.yaml after sync.
  Triggers: "upstream audit", "uds check", "repo overlap", "sync maintenance", "上游同步", "上游檢查", "上游維護".
---

# Upstream Ops | 上游操作統一入口

管理所有跟上游 repo 相關的操作。依 argument 路由到 `modes/<name>.md`。

## 用法

```bash
/custom-skills-upstream-ops                           # 預設 = audit
/custom-skills-upstream-ops audit [--source <name>] [--archive]
/custom-skills-upstream-ops uds-check [--verbose] [--report]
/custom-skills-upstream-ops overlap <repo-path-or-source-name>
/custom-skills-upstream-ops maintenance <sub>
```

## Mode 選擇表

| 我想…… | 用哪個 mode |
|-------|-----------|
| 看上游有哪些變動、該怎麼同步 | `audit`（預設） |
| 知道 `.standards/` 跟 UDS 有哪些檔案不一致 | `uds-check` |
| 評估某個 repo 跟本專案有多少重疊功能 | `overlap` |
| 同步完成後更新 `last-sync.yaml`、清理舊報告 | `maintenance` |

## Modes

- **audit** — 讀 `upstream/sources.yaml` + `last-sync.yaml`，對每個上游跑 `git log` / `git diff --stat`，輸出同步決策清單。見 `modes/audit.md`。
- **uds-check** — UDS 的 `.standards/` 與鏡像 `skills/<id>/` 檔案級 SHA-256 比對。用 `scripts/check_uds.py`。見 `modes/uds-check.md`。
- **overlap** — 任一 repo vs 本專案的功能重疊偵測；輸出可複製到 `overlaps.yaml` 的 YAML 片段（不寫檔）。見 `modes/overlap.md`。
- **maintenance** — `update-last-sync`、`archive-reports`、`list-orphans` 三個子命令。見 `modes/maintenance.md`。

## References

- `references/install-methods.md` — 各上游 `install_method` 的同步命令 one-liner
- `references/decision-patterns.md` — audit 結果判讀規則（取代舊 upstream-compare 的 reading guide）

## 相關

- `ai-dev update --only repos` — 拉取上游檔案
- `ai-dev clone` — 分發 `.standards/` 與 `skills/`
- `custom-skills-tool-overlap-analyzer` — 分析**本專案內部**工具重疊（不同職責）
