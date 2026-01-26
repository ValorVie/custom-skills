# Upstream Sync | 上游同步

Synchronize third-party repositories and generate diff reports for review.

同步第三方儲存庫並產生差異報告供審核。

## Usage | 使用方式

```
/custom-skills-upstream-sync [options]
```

## Options | 選項

| Option | Description | 說明 |
|--------|-------------|------|
| `--check` | Check for updates only | 僅檢查更新 |
| `--pull` | Pull all upstream repos | 拉取所有上游 repo |
| `--diff` | Generate diff report | 產生差異報告 |
| `--full` | Full workflow (pull + check + diff) | 完整流程 |
| `--source <name>` | Sync specific source | 同步特定來源 |

## Workflow | 工作流程

### Step 1: Check Updates | 步驟 1：檢查更新

```bash
python skills/custom-skills-upstream-sync/scripts/sync_upstream.py --check
```

Lists sources with updates without making changes.

列出有更新的來源，不做任何變更。

### Step 2: Pull and Generate Report | 步驟 2：拉取並產生報告

```bash
python skills/custom-skills-upstream-sync/scripts/sync_upstream.py --full
```

1. Pull all upstream repos
2. Check for new commits
3. Generate `upstream/diff-report-YYYY-MM-DD.md`

### Step 3: Review | 步驟 3：審核

Read the diff report and decide:
- Which changes to accept
- Which changes to reject
- Which need modification

閱讀差異報告並決定：
- 接受哪些變更
- 拒絕哪些變更
- 哪些需要修改

### Step 4: Apply Changes | 步驟 4：套用變更

After approval:

1. Copy approved files from upstream to custom-skills
2. Update `upstream/<source>/last-sync.yaml`
3. Commit changes

核准後：

1. 複製核准的檔案從上游到 custom-skills
2. 更新 `upstream/<source>/last-sync.yaml`
3. 提交變更

## Sources Configuration | 來源配置

See `upstream/sources.yaml` for configured sources.

查看 `upstream/sources.yaml` 了解已配置的來源。

## Example | 範例

```bash
# Check all sources
/custom-skills-upstream-sync --check

# Full sync for ecc only
/custom-skills-upstream-sync --full --source everything-claude-code

# Generate report without pulling
/custom-skills-upstream-sync --diff
```
