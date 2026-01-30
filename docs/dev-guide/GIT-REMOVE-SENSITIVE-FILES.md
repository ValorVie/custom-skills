# Git 敏感檔案移除指南

本指南說明如何安全地從 Git 歷史中移除不應被追蹤的檔案，包括非敏感與敏感兩種情境。

---

## 快速參考

| 情境 | 方法 | 風險 | 適用場景 |
|------|------|------|---------|
| 檔案無敏感資訊 | `git rm --cached` + 新 commit | 低 | 移除本地設定檔、IDE 檔案等 |
| 檔案含敏感資訊 | `git filter-repo` 改寫歷史 | 高 | 密鑰、token、密碼外洩 |
| 大型 repo 含敏感資訊 | BFG Repo-Cleaner | 高 | 大型 repo 的快速清理 |

---

## 方案一：移除追蹤（不改寫歷史）

**適用情境**：檔案不含密鑰或敏感資訊，只是不應被版本控制追蹤（如 IDE 設定、本地設定檔）。

### 步驟

```bash
# 1. 確認檔案仍在 git 追蹤中
git ls-files -- <file-path>

# 2. 從 git 追蹤移除，保留本地檔案
git rm --cached <file-path>

# 3. 確認 .gitignore 已包含該檔案（如未包含則新增）
echo "<file-path>" >> .gitignore

# 4. 提交變更
git add .gitignore
git commit -m "雜項: 移除不應追蹤的檔案 <file-path>"

# 5. 推送到遠端
git push origin main
```

### 注意事項

- 歷史 commit 中仍可查到檔案內容，但因為不含敏感資訊所以可接受
- 不影響其他協作者的工作流程
- 不破壞 merge commit 鏈

---

## 方案二：改寫歷史（徹底清除）

**適用情境**：檔案包含密鑰、token、密碼等敏感資訊，必須從所有歷史 commit 中徹底移除。

### 前置作業（必做）

在改寫歷史之前，**必須先完成**：

1. **立即 rotate 所有外洩的密鑰**（改密碼、重新產生 API key 等）
   - 即使清除歷史，也必須假設密鑰已被讀取
2. **通知所有協作者**即將改寫歷史
3. **備份 repo**

```bash
# 備份整個 repo
cp -r .git .git-backup
```

### 方法 A：git filter-repo（推薦）

`git filter-repo` 是 Git 官方推薦取代 `git filter-branch` 的工具。

```bash
# 安裝
brew install git-filter-repo

# 從所有歷史中徹底移除指定檔案
git filter-repo --invert-paths --path <file-path>

# 如需移除多個檔案
git filter-repo --invert-paths \
  --path path/to/secret1.json \
  --path path/to/secret2.env

# 重新設定 remote（filter-repo 會移除 remote 設定）
git remote add origin <repo-url>

# 強制推送到遠端（覆寫所有分支歷史）
git push origin --force --all
git push origin --force --tags
```

### 方法 B：BFG Repo-Cleaner

適合大型 repo，語法更簡潔。

```bash
# 安裝
brew install bfg

# 先確保最新版本不含敏感檔案（BFG 預設保護 HEAD）
git rm <file-path>
git commit -m "移除敏感檔案"

# 從歷史中移除指定檔案
bfg --delete-files <filename>

# 或替換檔案中的敏感字串
bfg --replace-text passwords.txt

# 清理並強制推送
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push origin --force --all
```

### 改寫後的必要善後

改寫歷史後，**必須完成**以下步驟：

| 步驟 | 操作 | 說明 |
|------|------|------|
| 1 | Rotate 密鑰 | 前置作業已做，此處再次確認 |
| 2 | 通知協作者重新 clone | 舊的本地 repo 無法正常 pull |
| 3 | 聯繫 GitHub Support | 請求清除 dangling commit 快取 |
| 4 | 檢查 Fork | 已被 fork 的 repo 仍保有舊歷史 |
| 5 | 更新 .gitignore | 確保該檔案不會再被追蹤 |
| 6 | 驗證清除結果 | 見下方驗證步驟 |

### 驗證清除結果

```bash
# 確認檔案已從所有歷史中移除
git log --all --full-history -- <file-path>
# 應該沒有任何輸出

# 搜尋歷史中是否還有敏感字串
git log --all -p | grep -c "<sensitive-string>"
# 應該為 0
```

---

## 改寫歷史的風險

| 風險 | 說明 |
|------|------|
| 破壞協作者的本地 repo | 其他人必須重新 clone，無法正常 pull |
| PR / Issue 連結失效 | Commit hash 全部改變，引用舊 hash 的連結會斷掉 |
| Merge commit 重建 | 複雜的合併歷史可能變得混亂 |
| Fork 不受影響 | 已 fork 的 repo 仍保有舊歷史，敏感資訊仍可能外洩 |
| GitHub 快取 | 即使 force push，GitHub 仍可能快取舊 commit |
| **PR 殘留舊 commit** | **GitHub PR 頁面綁定原始 commit SHA，force push 後仍可存取** |

---

## GitHub PR 殘留問題

`git filter-repo` 改寫歷史後，`git log` 中確實不會再出現敏感檔案。但 **GitHub PR 仍然會殘留舊 commit**，這是最容易被忽略的盲點。

### 為什麼 PR 中的檔案內容不會消失

GitHub PR 的 Files changed 頁面**不是快取**，而是直接引用 Git 物件。即使改寫 commit 歷史，底層的 blob（檔案內容物件）和 tree 仍獨立存在於 GitHub 的 object store 中：

```
PR Files changed → commit SHA → tree SHA → blob SHA（檔案內容）
                   ↑                        ↑
                   force push 改寫了這個      但這個仍然存在
```

具體來說：

1. **Blob 是 content-addressable** — blob SHA 由檔案內容的 hash 決定，與 commit 無關，獨立存在
2. **PR 保留原始 commit 參照** — PR 記錄的 commit SHA 不會隨 force push 更新
3. **GitHub 不自動 GC dangling objects** — 無 branch 指向的 commit、tree、blob 仍可透過 API 存取

### 驗證方式

```bash
# 檢查 PR 的 files changed 是否仍包含敏感檔案
gh api repos/<owner>/<repo>/pulls/<pr-number>/files \
  --jq '.[] | select(.filename | test("<filename>")) | {filename, sha}'

# 如果有結果，透過 blob SHA 可直接讀取檔案完整內容
gh api repos/<owner>/<repo>/git/blobs/<blob-sha> --jq '.content' | base64 -d
```

### 徹底清除的選項

僅靠 `git filter-repo` + `git push --force` **不足以**從 GitHub 徹底移除敏感資訊。

#### 選項 A：聯繫 GitHub Support（推薦）

```
git filter-repo → force push → 刪除殘留 ref → 聯繫 GitHub Support
```

1. **執行 `git filter-repo`**（改寫本地歷史）
2. **Force push 所有分支和 tags**
3. **刪除殘留的分支 ref**
   ```bash
   git ls-remote origin
   git push origin --delete <branch-name>
   ```
4. **聯繫 GitHub Support**
   - 到 https://support.github.com 提交請求
   - 說明需要清除 dangling objects（附上受影響的 blob SHA 和 commit SHA）
   - GitHub Support 會清除不可達的 git objects，包括 blob
   - 這是**唯一能讓 PR Files changed 中檔案內容消失**的方式
   - 處理時間通常數天

#### 選項 B：刪除並重建 repo

如果無法等待 GitHub Support，或 repo 狀況允許：

1. 在本地完成 `git filter-repo` 清理
2. 在 GitHub 上**刪除整個 repo**（Settings → Delete this repository）
3. 以相同名稱**重新建立 repo**
4. 將清理後的本地 repo push 上去

**代價**：所有 PR、Issue、Star、Watch、Wiki、GitHub Actions 歷史**全部消失**。

#### 選項 C：接受殘留，僅靠 rotate 密鑰防護

如果敏感資訊是密鑰類（API key、token），rotate 後舊值即失效，PR 中殘留的內容已無利用價值。這在實務上是最務實的做法。

5. **如果是 public repo** — 無論選哪個選項，都必須假設資料已被外部爬取或快取，rotate 密鑰是最優先

### 結論

> **改寫 git 歷史無法保證從 GitHub 徹底移除敏感資訊。**
> 最重要的永遠是第一步：**立即 rotate 所有外洩的密鑰。**

---

## 預防措施

避免敏感檔案被 commit 的最佳做法：

```bash
# 1. 在 .gitignore 中排除敏感檔案模式
*.local.json
.env
.env.*
credentials.*
**/secrets/

# 2. 使用 git-secrets 自動掃描
brew install git-secrets
git secrets --install
git secrets --register-aws  # 例：掃描 AWS 密鑰

# 3. 使用 pre-commit hook 檢查
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
```

---

## 相關文件

- [GIT-WORKFLOW.md](GIT-WORKFLOW.md) - Git 分支管理與 PR 流程
- [DEVELOPMENT-WORKFLOW.md](DEVELOPMENT-WORKFLOW.md) - OpenSpec 開發工作流程
