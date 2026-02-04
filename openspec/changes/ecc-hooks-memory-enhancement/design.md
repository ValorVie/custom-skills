## Context

ecc-hooks 的記憶持久化腳本從上游 everything-claude-code 繼承，目前只產生空模板。使用者同時安裝了 claude-mem，該系統透過 AI 呼叫做語意記憶。ecc-hooks 的定位是提供零成本、純本地的結構化事實記錄，與 claude-mem 互補。

現有腳本位於 `plugins/ecc-hooks/scripts/memory-persistence/`，使用 Python 標準庫，工具函式在 `scripts/utils.py`。Hook 透過 `hooks/hooks.json` 註冊，stdin 接收 JSON 格式的 hook 資料。

## Goals / Non-Goals

**Goals:**
- SessionEnd 時記錄本次會話的結構化事實（git 變更、修改檔案、commit 歷史）
- SessionStart 時載入最近會話的結構化事實並注入上下文
- PreCompact 時保存當前工作狀態的 git 快照
- 零外部依賴（僅 Python 標準庫 + git CLI）
- 零 AI 呼叫成本

**Non-Goals:**
- 語意分析或自然語言摘要（claude-mem 負責）
- 搜尋功能（claude-mem 的 MCP 工具負責）
- 修改 hooks.json 的 Hook 註冊方式
- 修改 sessions 指令系統（session-manager.js、session-aliases.js）
- 修改 evaluate-session.py（維持現狀）

## Decisions

### 1. 直接修改現有腳本，不另建獨立腳本

**選擇**：修改 session-end.py、session-start.py、pre-compact.py

**理由**：先前考慮過新增獨立腳本以避免上游同步衝突，但決定不再追蹤上游的記憶腳本（上游只是空殼），直接修改更簡潔。

**捨棄方案**：新增 session-snapshot.py 並行掛載 — 增加複雜度，兩個腳本寫同一個 .tmp 檔會有競爭。

### 2. .tmp 檔案格式保持 Markdown，擴充內容區塊

**選擇**：保留現有 Markdown 模板結構，用實際資料填充各區塊。

```markdown
# Session: 2026-02-04
**Date:** 2026-02-04
**Project:** custom-skills
**Started:** 18:48
**Last Updated:** 20:30

---

## Git 變更摘要
- 3 files changed, 289 insertions(+), 12 deletions(-)

## 修改的檔案
- docs/dev-guide/MEMORY-PLUGINS-GUIDE.md (新增)
- plugins/ecc-hooks/scripts/memory-persistence/session-end.py (修改)

## Commit 記錄
- a5d22d9 文件(記憶外掛): 新增 ecc-hooks 與 claude-mem 並用指南

## 工作目錄狀態
- clean（或列出未提交的變更）
```

**理由**：Markdown 可讀性好，sessions 指令系統已能解析 .tmp 檔，保持格式相容。

**捨棄方案**：JSON 格式 — 機器友善但人類不好讀，且需要修改 session-manager.js 的解析邏輯。

### 3. 資料收集僅使用 git CLI

**選擇**：透過 `subprocess.run(['git', ...])` 收集資料。

需要的 git 指令：
- `git diff --stat HEAD` — 工作目錄變更統計
- `git diff --name-status HEAD` — 修改的檔案清單與狀態
- `git log --oneline --since="SESSION_START_TIME"` — 本次會話期間的 commit
- `git rev-parse --show-toplevel` — 專案名稱（已在 utils.py 中有）
- `git status --porcelain` — 工作目錄乾淨度

**理由**：git 是唯一的外部依賴，且所有使用場景都有 git。每個指令執行時間 < 100ms。

### 4. SessionStart 載入最近一個會話（非全部）

**選擇**：只載入最近的 1 個 .tmp 檔內容，透過 stdout 注入上下文。

**理由**：
- 避免佔用過多上下文視窗（單檔約 2-5 KB ≈ 500-1200 tokens）
- claude-mem 已提供多會話的歷史摘要索引
- 使用者可透過 `/sessions load` 手動載入更多

### 5. PreCompact 保存 git status 快照

**選擇**：在壓縮前追加當前 `git status --porcelain` 和 `git diff --stat` 到 .tmp 檔。

**理由**：壓縮會丟失上下文中的工作進度，記錄 git 狀態讓壓縮後仍能知道「做到哪了」。

## Risks / Trade-offs

- **[風險] 非 git 專案沒有資料可記錄** → 降級為只記錄日期時間和 `[非 git 專案]` 標記，不會報錯
- **[風險] git 指令失敗（detached HEAD、bare repo）** → 所有 subprocess 呼叫都用 try/except 包裹，失敗時靜默跳過該區塊
- **[風險] .tmp 檔案變大** → 限制 commit 記錄最多 20 筆、diff stat 最多 50 行，單檔預計不超過 5 KB
- **[取捨] 不記錄對話內容** → 有意為之，對話語意由 claude-mem 處理，我們只記錄可驗證的客觀事實
- **[取捨] 放棄上游同步** → 上游記憶腳本是空殼，同步沒有價值。代碼品質腳本仍可獨立同步
