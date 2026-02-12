---
title: Git Pull 部署指南
type: guide
date: 2026-02-12
author: arlen
status: draft
---

# Git Pull 部署指南

## 概述

這份指南說明如何在使用 `git pull` 部署的專案中，妥善處理 AI 開發工具檔案（`.standards/`、`.claude/`、`CLAUDE.md`、`docs/` 等），讓**開發環境完整、正式環境乾淨**。

適用對象：使用 `git pull` 作為部署方式的團隊。

---

## 核心策略

```
開發端                                    伺服器端
┌──────────────────────┐                 ┌──────────────────────┐
│ 完整 repo            │    git push     │ git pull             │
│ ├── .standards/      │ ──────────────► │ ├── (不出現)          │
│ ├── .claude/         │                 │ ├── (不出現)          │
│ ├── CLAUDE.md        │                 │ ├── (不出現)          │
│ ├── docs/            │                 │ ├── (不出現)          │
│ ├── index.php    ✓   │                 │ ├── index.php    ✓   │
│ └── system/      ✓   │                 │ └── system/      ✓   │
└──────────────────────┘                 └──────────────────────┘
        全部進 git                         Sparse Checkout 過濾
```

**原則**：版控追蹤所有開發相關檔案，checkout 層按環境決定要哪些檔案。

---

## 前置條件

- Git 1.7+（舊式 sparse checkout）或 Git 2.25+（新式 `git sparse-checkout` 子命令）
- 伺服器已有 `git clone` 的 repo

驗證 Git 版本：

```bash
git --version
# 2.25+ → 使用「快速開始」
# 1.7 ~ 2.24 → 使用「舊版 Git 替代方案」
```

---

## 快速開始

在伺服器上執行三行指令，即可讓 `git pull` 自動排除 AI 開發檔案：

```bash
git sparse-checkout init
git sparse-checkout set --no-cone '/*' '!/.standards' '!/.claude' '!/CLAUDE.md' '!/docs'
git checkout
```

之後 `git pull` 流程完全不變，排除的檔案不會出現在伺服器磁碟上。

---

## 完整流程

### 步驟 1: 在伺服器啟用 Sparse Checkout

```bash
# SSH 到伺服器
ssh user@server

# 進入專案目錄
cd /var/www/your-project

# 啟用 sparse-checkout
git sparse-checkout init
```

> **說明**: `sparse-checkout init` 會在 `.git/info/sparse-checkout` 建立設定檔，不影響 repo 內容。

### 步驟 2: 設定排除規則

```bash
git sparse-checkout set --no-cone \
  '/*' \
  '!/.standards' \
  '!/.claude' \
  '!/CLAUDE.md' \
  '!/.cursorrules' \
  '!/docs'
```

**規則說明**：

| 規則 | 意義 |
|------|------|
| `/*` | 預設包含所有檔案 |
| `!/.standards` | 排除 `.standards/` 目錄 |
| `!/.claude` | 排除 `.claude/` 目錄 |
| `!/CLAUDE.md` | 排除根目錄的 CLAUDE.md |
| `!/.cursorrules` | 排除 Cursor 設定檔 |
| `!/docs` | 排除 `docs/` 文件目錄 |

> **提示**: 根據專案實際情況調整排除清單。只排除「純開發工具」的檔案，不要排除應用程式需要的檔案。

### 步驟 3: 套用設定

```bash
# 套用 sparse-checkout 規則，排除的檔案會從工作目錄移除
git checkout
```

### 步驟 4: 驗證結果

```bash
# 確認排除的檔案不存在
ls -la .standards/   # 應顯示 No such file or directory
ls -la CLAUDE.md     # 應顯示 No such file or directory

# 確認應用程式檔案正常
ls index.php         # 應存在
ls system/           # 應存在

# 查看目前的 sparse-checkout 設定
git sparse-checkout list
```

### 步驟 5: 日常部署（不需改變）

```bash
# 跟以前完全一樣
git pull origin main
```

排除的檔案會自動被過濾，不需要任何額外操作。

---

## 舊版 Git 替代方案（Git 1.7 ~ 2.24）

適用於無法升級 Git 的環境（如 Debian 9 的 Git 2.11）。使用 `core.sparseCheckout` 設定達成相同效果。

### 快速開始（舊式）

```bash
# 啟用 sparse checkout
git config core.sparseCheckout true

# 寫入排除規則
cat > .git/info/sparse-checkout << 'EOF'
/*
!/.standards
!/.claude
!/CLAUDE.md
!/.cursorrules
!/docs
EOF

# 套用規則
git read-tree -mu HEAD
```

之後 `git pull` 流程完全不變，排除的檔案不會出現在工作目錄中。

### 完整流程（舊式）

#### 步驟 1: 啟用 Sparse Checkout

```bash
ssh user@server
cd /var/www/your-project

git config core.sparseCheckout true
```

#### 步驟 2: 編輯排除規則

```bash
cat > .git/info/sparse-checkout << 'EOF'
/*
!/.standards
!/.claude
!/CLAUDE.md
!/.cursorrules
!/docs
EOF
```

**規則語法**：每行一條規則，與新式 `git sparse-checkout set --no-cone` 的 pattern 相同。`!` 開頭表示排除。

#### 步驟 3: 套用設定

```bash
git read-tree -mu HEAD
```

> **說明**: `git read-tree -mu HEAD` 會根據 sparse-checkout 規則重新建立工作目錄，排除的檔案會被移除。

#### 步驟 4: 驗證結果

```bash
# 確認排除的檔案不存在
ls -la .standards/   # 應顯示 No such file or directory
ls -la CLAUDE.md     # 應顯示 No such file or directory

# 確認應用程式檔案正常
ls index.php         # 應存在

# 查看目前的規則
cat .git/info/sparse-checkout
```

#### 步驟 5: 日常部署（不需改變）

```bash
git pull origin main
```

#### 新增排除項目（舊式）

直接編輯 `.git/info/sparse-checkout` 檔案，加入新規則後重新套用：

```bash
echo '!/.aider' >> .git/info/sparse-checkout
git read-tree -mu HEAD
```

#### 臨時查看被排除的檔案（舊式）

```bash
# 方法 1: 用 git show 查看，不改變工作目錄
git show HEAD:CLAUDE.md
git show HEAD:.standards/commit-message.ai.yaml

# 方法 2: 臨時停用 sparse checkout
git config core.sparseCheckout false
git read-tree -mu HEAD
# ... 查看完畢 ...
git config core.sparseCheckout true
git read-tree -mu HEAD
```

#### 多台伺服器統一設定（舊式）

```bash
#!/bin/bash
# deploy-init-legacy.sh — Git < 2.25 伺服器執行一次

set -e

git config core.sparseCheckout true

cat > .git/info/sparse-checkout << 'EOF'
/*
!/.standards
!/.claude
!/CLAUDE.md
!/.cursorrules
!/docs
EOF

git read-tree -mu HEAD

echo "Sparse checkout configured (legacy mode). Excluded:"
echo "  .standards/, .claude/, CLAUDE.md, .cursorrules, docs/"
```

---

## 進階用法

### 情境 A: 新增排除項目

專案引入了新的 AI 工具（例如 `.aider/`），需要追加排除：

```bash
# 查看目前規則
git sparse-checkout list

# 重新設定（必須包含所有規則）
git sparse-checkout set --no-cone \
  '/*' \
  '!/.standards' \
  '!/.claude' \
  '!/CLAUDE.md' \
  '!/.cursorrules' \
  '!/.aider' \
  '!/docs'
```

### 情境 B: 臨時需要查看被排除的檔案

在伺服器上需要檢查某個被排除的文件：

```bash
# 方法 1: 用 git show 查看，不改變工作目錄
git show HEAD:CLAUDE.md
git show HEAD:.standards/commit-message.ai.yaml

# 方法 2: 臨時停用 sparse-checkout
git sparse-checkout disable    # 所有檔案出現
# ... 查看完畢 ...
git sparse-checkout reapply    # 重新套用規則
```

### 情境 C: 多台伺服器統一設定

建立部署腳本確保每台伺服器設定一致：

```bash
#!/bin/bash
# deploy-init.sh — 在新伺服器上執行一次

set -e

EXCLUDE_PATTERNS=(
  '/*'
  '!/.standards'
  '!/.claude'
  '!/CLAUDE.md'
  '!/.cursorrules'
  '!/docs'
)

git sparse-checkout init
git sparse-checkout set --no-cone "${EXCLUDE_PATTERNS[@]}"
git checkout

echo "Sparse checkout configured. Excluded:"
echo "  .standards/, .claude/, CLAUDE.md, .cursorrules, docs/"
```

將此腳本放在專案中（例如 `scripts/deploy-init.sh`），新伺服器 clone 後執行一次即可。

---

## 方案比較

如果 Sparse Checkout 不適合你的情境，以下是其他方案的比較：

| 方案 | 做法 | 優點 | 缺點 |
|------|------|------|------|
| **Sparse Checkout**（推薦） | 伺服器設定排除規則 | 零成本日常操作、伺服器完全乾淨 | 初次設定（Git 1.7+ 即可） |
| **不處理，直接留著** | 所有檔案都在伺服器上 | 零設定 | `.` 開頭目錄本來就不影響，但強迫症不舒服 |
| **Web Server 擋** | `.htaccess` / Nginx 規則 | 檔案在但外部訪問不到 | 檔案仍佔磁碟、目錄看起來雜 |
| **Post-pull Hook** | `post-merge` hook 刪檔案 | 自動化 | 每次 pull 都刪、fragile |
| **多個 Clone** | 開發/部署用不同 repo | 完全隔離 | 維護兩份 remote、容易忘記同步 |

---

## 常見問題

**Q: Sparse Checkout 會影響 `git pull` 的速度嗎？**

A: 不會。Git 仍然會下載所有 commit 資料，只是不把排除的檔案寫入工作目錄。網路傳輸量相同，差異僅在磁碟寫入（可忽略）。

**Q: 如果開發端有人修改了被排除的檔案，伺服器 pull 會出錯嗎？**

A: 不會。Git 會正常拉取所有變更，只是被排除的檔案不會出現在工作目錄中。`.git` 物件庫中仍然有完整歷史。

**Q: 能不能在開發端也用 Sparse Checkout？**

A: 技術上可以，但**不建議**。開發端應該看到完整的 repo 內容。Sparse Checkout 是為部署環境設計的。

**Q: 已經部署的舊伺服器可以直接啟用嗎？**

A: 可以。在現有的 repo 目錄中執行「快速開始」的三行指令即可，排除的檔案會立即從工作目錄消失，不影響其他檔案。

---

## 疑難排解

| 問題 | 原因 | 解決方式 |
|------|------|----------|
| `git sparse-checkout` 指令不存在 | Git 版本低於 2.25 | 改用「舊版 Git 替代方案」章節的 `core.sparseCheckout` 方式 |
| 排除的檔案仍然出現 | 設定後未執行 `git checkout` | 執行 `git checkout` 套用 |
| `git pull` 後排除失效 | Sparse Checkout 被停用 | `git sparse-checkout reapply` |
| 不確定目前排除了什麼 | — | `git sparse-checkout list` 查看 |

---

## 相關資源

- [GIT-WORKFLOW.md](./GIT-WORKFLOW.md) — 基礎 Git 工作流程
- [GIT-WORKTREE-WORKFLOW.md](./GIT-WORKTREE-WORKFLOW.md) — Worktree 並行開發
- [Git Sparse Checkout 官方文件](https://git-scm.com/docs/git-sparse-checkout)
