# Mode: maintenance

上游同步相關的維護操作。AI workflow + 必要時輔以 shell 命令。

## 觸發

```
/custom-skills-upstream-ops maintenance update-last-sync <source>
/custom-skills-upstream-ops maintenance archive-reports
/custom-skills-upstream-ops maintenance list-orphans
```

## 子命令

### update-last-sync <source>

用途：套用完上游同步後，把 `upstream/last-sync.yaml` 該來源的 commit 更新為當前 HEAD。

執行流程：
1. 讀 `upstream/sources.yaml` 確認 source 存在，取 `local_path`
2. `git -C <local_path> rev-parse HEAD` 取當前 HEAD
3. 讀 `upstream/last-sync.yaml` 取舊 commit，對比確認有差異
4. **人工確認**：顯示「舊：<old> → 新：<new>，確認更新？」
5. 確認後寫入：
   ```yaml
   <source>:
     commit: <new-head>
     synced_at: '<current ISO-8601>'
   ```

範例：
```
/custom-skills-upstream-ops maintenance update-last-sync universal-dev-standards
```

### archive-reports

用途：把 `upstream/reports/` 下過期（預設 > 90 天）的報告移到 `upstream/reports/archive/`。

執行流程：
1. 掃描 `upstream/reports/{structured,new-repos,analysis,uds-update,audit}/` 的所有檔案
2. 比對 mtime 與今日差距
3. 對 > 90 天的檔案列出清單
4. **人工確認**：顯示清單，「確認移動？」
5. 確認後建立 `upstream/reports/archive/YYYY-MM-DD/` 並 `git mv` 過去

範例：
```
/custom-skills-upstream-ops maintenance archive-reports
```

### list-orphans

用途：偵測 `sources.yaml` 與 `last-sync.yaml` 的不一致。

執行流程：
1. 讀兩個 YAML
2. 找出：
   - `last-sync.yaml` 有、`sources.yaml` 無 → orphan sync entry
   - `sources.yaml` 有、`last-sync.yaml` 無 → never synced
   - `sources.yaml` 的 `local_path` 不存在 → missing repo
3. 列出分類結果，給清理建議（不自動刪除）

範例：
```
/custom-skills-upstream-ops maintenance list-orphans
```

輸出範例：
```markdown
## Orphan Check

### last-sync 但 sources.yaml 無紀錄
（無）

### sources.yaml 有但從未同步
- auto-skill（建議：跑 `audit` 然後 `update-last-sync`）

### local_path 不存在
（無）
```

## 設計原則

- 所有子命令**都要人工確認**後才寫檔（避免意外覆寫）
- 寫檔時保留原有 YAML 格式與註解
- 失敗時不留半寫狀態
