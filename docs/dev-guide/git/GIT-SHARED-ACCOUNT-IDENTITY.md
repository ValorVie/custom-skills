# 共用帳號 Git 身分管理指南

多人共用一個 Linux 帳號時，如何讓每個人使用各自的 Git 身分（SSH Key + Commit Identity）進行操作。

---

## 目錄

- [情境說明](#情境說明)
- [前置條件](#前置條件)
- [方法一：core.sshCommand（推薦）](#方法一coresshcommand推薦)
- [方法二：SSH Agent Forwarding](#方法二ssh-agent-forwarding)
- [方法三：includeIf 依路徑自動切換](#方法三includeif-依路徑自動切換)
- [方法比較](#方法比較)
- [最佳實踐](#最佳實踐)
- [常見問題](#常見問題)

---

## 情境說明

團隊共同維護一個 Linux test 帳號，需要：

- 各自用自己的 Git 帳號 / SSH Key 操作 private repo
- Commit 記錄保留正確的作者身分
- 權限隔離需求較低（已共用 OS 帳號）

**核心問題：Git 認證分離 + Commit 身分正確。**

---

## 前置條件

在開始設定前，每位成員需要在**自己的本機**完成以下準備。

### 1. 產生 SSH Key（每位成員各自操作）

如果還沒有 SSH Key，在**自己的筆電**上產生：

```bash
# 推薦使用 Ed25519（更安全、Key 更短）
ssh-keygen -t ed25519 -C "your_email@example.com" -f ~/.ssh/id_ed25519

# 如果環境不支援 Ed25519，使用 RSA
ssh-keygen -t rsa -b 4096 -C "your_email@example.com" -f ~/.ssh/id_rsa
```

產生後會有兩個檔案：
- `~/.ssh/id_ed25519` — Private Key（**絕不外洩**）
- `~/.ssh/id_ed25519.pub` — Public Key（用來註冊到 GitHub/GitLab）

### 2. 將 Public Key 加到 GitHub / GitLab

```bash
# 複製 Public Key 內容
cat ~/.ssh/id_ed25519.pub
```

貼到對應平台：
- **GitHub：** Settings → SSH and GPG keys → New SSH key
- **GitLab：** Preferences → SSH Keys → Add new key

### 3. 確認本機 SSH Agent 正在運行

```bash
# 檢查 Agent 狀態
ssh-add -l
```

#### macOS

macOS 由 `launchd` 內建管理 SSH Agent，**不需要手動啟動**。只需在 `~/.ssh/config` 加入：

```
Host *
    AddKeysToAgent yes
    UseKeychain yes
```

然後將 Key 加入 Keychain（只需做一次，重開機後也不用重新載入）：

```bash
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
```

> **注意：** 不要在 `~/.zshrc` 中寫 `eval "$(ssh-agent -s)"`，這會啟動一個全新的空 Agent，覆蓋系統 Agent 和 Keychain 整合，也會導致 SSH Agent Forwarding 失效。

#### Linux

如果出現 `Could not open a connection to your authentication agent`：

```bash
# 啟動 SSH Agent
eval "$(ssh-agent -s)"

# 載入 Key
ssh-add ~/.ssh/id_ed25519
```

如果要寫在 shell rc 檔中，建議加上條件判斷，避免覆蓋已有的 Agent（例如 forwarded agent）：

```bash
# ~/.bashrc 或 ~/.zshrc
if [ -z "$SSH_AUTH_SOCK" ]; then
    eval "$(ssh-agent -s)"
fi
```

### 4. 測試連線

```bash
ssh -T git@github.com
# 成功會顯示：Hi <username>! You've successfully authenticated, but GitHub does not provide shell access.
```

### 5. 前置條件依方法不同

| 前置條件 | 方法一 | 方法二 | 方法三 |
|---------|--------|--------|--------|
| 本機產生 SSH Key | V | V | V |
| Public Key 加到 GitHub/GitLab | V | V | V |
| 本機 SSH Agent 運行 | — | V | — |
| Private Key 複製到 Server | V | — | V |
| Server 允許 Agent Forwarding | — | V | — |

> **方法一、三**需要將 Private Key 複製到共用 Server 上；**方法二**不需要，Key 只留在本機。

### 將 Private Key 放到 Server（方法一、三適用）

```bash
# 從本機複製 Key 到 Server
scp ~/.ssh/id_ed25519 test@linux-server:~/.ssh/id_ed25519_yourname

# 登入 Server 後設定權限（必要，否則 SSH 會拒絕使用）
ssh test@linux-server
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519_yourname
```

---

## 方法一：core.sshCommand（推薦）

針對每個 Repository 設定獨立的 SSH Key，最直覺也最不易出錯。

### 1. 準備 SSH Key

從本機將 Private Key 複製到 Server，並確保權限正確：

```bash
# 從本機複製 Key 到 Server（在本機執行）
scp ~/.ssh/id_ed25519_yourname test@linux-server:~/.ssh/id_ed25519_yourname

# 登入 Server 後設定權限（必要，否則 SSH 會拒絕使用）
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519_yourname

# 確認 Key 已就位
ls -la ~/.ssh/id_ed25519_*
```

### 2. Clone 時指定 Key

```bash
GIT_SSH_COMMAND='ssh -i ~/.ssh/id_rsa_userA -o IdentitiesOnly=yes' \
  git clone git@github.com:org/repo.git
```

> `-o IdentitiesOnly=yes` 確保 SSH 只使用指定的 Key，不會嘗試其他 Key。

### 3. 設定 Repository 永久生效

進入 repo 資料夾，寫入 local config：

```bash
cd repo
git config core.sshCommand "ssh -i ~/.ssh/id_rsa_userA -o IdentitiesOnly=yes"
```

### 4. 設定 Commit 身分

```bash
git config user.name "User A"
git config user.email "usera@example.com"
```

### 驗證

```bash
# 確認 SSH Key 生效
git config core.sshCommand

# 確認 Commit 身分
git config user.name
git config user.email

# 測試連線
git ls-remote origin
```

---

## 方法二：SSH Agent Forwarding

伺服器上完全不需要存放任何人的 Private Key，認證透過轉發本機的 SSH Agent 完成。

**原理：**

```
你的筆電 (Private Key) --> SSH Agent Forwarding --> Linux Server --> GitHub/GitLab
```

### 1. Server 端設定

確認 `/etc/ssh/sshd_config` 允許轉發（通常預設開啟）：

```
AllowAgentForwarding yes
```

修改後重載 sshd：

```bash
sudo systemctl reload sshd
```

### 2. Client 端連線

連線時加上 `-A` 參數：

```bash
ssh -A test@linux-server
```

或在筆電的 `~/.ssh/config` 中設定：

```
Host linux-server
    HostName 192.168.1.100
    User test
    ForwardAgent yes
```

### 3. 驗證 Agent 轉發

```bash
# 登入 Server 後，確認 Agent 可用
ssh-add -l

# 測試 GitHub 連線
ssh -T git@github.com
```

### 4. 設定 Commit 身分

Agent Forwarding 只處理認證，Commit 身分仍需手動設定：

```bash
cd repo
git config user.name "User A"
git config user.email "usera@example.com"
```

### Client 端前置條件

Agent Forwarding 要求你的**本機 SSH Agent 已載入 Key**，否則 Server 端沒有 Key 可以轉發：

```bash
# 1. 確認 Agent 運行（macOS 不需手動啟動，見前置條件第 3 步）
ssh-add -l

# 2. 如果沒有 Key，載入它
ssh-add ~/.ssh/id_ed25519

# 3. 確認本機可以直連 GitHub
ssh -T git@github.com
```

> 如果本機這一步就失敗，Agent Forwarding 不可能成功。先解決本機的 SSH 連線問題。

### 安全注意事項

- Agent Forwarding 會讓 Server 上的 root 使用者能透過你的 Agent 進行認證
- 僅在**信任的 Server** 上啟用
- Session 斷線後轉發失效，需重新連線

---

## 方法三：includeIf 依路徑自動切換

依資料夾結構自動載入對應的 Git 設定，適合專案多且有明確的目錄規劃。

### 目錄規劃

```
~/project/
  userA/
    repo1/
    repo2/
  userB/
    repo3/
```

### 1. 編輯全域 `~/.gitconfig`

```ini
[includeIf "gitdir:~/project/userA/"]
    path = ~/.gitconfig-userA

[includeIf "gitdir:~/project/userB/"]
    path = ~/.gitconfig-userB
```

> **注意：** `gitdir:` 路徑結尾必須有 `/`，才能匹配該目錄下所有 repo。

### 2. 建立個人設定檔

`~/.gitconfig-userA`：

```ini
[user]
    name = User A
    email = usera@example.com

[core]
    sshCommand = ssh -i ~/.ssh/id_rsa_userA -o IdentitiesOnly=yes
```

`~/.gitconfig-userB`：

```ini
[user]
    name = User B
    email = userb@example.com

[core]
    sshCommand = ssh -i ~/.ssh/id_rsa_userB -o IdentitiesOnly=yes
```

### 驗證

```bash
# 進入 userA 的 repo，確認設定自動載入
cd ~/project/userA/repo1
git config user.name   # 應顯示 User A
git config user.email  # 應顯示 usera@example.com
```

---

## 方法比較

| 項目 | 方法一：core.sshCommand | 方法二：Agent Forwarding | 方法三：includeIf |
|------|------------------------|------------------------|------------------|
| **Key 存放** | Server 上 | 僅在本機 | Server 上 |
| **設定粒度** | 每個 repo | 每次連線 | 每個目錄 |
| **自動化程度** | 低（每個 repo 需設定） | 中（連線時自動） | 高（放對資料夾即可） |
| **安全性** | 中 | 高 | 中 |
| **斷線影響** | 無 | 需重新連線 | 無 |
| **適合場景** | repo 少、成員少 | 重視安全、不想留 Key | 專案多、目錄規劃清楚 |

### 推薦選擇

- **操作最直覺、不改連線習慣** → 方法一（core.sshCommand）
- **重視安全、Key 不留在 Server** → 方法二（Agent Forwarding）
- **專案多、可接受目錄分類** → 方法三（includeIf）

---

## 最佳實踐

### 1. 永遠設定 local user identity

不要依賴 global config 的 user.name / user.email。在共用帳號環境下，global 設定會讓其他人的 commit 冒名：

```bash
# 正確：每個 repo 設定 local
cd repo && git config user.name "Your Name"

# 避免：設定 global（會影響所有人）
# git config --global user.name "Your Name"  # 不要這樣做
```

### 2. 用 alias 簡化重複操作

如果採用方法一，可以建立 shell alias 減少打字：

```bash
# ~/.bashrc 或 ~/.zshrc
alias git-clone-a='GIT_SSH_COMMAND="ssh -i ~/.ssh/id_rsa_userA -o IdentitiesOnly=yes" git clone'
alias git-clone-b='GIT_SSH_COMMAND="ssh -i ~/.ssh/id_rsa_userB -o IdentitiesOnly=yes" git clone'
```

### 3. 用 script 一次完成 clone + 設定

```bash
#!/bin/bash
# git-clone-as.sh - Clone repo 並自動設定身分
# 用法: ./git-clone-as.sh <user> <repo-url>

USER_ID="$1"
REPO_URL="$2"

KEY_FILE="$HOME/.ssh/id_rsa_${USER_ID}"
CONFIG_FILE="$HOME/.gitconfig-${USER_ID}"

if [ ! -f "$KEY_FILE" ]; then
    echo "Error: Key file not found: $KEY_FILE"
    exit 1
fi

# Clone with specified key
GIT_SSH_COMMAND="ssh -i $KEY_FILE -o IdentitiesOnly=yes" git clone "$REPO_URL"

# Get repo directory name
REPO_DIR=$(basename "$REPO_URL" .git)
cd "$REPO_DIR" || exit 1

# Set SSH command
git config core.sshCommand "ssh -i $KEY_FILE -o IdentitiesOnly=yes"

# Set user identity from config file if exists
if [ -f "$CONFIG_FILE" ]; then
    NAME=$(git config -f "$CONFIG_FILE" user.name)
    EMAIL=$(git config -f "$CONFIG_FILE" user.email)
    [ -n "$NAME" ] && git config user.name "$NAME"
    [ -n "$EMAIL" ] && git config user.email "$EMAIL"
    echo "Configured as: $NAME <$EMAIL>"
else
    echo "Warning: No config file found at $CONFIG_FILE"
    echo "Please set user.name and user.email manually"
fi
```

### 4. 防止 global identity 汙染 commit

在 global config 中不設定 user.name / user.email，讓 Git 在缺少 local 設定時直接報錯：

```bash
# 移除 global identity（如果有的話）
git config --global --unset user.name
git config --global --unset user.email
```

這樣未設定 local identity 的 repo 在 commit 時會報錯，強制你先設定正確身分。

### 5. SSH Key 命名慣例

```
~/.ssh/
  id_ed25519_userA        # 推薦使用 Ed25519
  id_ed25519_userB
  id_rsa_userA            # RSA 也可以
  id_rsa_userB
```

> **推薦使用 Ed25519** 而非 RSA，更安全且 Key 更短：
> ```bash
> ssh-keygen -t ed25519 -C "usera@example.com" -f ~/.ssh/id_ed25519_userA
> ```

---

## 常見問題

### Q: push 時出現 Permission denied (publickey)

確認使用的 Key 有加到 GitHub/GitLab 帳號：

```bash
# 測試指定 Key 是否能連線
ssh -i ~/.ssh/id_rsa_userA -T git@github.com
```

### Q: commit 作者顯示錯誤

檢查 local config 是否正確設定：

```bash
git config user.name
git config user.email

# 如果為空或錯誤，重新設定
git config user.name "Correct Name"
git config user.email "correct@email.com"
```

### Q: 如何修正已經 commit 的錯誤作者？

```bash
# 修改最後一個 commit 的作者（尚未 push 的情況）
git commit --amend --author="User A <usera@example.com>"
```

> **警告：** 已 push 的 commit 不建議修改作者，會改寫歷史。

### Q: Agent Forwarding 連線後 ssh-add -l 顯示 "Could not open a connection to your authentication agent"

確認本機的 SSH Agent 正在運行且已載入 Key：

```bash
# macOS：Agent 由系統管理，只需確認 Key 已載入
ssh-add -l
ssh-add --apple-use-keychain ~/.ssh/id_ed25519

# Linux：可能需要手動啟動 Agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

然後重新以 `ssh -A` 連線。

> **常見陷阱：** 如果 Server 端的 `.bashrc` 無條件執行 `eval "$(ssh-agent -s)"`，會啟動新的空 Agent 覆蓋掉 forwarded agent。應使用條件判斷，見前置條件第 3 步的 Linux 說明。

### Q: includeIf 設定沒有生效

- 確認 `gitdir:` 路徑結尾有 `/`
- 確認 repo 確實在指定的目錄下
- 使用 `git config --show-origin user.name` 查看設定來源
