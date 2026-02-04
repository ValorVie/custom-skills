# ecc-hooks 記憶持久化改寫差異報告

**改寫日期：** 2026-02-04
**變更名稱：** ecc-hooks-memory-enhancement
**OpenSpec Artifacts：** `openspec/changes/ecc-hooks-memory-enhancement/`

---

## 總覽

舊版記憶持久化腳本源自上游 [everything-claude-code](https://github.com/anthropics/everything-claude-code)（2026-01-24 同步），但僅為空殼佔位符，實際上**不記錄任何有意義的會話資料**。新版改寫為記錄結構化 git 事實，與 claude-mem 的語意記憶形成互補。

| 項目 | 舊版 | 新版 |
|------|------|------|
| 來源 | upstream (everything-claude-code) | 自行改寫 |
| 記錄內容 | 空模板（佔位符） | 結構化 git 事實 |
| 上下文注入 | 僅 log 訊息（~50 tokens） | 完整會話內容（~500-1200 tokens） |
| git 整合 | 無 | git diff/status/log |
| 非 git 支援 | 無（建立空模板） | 有（降級顯示「不適用」） |

---

## 檔案差異明細

### 1. `utils.py`

**新增函式：**

| 函式 | 說明 |
|------|------|
| `run_git_command(args, timeout=5)` | 封裝 git subprocess 呼叫，超時/錯誤靜默回傳 `None` |
| `is_git_repo()` | 判斷當前目錄是否為 git 倉庫 |

**修改函式：**

| 函式 | 舊版行為 | 新版行為 |
|------|---------|---------|
| `get_project_name()` | 直接呼叫 `subprocess.run(['git', ...])` | 改用 `run_git_command()` 封裝，消除重複的 subprocess 呼叫 |

其餘函式（`find_files`, `read_file`, `write_file`, `append_file`, `detect_package_manager` 等）**完全未變動**。

---

### 2. `session-end.py`（SessionEnd Hook）

**舊版行為：**
- 建立/更新 `.tmp` 檔，內容為空模板
- 模板包含 `[Session context goes here]`、空的 `Completed`/`In Progress`/`Notes` 區塊
- 如果檔案已存在，只更新 `**Last Updated:**` 時間戳
- 產出的 `.tmp 檔約 258 bytes，無任何實質內容

```
# Session: 2026-02-04
**Date:** 2026-02-04
**Started:** 18:48
**Last Updated:** 20:25

---

## Current State
[Session context goes here]

### Completed
- [ ]

### In Progress
- [ ]

### Notes for Next Session
-

### Context to Load
[relevant files]
```

**新版行為：**
- 自動收集 4 種結構化 git 事實：
  1. **Git 變更摘要** (`git diff --stat HEAD`，最多 50 行)
  2. **修改的檔案** (`git diff --name-status HEAD`，標示新增/修改/刪除)
  3. **Commit 記錄** (`git log --oneline --since=<started_time>`，最多 20 筆)
  4. **工作目錄狀態** (`git status --porcelain`)
- 非 git 專案各區塊顯示「不適用」
- 保留既有的 compaction 記錄
- 產出的 .tmp 檔包含完整的工作紀錄

```
# Session: 2026-02-04
**Date:** 2026-02-04
**Project:** custom-skills
**Started:** 18:48
**Last Updated:** 20:25

---

## Git 變更摘要
.../memory-persistence/session-end.py | 164 ++++++++++++++++-----
.../memory-persistence/session-start.py | 67 ++++++---
5 files changed, 257 insertions(+), 88 deletions(-)

## 修改的檔案
- plugins/ecc-hooks/scripts/utils.py (修改)
- plugins/ecc-hooks/scripts/memory-persistence/session-end.py (修改)

## Commit 記錄
- 1ebb81a WIP-1
- a5d22d9 文件(記憶外掛): 新增 ecc-hooks 與 claude-mem 並用指南

## 工作目錄狀態
- M plugins/ecc-hooks/scripts/utils.py
-  M plugins/ecc-hooks/scripts/memory-persistence/pre-compact.py
```

**新增的內部函式：**

| 函式 | 說明 |
|------|------|
| `_collect_git_diff_stat(max_lines=50)` | 收集 `git diff --stat HEAD` |
| `_collect_modified_files()` | 收集 `git diff --name-status HEAD`，帶中文狀態標籤 |
| `_collect_commits(started_time, today, max_count=20)` | 收集會話期間的 commit |
| `_collect_working_dir_status()` | 收集 `git status --porcelain` |
| `_get_started_time(session_file)` | 從既有檔案提取啟動時間 |

**移除的 import：** `replace_in_file`（舊版用於更新時間戳，新版每次全量寫入）

---

### 3. `session-start.py`（SessionStart Hook）

**舊版行為：**
- 找到最近的 `.tmp` 檔後，只透過 `log()` 輸出 stderr 訊息（如 `Found 3 recent session(s)`）
- **不讀取** .tmp 檔案內容，不注入任何上下文到 Claude
- 上下文佔用約 50-100 tokens（僅 log 元資訊）

**新版行為：**
- 讀取最近 `.tmp` 檔的**完整內容**
- 透過 `output()` 寫入 stdout，注入 Claude 的上下文視窗
- 內容包裹在邊界標記中：`[上次會話摘要 - <date>]...[/上次會話摘要]`
- 10 KB 截斷保護（超過則截斷並標示 `[內容已截斷]`）
- 上下文佔用約 500-1200 tokens（完整結構化事實）

**新增的內部函式：**

| 函式 | 說明 |
|------|------|
| `_load_recent_session(sessions_dir)` | 讀取最近 .tmp 檔，截斷保護，stdout 輸出 |

**保留的功能：** 套件管理器偵測、別名顯示（`_show_session_aliases`）

**新增常數：** `MAX_CONTEXT_BYTES = 10 * 1024`

---

### 4. `pre-compact.py`（PreCompact Hook）

**舊版行為：**
- 記錄 compaction 事件到 `compaction-log.txt`
- 在 .tmp 檔追加一行文字：`**[Compaction occurred at HH:MM]** - Context was summarized`
- 不包含任何 git 狀態資訊

**新版行為：**
- 保留 `compaction-log.txt` 記錄
- 追加 git 狀態快照到 .tmp 檔：
  - 工作目錄狀態（`git status --porcelain` 的檔案數）
  - diff 統計（`git diff --stat HEAD`，最多 20 行）
- 非 git 專案顯示 `(非 git 專案)`

**新增的內部函式：**

| 函式 | 說明 |
|------|------|
| `_collect_compact_snapshot()` | 收集 git status + diff stat 快照 |

**新增 import：** `is_git_repo`, `run_git_command`（取代無操作的追加）

---

### 5. `evaluate-session.py`（Stop Hook）

**未修改。** 此腳本負責提取可重用模式（learned skills），與記憶持久化無直接關係。

---

## 目錄結構對照

```
plugins/
├── ecc-hooks/                    ← 新版（目前使用中）
│   └── scripts/
│       ├── utils.py              ← +run_git_command, +is_git_repo, refactored get_project_name
│       └── memory-persistence/
│           ├── session-end.py    ← 全面改寫：結構化 git 事實
│           ├── session-start.py  ← 全面改寫：載入並注入上下文
│           ├── pre-compact.py    ← 全面改寫：git 狀態快照
│           └── evaluate-session.py ← 未修改
│
└── ecc-hooks-old/                ← 舊版（保留備份）
    └── scripts/
        ├── utils.py              ← 原始版本，無 git 輔助函式
        └── memory-persistence/
            ├── session-end.py    ← 空模板生成
            ├── session-start.py  ← 僅 log 元資訊
            ├── pre-compact.py    ← 僅追加時間戳文字
            └── evaluate-session.py ← 與新版相同
```
