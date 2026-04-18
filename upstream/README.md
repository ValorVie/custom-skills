# Upstream Tracking | 上游追蹤

追蹤所有第三方 repo 的同步狀態與變更分析。

## 目錄結構

```
upstream/
├── sources.yaml              # 上游 repo 註冊表
├── last-sync.yaml            # 最後同步狀態
├── reports/
│   ├── audit/
│   │   └── audit-YYYY-MM-DD.md          # audit --archive 寫出的 Markdown 摘要
│   └── new-repos/
│       └── eval-{name}-{timestamp}.yaml # 舊版新 repo 評估報告（新架構改走 overlap）
└── README.md
```

## 檔案說明

### sources.yaml

定義所有上游來源：

| 欄位 | 說明 |
|------|------|
| `repo` | GitHub repo 路徑 (owner/repo) |
| `branch` | 追蹤的分支 |
| `local_path` | 本地 clone 位置 |
| `format` | 檔案格式 (`uds` 或 `claude-code-native`) |

### last-sync.yaml

記錄最後分析時的 commit：

```yaml
superpowers:
  commit: abc123def456
  synced_at: "2026-01-24T18:00:00"
```

### reports/audit/

存放 `/custom-skills-upstream-ops audit --archive` 寫出的 Markdown 摘要（`audit-YYYY-MM-DD.md`）。預設 audit 只輸出到對話，不寫檔；`--archive` 才會落地。

> 歷史備註：舊版 `custom-skills-upstream-sync` 會輸出 `reports/structured/analysis-*.yaml` 結構化報告，目前 audit mode 已不再產生 YAML。

### reports/new-repos/

存放舊版新 repo 評估報告（新架構改用 `overlap` mode，直接輸出到對話）。

## 使用流程

### 日常同步流程

```
┌─────────────────────────────────────────────────────────────┐
│                    UPSTREAM WORKFLOW                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. ai-dev update                                            │
│     └── 拉取所有上游 repo 到 ~/.config/                      │
│                        ↓                                     │
│  2. /custom-skills-upstream-ops audit                        │
│     ├── 分析 commit 差異                                     │
│     ├── 生成整合建議（AI workflow）                          │
│     └── 預設輸出 Markdown 到對話；--archive 時寫到           │
│         upstream/reports/audit/audit-YYYY-MM-DD.md           │
│                        ↓                                     │
│  3. /openspec:proposal (可選)                                │
│     └── 建立整合提案                                         │
│                        ↓                                     │
│  4. /custom-skills-upstream-ops maintenance \                │
│         update-last-sync <source>                            │
│     └── 更新 last-sync.yaml                                  │
│                        ↓                                     │
│  5. ai-dev clone                                             │
│     └── 分發內容到各工具目錄                                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 新 Repo 評估流程

```
┌─────────────────────────────────────────────────────────────┐
│                    NEW REPO EVALUATION                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. git clone <repo> ~/.config/<name>                        │
│     └── Clone 新 repo 到本地                                 │
│                        ↓                                     │
│  2. /custom-skills-upstream-ops overlap <name>               │
│     ├── 掃描目標 repo 結構（skills/agents/commands）         │
│     ├── 與本專案對應目錄比對，標註功能重疊                   │
│     └── 輸出 Markdown 摘要與可貼的 overlaps.yaml 片段        │
│                        ↓                                     │
│  3. 決定是否整合                                             │
│     ├── 是 → 加入 sources.yaml + /openspec:proposal          │
│     └── 否 → 刪除本地 clone                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 常用指令

```bash
# 拉取上游最新內容
ai-dev update

# 分析已註冊上游變更（預設 audit mode）
/custom-skills-upstream-ops

# 分析特定 repo
/custom-skills-upstream-ops audit --source superpowers

# 評估新的本地 repo（偵測與本專案的功能重疊）
/custom-skills-upstream-ops overlap ~/.config/awesome-skills

# 檢查 UDS .standards/ 檔案級漂移
/custom-skills-upstream-ops uds-check

# 任一 repo vs 本專案重疊偵測
/custom-skills-upstream-ops overlap <repo>

# 更新同步狀態（套用完成後使用）
/custom-skills-upstream-ops maintenance update-last-sync <source>

# 分發到工具目錄
ai-dev clone
```

## 相關 Skills

- `/custom-skills-upstream-ops` - 上游操作統一入口，支援 `audit`、`uds-check`、`overlap`、`maintenance` 四種 mode（compare 功能已併入 audit）

## 格式說明

| 格式 | 說明 | 來源 |
|------|------|------|
| `claude-code-native` | 純 Markdown | superpowers, obsidian-skills, anthropic-skills |
| `uds` | YAML frontmatter + Markdown | universal-dev-standards |

---

## 整合決定記錄

### 2026-01-26 整合

**來源報告：** `reports/analysis/compare-2026-01-26.md`

#### 已整合項目

| 來源 | 項目 | 類型 | 說明 |
|------|------|------|------|
| everything-claude-code | database-reviewer | Agent | PostgreSQL 專家，Supabase patterns |
| everything-claude-code | cloud-infrastructure-security | Skill | 雲端安全檢查清單 |

#### 暫不整合項目

| 來源 | 項目 | 原因 |
|------|------|------|
| everything-claude-code | orchestrate command | 現有 commands 已足夠 |
| everything-claude-code | setup-pm command | 現有 commands 已足夠 |
| superpowers | OpenCode support | 需求不明確 |
| superpowers | Codex support | 需求不明確 |

#### 新框架決定

| 框架 | 決定 | 說明 |
|------|------|------|
| Claude Plugin System | ✅ 維持 | 已有支援 |
| OpenCode Support | ⏸️ 暫緩 | 需求不明確，按需再評估 |
| Codex Support | ⏸️ 暫緩 | 需求不明確，按需再評估 |
| Hook System | 📖 參考 | 現有機制足夠 |
| MCP Integration | 📖 參考 | 按需整合 |
