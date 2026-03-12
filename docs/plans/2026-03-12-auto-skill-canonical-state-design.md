# 設計文件：auto-skill canonical state 與多工具投影

**日期：** 2026-03-12
**狀態：** 已實作
**範圍：** ai-dev CLI 的 `update`、`clone` 與 auto-skill 路徑管理

---

## 目標

將 `auto-skill` 從「各工具各自持有副本」改成：

1. `~/.config/ai-dev/skills/auto-skill` 作為 canonical state
2. `clone` 階段投影到 `~/.claude`、`~/.codex`、`~/.gemini` 等工具目錄
3. 預設使用 `symlink`，Windows 優先 `junction`，失敗 fallback `copy`

---

## 設計決策

### 路徑分層

- `~/.config/custom-skills/skills/auto-skill`
  - template
- `~/.config/auto-skill`
  - upstream repo
- `~/.config/ai-dev/skills/auto-skill`
  - canonical state
- `~/.claude/skills/auto-skill`
- `~/.codex/skills/auto-skill`
- `~/.gemini/skills/auto-skill`
  - tool projections

### 責任分工

- `update`
  - 更新 upstream repo
  - refresh canonical state
  - 不直接分發到各工具

- `clone`
  - refresh/ensure canonical state
  - 將 canonical state 投影到各工具

### merge 策略

canonical state 合併順序：

1. template
2. upstream

衝突時保留既有 state，僅補齊缺漏與可安全合併的 `_index.json`。

---

## 實作邊界

### 目標

- 新增 canonical path helper
- 新增 state refresh helper
- 新增 projection helper
- 將 `shared.py`、`update.py` 接入新模型

### 非目標

- 不重構整個 Stage 2 / Stage 3 架構
- 不把所有 Skills 都改成 symlink 模式
- 不調整 auto-skill 內容格式

---

## 驗證

- path helper 測試
- canonical state refresh 測試
- projection symlink/copy fallback 測試
- clone policy 回歸測試
- 全量 pytest 回歸
