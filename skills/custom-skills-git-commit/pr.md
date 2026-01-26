---
name: git-commit-pr
description: Git Commit 工作流 - 建立 Pull Request
---

## PR 模式 (Pull Request)

自動化「整理提交 → 推送 → 建立 PR」的完整流程。

---

## 1. 前置檢查

### 1.1 分支檢查

```bash
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# 確認不在主分支上
if [ "$CURRENT_BRANCH" = "$MAIN_BRANCH" ]; then
    echo "❌ 無法在主分支 ($MAIN_BRANCH) 上建立 PR"
    echo "   請切換到功能分支後再執行"
    exit 1
fi
```

### 1.2 gh CLI 檢查

```bash
# 檢查 gh CLI 是否安裝
if ! command -v gh &> /dev/null; then
    echo "❌ 未安裝 gh CLI"
    echo "   請執行：brew install gh (macOS) 或參考 https://cli.github.com/"
    exit 1
fi

# 檢查是否已登入
if ! gh auth status &> /dev/null; then
    echo "❌ gh CLI 未登入"
    echo "   請執行：gh auth login"
    exit 1
fi
```

### 1.3 遠端檢查

```bash
# 確認有 origin remote
if ! git remote get-url origin &> /dev/null; then
    echo "❌ 未設定 origin remote"
    echo "   請先執行：git remote add origin <url>"
    exit 1
fi
```

---

## 2. 範圍判定

> **前置條件**：已從 `_utils.md` 取得 `$MAIN_BRANCH` 變數

### 2.1 解析參數

依優先順序判定基準點：

#### 若指定 `--range a..b`

```bash
# 直接使用指定範圍
BASE_SHA=$(echo "$RANGE" | cut -d'.' -f1)
HEAD_SHA=$(echo "$RANGE" | cut -d'.' -f3)
```

#### 若指定 `--from <commit>`

```bash
# 從指定 commit 到 HEAD
BASE_SHA=$(git rev-parse "$FROM_COMMIT")
HEAD_SHA=$(git rev-parse HEAD)
```

#### 若未指定（自動偵測）

```bash
# 嘗試使用 origin/$MAIN_BRANCH 作為基準
if git rev-parse --verify "origin/$MAIN_BRANCH" &> /dev/null; then
    BASE_SHA=$(git merge-base HEAD "origin/$MAIN_BRANCH")
else
    BASE_SHA=$(git merge-base HEAD "$MAIN_BRANCH")
fi
HEAD_SHA=$(git rev-parse HEAD)
```

### 2.2 驗證範圍

```bash
# 計算範圍內的提交數量
COMMIT_COUNT=$(git rev-list --count $BASE_SHA..$HEAD_SHA)

if [ "$COMMIT_COUNT" -eq 0 ]; then
    echo "📭 無任何變更需要建立 PR"
    echo "   目前分支與 $MAIN_BRANCH 相同"
    exit 0
fi

echo "📊 共有 $COMMIT_COUNT 個提交將納入 PR"
```

---

## 3. 變更分析

讀取並執行 `pr-analyze.md`，取得：
- `$PR_TITLE`：PR 標題
- `$PR_BODY`：PR 內文

---

## 4. 檢查現有 PR

> **⚠️ 重要**：此步驟必須在提交整理（squash）之前執行！
> 若分支已有 OPEN 狀態的 PR，squash 會覆蓋該 PR 的所有提交。
> 必須先確認使用者意圖後才能繼續。

### 4.1 查詢現有 PR

```bash
EXISTING_PR=$(gh pr view --json number,url,state,title 2>/dev/null)

if [ -n "$EXISTING_PR" ]; then
    PR_NUMBER=$(echo "$EXISTING_PR" | jq -r '.number')
    PR_URL=$(echo "$EXISTING_PR" | jq -r '.url')
    PR_STATE=$(echo "$EXISTING_PR" | jq -r '.state')
    PR_TITLE=$(echo "$EXISTING_PR" | jq -r '.title')

    echo "📝 此分支已有 PR #$PR_NUMBER"
    echo "   標題：$PR_TITLE"
    echo "   狀態：$PR_STATE"
    echo "   $PR_URL"
fi
```

### 4.2 狀態判斷邏輯

| PR 狀態 | 處理方式 |
|---------|----------|
| `MERGED` | 直接建立新 PR（舊 PR 已合併完成） |
| `CLOSED` | 直接建立新 PR（舊 PR 已關閉） |
| `OPEN` | **必須詢問使用者**，確認後才能繼續 |
| 無 PR | 直接建立新 PR |

### 4.3 若 PR 為 OPEN 狀態

**必須詢問使用者**，提供以下選項：

1. **更新此 PR**：繼續執行 squash 和推送，PR 內容會自動更新
2. **建立新 PR**：需先建立新分支，再建立獨立的 PR
3. **中止操作**：取消本次操作，不做任何變更

```markdown
⚠️ 此分支已有進行中的 PR #$PR_NUMBER
   標題：$PR_TITLE

本次變更分析結果：
   標題：$NEW_PR_TITLE

請選擇：
1. 更新此 PR（將執行 squash 並推送）
2. 建立新分支並建立新 PR
3. 中止操作
```

**判斷提示**：
- 若現有 PR 標題與本次變更**相關**（如都是同一功能的迭代）→ 建議選擇 1
- 若現有 PR 標題與本次變更**無關**（如完全不同的功能）→ 建議選擇 2

### 4.4 若選擇「建立新 PR」

```bash
# 1. 詢問新分支名稱
NEW_BRANCH="feature/xxx"  # 由使用者指定

# 2. 建立並切換到新分支（從當前 HEAD）
git checkout -b $NEW_BRANCH

# 3. 繼續執行後續流程（squash、推送、建立 PR）
```

### 4.5 若選擇「中止操作」

```bash
echo "❌ 操作已中止"
exit 0
```

---

## 5. 提交整理

### 若未使用 `--no-squash`（預設行為）

將所有提交整合為一筆：

```bash
# 1. 記錄當前位置
ORIGINAL_HEAD=$(git rev-parse HEAD)

# 2. Soft reset 到 base
git reset --soft $BASE_SHA

# 3. 重新提交（使用分析階段產生的訊息）
git add .
git commit -m "$SQUASHED_MESSAGE"

echo "✅ 已將 $COMMIT_COUNT 個提交整合為 1 個"
```

### 若使用 `--no-squash`

跳過整合步驟，保留所有原始提交。

---

## 6. 推送

```bash
# 檢查是否需要 force push（因為整合提交會改寫歷史）
if [ "$NO_SQUASH" != true ]; then
    # 整合模式：需要 force push
    git push --force-with-lease -u origin $CURRENT_BRANCH
else
    # 保留模式：正常 push
    git push -u origin $CURRENT_BRANCH
fi
```

### 處理推送失敗

若推送失敗，檢查原因：

```bash
# 檢查是否有遠端變更
git fetch origin $CURRENT_BRANCH

if git diff $CURRENT_BRANCH origin/$CURRENT_BRANCH --quiet 2>/dev/null; then
    echo "✅ 遠端分支已是最新"
else
    echo "⚠️ 遠端分支有變更"
    echo "   建議先執行 git pull --rebase 後重試"
fi
```

---

## 7. 建立/更新 PR

### 若步驟 4 選擇「更新此 PR」

推送已完成，PR 內容會自動更新。可選擇是否更新 PR 標題和描述：

```bash
# 詢問是否更新 PR 標題和描述
# 若使用者確認，執行：
gh pr edit $PR_NUMBER --title "$PR_TITLE" --body "$PR_BODY"
```

### 若需建立新 PR

```bash
# 決定是否為草稿
if [ "$DIRECT" = true ]; then
    DRAFT_FLAG=""
    PR_TYPE="正式"
else
    DRAFT_FLAG="--draft"
    PR_TYPE="草稿"
fi

# 決定 base 分支
BASE_BRANCH="${BASE_BRANCH:-$MAIN_BRANCH}"

# 建立 PR
PR_URL=$(gh pr create \
    --title "$PR_TITLE" \
    --body "$PR_BODY" \
    --base "$BASE_BRANCH" \
    $DRAFT_FLAG)
```

---

## 8. 完成

顯示結果（不自動開啟瀏覽器）：

```bash
echo ""
echo "════════════════════════════════════════════════════════"
if [ "$UPDATED_EXISTING_PR" = true ]; then
    echo "✅ PR #$PR_NUMBER 已更新"
elif [ "$DIRECT" = true ]; then
    echo "✅ 正式 PR 已建立"
else
    echo "✅ 草稿 PR 已建立"
fi
echo ""
echo "   $PR_URL"
echo ""
echo "════════════════════════════════════════════════════════"
```

---

## 參數說明

| 參數 | 說明 | 預設值 |
|------|------|--------|
| `--direct` | 建立正式 PR（非草稿） | 草稿 PR |
| `--no-squash` | 保留所有提交，不整合 | 整合為一筆 |
| `--from <commit>` | 指定起始 commit | merge-base |
| `--range <a>..<b>` | 指定 commit 範圍 | 自動偵測 |
| `--base <branch>` | 指定 PR 的 base 分支 | main/master |
| `--title <string>` | 指定 PR 標題 | 自動生成 |
| `--body <string>` | 指定 PR 內文 | 自動生成 |

---

## 完成後

流程結束，PR URL 已顯示。
