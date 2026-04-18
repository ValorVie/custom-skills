# Mode: overlap

任一 repo vs 本專案的功能重疊偵測。純 AI workflow。

取代舊 `custom-skills-upstream-compare --generate-overlaps` 與 `--new-repo` 的重疊偵測能力。

## 觸發

```
/custom-skills-upstream-ops overlap <source-name>         # 已註冊來源（讀 sources.yaml 取路徑）
/custom-skills-upstream-ops overlap <path-to-local-dir>   # 任意本地 repo 目錄
```

範例：
```
/custom-skills-upstream-ops overlap everything-claude-code
/custom-skills-upstream-ops overlap ~/.config/some-new-repo
```

## 執行流程

1. **解析目標**
   - 若是來源名稱：讀 `upstream/sources.yaml` 取 `local_path`
   - 若是路徑：直接使用
   - 驗證路徑存在且為 git repo

2. **掃描目標 repo 結構**：
   - `skills/` 下的目錄
   - `agents/` 下的檔案
   - `commands/` 下的檔案
   - 其他特殊目錄（`hooks/`、`prompts/` 等）

3. **讀本專案對應目錄**：
   - `skills/`、`agents/claude/`、`commands/claude/` 等

4. **對每個類型（skills、agents、commands）分別判斷重疊**：
   - **名稱完全相同**：exact match
   - **名稱相似**（Levenshtein distance < 3 或明顯縮寫／同義詞）：similar
   - **功能關鍵字匹配**：讀 frontmatter description 與前 20 行，比對關鍵字（tdd/test/commit/review 等）：functional

5. **對每個重疊組別**：
   - 列出本地 ↔ 目標對應項目
   - 標註重疊類型
   - 給整合建議

6. **輸出 Markdown 摘要到對話**，含可複製的 YAML 片段（對話內，不寫檔）

## 輸出格式

```markdown
## Overlap Analysis: <target-name>

**Target**: <repo-path-or-source-name>
**Scanned**: X skills, Y agents, Z commands

### 重疊清單

#### Exact Match（名稱相同）
| 本地 | 目標 | 類型 | 建議 |
|------|------|------|------|
| `testing-guide` | `testing-guide` | skills | 比較內容決定版本 |

#### Similar Names（名稱相近）
| 本地 | 目標 | 相似度原因 | 建議 |
|------|------|-----------|------|
| `custom-skills-git-commit` | `commit-assistant` | commit 相關 | 評估功能是否等價 |

#### Functional Overlap（功能重疊）
| 本地 | 目標 | 關鍵字 | 建議 |
|------|------|-------|------|
| `testing-guide` | `tdd-runner` | tdd, test | 補充互補，考慮同 profile 只留一個 |

### 全新項目（目標有、本地無）

1. `<new-skill-1>` — <功能說明> — 建議：可直接整合／評估後整合／跳過
2. ...

### 建議 overlaps.yaml 片段

> 若決定在 Profile 切換時管理這些重疊，可把下列片段加入 `.standards/profiles/overlaps.yaml`。**只是建議，請人工審閱後再貼上。**

```yaml
groups:
  testing-related:
    description: "測試相關（本地 testing-guide ↔ 目標 tdd-runner）"
    mutual_exclusive: true
    local:
      skills:
        - testing-guide
    <target-profile-name>:
      skills:
        - tdd-runner
```

### 下一步

- 若決定整合：用 `audit` mode 取得 commit 差異、實際同步
- 若決定排除：加入 `upstream/distribution.yaml` 的 `exclude` 列表（ECC-style）
- 若為 Profile 管理：貼上上述 YAML 片段到 `.standards/profiles/overlaps.yaml`
```

## 明確不做

- ❌ 不自動寫 `overlaps.yaml.draft` 到檔案（YAML 片段只輸出到對話）
- ❌ 不計算數值相似度分數（權重 40/30/30 那套）
- ❌ 不呼叫 Python 腳本

## 與 tool-overlap-analyzer 的差別

- **overlap**（本 mode）：**外部 repo** vs 本專案
- **tool-overlap-analyzer**：**本專案內部**工具之間的重疊（例如兩個 skill 功能相近）
- 兩者職責不同，不要混用
