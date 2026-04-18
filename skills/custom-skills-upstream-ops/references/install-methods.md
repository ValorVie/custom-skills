# Install Methods | 同步方式對照

各上游 repo 的 `install_method` 對應正確的同步命令。對照 `upstream/sources.yaml` 使用。

## 對照表

| install_method | 同步命令 | 典型來源 | 備註 |
|---------------|---------|---------|------|
| `plugin` | `claude plugin update <plugin_id>` + 重啟 Claude Code | superpowers | 不需手動複製檔案 |
| `ai-dev` | `ai-dev update --only repos` → `ai-dev clone` | obsidian-skills, anthropic-skills, auto-skill | 自動同步到 `skills/` |
| `standards` | `ai-dev update --only repos` → `ai-dev clone` → `uds-check` mode 做 diff | universal-dev-standards | `.standards/` 需逐檔合併 |
| `selective` | `ai-dev clone`（讀 `distribution.yaml` 過濾） | everything-claude-code | 依排除清單選擇性分發 |
| `manual` | 手動比對與複製 | （本專案目前無） | 本地有深度客製時用 |

## 常見誤判

- **plugin 類型顯示 High 變動**：不代表要手動複製檔案，只需 `claude plugin update`
- **ai-dev 類型顯示有變更**：先跑 `ai-dev clone`，可能 diff 已為零
- **standards 類型**：需注意本地 `.standards/` 可能有客製化修改（見 `uds-check` 的 `only_local` 類別）
- **selective 類型**：`distribution.yaml` 的 exclude list 會過濾掉特定 skill

## 同步後必做

套用完變更後，更新 `upstream/last-sync.yaml` 對應來源的 commit 為新 HEAD：

```yaml
<source-name>:
  commit: <new-head-sha>
  synced_at: '<ISO-8601-timestamp>'
```

使用 `maintenance update-last-sync <source>` 互動式完成，或手動編輯。
