# Lazygit 終端 Git UI 完整指南

## 目錄

- [簡介與定位](#簡介與定位)
- [安裝方式（多平台）](#安裝方式多平台)
- [設定檔路徑](#設定檔路徑)
- [快速開始](#快速開始)
- [核心工作流](#核心工作流)
- [進階操作與風險提示](#進階操作與風險提示)
- [與 VS Code Code Review 協作](#與-vs-code-code-review-協作)
- [常見問題](#常見問題)
- [參考資料](#參考資料)

---

## 簡介與定位

Lazygit 是終端中的 Git UI，適合把 `status`、`stage`、`commit`、`branch`、`rebase`、`conflict` 整合在同一個視窗。

在你的開發框架中，Lazygit 建議定位為：

- 日常 Git 操作主入口
- 快速檢查差異與 staging 的中繼層
- 進入 VS Code review 前的整理站

---

## 安裝方式（多平台）

### Windows

```powershell
# Winget
winget install -e --id=JesseDuffield.lazygit

# Scoop
scoop bucket add extras
scoop install lazygit

# Chocolatey
choco install lazygit
```

### macOS

```bash
brew install lazygit
```

### Linux

```bash
# Debian / Ubuntu（新版本可直接 apt）
sudo apt install lazygit

# Arch
sudo pacman -S lazygit

# Fedora（COPR）
sudo dnf copr enable dejan/lazygit
sudo dnf install lazygit
```

### 用 Go 安裝（適合 apt 套件過舊）

```bash
go install github.com/jesseduffield/lazygit@latest
```

若安裝後找不到指令，確認 `go/bin` 在 PATH：

```bash
export PATH="$HOME/go/bin:$PATH"
```

Windows（PowerShell）可檢查：

```powershell
# 典型路徑為 %USERPROFILE%\go\bin
$env:Path
```

### 驗證版本

```bash
lazygit --version
```

---

## 設定檔路徑

全域設定檔 `config.yml`：

| 平台 | 路徑 |
|------|------|
| Linux | `~/.config/lazygit/config.yml` |
| macOS | `~/Library/Application Support/lazygit/config.yml` |
| Windows | `%LOCALAPPDATA%\lazygit\config.yml`（也會找 `%APPDATA%\lazygit\config.yml`） |

Repo 專屬設定：

- `<repo>/.git/lazygit.yml`
- 父目錄也可放 `.lazygit.yml` 進行共用覆寫

---

## 快速開始

在 Git repo 內啟動：

```bash
lazygit
```

建議常用鍵（入門版）：

- `R`: Refresh
- `Space`: stage/unstage
- `c`: Commit
- `n`: 新分支
- `Tab`: 切換面板
- `q`: 離開

---

## 核心工作流

### 1) 檢查與整理變更

1. 進 `Files` 面板確認變更
2. 用 `Space` 只 stage 本次要提交的檔案
3. 先看 diff 再 commit，避免把雜訊一起送出

### 2) 提交與同步

1. `c` 建立 commit
2. `f` fetch（確認遠端狀態）
3. 視團隊策略進行 push / PR

### 3) 分支與整線

1. `n` 建功能分支
2. 在 `Branches` 面板做 checkout
3. 需要整線時做 rebase / merge

### 4) 衝突處理

1. 進入衝突檔案
2. 用衝突導覽與 hunk 選擇完成解決
3. 再次檢查 diff 後提交

---

## 進階操作與風險提示

高風險操作請先確認：

- `force checkout` 可能丟失工作區未保存變更
- `commit without hook` 會跳過 pre-commit 驗證
- `interactive rebase` 會改寫歷史，推送前要特別檢查

建議團隊層級在設定檔保留安全護欄，例如：

- 禁用 force push
- 保留 commit 前警告

---

## 與 VS Code Code Review 協作

你目前仍以 VS Code 做主要 review，可以用下列分工：

- Lazygit：快速整理 commit、stage、分支與歷史
- VS Code：深入看程式碼脈絡、註解與 PR 討論

推薦節奏：

1. 在 Lazygit 完成「乾淨 commit」
2. 切到 VS Code 做 final review
3. 回到 Lazygit 做最後同步與推送

---

## 常見問題

### 套件版本和官方 release 不一致

- 套件管理器更新頻率可能落後，需以 `lazygit --version` 實測。

### 看不到自訂設定

- 先確認 config 是否放在正確平台路徑。
- 檢查是否有 repo-local 設定覆蓋全域設定。

### 分支操作出現意外

- 先在 `status` 確認是否有未提交變更，再做 checkout/rebase。

---

## 參考資料

- 官方 README：https://github.com/jesseduffield/lazygit
- 官方設定文件：https://github.com/jesseduffield/lazygit/blob/master/docs/Config.md
- 官方快捷鍵文件：https://github.com/jesseduffield/lazygit/blob/master/docs/keybindings/Keybindings_en.md
- Releases：https://github.com/jesseduffield/lazygit/releases
