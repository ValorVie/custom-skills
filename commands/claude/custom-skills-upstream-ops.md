# Upstream Ops | 上游操作

Unified upstream repo operations: audit drift, check UDS files, detect overlap, maintain sync state.

統一上游 repo 操作入口：audit 變動 / 檢查 UDS 檔案 / 偵測重疊 / 維護同步狀態。

## Usage | 使用方式

```
/custom-skills-upstream-ops                               # 預設 audit
/custom-skills-upstream-ops audit [--source <n>] [--archive]
/custom-skills-upstream-ops uds-check [--verbose] [--report]
/custom-skills-upstream-ops overlap <repo-path-or-source-name>
/custom-skills-upstream-ops maintenance <sub>
```

## Modes | 模式

| Mode | 說明 | 範例 |
|------|------|------|
| `audit`（預設） | 上游 commit 差異 + 同步建議（AI workflow） | `/custom-skills-upstream-ops` |
| `uds-check` | UDS 檔案級漂移（SHA-256 腳本） | `/custom-skills-upstream-ops uds-check --verbose` |
| `overlap` | 任一 repo vs 本專案重疊偵測 | `/custom-skills-upstream-ops overlap everything-claude-code` |
| `maintenance` | last-sync 更新、歸檔、孤兒偵測 | `/custom-skills-upstream-ops maintenance list-orphans` |

## Files | 檔案

- `skills/custom-skills-upstream-ops/SKILL.md` — 入口
- `skills/custom-skills-upstream-ops/modes/*.md` — 各 mode 實作
- `skills/custom-skills-upstream-ops/references/*.md` — 決策表與 reading guide
- `skills/custom-skills-upstream-ops/scripts/check_uds.py` — 唯一保留的 Python

## Related | 相關

- `ai-dev update --only repos` — 拉取上游檔案
- `ai-dev clone` — 分發 `.standards/` 與 `skills/`
- `custom-skills-tool-overlap-analyzer` — 本專案內部工具重疊（不同職責）
