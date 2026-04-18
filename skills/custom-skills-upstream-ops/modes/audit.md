# Mode: audit

上游 commit 差異 + 同步決策。純 AI workflow，無 Python 腳本。

## 觸發

```
/custom-skills-upstream-ops                          # 等同 audit（預設 mode）
/custom-skills-upstream-ops audit
/custom-skills-upstream-ops audit --source <name>    # 單一來源
/custom-skills-upstream-ops audit --archive          # 寫 Markdown 摘要到 upstream/reports/audit/
```

## 執行流程

1. **讀配置**
   - `upstream/sources.yaml` 取所有來源（name、local_path、install_method）
   - `upstream/last-sync.yaml` 取各來源上次同步 commit

2. **對每個上游**（或 `--source` 指定的單一來源）：
   ```bash
   git -C <local_path> rev-parse HEAD
   ```
   若 `HEAD == last_sync_commit`：跳過（標記 up-to-date）。

3. **若有落差**：
   ```bash
   git -C <local_path> log --oneline --no-merges <last_sync>..HEAD
   git -C <local_path> diff --stat <last_sync>..HEAD
   ```

4. **依 `references/decision-patterns.md` 判讀**：
   - 優先級
   - 變更分類
   - 新架構偵測

5. **依 `references/install-methods.md` 產出同步命令**：
   - plugin → `claude plugin update <id>`
   - ai-dev → `ai-dev update --only repos` 然後 `ai-dev clone`
   - standards → 同上 + `uds-check` mode
   - selective → `ai-dev clone`
   - manual → 手動

6. **輸出 Markdown 摘要到對話**。

7. **若 `--archive`**：同時寫到 `upstream/reports/audit/audit-YYYY-MM-DD.md`。

## 輸出格式

```markdown
## Upstream Audit — YYYY-MM-DD

### <source-name> (<install_method>)
- <N> commits behind · 優先級：<High|Medium|Low|Skip>
- 主要變更：<3 句內 AI 摘要>
- 同步：`<one-liner command>`
- 備註：<若有新架構偵測或特殊情況>

### <next source>
...

## 下一步建議

1. 優先處理 High：<列出>
2. 套用完成後跑 `/custom-skills-upstream-ops maintenance update-last-sync <source>` 更新 last-sync
```

## 明確不做

- ❌ 不用 regex 解析 commit subject 分類 feat/fix/refactor（AI 讀 subject 就夠）
- ❌ 不計算 High/Medium/Low 數值分數（AI 直接判斷）
- ❌ 不輸出 YAML 結構化報告
- ❌ 不呼叫 Python 腳本
- ❌ 不自動跑同步命令（只給建議，使用者自己決定是否執行）

## 輸出範例

```markdown
## Upstream Audit — 2026-04-18

### universal-dev-standards (standards)
- 53 commits behind · 優先級：High
- 主要變更：XSPEC-035~044（雙階段輸出、斷路器、token budget）、DEC-043 Wave 1 Reliability、anti-sycophancy-prompting
- 同步：`ai-dev update --only repos` → `ai-dev clone` → `/custom-skills-upstream-ops uds-check` 處理檔案合併
- 備註：新增 6 份 meta standards，影響現有 .standards/ 閱讀結構

### superpowers (plugin)
- 12 commits behind · 優先級：Medium
- 主要變更：brainstorming skill 擴充、新增 visual companion
- 同步：`claude plugin update superpowers@superpowers-marketplace` + 重啟 Claude Code
```
