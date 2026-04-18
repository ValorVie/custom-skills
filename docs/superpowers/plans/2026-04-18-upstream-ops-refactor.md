# Upstream Ops Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 4 個上游同步相關 skill 合併為單一 `custom-skills-upstream-ops`，以 modes 子目錄區分 audit / uds-check / overlap / maintenance 四種功能，僅保留 SHA-256 檔案比對的 Python 腳本。

**Architecture:** 純 markdown skill（除 `scripts/check_uds.py` 外）。SKILL.md 是入口，依使用者 argument 路由到 `modes/<name>.md`；`references/` 放跨 mode 共用的決策表與 reading guide。

**Tech Stack:** Markdown（skill + slash command）、Python 3.9+（僅 `check_uds.py`，PyYAML 已在專案 `.venv`）、bash（驗證命令）。

**Spec:** `docs/superpowers/specs/2026-04-18-upstream-ops-refactor-design.md`

---

## File Structure

### 新建

```
skills/custom-skills-upstream-ops/
├── SKILL.md
├── modes/
│   ├── audit.md
│   ├── uds-check.md
│   ├── overlap.md
│   └── maintenance.md
├── references/
│   ├── install-methods.md
│   └── decision-patterns.md
└── scripts/
    └── check_uds.py             # 從 custom-skills-uds-update/ 搬移

commands/claude/custom-skills-upstream-ops.md
commands/opencode/custom-skills-upstream-ops.md
```

### 修改

- `script/commands/add_repo.py`（第 246-258 行：移除 subprocess 呼叫、更新提示）
- `openspec/specs/upstream-skills/spec.md`（改名）
- `openspec/specs/overlap-detection/spec.md`（重寫觸發入口）
- `docs/AI開發環境設定指南.md`（第 1473-1476 行）
- `docs/dev-guide/workflow/copy-architecture.md`（第 60 行）
- `docs/ai-dev指令與資料流參考.md`（因 add_repo.py 改了）
- `CHANGELOG.md`

### 刪除

- `skills/custom-skills-upstream-sync/`（整個目錄，含 `analyze_upstream.py`、`sync_upstream.py`）
- `skills/custom-skills-upstream-compare/`（整個目錄）
- `skills/custom-skills-uds-update/`（整個目錄，`check_uds.py` 已先搬走）
- `commands/claude/custom-skills-upstream-sync.md`
- `commands/claude/custom-skills-upstream-compare.md`
- `commands/claude/uds-update.md`
- `commands/opencode/custom-skills-upstream-sync.md`（若存在）
- `commands/opencode/custom-skills-upstream-compare.md`（若存在）
- `commands/opencode/uds-update.md`

---

### Task 1: 建立 skill 骨架與目錄結構

**Files:**
- Create: `skills/custom-skills-upstream-ops/SKILL.md`
- Create: `skills/custom-skills-upstream-ops/modes/` (directory)
- Create: `skills/custom-skills-upstream-ops/references/` (directory)
- Create: `skills/custom-skills-upstream-ops/scripts/` (directory)

- [ ] **Step 1: 建立目錄結構**

```bash
mkdir -p skills/custom-skills-upstream-ops/modes
mkdir -p skills/custom-skills-upstream-ops/references
mkdir -p skills/custom-skills-upstream-ops/scripts
```

- [ ] **Step 2: 建立 SKILL.md 入口檔**

Write `skills/custom-skills-upstream-ops/SKILL.md`：

```markdown
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
```

- [ ] **Step 3: Commit**

```bash
git add skills/custom-skills-upstream-ops/SKILL.md
git commit -m "feat(upstream-ops): 建立 skill 骨架與入口 SKILL.md"
```

---

### Task 2: 寫 references/install-methods.md

**Files:**
- Create: `skills/custom-skills-upstream-ops/references/install-methods.md`

- [ ] **Step 1: 撰寫 install-methods.md 完整內容**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add skills/custom-skills-upstream-ops/references/install-methods.md
git commit -m "feat(upstream-ops): 新增 install-methods 同步方式對照表"
```

---

### Task 3: 寫 references/decision-patterns.md

**Files:**
- Create: `skills/custom-skills-upstream-ops/references/decision-patterns.md`

- [ ] **Step 1: 撰寫 decision-patterns.md 完整內容**

```markdown
# Decision Patterns | Audit 結果判讀規則

audit mode 產出的 commit 清單與 diff stat 如何判斷優先級與動作。取代舊 `custom-skills-upstream-compare` 的 reading guide。

## 優先級判斷

讀 commit subject 與 `git diff --stat` 輸出後，自行判斷優先級，不套死分數：

| 判斷依據 | 優先級 |
|---------|-------|
| 多個新 skill / 多個新 standards / 新框架支援 | **High**（建議近期整合） |
| 有價值的改進、文件更新、新配置模式 | **Medium**（評估後整合） |
| 小幅調整、維護性變更 | **Low**（選擇性） |
| 無變更或僅微調 | **Skip** |

判斷示例：
- 「add 6 standards」→ High
- 「fix typo in README」→ Skip
- 「refactor sources-schema」→ Medium（影響文件閱讀）
- 「chore(release): v5.1.0-beta.7」→ Low（通常是 bump）

## 變更分類

依檔案路徑歸類：

- `skills/` — skill 變更（直接影響 AI 行為）
- `agents/` 或 `.claude/agents/` — agent 變更
- `commands/` — slash command 變更
- `.standards/` 或 `ai/standards/` — 標準文件
- `hooks/` — hook 變更
- `*.md`（根目錄）— 文件
- `*.json` / `*.yaml`（配置）— 配置變更

優先序：**新框架 > skills > agents > commands > hooks > 配置 > docs**。

## install_method 對應動作

參考 `install-methods.md`。每個 audit 條目輸出的「同步」命令必須對應該來源的 install_method，不要建議錯誤方式（例：對 plugin 類型說要手動複製檔案）。

## 新架構偵測

若 commit 涉及：
- 新目錄（例如從未出現的 `prompts/`、`hooks/`、`.claude-plugin/`）
- 新檔案類型（`.codex`、`.gitattributes` 等）
- 新配置檔（`plugin.json`、`hooks.json`）

應在 audit 輸出中**特別標註**「新架構偵測」，即使整體 commit 量不高也可能是 High 優先級。

## 輸出語氣

- 每個上游一個段落，開頭一句「Xxx 落後 N commits」
- 主要變更摘要 **3 句內**（AI 讀 commit subject 後自行濃縮）
- 結尾給一條明確命令（one-liner）
- 不輸出 YAML、不輸出評分數字
```

- [ ] **Step 2: Commit**

```bash
git add skills/custom-skills-upstream-ops/references/decision-patterns.md
git commit -m "feat(upstream-ops): 新增 decision-patterns 判讀規則"
```

---

### Task 4: 寫 modes/audit.md

**Files:**
- Create: `skills/custom-skills-upstream-ops/modes/audit.md`

- [ ] **Step 1: 撰寫 audit.md 完整內容**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add skills/custom-skills-upstream-ops/modes/audit.md
git commit -m "feat(upstream-ops): 新增 audit mode（純 AI workflow）"
```

---

### Task 5: 搬移 check_uds.py 並寫 modes/uds-check.md

**Files:**
- Create: `skills/custom-skills-upstream-ops/scripts/check_uds.py`（從 `skills/custom-skills-uds-update/scripts/check_uds.py` 搬來）
- Create: `skills/custom-skills-upstream-ops/modes/uds-check.md`
- Modify: `skills/custom-skills-upstream-ops/scripts/check_uds.py`（更新 `PROJECT_ROOT` 的 parents 層級）

- [ ] **Step 1: 複製腳本到新位置**

```bash
cp skills/custom-skills-uds-update/scripts/check_uds.py \
   skills/custom-skills-upstream-ops/scripts/check_uds.py
```

- [ ] **Step 2: 修正 PROJECT_ROOT 推導**

舊路徑層級為 `skills/custom-skills-uds-update/scripts/check_uds.py`（`parents[3]` 到專案根）
新路徑層級為 `skills/custom-skills-upstream-ops/scripts/check_uds.py`（仍然 `parents[3]`）

**驗證**：層級相同，不需要改。

Run:
```bash
.venv/bin/python -c "
from pathlib import Path
p = Path('skills/custom-skills-upstream-ops/scripts/check_uds.py').resolve()
print('parents[3]:', p.parents[3])
"
```

Expected output: `parents[3]: <absolute-path-to-custom-skills>`

- [ ] **Step 3: 執行腳本驗證仍可運作**

Run:
```bash
.venv/bin/python skills/custom-skills-upstream-ops/scripts/check_uds.py 2>&1 | head -5
```

Expected:
```
UDS Update Check
generated_at: <current timestamp>

【Commit 狀態】
```

- [ ] **Step 4: 撰寫 modes/uds-check.md**

```markdown
# Mode: uds-check

UDS（universal-dev-standards）的 `.standards/` 與鏡像 `skills/<id>/` SHA-256 檔案級漂移檢測。

**唯一保留 Python 腳本的 mode**——檔案級比對是確定性機械勞動，腳本快且穩定。

## 觸發

```
/custom-skills-upstream-ops uds-check
/custom-skills-upstream-ops uds-check --verbose              # 列出所有漂移檔案
/custom-skills-upstream-ops uds-check --report               # 寫 YAML 報告到 upstream/reports/uds-update/
/custom-skills-upstream-ops uds-check --json                 # JSON 輸出
/custom-skills-upstream-ops uds-check --exit-nonzero-on-drift  # CI 用，有漂移 exit 1
```

## 執行

```bash
.venv/bin/python skills/custom-skills-upstream-ops/scripts/check_uds.py [options]
```

## Requirements

- Python 3.9+
- PyYAML（本專案 `.venv` 已安裝）

## 比對範圍

| 本地位置 | 上游來源 |
|---------|---------|
| `.standards/` | `~/.config/universal-dev-standards/ai/standards/` |
| `skills/<id>/`（僅同名目錄） | `~/.config/universal-dev-standards/skills/<id>/` |

## 輸出分類

對每個檔案以 SHA-256 比對，分三類：

- **modified**：雙邊都有但內容不同（最重要，代表上游已更新或本地已客製）
- **added_upstream**：上游新增、本地尚未安裝
- **only_local**：本地獨有（可能是本專案客製化，**勿直接覆寫**）

## 決策表

| 情況 | 動作 |
|------|------|
| 完全同步 | 無動作 |
| commit behind，檔案無漂移 | `ai-dev clone` 已同步過，用 `maintenance update-last-sync` 更新 `last-sync.yaml` |
| `.standards/` modified | 對每檔 `diff` 上游 vs 本地，人工決定合併；保留本地客製 |
| `skills/` drift | `ai-dev clone` 重新分發，或對個別 skill 手動 diff |
| upstream_only 有新 skill | 依需求評估是否加入本專案 |
| only_local 有檔案 | **勿覆寫**，這是本專案延伸 |

## 何時用這個 mode

- `audit` 看到 UDS 落後時，跟進跑 uds-check 取得檔案級細節
- 套用 `ai-dev clone` 後，確認是否還有殘留漂移
- 定期稽核本專案 `.standards/` 是否偏離上游太遠
```

- [ ] **Step 5: Commit**

```bash
git add skills/custom-skills-upstream-ops/scripts/check_uds.py \
        skills/custom-skills-upstream-ops/modes/uds-check.md
git commit -m "feat(upstream-ops): 搬移 check_uds.py 並新增 uds-check mode 文件"
```

---

### Task 6: 寫 modes/overlap.md

**Files:**
- Create: `skills/custom-skills-upstream-ops/modes/overlap.md`

- [ ] **Step 1: 撰寫 overlap.md 完整內容**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add skills/custom-skills-upstream-ops/modes/overlap.md
git commit -m "feat(upstream-ops): 新增 overlap mode（任一 repo vs 本專案重疊偵測）"
```

---

### Task 7: 寫 modes/maintenance.md

**Files:**
- Create: `skills/custom-skills-upstream-ops/modes/maintenance.md`

- [ ] **Step 1: 撰寫 maintenance.md 完整內容**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add skills/custom-skills-upstream-ops/modes/maintenance.md
git commit -m "feat(upstream-ops): 新增 maintenance mode（last-sync 更新／歸檔／孤兒偵測）"
```

---

### Task 8: 建立 slash commands（claude + opencode）

**Files:**
- Create: `commands/claude/custom-skills-upstream-ops.md`
- Create: `commands/opencode/custom-skills-upstream-ops.md`

- [ ] **Step 1: 撰寫 Claude slash command**

Write `commands/claude/custom-skills-upstream-ops.md`：

```markdown
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
```

- [ ] **Step 2: 撰寫 opencode slash command**

Write `commands/opencode/custom-skills-upstream-ops.md`：

```markdown
# Upstream Ops | 上游操作

Unified upstream repo operations.

## Usage

```
/custom-skills-upstream-ops [audit | uds-check | overlap <target> | maintenance <sub>] [--options]
```

Default: `audit`.

## Modes

- **audit** — commit drift + sync recommendations (AI workflow)
- **uds-check** — UDS file-level SHA-256 drift (Python script)
- **overlap** — any repo vs this project overlap detection
- **maintenance** — update-last-sync / archive-reports / list-orphans

See full docs: `skills/custom-skills-upstream-ops/SKILL.md`.
```

- [ ] **Step 3: Commit**

```bash
git add commands/claude/custom-skills-upstream-ops.md \
        commands/opencode/custom-skills-upstream-ops.md
git commit -m "feat(upstream-ops): 新增 /custom-skills-upstream-ops slash command"
```

---

### Task 9: 冒煙測試（Smoke Test）新 skill

**Files:**
- Test: `skills/custom-skills-upstream-ops/scripts/check_uds.py`

- [ ] **Step 1: 跑 uds-check mode 驗證腳本能跑**

```bash
.venv/bin/python skills/custom-skills-upstream-ops/scripts/check_uds.py 2>&1 | tail -20
```

Expected：輸出 commit 狀態、`.standards/` 漂移、skills/ 漂移、建議動作四個區塊，不崩潰。

- [ ] **Step 2: 跑 `--report` 驗證能寫檔**

```bash
.venv/bin/python skills/custom-skills-upstream-ops/scripts/check_uds.py --report 2>&1 | tail -3
ls upstream/reports/uds-update/
```

Expected：最後一行顯示「報告已寫入: upstream/reports/uds-update/uds-update-YYYY-MM-DD.yaml」；`ls` 顯示檔案存在。

- [ ] **Step 3: 驗證 exit code**

```bash
.venv/bin/python skills/custom-skills-upstream-ops/scripts/check_uds.py --exit-nonzero-on-drift > /dev/null 2>&1
echo "exit=$?"
```

Expected：`exit=1`（因當前確實有漂移）。若當前無漂移，預期 `exit=0`。

- [ ] **Step 4: 確認 SKILL.md 內容一致**

Run:
```bash
grep -c "modes/audit.md\|modes/uds-check.md\|modes/overlap.md\|modes/maintenance.md" \
     skills/custom-skills-upstream-ops/SKILL.md
```

Expected：`4`（四個 mode 文件都在 SKILL.md 提到）。

**無需 commit（只是驗證）**

---

### Task 10: 修改 script/commands/add_repo.py

**Files:**
- Modify: `script/commands/add_repo.py:243-260`

- [ ] **Step 1: 讀當前內容**

```bash
sed -n '240,265p' script/commands/add_repo.py
```

預期看到：
- 第 246 行：`python skills/custom-skills-upstream-sync/scripts/analyze_upstream.py --new-repo ...`
- 第 247 行：`/upstream-compare --new-repo`
- 第 254 行：`script_path = sources_path.parent.parent / "skills" / "custom-skills-upstream-sync" / "scripts" / "analyze_upstream.py"`
- 第 256-259 行：`subprocess.run(["python", str(script_path), ...], check=False)`

- [ ] **Step 2: 以 Edit 工具替換**

替換 `console.print` 提示區塊（約 243-247 行）：

舊：
```python
    console.print()
    console.print("[bold green]✓ 完成！[/bold green]")
    console.print()
    console.print("[dim]下一步：[/dim]")
    console.print(f"[dim]  1. 分析 repo: python skills/custom-skills-upstream-sync/scripts/analyze_upstream.py --new-repo {target_dir}[/dim]")
    console.print(f"[dim]  2. AI 評估: /upstream-compare --new-repo[/dim]")
```

新：
```python
    console.print()
    console.print("[bold green]✓ 完成！[/bold green]")
    console.print()
    console.print("[dim]下一步：[/dim]")
    console.print(f"[dim]  1. 重疊偵測: /custom-skills-upstream-ops overlap {name}[/dim]")
    console.print(f"[dim]  2. commit 稽核: /custom-skills-upstream-ops audit --source {name}[/dim]")
```

替換 `--analyze` flag 實作區塊（約 249-260 行）：

舊：
```python
    # 可選：執行分析
    if analyze and target_dir.exists():
        console.print()
        console.print("[cyan]正在執行分析...[/cyan]")
        # 找到分析腳本
        script_path = sources_path.parent.parent / "skills" / "custom-skills-upstream-sync" / "scripts" / "analyze_upstream.py"
        if script_path.exists():
            subprocess.run(
                ["python", str(script_path), "--new-repo", str(target_dir)],
                check=False,
            )
```

新：
```python
    # 可選：分析提示（原 subprocess 呼叫 analyze_upstream.py 已移除）
    if analyze and target_dir.exists():
        console.print()
        console.print("[cyan]提示：分析請透過 AI workflow 執行：[/cyan]")
        console.print(f"[cyan]  /custom-skills-upstream-ops overlap {name}[/cyan]")
        console.print(f"[cyan]  /custom-skills-upstream-ops audit --source {name}[/cyan]")
```

- [ ] **Step 3: 確認 subprocess import 若不再使用可移除**

```bash
grep -n "^import subprocess\|^from subprocess" script/commands/add_repo.py
grep -n "subprocess\." script/commands/add_repo.py
```

- 若第二個命令沒輸出（不再用 subprocess），從第一個 import 移除 `subprocess`
- 若仍有其他 subprocess 呼叫（例如 `clone_repo` 內部），保留 import

- [ ] **Step 4: 更新 docstring**

替換 docstring 中的「3. [可選] 執行 custom-skills-upstream-sync 分析」：

舊：
```python
    """新增上游 repo 並開始追蹤。

    此指令會：
    1. Clone repo 到 ~/.config/<repo-name>/
    2. 將 repo 資訊加入 upstream/sources.yaml
    3. [可選] 執行 custom-skills-upstream-sync 分析
    ...
    """
```

新：
```python
    """新增上游 repo 並開始追蹤。

    此指令會：
    1. Clone repo 到 ~/.config/<repo-name>/
    2. 將 repo 資訊加入 upstream/sources.yaml
    3. [可選] 提示用 /custom-skills-upstream-ops 進行 overlap/audit
    ...
    """
```

- [ ] **Step 5: 語法驗證**

```bash
.venv/bin/python -c "import ast; ast.parse(open('script/commands/add_repo.py').read()); print('OK')"
```

Expected：`OK`

- [ ] **Step 6: Commit**

```bash
git add script/commands/add_repo.py
git commit -m "refactor(ai-dev): add_repo 改由 /custom-skills-upstream-ops 提供分析能力"
```

---

### Task 11: 更新 openspec/specs/upstream-skills/spec.md

**Files:**
- Modify: `openspec/specs/upstream-skills/spec.md`（僅改提到 upstream-sync/compare 的句子）

- [ ] **Step 1: 找出所有提到舊 skill 名稱的行**

```bash
grep -n "upstream-sync\|upstream-compare" openspec/specs/upstream-skills/spec.md
```

- [ ] **Step 2: 逐行替換**

以 Edit 工具，對每個命中的行：
- `upstream-sync` → `custom-skills-upstream-ops audit`
- `upstream-compare` → `custom-skills-upstream-ops audit`（compare 功能已併入 audit）
- 若句子提到「追蹤該來源的 commit 差異」：改成「`custom-skills-upstream-ops audit` SHALL 正常追蹤該來源的 commit 差異」

範例：
舊：`- **THEN** upstream-sync 和 upstream-compare 仍 SHALL 正常追蹤該來源的 commit 差異`
新：`- **THEN** /custom-skills-upstream-ops audit 仍 SHALL 正常追蹤該來源的 commit 差異`

- [ ] **Step 3: 驗證替換完成**

```bash
grep -n "upstream-sync\|upstream-compare" openspec/specs/upstream-skills/spec.md
```

Expected：無輸出（所有出現都已替換）。

- [ ] **Step 4: Commit**

```bash
git add openspec/specs/upstream-skills/spec.md
git commit -m "docs(spec): upstream-skills spec 替換為 upstream-ops 命名"
```

---

### Task 12: 重寫 openspec/specs/overlap-detection/spec.md

**Files:**
- Modify: `openspec/specs/overlap-detection/spec.md`（整份重寫）

- [ ] **Step 1: 讀當前內容以保留 Requirement 骨架**

```bash
cat openspec/specs/overlap-detection/spec.md
```

- [ ] **Step 2: 以 Write 工具整份覆寫**

```markdown
# overlap-detection Specification

## Purpose

定義功能重疊偵測機制，用於識別任一 repo（上游或新候選）與本專案之間的功能重疊，並輔助 Profile 切換決策。

重疊偵測由 `/custom-skills-upstream-ops overlap <target>` mode 提供（原 `/upstream-compare --new-repo` 與 `--generate-overlaps` 能力合併於此）。

## Requirements

### Requirement: 重疊偵測功能

系統 SHALL 提供功能重疊偵測能力，識別目標 repo 與本專案之間的功能重疊。

#### Scenario: 對已註冊來源偵測

- **GIVEN** 使用者執行 `/custom-skills-upstream-ops overlap <source-name>`
- **WHEN** target 存在於 `upstream/sources.yaml`
- **THEN** 讀取該來源的 `local_path`
- **AND** 比較 target 的 skills/commands/agents 與本專案對應目錄
- **AND** 輸出重疊清單（exact match / similar names / functional overlap）

#### Scenario: 對任意本地目錄偵測

- **GIVEN** 使用者執行 `/custom-skills-upstream-ops overlap <local-path>`
- **WHEN** 指定路徑是有效的本地目錄（不必為 git repo）
- **THEN** 掃描該目錄的 skills/commands/agents
- **AND** 比較本專案對應目錄
- **AND** 輸出重疊清單

#### Scenario: 重疊判斷依據

- **GIVEN** 比較兩個項目
- **WHEN** AI 判斷是否重疊
- **THEN** 考慮名稱完全相同（exact match）
- **AND** 考慮名稱相似（Levenshtein distance < 3 或縮寫／同義詞）
- **AND** 考慮功能關鍵字匹配（tdd、test、commit、review 等領域詞）
- **AND** 考慮 frontmatter description 與前 20 行的語意相似
- **AND** 不使用硬性數值門檻（由 AI 當下判斷）

### Requirement: overlaps.yaml 片段建議

系統 SHALL 在偵測到重疊時輸出可複製到 `.standards/profiles/overlaps.yaml` 的 YAML 片段。

#### Scenario: 對話輸出片段

- **GIVEN** overlap mode 偵測到重疊
- **WHEN** 產出報告
- **THEN** 報告內含「建議 overlaps.yaml 片段」章節
- **AND** 片段符合 `overlaps.yaml` 現有 groups/mutual_exclusive 結構
- **AND** 片段標註「需人工審閱後再貼上」
- **AND** **不自動寫檔**——不建立 `overlaps.yaml.draft`，不修改 `overlaps.yaml`

#### Scenario: 無重疊時不生成片段

- **GIVEN** overlap mode 分析結果無重疊
- **WHEN** 產出報告
- **THEN** 報告僅列「全新項目」清單
- **AND** 不輸出 YAML 片段

### Requirement: 重疊分析報告

系統 SHALL 在 overlap mode 輸出結構化的 Markdown 報告。

#### Scenario: 報告包含重疊分類

- **GIVEN** 偵測完成
- **WHEN** 輸出報告
- **THEN** 包含「重疊清單」章節，分為 Exact Match / Similar Names / Functional Overlap 三類
- **AND** 每個重疊項包含本地 ↔ 目標對應項目與類型

#### Scenario: 報告包含全新項目

- **GIVEN** 目標 repo 有本專案無的項目
- **WHEN** 輸出報告
- **THEN** 列在「全新項目」章節
- **AND** 建議直接整合／評估後整合／跳過

#### Scenario: 報告包含下一步

- **GIVEN** 分析完成
- **WHEN** 輸出報告
- **THEN** 包含「下一步」章節
- **AND** 建議可能動作：整合（audit mode）、排除（distribution.yaml）、Profile 管理（overlaps.yaml）

### Requirement: 重疊驗證

系統 SHALL 驗證 `.standards/profiles/overlaps.yaml` 的正確性。

> 此 Requirement 不屬於 overlap mode 的責任，由 `ai-dev standards validate-overlaps` 指令處理，維持原有實作。此處僅保留 Requirement 供交叉引用。

#### Scenario: 項目存在性驗證

- **GIVEN** `overlaps.yaml` 定義了項目
- **WHEN** 執行 `ai-dev standards validate-overlaps`
- **THEN** 檢查所有列出的 skills 是否存在
- **AND** 檢查所有列出的 standards 是否存在
- **AND** 報告不存在的項目
```

- [ ] **Step 3: 驗證不再引用舊命令**

```bash
grep -n "upstream-sync\|upstream-compare\|generate-overlaps\|--new-repo" openspec/specs/overlap-detection/spec.md
```

Expected：無輸出。

- [ ] **Step 4: Commit**

```bash
git add openspec/specs/overlap-detection/spec.md
git commit -m "docs(spec): overlap-detection 重寫為 upstream-ops overlap mode 行為"
```

---

### Task 13: 更新文件（AI開發環境設定指南 / copy-architecture / ai-dev指令與資料流參考）

**Files:**
- Modify: `docs/AI開發環境設定指南.md:1473-1476`
- Modify: `docs/dev-guide/workflow/copy-architecture.md:60`
- Modify: `docs/ai-dev指令與資料流參考.md`（因 add_repo.py 改了）

- [ ] **Step 1: 更新 AI開發環境設定指南.md**

讀取第 1470-1480 行：

```bash
sed -n '1470,1480p' docs/AI開發環境設定指南.md
```

以 Edit 替換：

舊：
```markdown
# 使用 Skills 進行上游審核
/custom-skills-upstream-sync      # 生成結構化分析報告
/upstream-compare   # AI 生成整合建議
```

新：
```markdown
# 使用 Skills 進行上游審核
/custom-skills-upstream-ops              # 預設 audit mode：commit 差異 + 同步建議
/custom-skills-upstream-ops uds-check    # UDS .standards/ 檔案級漂移
/custom-skills-upstream-ops overlap <repo>  # 任一 repo vs 本專案重疊偵測
```

- [ ] **Step 2: 更新 copy-architecture.md**

讀取第 55-65 行：

```bash
sed -n '55,65p' docs/dev-guide/workflow/copy-architecture.md
```

以 Edit 替換：

舊：
```markdown
使用 `/custom-skills-upstream-sync` skill 進行上游同步分析與審核。
```

新：
```markdown
使用 `/custom-skills-upstream-ops` skill 進行上游同步分析與審核（預設 audit mode）。
```

- [ ] **Step 3: 更新 ai-dev指令與資料流參考.md**

```bash
grep -n "upstream-sync\|upstream-compare\|analyze_upstream\|add-repo" docs/ai-dev指令與資料流參考.md
```

對每個命中：
- `upstream-sync` / `upstream-compare` → `custom-skills-upstream-ops`
- `analyze_upstream.py` 相關說明：改為「由 AI workflow 處理，不再呼叫 Python 腳本」
- `ai-dev add-repo --analyze` 段落：更新行為描述為「僅輸出建議命令（`/custom-skills-upstream-ops overlap/audit`），不再 subprocess 呼叫」

- [ ] **Step 4: 驗證三份文件**

```bash
grep -n "upstream-sync\|upstream-compare" docs/AI開發環境設定指南.md docs/dev-guide/workflow/copy-architecture.md docs/ai-dev指令與資料流參考.md
```

Expected：只剩「歷史說明、已棄用」之類的脈絡說明，不再有活躍引用。

- [ ] **Step 5: Commit**

```bash
git add docs/AI開發環境設定指南.md \
        docs/dev-guide/workflow/copy-architecture.md \
        docs/ai-dev指令與資料流參考.md
git commit -m "docs: 更新 upstream 工作流引用為 /custom-skills-upstream-ops"
```

---

### Task 14: 刪除舊 skill 目錄

**Files:**
- Delete: `skills/custom-skills-upstream-sync/`
- Delete: `skills/custom-skills-upstream-compare/`
- Delete: `skills/custom-skills-uds-update/`

- [ ] **Step 1: 最後確認 check_uds.py 已正確搬移**

```bash
diff skills/custom-skills-uds-update/scripts/check_uds.py \
     skills/custom-skills-upstream-ops/scripts/check_uds.py
```

Expected：無差異（檔案完全相同）。

- [ ] **Step 2: 刪除三個舊 skill 目錄**

```bash
git rm -r skills/custom-skills-upstream-sync/
git rm -r skills/custom-skills-upstream-compare/
git rm -r skills/custom-skills-uds-update/
```

- [ ] **Step 3: 驗證目錄已移除**

```bash
ls skills/ | grep -E "custom-skills-(upstream-sync|upstream-compare|uds-update)"
```

Expected：無輸出。

- [ ] **Step 4: Commit**

```bash
git commit -m "chore(skills): 刪除 custom-skills-upstream-sync/compare/uds-update（已併入 upstream-ops）"
```

---

### Task 15: 刪除舊 slash commands

**Files:**
- Delete: `commands/claude/custom-skills-upstream-sync.md`
- Delete: `commands/claude/custom-skills-upstream-compare.md`
- Delete: `commands/claude/uds-update.md`
- Delete: `commands/opencode/custom-skills-upstream-sync.md`（若存在）
- Delete: `commands/opencode/custom-skills-upstream-compare.md`（若存在）
- Delete: `commands/opencode/uds-update.md`

- [ ] **Step 1: 確認檔案存在**

```bash
ls commands/claude/custom-skills-upstream-sync.md \
   commands/claude/custom-skills-upstream-compare.md \
   commands/claude/uds-update.md 2>&1
ls commands/opencode/custom-skills-upstream-sync.md \
   commands/opencode/custom-skills-upstream-compare.md \
   commands/opencode/uds-update.md 2>&1
```

記下實際存在的檔案。

- [ ] **Step 2: 刪除存在的檔案**

對每個確實存在的檔案：

```bash
git rm commands/claude/custom-skills-upstream-sync.md
git rm commands/claude/custom-skills-upstream-compare.md  # 若存在
git rm commands/claude/uds-update.md
git rm commands/opencode/custom-skills-upstream-sync.md  # 若存在
git rm commands/opencode/custom-skills-upstream-compare.md  # 若存在
git rm commands/opencode/uds-update.md  # 若存在
```

- [ ] **Step 3: 檢查是否有 README 索引檔需更新**

```bash
grep -l "custom-skills-upstream-sync\|custom-skills-upstream-compare\|uds-update" \
     commands/claude/README.md commands/opencode/README.md 2>/dev/null
```

若命中任一 README，讀取並以 Edit 替換為 `custom-skills-upstream-ops`（或移除 entry）。

- [ ] **Step 4: Commit**

```bash
git add -u commands/
git commit -m "chore(commands): 刪除舊 upstream-sync/compare/uds-update slash commands"
```

---

### Task 16: 最終交叉引用掃描

**Files:**
- Verify across project

- [ ] **Step 1: 全專案 grep 舊名稱**

```bash
git grep -E "analyze_upstream|sync_upstream|upstream-compare|upstream-sync|custom-skills-uds-update" \
  -- . \
  ':!openspec/changes/archive' \
  ':!upstream/reports' \
  ':!CHANGELOG.md' \
  ':!docs/report' \
  ':!docs/superpowers/specs' \
  ':!docs/superpowers/plans'
```

Expected：無輸出（或僅剩歷史背景說明類）。**若仍有活躍引用**，修補該檔案再回此 Task。

- [ ] **Step 2: 驗證新 skill 完整性**

```bash
ls -la skills/custom-skills-upstream-ops/
ls skills/custom-skills-upstream-ops/modes/
ls skills/custom-skills-upstream-ops/references/
ls skills/custom-skills-upstream-ops/scripts/
```

Expected：
- 根目錄：`SKILL.md` + 3 個子目錄
- `modes/`：`audit.md`、`uds-check.md`、`overlap.md`、`maintenance.md`
- `references/`：`install-methods.md`、`decision-patterns.md`
- `scripts/`：`check_uds.py`

- [ ] **Step 3: 再跑一次 check_uds.py 確保搬家後可運作**

```bash
.venv/bin/python skills/custom-skills-upstream-ops/scripts/check_uds.py 2>&1 | tail -5
```

Expected：看到建議動作區塊，無錯誤。

- [ ] **Step 4: ai-dev add-repo 語法檢查**

```bash
.venv/bin/python -c "
import ast
ast.parse(open('script/commands/add_repo.py').read())
print('add_repo.py syntax OK')
"
```

Expected：`add_repo.py syntax OK`

**無需 commit（僅驗證）**

---

### Task 17: 更新 CHANGELOG.md

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: 讀目前 CHANGELOG 最上面的 Unreleased 區塊**

```bash
sed -n '1,40p' CHANGELOG.md
```

- [ ] **Step 2: 在 `## [Unreleased]` 下新增條目**

以 Edit 工具在 `## [Unreleased]` 下方加入（若已有 `### Changed`/`### Removed` 等分類則接入對應分類；若沒有則新建）：

```markdown
### Changed

- **refactor(skills)**: 合併 `custom-skills-upstream-sync`、`custom-skills-upstream-compare`、`custom-skills-uds-update` 為單一 `custom-skills-upstream-ops`，以 `modes/` 子目錄區分 audit / uds-check / overlap / maintenance 四種功能。僅保留 SHA-256 檔案比對的 Python 腳本（`scripts/check_uds.py`），其餘轉為純 AI workflow。
- **refactor(ai-dev)**: `ai-dev add-repo --analyze` 不再 subprocess 呼叫 `analyze_upstream.py`，改為提示 `/custom-skills-upstream-ops overlap/audit`。

### Removed

- `skills/custom-skills-upstream-sync/`（含 1284 行 `analyze_upstream.py`、`sync_upstream.py`）
- `skills/custom-skills-upstream-compare/`
- `skills/custom-skills-uds-update/`（`check_uds.py` 已搬至 `custom-skills-upstream-ops/scripts/`）
- `commands/{claude,opencode}/custom-skills-upstream-sync.md`
- `commands/{claude,opencode}/custom-skills-upstream-compare.md`
- `commands/{claude,opencode}/uds-update.md`

### Added

- `skills/custom-skills-upstream-ops/` — 統一上游操作入口
- `commands/{claude,opencode}/custom-skills-upstream-ops.md`
```

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): 記錄 upstream-ops 重構"
```

---

## Self-Review Notes

（由 writing-plans skill 自行 review 後的備註，執行前可忽略）

- 所有 17 個 Task 對應 spec 的遷移步驟 1-10 + 驗收標準 1-7。
- uds-check mode 透過 `check_uds.py` 沿用原 uds-update 行為（對應驗收 7）。
- `status-upstream-sync` spec 未動（spec out-of-scope 標註）。
- overlap mode 明確不寫檔，`overlaps.yaml` 保留由人工維護（對應驗收 6）。
- `script/commands/add_repo.py` 改為提示不跑（對應驗收 3）。
- Task 16 的 `git grep` 對應驗收 4。

---

## 執行選項

計畫已寫好並 commit 後，兩種執行方式：

**1. Subagent-Driven（推薦）** — 每個 task 派新 subagent，逐 task review，迭代快
**2. Inline Execution** — 在當前對話逐 task 跑，with checkpoint

選哪個？
