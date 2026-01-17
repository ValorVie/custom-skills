---
name: git-commit-utils
description: Git Commit 工作流的共用工具函式
---

## 主分支判斷

在執行任何操作前，必須先判斷專案使用的主分支名稱：

```bash
# 判斷主分支名稱
if git rev-parse --verify main >/dev/null 2>&1; then
    MAIN_BRANCH="main"
elif git rev-parse --verify master >/dev/null 2>&1; then
    MAIN_BRANCH="master"
else
    echo "❌ 無法找到 main 或 master 分支"
    exit 1
fi

echo "📌 主分支：$MAIN_BRANCH"
```

### 遠端主分支

```bash
REMOTE_MAIN="origin/$MAIN_BRANCH"
```

---

## 當前分支判斷

```bash
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# 檢查是否為主分支
if [ "$CURRENT_BRANCH" = "$MAIN_BRANCH" ]; then
    IS_MAIN_BRANCH=true
else
    IS_MAIN_BRANCH=false
fi
```

---

## 分支類型判斷

| 分支類型 | 判斷依據 | 同步策略 |
|----------|----------|----------|
| **主分支** | 名稱為 `main` 或 `master` | 視 `--direct` 參數而定 |
| **整合測試分支** | 名稱開頭為 `test-dev-` | **Merge**（保留合併節點） |
| **功能分支** | 其他所有分支 | **Rebase**（保持線性歷史） |

```bash
# 判斷同步策略
if [[ "$NO_REBASE" == true ]] || [[ "$CURRENT_BRANCH" == test-dev-* ]]; then
    SYNC_STRATEGY="merge"
else
    SYNC_STRATEGY="rebase"
fi
```

---

## 衝突處理指引

若發生衝突：

1. 執行 `git diff --name-only --diff-filter=U` 列出衝突檔案
2. 分析每個衝突檔案的差異，向使用者說明：
   - **衝突位置**
   - **開發分支變更內容**
   - **主分支變更內容**
   - **建議解決方案**
3. 等待使用者決策後協助解決
4. 解決後執行：
   ```bash
   git add <file>
   git rebase --continue  # 若為 rebase
   # 或
   git commit             # 若為 merge
   ```

---

## 提交訊息規範

- **使用繁體中文撰寫**
- **語言風格**：以臺灣習慣用語為主（如：使用「分支」而非「分叉」，「提交」而非「遞交」）
- **遵循規範**：參考 `commit-standards` 這個 SKILL 的標準進行撰寫

### 標題格式

```
<type>(<scope>): <subject>
```

### 類型 (type)

| 類型 | 說明 |
|------|------|
| `feat` | 新功能 |
| `fix` | 錯誤修復 |
| `docs` | 文件更新 |
| `style` | 格式調整（無邏輯變更） |
| `refactor` | 重構（無功能變更） |
| `test` | 測試相關 |
| `chore` | 維護任務 |

---

## 異常處理原則

1. **衝突處理**：任何 Rebase 或 Stash Pop 階段的衝突，必須優先列出衝突檔案並給予解決建議，切勿自行強行覆蓋。
2. **無變更處理**：若發現與 base 無差異，請告知使用者並中止流程。
3. **資訊保留**：在執行 `git reset --soft` 之前，務必確保已讀取並記錄了所有的 `git log` 資訊。
