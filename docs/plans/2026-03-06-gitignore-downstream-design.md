# .gitignore-downstream 標記區塊合併設計

**日期：** 2026-03-06
**狀態：** 已核准

## 背景

模版 repo（如 `qdm-ai-base`）中有些檔案/目錄需要在模版端追蹤（如 `.atlas/`），但複製到下游專案後不應進版控。現有的 `.gitignore` 無法同時滿足兩個層面的需求。

## 設計

### 模版端

模版 repo 根目錄放置 `.gitignore-downstream`，格式為標準 `.gitignore` 語法：

```gitignore
# 由模版產生的檔案，下游專案不需追蹤
.atlas/
```

### init-from 行為

**首次初始化：**

1. 偵測模版中是否有 `.gitignore-downstream`
2. 若有，讀取內容，在目標 `.gitignore` 尾部插入標記區塊
3. `.gitignore-downstream` 本身不複製到目標（加入 `EXCLUDE_PATHS`）

**--update 時：**

1. 讀取模版最新的 `.gitignore-downstream`
2. 搜尋目標 `.gitignore` 中的標記區塊
3. 若找到 → 替換區塊內容
4. 若未找到 → 附加到尾部

**標記格式：**

```gitignore
# >>> {template_name} (managed by ai-dev init-from, DO NOT EDIT)
.atlas/
# <<< {template_name}
```

### 邊界情況

| 情況 | 行為 |
|------|------|
| 模版無 `.gitignore-downstream` | 不動 `.gitignore`，跳過 |
| 目標無 `.gitignore` | 建立新檔，只含標記區塊 |
| 使用者手動編輯區塊內容 | 下次 `--update` 會被覆蓋（標記已警告 DO NOT EDIT） |
| 使用者刪除標記行 | 視為區塊不存在，附加新區塊到尾部 |
| `.gitignore-downstream` 被刪除 | 移除目標中的標記區塊 |

## 程式碼變更範圍

| 檔案 | 變更 |
|------|------|
| `script/utils/smart_merge.py` | `EXCLUDE_PATHS` 加入 `.gitignore-downstream` |
| `script/utils/gitignore_downstream.py`（新） | 區塊讀取/插入/替換邏輯 |
| `script/commands/init_from.py` | 首次初始化和 `--update` 中呼叫合併函式 |
