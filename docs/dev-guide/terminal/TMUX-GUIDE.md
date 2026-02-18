# tmux 終端多工器完整指南

## 目錄

- [簡介與特色](#簡介與特色)
- [安裝方式](#安裝方式)
- [核心概念](#核心概念)
- [基本操作](#基本操作)
- [快捷鍵速查表](#快捷鍵速查表)
- [設定檔](#設定檔)
- [推薦設定](#推薦設定)
- [Plugin 管理（TPM）](#plugin-管理tpm)
- [Session 管理](#session-管理)
- [與 Zellij 比較](#與-zellij-比較)
- [搭配工具建議](#搭配工具建議)
- [參考資源](#參考資源)

---

## 簡介與特色

tmux（**t**erminal **mu**ltiple**x**er）是最經典、最廣泛使用的終端多工器。它讓你在一個終端視窗中管理多個 session、window 和 pane，並且可以在 SSH 斷線後無縫恢復工作。

### 核心特色

- **C 語言建構**：以 C 語言開發，極致輕量，幾乎沒有依賴。
- **伺服器必備**：幾乎所有 Linux 發行版預裝或可立即安裝，是遠端工作的標準工具。
- **SSH 斷線恢復**：detach/attach 機制讓你在網路中斷後能完整恢復工作環境。
- **成熟生態系統**：超過 20 年的歷史，擁有大量 plugin、設定範例和社群資源。
- **高度可自訂**：從快捷鍵到狀態列，幾乎所有行為都可透過 `tmux.conf` 設定。
- **穩定可靠**：API 變動極少，設定檔可長期使用不需修改。
- **Scripting 支援**：完整的命令介面，可透過 shell script 自動化工作流。

---

## 安裝方式

### macOS

```bash
brew install tmux
```

### Linux

```bash
# Ubuntu / Debian
sudo apt install tmux

# Fedora / RHEL
sudo dnf install tmux

# Arch Linux
sudo pacman -S tmux

# Alpine
sudo apk add tmux
```

### Windows（透過 WSL）

tmux 不原生支援 Windows，但可在 WSL（Windows Subsystem for Linux）中使用：

```bash
# 在 WSL 中
sudo apt install tmux
```

### 從原始碼編譯

```bash
# 安裝依賴
sudo apt install libevent-dev ncurses-dev build-essential bison pkg-config

# 下載並編譯
git clone https://github.com/tmux/tmux.git
cd tmux
sh autogen.sh
./configure && make
sudo make install
```

### 驗證安裝

```bash
tmux -V
# tmux 3.5a
```

---

## 核心概念

### 架構階層

tmux 採用 Server → Session → Window → Pane 的四層架構：

```
tmux server
├── Session: "work"
│   ├── Window 1: "editor"    [active]
│   │   ├── Pane 1: vim        [active]
│   │   └── Pane 2: terminal
│   ├── Window 2: "server"
│   │   └── Pane 1: npm start
│   └── Window 3: "git"
│       └── Pane 1: lazygit
└── Session: "personal"
    └── Window 1: "shell"
        └── Pane 1: zsh
```

| 層級 | 說明 | 類比 |
|------|------|------|
| **Server** | tmux 背景程序，管理所有 session | 作業系統 |
| **Session** | 一組相關的 window，可 detach/attach | 桌面/工作區 |
| **Window** | 佔滿整個終端畫面的容器，包含一或多個 pane | 瀏覽器分頁 |
| **Pane** | window 中的子區域，各自執行獨立的 shell | 分割視窗 |

### Prefix Key 概念

tmux 使用「prefix key + 操作鍵」的兩段式快捷鍵機制：

1. 先按下 prefix key（預設 `Ctrl+B`，推薦改為 `Ctrl+A`）
2. 放開後按下操作鍵（如 `c` 建立 window、`|` 分割 pane）

這種設計避免了與終端程式的快捷鍵衝突。tmux 只在你按下 prefix 後才攔截按鍵，平時所有輸入直接傳遞給終端程式。

### 與其他多工器的對應

| 概念 | tmux | Zellij | WezTerm |
|------|------|--------|---------|
| 快捷鍵觸發 | Prefix key | 模式切換（Ctrl+X） | Key Table |
| 面板分割 | Pane | Pane | Pane |
| 分頁 | Window | Tab | Tab |
| 工作區 | Session | Session | Window |
| 斷線恢復 | 原生 detach/attach | 內建 resurrect | 不支援 |

---

## 基本操作

### Session 操作

```bash
# 建立新 session
tmux new-session -s work
# 簡寫
tmux new -s work

# 列出所有 session
tmux list-sessions
# 簡寫
tmux ls

# 附加到現有 session
tmux attach-session -t work
# 簡寫
tmux a -t work

# 附加到最近的 session
tmux a

# Detach（在 tmux 內）
# prefix + d

# 終止指定 session
tmux kill-session -t work

# 終止所有 session
tmux kill-server

# 重新命名 session（在 tmux 內）
# prefix + $
```

### Window 操作

所有 window 操作皆在 tmux 內，以 prefix key 起手：

| 操作 | 快捷鍵 | 說明 |
|------|---------|------|
| 建立 window | `prefix + c` | 新建 window（保留當前路徑） |
| 關閉 window | `prefix + &` | 關閉當前 window（會確認） |
| 重新命名 | `prefix + ,` | 為當前 window 命名 |
| 上一個 | `prefix + [` | 切換到上一個 window |
| 下一個 | `prefix + ]` | 切換到下一個 window |
| 依編號切換 | `prefix + 1-9` | 切換到指定編號 window |
| 最近的 window | `prefix + Space` | 切換到上次使用的 window |
| 列出所有 | `prefix + w` | 互動式選擇 window |

### Pane 操作

| 操作 | 快捷鍵 | 說明 |
|------|---------|------|
| 水平分割 | `prefix + \|` | 左右分割（推薦設定） |
| 垂直分割 | `prefix + -` | 上下分割（推薦設定） |
| 關閉 pane | `prefix + x` | 關閉當前 pane（會確認） |
| 導航至左方 | `prefix + h` | Vim 風格（推薦設定） |
| 導航至下方 | `prefix + j` | Vim 風格（推薦設定） |
| 導航至上方 | `prefix + k` | Vim 風格（推薦設定） |
| 導航至右方 | `prefix + l` | Vim 風格（推薦設定） |
| 放大左方 | `prefix + H` | 連續調整（推薦設定） |
| 放大下方 | `prefix + J` | 連續調整（推薦設定） |
| 放大上方 | `prefix + K` | 連續調整（推薦設定） |
| 放大右方 | `prefix + L` | 連續調整（推薦設定） |
| 全螢幕切換 | `prefix + z` | Zoom 當前 pane |
| 顯示編號 | `prefix + q` | 短暫顯示 pane 編號 |
| 交換（向下） | `prefix + >` | 與下方 pane 交換（推薦設定） |
| 交換（向上） | `prefix + <` | 與上方 pane 交換（推薦設定） |

---

## 快捷鍵速查表

> 以下使用推薦設定（prefix = `Ctrl+A`）。標記「預設」的為 tmux 原始設定，標記「自訂」的為推薦設定新增。
> 在 tmux 中按 `prefix + ?` 可顯示互動式速查彈窗。

### Session

| 快捷鍵 | 功能 | 來源 |
|---------|------|------|
| `prefix + d` | Detach（脫離 session） | 預設 |
| `prefix + s` | 列出所有 session（互動式切換） | 預設 |
| `prefix + $` | 重新命名當前 session | 預設 |
| `prefix + (` | 切換至上一個 session | 預設 |
| `prefix + )` | 切換至下一個 session | 預設 |

### Window

| 快捷鍵 | 功能 | 來源 |
|---------|------|------|
| `prefix + c` | 新建 window | 預設 |
| `prefix + ,` | 重新命名 window | 預設 |
| `prefix + &` | 關閉 window | 預設 |
| `prefix + w` | 列出所有 window（互動式） | 預設 |
| `prefix + 1-9` | 切換至指定編號 | 預設 |
| `prefix + [` | 上一個 window | 自訂 |
| `prefix + ]` | 下一個 window | 自訂 |
| `prefix + Space` | 最近使用的 window | 自訂 |

### Pane

| 快捷鍵 | 功能 | 來源 |
|---------|------|------|
| `prefix + \|` | 水平分割（左右） | 自訂 |
| `prefix + -` | 垂直分割（上下） | 自訂 |
| `prefix + x` | 關閉 pane | 預設 |
| `prefix + z` | 全螢幕切換 | 預設 |
| `prefix + q` | 顯示 pane 編號 | 預設 |
| `prefix + h/j/k/l` | Vim 風格面板導航 | 自訂 |
| `prefix + H/J/K/L` | Vim 風格調整大小 | 自訂 |
| `prefix + >` | 與下方 pane 交換 | 自訂 |
| `prefix + <` | 與上方 pane 交換 | 自訂 |

### Copy Mode（Vi 模式）

| 快捷鍵 | 功能 | 來源 |
|---------|------|------|
| `prefix + v` | 進入 copy mode | 自訂 |
| `v` | 開始選取 | 自訂 |
| `V` | 整行選取 | 自訂 |
| `Ctrl+v` | 矩形選取切換 | 自訂 |
| `y` | 複製選取並離開 | 自訂 |
| `/` | 搜尋（向前） | 預設 |
| `?` | 搜尋（向後） | 預設 |
| `n` | 下一個搜尋結果 | 預設 |
| `N` | 上一個搜尋結果 | 預設 |
| `q` | 離開 copy mode | 預設 |

### 其他

| 快捷鍵 | 功能 | 來源 |
|---------|------|------|
| `prefix + :` | 命令提示字元 | 預設 |
| `prefix + ?` | 快捷鍵速查彈窗 | 自訂 |
| `prefix + r` | 重新載入設定檔 | 自訂 |
| `prefix + I` | 安裝 TPM plugin | TPM |
| `prefix + U` | 更新 TPM plugin | TPM |

### 與 Zellij / WezTerm 快捷鍵對照

| 功能 | tmux（推薦設定） | Zellij | WezTerm |
|------|-------------------|--------|---------|
| 水平分割 | `prefix + \|` | `Ctrl+p` → `d` | `Ctrl+Shift+D` |
| 垂直分割 | `prefix + -` | `Ctrl+p` → `n` | `Ctrl+Shift+%` |
| 面板導航 | `prefix + h/j/k/l` | `Ctrl+p` → `h/j/k/l` | `Ctrl+Shift+方向鍵` |
| 關閉面板 | `prefix + x` | `Ctrl+p` → `x` | `Ctrl+Shift+W` |
| 全螢幕 | `prefix + z` | `Ctrl+p` → `f` | `Ctrl+Shift+Z` |
| 新建分頁 | `prefix + c` | `Ctrl+t` → `n` | `Ctrl+Shift+T` |
| 切換分頁 | `prefix + 1-9` | `Ctrl+t` → `1-9` | `Ctrl+1-9` |
| 離開/Detach | `prefix + d` | `Ctrl+o` → `d` | 不支援 |
| 搜尋 | `prefix + v` → `/` | `Ctrl+s` → `s` | `Ctrl+Shift+F` |
| 鍵盤提示 | `prefix + ?` | 畫面底部常駐 | `Ctrl+Shift+L` |

---

## 設定檔

### 路徑

tmux 依以下順序尋找設定檔（使用找到的第一個）：

1. `~/.tmux.conf`（傳統路徑，最常用）
2. `~/.config/tmux/tmux.conf`（XDG 相容路徑，tmux 3.1+）

### 基本語法

```bash
# set：設定伺服器或 session 選項
set -g option value        # -g 表示全域（global）

# setw / set-window-option：設定 window 選項
setw -g option value

# bind-key：綁定快捷鍵
bind key command           # 等同 bind-key key command
bind -r key command        # -r 允許在 repeat-time 內連續按
bind -T table key command  # 在指定 key table 中綁定

# unbind-key：解除快捷鍵
unbind key

# if-shell：條件判斷（依 shell 指令回傳值）
if-shell "condition" "command-if-true" "command-if-false"

# run-shell：執行 shell 指令
run-shell "command"

# source-file：載入其他設定檔
source-file /path/to/file.conf
```

### 重要選項說明

| 選項 | 說明 | 推薦值 |
|------|------|--------|
| `default-terminal` | 終端類型 | `"tmux-256color"` |
| `terminal-overrides` | True Color 覆寫 | `",*256col*:Tc"` |
| `mouse` | 滑鼠支援 | `on` |
| `base-index` | Window 起始編號 | `1` |
| `pane-base-index` | Pane 起始編號 | `1` |
| `escape-time` | Esc 鍵延遲（ms） | `0` |
| `history-limit` | 捲動歷史行數 | `50000` |
| `renumber-windows` | 自動重新編號 | `on` |
| `mode-keys` | Copy mode 按鍵風格 | `vi` |
| `set-clipboard` | 系統剪貼簿 | `on` |

---

## 推薦設定

完整設定檔位於 [`config/tmux.conf`](./config/tmux.conf)，以下為架構總覽與重點說明。

### 設定架構

```
tmux.conf
├── 一般設定 .......... True Color、滑鼠、編號、歷史
├── Prefix 鍵 ......... Ctrl+A（取代預設 Ctrl+B）
├── Pane 操作 ......... | / - 分割、hjkl 導航、HJKL 調整大小
├── Window 操作 ....... [] 切換、Space 最近、c 新建
├── Copy Mode ......... Vi 模式、系統剪貼簿整合
├── 狀態列 ............ Catppuccin Mocha 配色
├── 外觀設定 .......... 面板邊框、訊息列顏色
├── 速查彈窗 .......... prefix + ? 顯示互動式速查表
└── TPM Plugin ........ sensible / resurrect / continuum / yank
```

### Prefix 鍵：Ctrl+A

推薦將 prefix 從預設的 `Ctrl+B` 改為 `Ctrl+A`，理由：

- `Ctrl+A` 比 `Ctrl+B` 更容易單手按到（A 在主列，B 需伸手）
- 源自 GNU Screen 的傳統，許多老手已習慣此鍵位
- 雙按 `Ctrl+A` 可將實際的 Ctrl+A 送入終端程式（如在 shell 中跳到行首）

```bash
unbind C-b
set -g prefix C-a
bind C-a send-prefix
```

### Vim 風格導航

所有方向操作統一使用 `h/j/k/l`，與 Vim/Neovim 操作一致：

```bash
# 面板導航
bind h select-pane -L    # 左
bind j select-pane -D    # 下
bind k select-pane -U    # 上
bind l select-pane -R    # 右

# 面板大小調整（-r 允許連續按）
bind -r H resize-pane -L 5
bind -r J resize-pane -D 5
bind -r K resize-pane -U 5
bind -r L resize-pane -R 5
```

### 直覺式分割鍵

用 `|` 和 `-` 取代難記的 `%` 和 `"`，視覺上直接對應分割方向：

```bash
# | 看起來就是左右分割
bind | split-window -h -c "#{pane_current_path}"
# - 看起來就是上下分割
bind - split-window -v -c "#{pane_current_path}"
```

`-c "#{pane_current_path}"` 確保新 pane 繼承當前工作目錄。

### 系統剪貼簿整合

設定檔使用 `if-shell` 自動偵測平台，選擇正確的剪貼簿指令：

| 平台 | 剪貼簿指令 |
|------|------------|
| macOS | `pbcopy` |
| Linux（X11） | `xclip -selection clipboard` |
| Linux（Wayland） | `wl-copy` |

### Catppuccin Mocha 狀態列

推薦設定採用手動配色方式實現 Catppuccin Mocha 主題的狀態列，不依賴外部主題 plugin：

```
┌────────────────────────────────────────────────────────────┐
│ ▌work▐           1:editor  2:server  3:git      2025-01-01│
│  Session                    Windows                  Time  │
└────────────────────────────────────────────────────────────┘
```

- 左側：醒目藍底顯示 session 名稱
- 中間：置中對齊的 window 列表，當前 window 高亮
- 右側：日期與時間

### 彈出式速查表

按 `prefix + ?` 會顯示一個互動式彈窗，列出所有常用快捷鍵（需 tmux 3.2+ 的 `display-popup` 功能）。按 Enter 或 q 即可關閉。

---

## Plugin 管理（TPM）

[TPM](https://github.com/tmux-plugins/tpm)（Tmux Plugin Manager）是 tmux 的標準 plugin 管理器。

### 安裝 TPM

```bash
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
```

安裝後重新載入 tmux 設定：

```bash
tmux source-file ~/.tmux.conf
```

### TPM 操作快捷鍵

| 快捷鍵 | 功能 |
|---------|------|
| `prefix + I` | 安裝設定檔中宣告的 plugin |
| `prefix + U` | 更新所有 plugin |
| `prefix + Alt+u` | 移除不在設定檔中的 plugin |

### 推薦 Plugin

#### tmux-sensible

提供一組合理的預設值，適合所有 tmux 使用者：

```bash
set -g @plugin 'tmux-plugins/tmux-sensible'
```

包含：UTF-8 支援、更大的 history、更快的按鍵回應等。

#### tmux-resurrect

Session 持久化：儲存並恢復 tmux 的完整工作環境（window layout、pane 內容、工作目錄）。

```bash
set -g @plugin 'tmux-plugins/tmux-resurrect'
```

| 操作 | 快捷鍵 |
|------|---------|
| 儲存 | `prefix + Ctrl+s` |
| 還原 | `prefix + Ctrl+r` |

#### tmux-continuum

自動定時儲存 session（搭配 tmux-resurrect），無需手動操作：

```bash
set -g @plugin 'tmux-plugins/tmux-continuum'
set -g @continuum-save-interval '15'  # 每 15 分鐘自動儲存
```

#### tmux-yank

跨平台系統剪貼簿整合：

```bash
set -g @plugin 'tmux-plugins/tmux-yank'
```

自動偵測 macOS（pbcopy）、Linux X11（xclip）、Linux Wayland（wl-copy）、WSL（clip.exe）等環境。

### 在設定檔中宣告 Plugin

```bash
# 設定檔中
set -g @plugin 'tmux-plugins/tpm'
set -g @plugin 'tmux-plugins/tmux-sensible'
set -g @plugin 'tmux-plugins/tmux-resurrect'

# 此行必須在設定檔最底部
run '~/.tmux/plugins/tpm/tpm'
```

---

## Session 管理

### tmux-resurrect：手動存檔/還原

tmux-resurrect 能儲存以下狀態：

- 所有 session、window、pane 的 layout
- 每個 pane 的工作目錄
- 部分程式的執行狀態（vim、less、man 等）

```bash
# 手動儲存（在 tmux 內）
# prefix + Ctrl+s
# 儲存位置：~/.tmux/resurrect/

# 手動還原
# prefix + Ctrl+r
```

### tmux-continuum：自動備份

搭配 tmux-resurrect 使用，提供自動定時儲存功能：

```bash
# 設定自動儲存間隔（分鐘）
set -g @continuum-save-interval '15'

# 可選：tmux 啟動時自動還原上次 session
# set -g @continuum-restore 'on'
```

### tmuxinator：專案 Layout 範本

[tmuxinator](https://github.com/tmuxinator/tmuxinator) 使用 YAML 定義專案的 tmux layout，一個指令即可啟動完整的開發環境。

```bash
# 安裝
gem install tmuxinator

# 建立專案範本
tmuxinator new my-project
```

範本範例（`~/.config/tmuxinator/my-project.yml`）：

```yaml
name: my-project
root: ~/Code/my-project

windows:
  - editor:
      layout: main-vertical
      panes:
        - nvim .
        - # 空白 shell
  - server:
      panes:
        - npm run dev
  - git:
      panes:
        - lazygit
```

```bash
# 啟動專案
tmuxinator start my-project
# 簡寫
mux start my-project
```

---

## 與 Zellij 比較

| 比較項目 | tmux | Zellij |
|----------|------|--------|
| **實作語言** | C | Rust |
| **學習曲線** | 較高，需記憶或查閱快捷鍵 | 較低，UI 內建快捷鍵提示 |
| **預設體驗** | 需要手動設定才能獲得良好體驗 | 開箱即用，預設帶有 status bar 與 tab bar |
| **設定格式** | 自訂格式（tmux.conf） | KDL（結構化、易讀） |
| **Plugin 系統** | TPM + Shell script 為主 | WASM plugin，語言無關 |
| **Layout 系統** | 自訂格式，或搭配 tmuxinator（YAML） | KDL 格式，支援巢狀定義與 plugin |
| **Session 管理** | 原生 detach/attach，resurrect 需外掛 | 內建 detach / attach / resurrect |
| **浮動面板** | tmux 3.3+ popup | 原生支援 |
| **效能** | 優秀（C，輕量） | 優秀（Rust，記憶體安全） |
| **生態系統** | 成熟，大量外掛與設定範例 | 較新，社群成長中 |
| **遠端伺服器** | 幾乎所有伺服器皆預裝 | 需另行安裝 |
| **穩定性** | 非常穩定，API 變動極少 | 持續開發中，偶有 breaking change |

### 選擇建議

- **選擇 tmux**：需要在各種遠端伺服器上使用、已有成熟的 tmux 設定、重視長期穩定性與生態系統、需要深度 scripting 自動化。
- **選擇 Zellij**：偏好現代化的開箱即用體驗、不想花時間設定、喜歡 UI 內建的快捷鍵提示、有興趣開發 WASM plugin。

---

## 搭配工具建議

### 終端模擬器

tmux 搭配**輕量級**終端模擬器效果最佳，因為多工管理已由 tmux 負責：

- **Alacritty**：以 Rust 撰寫的 GPU 加速終端，輕量快速。Alacritty + tmux 是最經典的組合。
- **Ghostty**：新一代終端模擬器，原生效能優秀。
- **kitty**：功能豐富的 GPU 加速終端，支援圖片顯示。
- **WezTerm**：內建多工功能，搭配 tmux 時建議關閉 WezTerm 自身的 tab/pane。

> 搭配建議：使用 tmux 時，讓終端模擬器只負責「渲染」，將分頁、分割視窗、session 管理全權交給 tmux。

### Shell Prompt

- **Starship**：跨 shell 的高速 prompt（Rust 撰寫），可在 prompt 中顯示 Git 狀態、語言版本等資訊。

```bash
# 安裝
brew install starship

# 在 ~/.zshrc 或 ~/.bashrc 加入
eval "$(starship init zsh)"
```

### 自動啟動設定

若希望開啟終端時自動進入 tmux，可在 shell 設定檔中加入：

```bash
# ~/.zshrc 或 ~/.bashrc
# 僅在非 tmux 環境下自動啟動（避免巢狀）
if [ -z "$TMUX" ]; then
    tmux new-session -A -s main
fi
```

`-A` 選項表示若名為 `main` 的 session 已存在則直接 attach，否則建立新的。

### 搭配常用的 CLI 工具

| 工具 | 說明 | 搭配方式 |
|------|------|----------|
| `lazygit` | 終端 Git UI | 專用 window 執行 |
| `lsd` / `eza` | 現代化 ls 替代品 | 檔案瀏覽 pane 使用 |
| `bat` | 帶有語法高亮的 cat | 在 pane 中瀏覽檔案 |
| `fd` | 快速檔案搜尋 | 在專用 pane 中搜尋 |
| `ripgrep` | 快速文字搜尋 | 在專用 pane 中全文搜尋 |
| `btop` / `htop` | 系統監控 | 專用 window 監控系統 |
| `zoxide` | 智慧目錄切換 | 跨 pane 快速切換目錄 |
| `fzf` | 模糊搜尋 | 搭配 tmux popup 使用 |
| `yazi` | 終端檔案管理器 | 專用 pane 瀏覽檔案 |

---

## 參考資源

- GitHub 倉庫：https://github.com/tmux/tmux
- 官方 Wiki：https://github.com/tmux/tmux/wiki
- tmux man page：`man tmux`
- TPM（Plugin Manager）：https://github.com/tmux-plugins/tpm
- tmux-resurrect：https://github.com/tmux-plugins/tmux-resurrect
- tmux-continuum：https://github.com/tmux-plugins/tmux-continuum
- tmuxinator：https://github.com/tmuxinator/tmuxinator
- Catppuccin 主題：https://github.com/catppuccin/tmux
- 推薦設定檔：[config/tmux.conf](./config/tmux.conf)
