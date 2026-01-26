# Upstream Tracking | 上游追蹤

追蹤所有第三方 repo 的同步狀態與變更分析。

## 目錄結構

```
upstream/
├── sources.yaml              # 上游 repo 註冊表
├── last-sync.yaml            # 最後同步狀態
├── reports/
│   ├── structured/
│   │   └── analysis-YYYY-MM-DD.yaml      # 已註冊 repo 分析報告
│   └── new-repos/
│       └── eval-{name}-{timestamp}.yaml  # 新 repo 評估報告
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

### reports/structured/

存放 `upstream-sync` 生成的已註冊 repo 分析報告（YAML 格式）。

### reports/new-repos/

存放 `upstream-sync --new-repo` 生成的新 repo 評估報告。

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
│  2. /upstream-sync                                           │
│     ├── 分析 commit 差異                                     │
│     └── 生成 reports/structured/analysis-*.yaml             │
│                        ↓                                     │
│  3. /upstream-compare                                        │
│     ├── AI 讀取結構化報告                                    │
│     └── 生成自然語言建議                                     │
│                        ↓                                     │
│  4. /openspec:proposal (可選)                                │
│     └── 建立整合提案                                         │
│                        ↓                                     │
│  5. --update-sync                                            │
│     └── 更新 last-sync.yaml                                  │
│                        ↓                                     │
│  6. ai-dev clone                                             │
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
│  2. /upstream-sync --new-repo ~/.config/<name>               │
│     ├── 全量分析 repo 內容                                   │
│     └── 生成 reports/new-repos/eval-*.yaml                  │
│                        ↓                                     │
│  3. /upstream-compare --new-repo <report>                    │
│     ├── AI 評估內容品質                                      │
│     └── 給出整合建議                                         │
│                        ↓                                     │
│  4. 決定是否整合                                             │
│     ├── 是 → 加入 sources.yaml + /openspec:proposal         │
│     └── 否 → 刪除本地 clone                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 常用指令

```bash
# 拉取上游最新內容
ai-dev update

# 分析已註冊上游變更
python skills/upstream-sync/scripts/analyze_upstream.py

# 分析特定 repo
python skills/upstream-sync/scripts/analyze_upstream.py --source superpowers

# 評估新的本地 repo
python skills/upstream-sync/scripts/analyze_upstream.py --new-repo ~/.config/awesome-skills

# 更新同步狀態
python skills/upstream-sync/scripts/analyze_upstream.py --update-sync

# AI 分析報告
/upstream-compare

# AI 評估新 repo
/upstream-compare --new-repo eval-awesome-skills-*.yaml

# 分發到工具目錄
ai-dev clone
```

## 相關 Skills

- `/upstream-sync` - 生成結構化分析報告（支援 --new-repo）
- `/upstream-compare` - AI 生成自然語言建議（支援 --new-repo）

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
