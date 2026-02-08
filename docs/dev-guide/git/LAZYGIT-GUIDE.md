# Lazygit 終端 Git UI 完整指南

## 目錄

- [簡介與定位](#簡介與定位)
- [安裝方式（多平台）](#安裝方式多平台)
- [設定檔路徑](#設定檔路徑)
- [快速開始](#快速開始)
- [面板與導覽](#面板與導覽)
- [完整快捷鍵參考](#完整快捷鍵參考)
- [核心工作流](#核心工作流)
- [進階操作](#進階操作)
- [推薦設定](#推薦設定)
- [與開發工具協作](#與開發工具協作)
- [常見問題](#常見問題)
- [參考資料](#參考資料)

---

## 簡介與定位

[Lazygit](https://github.com/jesseduffield/lazygit) 是終端中的 Git UI，適合把 `status`、`stage`、`commit`、`branch`、`rebase`、`conflict` 整合在同一個視窗。

在開發框架中，Lazygit 建議定位為：

- 日常 Git 操作主入口
- 快速檢查差異與 staging 的中繼層
- 進入 VS Code review 前的整理站
- 搭配 Zellij layout 使用，在專用 tab 中開啟

---

## 安裝方式（多平台）

### Windows

```powershell
# Winget（推薦）
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

畫面分為 5 個面板，按 `Tab` 或數字鍵 `1`-`5` 在面板間切換：

```
┌───────────────────────────────────────────┐
│  ① Status    │  ④ Commits (Local)         │
│  ② Files     │  ⑤ Stash                   │
│  ③ Branches  │                             │
│              │──────────────────────────── │
│              │  [Diff / Staging Preview]   │
└───────────────────────────────────────────┘
```

---

## 面板與導覽

### 面板總覽

| 面板 | 快捷鍵 | 內容 |
|------|--------|------|
| Status | `1` | 目前分支、遠端同步狀態、最近 commit |
| Files | `2` | 變更檔案清單（unstaged / staged / untracked） |
| Branches | `3` | 本地分支、遠端分支、Tags |
| Commits | `4` | 本地 commit 歷史 |
| Stash | `5` | Stash 項目清單 |

### 通用導覽鍵

| 按鍵 | 功能 |
|------|------|
| `j` / `k` 或 `↑` / `↓` | 上下移動 |
| `h` / `l` 或 `←` / `→` | 左右切換面板 |
| `Tab` | 切換至下一個面板 |
| `Shift+Tab` | 切換至上一個面板 |
| `1`-`5` | 直接跳至指定面板 |
| `Enter` | 進入 / 展開項目 |
| `Esc` | 返回上一層 / 關閉對話框 |
| `q` | 退出 Lazygit |
| `?` | 顯示當前面板的快捷鍵說明 |
| `x` | 開啟當前面板的操作選單 |
| `R` | 重新整理畫面 |
| `/` | 搜尋過濾 |
| `[` / `]` | 在 diff 面板中切換分頁（Staged / Unstaged） |

---

## 完整快捷鍵參考

### Files 面板（`2`）

| 按鍵 | 功能 |
|------|------|
| `Space` | Stage / Unstage 當前檔案 |
| `a` | Stage / Unstage 所有檔案 |
| `c` | 提交（Commit）已 staged 的變更 |
| `C` | 使用編輯器撰寫 commit message |
| `w` | 提交選項選單（amend, no-verify 等） |
| `A` | 修改上一個 commit（amend） |
| `d` | 丟棄當前檔案的變更（Discard） |
| `D` | 丟棄變更選單（all, unstaged only 等） |
| `e` | 用編輯器開啟檔案 |
| `o` | 用系統預設程式開啟檔案 |
| `i` | 新增到 .gitignore |
| `r` | 重新整理 |
| `S` | Stash 變更選單 |
| `Enter` | Stage / Unstage 個別行（hunk staging） |
| `M` | 開啟 Merge / Rebase 選項 |
| `f` | Fetch |

### Hunk Staging（在 diff 預覽中）

在 Files 面板按 `Enter` 後，可以在 diff 預覽中做精確的 hunk/line staging：

| 按鍵 | 功能 |
|------|------|
| `Space` | Stage / Unstage 當前 hunk |
| `a` | Stage / Unstage 整個檔案 |
| `v` | 進入行選取模式 |
| `j` / `k` | 在行之間移動 |
| `Esc` | 退回 Files 面板 |

### Branches 面板（`3`）

| 按鍵 | 功能 |
|------|------|
| `Space` | Checkout 選取的分支 |
| `n` | 建立新分支 |
| `d` | 刪除分支 |
| `r` | Rebase 當前分支到選取的分支上 |
| `M` | Merge 選取的分支到當前分支 |
| `f` | Fast-forward 當前分支 |
| `c` | 以名稱 Checkout 分支 |
| `F` | Force Checkout |
| `R` | 重新命名分支 |
| `u` | 設定 upstream |
| `w` | 開啟 worktree 選單 |

### Commits 面板（`4`）

| 按鍵 | 功能 |
|------|------|
| `Space` | Checkout 選取的 commit |
| `r` | Reword：修改 commit message |
| `R` | 用編輯器修改 commit message |
| `s` | Squash：將此 commit 合併至上一個 |
| `f` | Fixup：合併至上一個（不保留 message） |
| `d` | Drop：刪除此 commit |
| `e` | Edit：標記此 commit 為 edit（interactive rebase） |
| `p` | Pick：還原為 pick 狀態 |
| `c` | Cherry-pick：複製選取的 commit |
| `C` | Cherry-pick 選取的範圍 |
| `v` | 貼上（放置）cherry-picked 的 commit |
| `g` | 開啟 Reset 選單（soft / mixed / hard） |
| `t` | 建立 Tag |
| `T` | 建立帶有訊息的 Tag |
| `o` | 用瀏覽器開啟 commit（GitHub/GitLab） |
| `y` | 複製 commit hash |
| `Enter` | 查看 commit 的檔案變更 |

### Stash 面板（`5`）

| 按鍵 | 功能 |
|------|------|
| `Space` | Apply stash（保留 stash） |
| `g` | Pop stash（apply 後刪除） |
| `d` | Drop stash（刪除） |
| `n` | 建立新 stash |
| `r` | Rename stash |
| `Enter` | 查看 stash 內容 |

### Status 面板（`1`）

| 按鍵 | 功能 |
|------|------|
| `Enter` | 切換到最近的 repo |
| `a` | 顯示所有分支的 log（全域） |
| `o` | 開啟設定檔 |
| `e` | 編輯設定檔 |
| `u` | 檢查更新 |

---

## 核心工作流

### 1) 檢查與整理變更

1. 進 `Files` 面板確認變更
2. 用 `Space` 只 stage 本次要提交的檔案
3. 需要精細控制時，按 `Enter` 進入 hunk staging，逐行 stage
4. 先看 diff 再 commit，避免把雜訊一起送出

### 2) 提交與同步

1. `c` 建立 commit（輸入 message 後 `Enter` 確認）
2. `f` fetch（確認遠端狀態）
3. `P` push 到遠端
4. `p` pull 最新變更

### 3) 分支與整線

1. `n` 建功能分支
2. 在 `Branches` 面板做 checkout（`Space`）
3. 需要整線時：選取目標分支後 `r`（rebase）或 `M`（merge）

### 4) 衝突處理

1. Merge/Rebase 遇到衝突時，Files 面板會標示衝突檔案
2. 選取衝突檔案按 `Enter`，進入衝突解決介面
3. 使用面板中的選項選擇保留哪一方的變更
4. 解決所有衝突後，`Space` stage 檔案，然後 `c` 繼續 commit

### 5) Cherry-Pick 工作流

1. 在 Commits 面板選取要複製的 commit
2. 按 `c` 複製（可多選）
3. Checkout 到目標分支
4. 按 `v` 貼上 commit

### 6) Stash 工作流

1. 在 Files 面板按 `S` 開啟 stash 選單
2. 選擇 stash 方式（全部 / 僅 staged / 僅 unstaged）
3. 切換分支處理其他事情
4. 回來後在 Stash 面板按 `Space`（apply）或 `g`（pop）還原

### 7) Interactive Rebase

1. 在 Commits 面板選取要開始 rebase 的 commit
2. 使用 `e`（edit）、`s`（squash）、`f`（fixup）、`d`（drop）標記各 commit
3. 標記完成後，Lazygit 會自動執行 interactive rebase
4. 遇到衝突時按照衝突處理流程解決

---

## 進階操作

### 風險提示

高風險操作請先確認：

| 操作 | 風險等級 | 說明 |
|------|----------|------|
| Force Checkout (`F`) | 高 | 丟失工作區未保存變更 |
| Commit without hook (`w` → no-verify) | 中 | 跳過 pre-commit 驗證 |
| Interactive Rebase | 中-高 | 改寫歷史，推送前要特別檢查 |
| Hard Reset (`g` → hard) | 高 | 不可復原地丟棄 commit |
| Force Push | 高 | 覆蓋遠端歷史 |

### 自訂指令 (Custom Commands)

在設定檔中定義自訂指令，可在 Lazygit 中快速執行：

```yaml
# config.yml
customCommands:
  - key: "<c-p>"
    description: "Push to origin with --force-with-lease"
    command: "git push --force-with-lease"
    context: "global"
    loadingText: "Force pushing..."
  - key: "C"
    description: "Commit with conventional format"
    command: "git commit -m '{{.Form.Type}}({{.Form.Scope}}): {{.Form.Message}}'"
    context: "files"
    prompts:
      - type: "menu"
        title: "Type"
        key: "Type"
        options:
          - name: "feat"
            value: "feat"
          - name: "fix"
            value: "fix"
          - name: "refactor"
            value: "refactor"
          - name: "docs"
            value: "docs"
          - name: "chore"
            value: "chore"
      - type: "input"
        title: "Scope"
        key: "Scope"
        initialValue: ""
      - type: "input"
        title: "Message"
        key: "Message"
        initialValue: ""
```

### Patch 操作

在 Commits 面板中，可以對 commit 中的部分變更建立 patch：

1. 選取 commit 按 `Enter` 查看檔案
2. 選取檔案按 `Enter` 查看 diff
3. `Space` 選取要加入 patch 的 hunk
4. 按 `Ctrl+p` 開啟 patch 操作選單

### Bisect

Lazygit 支援互動式 bisect：

1. 在 Commits 面板按 `b` 開始 bisect
2. 標記 good / bad commit
3. Lazygit 會自動導覽至中間 commit 供你測試

---

## 推薦設定

```yaml
# ~/.config/lazygit/config.yml

gui:
  # 語言（en, zh-TW, ja 等）
  language: "auto"
  # 主題（dark, light）
  theme:
    activeBorderColor:
      - green
      - bold
    inactiveBorderColor:
      - white
    selectedLineBgColor:
      - blue
  # 顯示檔案圖示（需要 Nerd Font）
  nerdFontsVersion: "3"
  # 顯示隨機提示
  showRandomTip: false
  # 顯示底部面板
  showBottomLine: true
  # 分割視窗方向（auto, vertical, horizontal）
  splitDiff: "auto"
  # 捲動速度
  scrollHeight: 2
  # 側邊面板寬度（0.1-0.5）
  sidePanelWidth: 0.3333

git:
  # 自動 fetch 間隔（秒，0 為停用）
  autoFetch: 60
  # 預設 merge/rebase 偏好
  pull:
    mode: "rebase"
  # Log 指令
  log:
    showGraph: "always"
    order: "topo-order"
  # commit 時跳過 hook
  skipHookPrefix: "WIP"

os:
  # 編輯器設定
  editPreset: "vscode"
  # 或自訂：
  # edit: "code --wait {{filename}}"
  # editAtLine: "code --wait --goto {{filename}}:{{line}}"

# 確認對話框
notARepository: "prompt"
promptToReturnFromSubprocess: false
```

### 編輯器預設值

| 預設值 | 編輯器 |
|--------|--------|
| `vscode` | VS Code |
| `nvim` | Neovim |
| `vim` | Vim |
| `emacs` | Emacs |
| `nano` | Nano |
| `sublime` | Sublime Text |

---

## 與開發工具協作

### 搭配 Zellij

建議在 Zellij layout 中固定一個 tab 給 Lazygit：

```kdl
// ~/.config/zellij/layouts/dev.kdl
layout {
    tab name="Code" focus=true {
        pane
    }
    tab name="Git" {
        pane {
            command "lazygit"
        }
    }
}
```

### 搭配 VS Code

推薦節奏：

1. 在 Lazygit 完成「乾淨 commit」（hunk staging + squash）
2. 切到 VS Code 做 final review（查看完整 diff、註解）
3. 回到 Lazygit 做最後同步與推送

VS Code 相關設定（在 Lazygit config.yml）：

```yaml
os:
  editPreset: "vscode"
```

### 搭配 Claude Code / OpenCode

在 AI 輔助開發流程中，Lazygit 適合作為：

- AI 產出程式碼後的 staging 整理站（用 hunk staging 精選變更）
- Commit message 最終確認點
- Interactive rebase 整理 WIP commits 為乾淨歷史

---

## 常見問題

### 套件版本和官方 release 不一致

- 套件管理器更新頻率可能落後，需以 `lazygit --version` 實測。
- 使用 `go install` 可獲得最新版本。

### 看不到自訂設定

- 先確認 config 是否放在正確平台路徑。
- 檢查是否有 repo-local 設定覆蓋全域設定。
- 在 Status 面板按 `o` 可直接開啟設定檔確認路徑。

### 分支操作出現意外

- 先在 Files 面板確認是否有未提交變更，再做 checkout/rebase。
- 使用 Stash（`S`）暫存變更後再操作。

### 中文 / Unicode 顯示問題

- 確認終端模擬器使用支援 Unicode 的字型（推薦 Nerd Font）。
- 在設定中啟用 `gui.nerdFontsVersion: "3"` 可顯示檔案圖示。

### 快捷鍵與終端衝突

- 若使用 Zellij，切記先按 `Ctrl+g` 進入 Locked 模式，再操作 Lazygit。
- 或者在 Zellij 的 Normal 模式下操作即可（Zellij 的 Normal 模式會將按鍵傳遞至程式）。

---

## 參考資料

- 官方 README：https://github.com/jesseduffield/lazygit
- 官方設定文件：https://github.com/jesseduffield/lazygit/blob/master/docs/Config.md
- 官方快捷鍵文件：https://github.com/jesseduffield/lazygit/blob/master/docs/keybindings/Keybindings_en.md
- 自訂指令文件：https://github.com/jesseduffield/lazygit/blob/master/docs/Custom_Command_Keybindings.md
- Releases：https://github.com/jesseduffield/lazygit/releases
