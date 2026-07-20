# tmux 終端多工器完整指南

## 目錄

- [簡介與特色](#簡介與特色)
- [安裝方式](#安裝方式)
- [快速安裝：自動恢復](#快速安裝自動恢復)
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

## 快速安裝：自動恢復

本節提供從乾淨系統一路完成 `tmux-resurrect` 與 `tmux-continuum` 的安裝流程。完成後會每 15 分鐘自動儲存，啟動新的 tmux server 時自動恢復，並保存最新一次的 Pane 終端歷史。

### 1. 安裝前置套件

TPM 本身需要 tmux 1.9 以上、Git 與 Bash。若要直接採用本指南的完整推薦設定，則需要 tmux 3.2 以上，因為設定檔使用了 `display-popup`：

```bash
# Ubuntu / Debian
sudo apt update
sudo apt install tmux git bash

# Fedora / RHEL
sudo dnf install tmux git bash

# Arch Linux
sudo pacman -S tmux git bash

# Alpine
sudo apk add tmux git bash

# macOS
brew install tmux git
```

確認三個指令都可用：

```bash
tmux -V
git --version
bash --version
```

### 2. 安裝 TPM

本指南統一使用傳統的 `~/.tmux.conf` 與 `~/.tmux/plugins` 路徑：

```bash
mkdir -p ~/.tmux/plugins
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
if [ -x ~/.tmux/plugins/tpm/tpm ]; then
    echo "TPM 安裝完成"
else
    echo "TPM 啟動檔不存在或無法執行"
fi
```

若 `git clone` 回報目標目錄已存在，先執行後續檢查。已正常安裝時不需重複執行 `git clone`；若目錄不完整，可保留舊目錄後重新安裝：

```bash
mv ~/.tmux/plugins/tpm ~/.tmux/plugins/tpm.incomplete."$(date +%Y%m%d%H%M%S)"
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
```

### 3. 加入自動恢復設定

把以下區塊加入 `~/.tmux.conf`。若已有設定檔，請合併，不要整份覆寫：

```bash
# 完整 Pane scrollback 最多保留 50000 行；只影響之後新建的 Pane
set -g history-limit 50000

set -g @plugin 'tmux-plugins/tpm'
set -g @plugin 'tmux-plugins/tmux-resurrect'
set -g @resurrect-delete-backup-after '30'
set -g @resurrect-capture-pane-contents 'on'
set -g @resurrect-pane-contents-area 'full'

# continuum 必須是 plugin 清單的最後一個
set -g @plugin 'tmux-plugins/tmux-continuum'
set -g @continuum-save-interval '15'
set -g @continuum-restore 'on'

# TPM 初始化必須位於整份設定檔最底部
run '~/.tmux/plugins/tpm/tpm'
```

若 `tmux -V` 顯示 3.2 以上，且目前位於本儲存庫根目錄，也可在目標檔不存在時採用完整推薦設定。較舊版本請只合併上一個最小自動恢復區塊：

```bash
if [ -e ~/.tmux.conf ]; then
    echo "~/.tmux.conf 已存在，請手動合併設定，不要直接覆寫。"
else
    cp docs/dev-guide/terminal/config/tmux.conf ~/.tmux.conf
    echo "已建立 ~/.tmux.conf。"
fi
```

### 4. 首次啟動或重新載入

先確認 tmux server 是否已執行：

```bash
tmux ls
```

依結果選一種方式，不要兩種都執行：

```bash
# 顯示「no server running」或 socket 不存在：啟動第一個 session
tmux new -s main

# 已列出現有 session：重新載入設定
tmux source-file ~/.tmux.conf
```

`tmux source-file` 只會要求**已存在的 tmux server**重新讀取設定，不會建立 server。全新安裝時直接執行它，便會看到 `/tmp/tmux-UID/default` 或 `/private/tmp/tmux-UID/default` 不存在的錯誤。

### 5. 安裝 Plugin

進入 tmux 後，按下實際使用的 prefix，放開後再按大寫 `I`：

- tmux 預設：`Ctrl+B`，放開，再按 `Shift+I`
- 本指南推薦設定：`Ctrl+A`，放開，再按 `Shift+I`

等待畫面顯示安裝完成，再檢查目錄與設定值：

```bash
plugin_dir="$(tmux show-environment -g TMUX_PLUGIN_MANAGER_PATH 2>/dev/null | sed -n 's/^TMUX_PLUGIN_MANAGER_PATH=//p')"
plugin_dir="${plugin_dir%/}"
if [ -z "$plugin_dir" ]; then
    echo "TPM 尚未載入，請回到常見安裝錯誤檢查"
else
    echo "$plugin_dir"
    test -d "$plugin_dir/tmux-resurrect" && echo "resurrect 已安裝"
    test -d "$plugin_dir/tmux-continuum" && echo "continuum 已安裝"
fi
tmux show-options -gqv @continuum-save-interval
tmux show-options -gqv @continuum-restore
```

第一行會顯示 TPM 實際管理的 Plugin 目錄；最後兩行應依序輸出 `15` 與 `on`。

### 6. 建立第一份快照

在 tmux 內按 `prefix + Ctrl+s`。首次快照應主動建立，不必先等 15 分鐘；詳細檢查方式見「[首次使用與驗證](#首次使用與驗證)」。

### 常見安裝錯誤

| 錯誤 | 原因與處理 |
|------|------------|
| `error connecting to .../default (No such file or directory)` | tmux server 尚未啟動。執行 `tmux new -s main`，不要把 `source-file` 當成啟動指令 |
| `'~/.tmux/plugins/tpm/tpm' returned 127` | Shell 找不到 TPM 啟動檔，或其 shebang 找不到 Bash。執行 `command -v bash` 與 `ls -l ~/.tmux/plugins/tpm/tpm` 檢查，再補裝 Bash 或重新安裝 TPM |
| `prefix + I` 沒有反應 | 確認使用正確的 prefix、大寫 `I`、TPM 初始化位於設定檔底部，並確認重新載入的是實際使用的設定檔 |

TPM 啟動檔與其管理的 Plugin 目錄是兩個不同位置：

- `run` 必須指向 TPM 啟動檔的實際安裝位置；依官方基本安裝可維持 `~/.tmux/plugins/tpm/tpm`。
- 若設定檔位於 `${XDG_CONFIG_HOME:-$HOME/.config}/tmux/tmux.conf`，TPM 預設會把其他 Plugin 安裝到 `${XDG_CONFIG_HOME:-$HOME/.config}/tmux/plugins`。
- 以 `tmux show-environment -g TMUX_PLUGIN_MANAGER_PATH` 查詢實際 Plugin 目錄，不要假設一定是 `~/.tmux/plugins`。

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

> 以下使用推薦設定（prefix = `Ctrl+A`）。
> 在 tmux 中按 `prefix + ?` 可顯示互動式速查彈窗。
>
> **欄位說明：**
> - **來源**：`預設` = tmux 原始設定、`自訂` = 推薦設定新增/覆寫、`TPM` = Plugin 提供
> - **預設該鍵功能**：該按鍵在 tmux 預設設定中的原始行為（`—` 表示該鍵預設未綁定，「相同」表示未修改）

### Session

| 快捷鍵 | 功能（推薦設定） | 來源 | 預設該鍵功能 |
|---------|------------------|------|--------------|
| `prefix + d` | Detach（脫離 session） | 預設 | 相同 |
| `prefix + s` | 列出所有 session（互動式切換） | 預設 | 相同 |
| `prefix + $` | 重新命名當前 session | 預設 | 相同 |
| `prefix + (` | 切換至上一個 session | 預設 | 相同 |
| `prefix + )` | 切換至下一個 session | 預設 | 相同 |
| `prefix + D` | 選擇要 detach 的 client | 預設 | 相同 |
| `prefix + Ctrl+s` | 手動儲存所有 session | TPM | — |
| `prefix + Ctrl+r` | 手動恢復已儲存的 session | TPM | — |

### Window

| 快捷鍵 | 功能（推薦設定） | 來源 | 預設該鍵功能 |
|---------|------------------|------|--------------|
| `prefix + c` | 新建 window（保留當前路徑） | 自訂 | `new-window`（不保留路徑） |
| `prefix + ,` | 重新命名 window | 預設 | 相同 |
| `prefix + &` | 關閉 window（會確認） | 預設 | 相同 |
| `prefix + w` | 列出所有 window（互動式） | 預設 | 相同 |
| `prefix + 0-9` | 切換至指定編號 | 預設 | 相同 |
| `prefix + [` | 上一個 window | 自訂 | `copy-mode`（進入複製模式） |
| `prefix + ]` | 下一個 window | 自訂 | `paste-buffer`（貼上緩衝區） |
| `prefix + Space` | 切換到上次使用的 window | 自訂 | `next-layout`（切換 pane 排列方式） |
| `prefix + S-Left` | 將 window 左移一位 | 自訂 | — |
| `prefix + S-Right` | 將 window 右移一位 | 自訂 | — |

> **被覆寫的預設 window 快捷鍵：**
>
> | 預設快捷鍵 | 預設功能 | 覆寫為 | 替代方式 |
> |------------|----------|--------|----------|
> | `prefix + n` | 下一個 window | 未覆寫，仍可用 | 也可用 `prefix + ]` |
> | `prefix + p` | 上一個 window | 未覆寫，仍可用 | 也可用 `prefix + [` |
> | `prefix + l` | 上次使用的 window | 覆寫為 pane 導航（右） | 改用 `prefix + Space` |
> | `prefix + [` | 進入 copy mode | 覆寫為上一個 window | 改用 `prefix + v` |
> | `prefix + ]` | 貼上緩衝區 | 覆寫為下一個 window | 改用 `prefix + =` 選擇緩衝區 |
> | `prefix + Space` | 切換 pane layout | 覆寫為上次使用的 window | 改用 `prefix + M-1` 至 `M-5` 選擇 layout |

### Pane

| 快捷鍵 | 功能（推薦設定） | 來源 | 預設該鍵功能 |
|---------|------------------|------|--------------|
| `prefix + \|` | 水平分割（左右，保留路徑） | 自訂 | — |
| `prefix + -` | 垂直分割（上下，保留路徑） | 自訂 | `delete-buffer`（刪除緩衝區） |
| `prefix + "` | 垂直分割（上下，保留路徑） | 自訂 | `split-window`（不保留路徑） |
| `prefix + %` | 水平分割（左右，保留路徑） | 自訂 | `split-window -h`（不保留路徑） |
| `prefix + x` | 關閉 pane（會確認） | 預設 | 相同 |
| `prefix + z` | 全螢幕切換（Zoom） | 預設 | 相同 |
| `prefix + q` | 顯示 pane 編號 | 預設 | 相同 |
| `prefix + h` | 導航至左方 pane | 自訂 | — |
| `prefix + j` | 導航至下方 pane | 自訂 | — |
| `prefix + k` | 導航至上方 pane | 自訂 | — |
| `prefix + l` | 導航至右方 pane | 自訂 | `last-window`（上次使用的 window） |
| `prefix + H` | 向左擴大 5 格（可連按） | 自訂 | — |
| `prefix + J` | 向下擴大 5 格（可連按） | 自訂 | — |
| `prefix + K` | 向上擴大 5 格（可連按） | 自訂 | — |
| `prefix + L` | 向右擴大 5 格（可連按） | 自訂 | `switch-client -l`（上次使用的 session） |
| `prefix + >` | 與下方 pane 交換 | 自訂 | `display-menu`（Pane 右鍵選單） |
| `prefix + <` | 與上方 pane 交換 | 自訂 | `display-menu`（Window 右鍵選單） |

> **被覆寫的預設 pane 快捷鍵：**
>
> | 預設快捷鍵 | 預設功能 | 覆寫為 | 替代方式 |
> |------------|----------|--------|----------|
> | `prefix + o` | 循環切換 pane | 未覆寫，仍可用 | 也可用 `h/j/k/l` 導航 |
> | `prefix + ;` | 上次使用的 pane | 未覆寫，仍可用 | — |
> | `prefix + {` | 與上方 pane 交換 | 未覆寫，仍可用 | 也可用 `prefix + <` |
> | `prefix + }` | 與下方 pane 交換 | 未覆寫，仍可用 | 也可用 `prefix + >` |
> | `prefix + -` | 刪除緩衝區 | 覆寫為垂直分割 | 改用 `tmux delete-buffer` 命令 |
> | `prefix + L` | 切換到上次 session | 覆寫為調整 pane 大小 | 改用 `prefix + (` / `)` 切換 session |

### Copy Mode（Vi 模式）

> 以下快捷鍵在 copy mode 內使用。推薦設定使用 `mode-keys vi`（預設為 `emacs`）。

| 快捷鍵 | 功能（推薦設定） | 來源 | Vi 預設行為 |
|---------|------------------|------|-------------|
| `prefix + v` | 進入 copy mode | 自訂 | — （預設用 `prefix + [` 進入） |
| `v` | 開始選取 | 自訂 | `rectangle-toggle`（矩形選取切換） |
| `V` | 整行選取 | 預設 | 相同 |
| `Ctrl+v` | 矩形選取切換 | 自訂 | 相同（`C-v` 預設也是 `rectangle-toggle`） |
| `y` | 複製選取並離開 | 自訂 | — （預設用 `Enter` 複製） |
| `Enter` | 複製選取並離開 | 預設 | 相同 |
| `/` | 搜尋（向下） | 預設 | 相同 |
| `?` | 搜尋（向上） | 預設 | 相同 |
| `n` | 下一個搜尋結果 | 預設 | 相同 |
| `N` | 上一個搜尋結果 | 預設 | 相同 |
| `q` | 離開 copy mode | 預設 | 相同 |
| `Escape` | 清除選取 | 預設 | 相同 |
| `Space` | 開始選取 | 預設 | 相同 |
| `h/j/k/l` | 方向移動 | 預設 | 相同 |
| `w/b/e` | 按單字移動 | 預設 | 相同 |
| `0/$` | 行首/行尾 | 預設 | 相同 |
| `^` | 行首非空白字元 | 預設 | 相同（`back-to-indentation`） |
| `g/G` | 跳至頂部/底部 | 預設 | 相同 |
| `H/M/L` | 跳至畫面頂/中/底 | 預設 | 相同 |
| `Ctrl+u/Ctrl+d` | 上/下半頁 | 預設 | 相同 |
| `Ctrl+b/Ctrl+f` | 上/下一頁 | 預設 | 相同 |
| `{/}` | 上/下一段 | 預設 | 相同 |
| `o` | 移至選取的另一端 | 預設 | 相同 |
| `滑鼠拖曳` | 選取後不離開 copy mode | 自訂 | 選取後自動複製並離開 |

> **Copy Mode 按鍵模式對照（Vi vs Emacs）：**
>
> | 功能 | Vi 模式 | Emacs 模式（預設） |
> |------|---------|-------------------|
> | 開始選取 | `Space` | `Ctrl+Space` |
> | 複製 | `Enter` | `M-w` / `Ctrl+w` |
> | 取消選取 | `Escape` | `Ctrl+g` |
> | 搜尋（向下） | `/` | `Ctrl+s` |
> | 搜尋（向上） | `?` | `Ctrl+r` |
> | 方向移動 | `h/j/k/l` | `Ctrl+b/n/p/f` |
> | 按單字移動 | `w/b` | `M-f/M-b` |
> | 行首/行尾 | `0/$` | `Ctrl+a/Ctrl+e` |
> | 頂部/底部 | `g/G` | `M-<` / `M->` |
> | 上/下半頁 | `Ctrl+u/Ctrl+d` | `M-Up/M-Down` |

### 其他

| 快捷鍵 | 功能（推薦設定） | 來源 | 預設該鍵功能 |
|---------|------------------|------|--------------|
| `prefix + :` | 命令提示字元 | 預設 | 相同 |
| `prefix + ?` | 快捷鍵速查彈窗 | 自訂 | `list-keys -N`（列出快捷鍵清單） |
| `prefix + r` | 重新載入設定檔 | 自訂 | `refresh-client`（重新整理終端顯示） |
| `prefix + I` | 安裝 TPM plugin | TPM | — |
| `prefix + U` | 更新 TPM plugin | TPM | — |
| `prefix + i` | 顯示當前 pane 資訊 | 預設 | 相同 |
| `prefix + t` | 顯示時鐘 | 預設 | 相同 |
| `prefix + ~` | 顯示歷史訊息 | 預設 | 相同 |
| `prefix + C` | 自訂選項介面 | 預設 | 相同 |
| `prefix + M-1~5` | 選擇預設 pane layout | 預設 | 相同 |

### 與 Zellij / WezTerm 快捷鍵對照

| 功能 | tmux 預設 | tmux 推薦設定 | Zellij | WezTerm |
|------|-----------|---------------|--------|---------|
| 水平分割 | `prefix + %` | `prefix + \|` | `Ctrl+p` → `d` | `Ctrl+Shift+D` |
| 垂直分割 | `prefix + "` | `prefix + -` | `Ctrl+p` → `n` | `Ctrl+Shift+%` |
| 面板導航 | `prefix + o`（循環） | `prefix + h/j/k/l` | `Ctrl+p` → `h/j/k/l` | `Ctrl+Shift+方向鍵` |
| 上次面板 | `prefix + ;` | `prefix + ;`（保留） | — | — |
| 關閉面板 | `prefix + x` | `prefix + x` | `Ctrl+p` → `x` | `Ctrl+Shift+W` |
| 全螢幕 | `prefix + z` | `prefix + z` | `Ctrl+p` → `f` | `Ctrl+Shift+Z` |
| 新建分頁 | `prefix + c` | `prefix + c`（保留路徑） | `Ctrl+t` → `n` | `Ctrl+Shift+T` |
| 上/下分頁 | `prefix + p/n` | `prefix + [/]` | `Ctrl+t` → `h/l` | `Ctrl+Tab` |
| 切換分頁 | `prefix + 0-9` | `prefix + 0-9` | `Ctrl+t` → `1-9` | `Ctrl+1-9` |
| 上次分頁 | `prefix + l` | `prefix + Space` | — | — |
| 離開/Detach | `prefix + d` | `prefix + d` | `Ctrl+o` → `d` | 不支援 |
| 進入複製 | `prefix + [` | `prefix + v` | `Ctrl+s` | — |
| 搜尋 | copy mode → `/` | `prefix + v` → `/` | `Ctrl+s` → `s` | `Ctrl+Shift+F` |
| 貼上緩衝區 | `prefix + ]` | `prefix + =`（選擇式） | — | `Ctrl+Shift+V` |
| 鍵盤提示 | `prefix + ?` | `prefix + ?`（彈窗） | 畫面底部常駐 | `Ctrl+Shift+L` |

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

| 選項 | 說明 | 預設值 | 推薦值 |
|------|------|--------|--------|
| `prefix` | Prefix 鍵 | `C-b` | `C-a` |
| `default-terminal` | 終端類型 | `"tmux-256color"` | `"tmux-256color"` |
| `terminal-overrides` | True Color 覆寫 | （無） | `",*256col*:Tc"` |
| `mouse` | 滑鼠支援 | `off` | `on` |
| `base-index` | Window 起始編號 | `0` | `1` |
| `pane-base-index` | Pane 起始編號 | `0` | `1` |
| `escape-time` | Esc 鍵延遲（ms） | `10` | `0` |
| `history-limit` | 捲動歷史行數 | `2000` | `50000` |
| `renumber-windows` | 自動重新編號 | `off` | `on` |
| `mode-keys` | Copy mode 按鍵風格 | `emacs` | `vi` |
| `set-clipboard` | 系統剪貼簿 | `external` | `on` |
| `set-titles` | 設定終端標題 | `off` | `on` |
| `display-time` | 訊息顯示時間（ms） | `750` | `3000` |
| `display-panes-time` | 面板編號顯示時間（ms） | `1000` | `2000` |
| `monitor-activity` | 監控 Window 活動 | `off` | `on` |
| `visual-activity` | 活動通知方式 | `off` | `off` |
| `status-interval` | 狀態列更新間隔（秒） | `15` | `5` |
| `status-position` | 狀態列位置 | `bottom` | `bottom` |
| `status-justify` | Window 列表對齊 | `left` | `centre` |
| `status-left-length` | 左側最大長度 | `10` | `40` |
| `status-right-length` | 右側最大長度 | `40` | `60` |

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
└── TPM Plugin ........ sensible / resurrect / yank / continuum
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
mkdir -p ~/.tmux/plugins
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
```

完整的前置套件、設定、首次啟動與驗證步驟見「[快速安裝：自動恢復](#快速安裝自動恢復)」。

安裝後若 tmux server 已執行，才重新載入設定：

```bash
tmux source-file ~/.tmux.conf
```

若 server 尚未執行，改用 `tmux new -s main` 啟動；tmux 會在啟動時載入設定。

### TPM 操作快捷鍵

| 快捷鍵 | 功能 |
|---------|------|
| `prefix + I` | 安裝設定檔中宣告的 plugin |
| `prefix + U` | 選擇並更新 plugin（可全部更新） |
| `prefix + Alt+u` | 移除不在設定檔中的 plugin |

### 推薦 Plugin

#### tmux-sensible

提供一組合理的預設值，適合所有 tmux 使用者：

```bash
set -g @plugin 'tmux-plugins/tmux-sensible'
```

包含：UTF-8 支援、更大的 history、更快的按鍵回應等。

#### tmux-resurrect

Session 持久化：儲存並恢復 session、window、pane、layout、工作目錄與終端歷史。Plugin 預設不儲存 Pane 內容，本指南的推薦設定會明確啟用。

```bash
set -g @plugin 'tmux-plugins/tmux-resurrect'
set -g @resurrect-delete-backup-after '30'
set -g @resurrect-capture-pane-contents 'on'
set -g @resurrect-pane-contents-area 'full'
```

| 操作 | 快捷鍵 |
|------|---------|
| 儲存 | `prefix + Ctrl+s` |
| 還原 | `prefix + Ctrl+r` |

#### tmux-continuum

搭配 tmux-resurrect 定時儲存，並可在 tmux server 啟動時自動恢復：

```bash
set -g @plugin 'tmux-plugins/tmux-continuum'
set -g @continuum-save-interval '15'  # 每 15 分鐘自動儲存
set -g @continuum-restore 'on'        # tmux server 啟動時自動恢復
```

自動儲存依賴 tmux 狀態列。若主題或其他 plugin 在 continuum 載入後覆寫 `status-right`，自動儲存可能停止；應把 continuum 放在 TPM plugin 清單最後。

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
set -g @resurrect-delete-backup-after '30'
set -g @resurrect-capture-pane-contents 'on'
set -g @resurrect-pane-contents-area 'full'
set -g @plugin 'tmux-plugins/tmux-yank'

# continuum 放在 plugin 清單最後
set -g @plugin 'tmux-plugins/tmux-continuum'
set -g @continuum-save-interval '15'
set -g @continuum-restore 'on'

# 此行必須在設定檔最底部
run '~/.tmux/plugins/tpm/tpm'
```

---

## Session 管理

### 自動儲存與恢復：tmux-resurrect + tmux-continuum

以下內容已於 2026-07-20 依兩個 plugin 的官方 `master` 文件查證。

| Plugin | 責任 | 是否自動 |
|--------|------|----------|
| `tmux-resurrect` | 建立與讀取 tmux 環境快照 | 預設使用快捷鍵手動儲存／恢復 |
| `tmux-continuum` | 定期呼叫 resurrect 儲存，並在 tmux server 啟動時恢復 | 安裝後自動儲存；自動恢復需明確啟用 |

#### 安裝與設定

前置條件為 tmux 1.9 以上、Git、Bash 與 TPM。若尚未安裝 TPM，先依「[Plugin 管理（TPM）](#plugin-管理tpm)」章節安裝。

把以下設定放在 `~/.tmux.conf` 或 `~/.config/tmux/tmux.conf`。`tmux-continuum` 必須是 plugin 清單的最後一個，TPM 初始化仍放在整份設定檔最底部：

```bash
set -g @plugin 'tmux-plugins/tpm'
set -g @plugin 'tmux-plugins/tmux-resurrect'
set -g @resurrect-delete-backup-after '30'
set -g @resurrect-capture-pane-contents 'on'
set -g @resurrect-pane-contents-area 'full'

# 其他 plugin 放在這裡

# continuum 放在 plugin 清單最後
set -g @plugin 'tmux-plugins/tmux-continuum'
set -g @continuum-save-interval '15'
set -g @continuum-restore 'on'

# TPM 初始化必須是設定檔最後一行
run '~/.tmux/plugins/tpm/tpm'
```

重新載入實際使用的設定檔，再於 tmux 內按 `prefix + I` 安裝：

```bash
# 傳統路徑
tmux source-file ~/.tmux.conf

# 若使用 XDG 路徑，改執行這一行
tmux source-file ~/.config/tmux/tmux.conf
```

推薦設定檔 [`config/tmux.conf`](./config/tmux.conf) 已包含上述設定。若 `~/.tmux.conf` 不存在，可用以下保護式命令採用完整範例；若檔案已存在，命令只會提示，不會覆寫，請手動合併上方 plugin 區塊：

```bash
if [ -e ~/.tmux.conf ]; then
    echo "~/.tmux.conf 已存在，請手動合併設定，不要直接覆寫。"
else
    cp docs/dev-guide/terminal/config/tmux.conf ~/.tmux.conf
    echo "已建立 ~/.tmux.conf。"
fi
```

完成複製或手動合併後，若 tmux server 正在執行，執行 `tmux source-file ~/.tmux.conf`；若尚未執行，直接啟動 `tmux` 便會載入設定。接著在 tmux 內按 `prefix + I`。若將範例部署到 `~/.config/tmux/tmux.conf`，需把範例內 `prefix + r` 的綁定路徑同步改為 XDG 路徑，否則快捷鍵仍會嘗試載入 `~/.tmux.conf`。

#### 首次使用與驗證

先確認設定值已載入：

```bash
tmux show-options -gqv @continuum-save-interval
# 預期：15

tmux show-options -gqv @continuum-restore
# 預期：on
```

接著在 tmux 內按 `prefix + Ctrl+s` 建立第一份快照。若未設定 `@resurrect-dir`，resurrect 會沿用既有的 `~/.tmux/resurrect`；全新環境則使用 `${XDG_DATA_HOME:-$HOME/.local/share}/tmux/resurrect`。可用以下指令找出預設目錄並檢查：

```bash
resurrect_dir="$HOME/.tmux/resurrect"
[ -d "$resurrect_dir" ] || resurrect_dir="${XDG_DATA_HOME:-$HOME/.local/share}/tmux/resurrect"
echo "$resurrect_dir"
ls -l "$resurrect_dir/last"
```

看到 `last` 連結即表示 resurrect 已完成儲存。若 `tmux show-options -gqv @resurrect-dir` 有輸出，請改查該自訂目錄。

日常操作：

| 操作 | 方法 | 說明 |
|------|------|------|
| 手動儲存 | `prefix + Ctrl+s` | 立即建立快照；重開機或更新 plugin 前建議先執行 |
| 手動恢復 | `prefix + Ctrl+r` | 在現有 tmux server 內讀取 `last` 快照 |
| 自動儲存 | 無須按鍵 | 預設每 15 分鐘執行；第一次會在 tmux 啟動 15 分鐘後發生 |
| 自動恢復 | 啟動新的 tmux server | 僅在 server 啟動時觸發；重新載入設定檔不會觸發 |

> **重要**：`@continuum-restore 'on'` 不會自行啟動 tmux。開啟終端後手動執行 `tmux`，或使用本指南的 shell 自動啟動設定，才會建立 server 並觸發恢復。`@continuum-boot 'on'` 是另一項「作業系統開機後啟動 tmux」功能，會建立 macOS 啟動項目或 Linux systemd 使用者服務，不建議未審查平台行為就直接啟用。

#### 恢復範圍與限制

resurrect 會恢復：

- session、window、pane、順序與 layout
- 各 pane 的工作目錄
- 目前與先前使用的 session/window、焦點與活動 pane
- 官方保守清單內的程式，例如 `vim`、`nvim`、`less`、`man`、`top`

resurrect 不會建立程序記憶體的檢查點，也不保證恢復未儲存的編輯器內容、登入狀態、SSH 連線或任意背景服務。它是依快照重建 tmux 結構並重新執行允許的命令，不等同虛擬機快照。

若確實要恢復額外程式，可明確列入：

```bash
set -g @resurrect-processes 'ssh psql mysql'
```

不要設定 `@resurrect-processes ':all:'`。官方文件明確警告，恢復所有命令可能在重開機後重新執行具破壞性的舊命令。

推薦設定會保存 Pane 終端歷史：

```bash
set -g @resurrect-capture-pane-contents 'on'
set -g @resurrect-pane-contents-area 'full'
```

Pane 內容與 Layout 快照採用不同的保留方式：

| 設定 | 可用值 | 推薦值 | 影響 |
|------|--------|--------|------|
| `@resurrect-pane-contents-area` | `full`、`visible` | `full` | `full` 保存目前畫面與 scrollback；`visible` 只保存目前可見畫面 |
| `history-limit` | 非負整數 | `50000` | 限制設定後新建 Pane 的 scrollback 行數，也是 `full` 捕捉的主要上限；`0` 表示不保留 scrollback |
| `@continuum-save-interval` | 分鐘；`0` 為停用 | `15` | 每 15 分鐘重建一次最新 Pane 內容壓縮檔 |
| `@resurrect-delete-backup-after` | 天數 | `30` | 只清理時間戳 Layout 快照；至少保留最新 5 份 |

Pane 終端歷史會壓縮成快照目錄內單一的 `pane_contents.tar.gz`，每次儲存直接覆寫。因此它只保留最後一次捕捉的內容，不會隨 30 天 Layout 快照各自累積一份。還原較舊的 Layout 快照時，只會嘗試套用最新 archive 中 `session 名稱 + window index + pane index` 相符的內容；若拓撲或索引已改變，不保證能與舊 Layout 完整對應。resurrect 沒有獨立的 Pane 內容容量上限；要降低容量可把範圍改成 `visible`，或降低 `history-limit`：

```bash
# 方案一：只保留目前看得到的 Pane 畫面
set -g @resurrect-pane-contents-area 'visible'

# 方案二：完整保存，但把之後新建 Pane 的 scrollback 降為 10000 行
set -g history-limit 10000
```

`history-limit` 只套用到設定後新建的 Pane，包含在既有 Window 內新分割的 Pane；既有 Pane 的 history 不會被重新配置或裁切。設定為 `0` 時不保留 scrollback，但目前可見的 Pane 畫面仍可被捕捉。可用以下指令檢查實際占用並收緊目錄權限：

```bash
resurrect_dir="$HOME/.tmux/resurrect"
[ -d "$resurrect_dir" ] || resurrect_dir="${XDG_DATA_HOME:-$HOME/.local/share}/tmux/resurrect"
chmod 700 "$resurrect_dir"
ls -ld "$resurrect_dir"
du -h "$resurrect_dir/pane_contents.tar.gz"
gzip -l "$resurrect_dir/pane_contents.tar.gz"
```

此功能只保存終端顯示內容，不會保存程序狀態。內容可能含 token、路徑或命令輸出等敏感資料。`chmod 700` 後，`ls -ld` 的權限欄應以 `drwx------` 開頭；若使用 `@resurrect-dir` 自訂路徑，請對實際目錄執行相同檢查。

啟用後另需檢查：

```bash
tmux show-options -gqv default-command
```

依官方已知限制，`default-command` 不應包含 `&&` 或 `||`；推薦設定未覆寫此選項。

#### 測試自動恢復

最安全的方式是在下次計畫性重開機或自然結束 tmux server 時驗證，不要只為測試而終止仍在工作的主要 server：

1. 建立一個測試 session、數個 window/pane，並切換到不同工作目錄。
2. 按 `prefix + Ctrl+s`，依上一節確認 `last` 快照存在。
3. 等到計畫性的系統重開機或 tmux server 結束。
4. 重新執行 `tmux`。新的 server 啟動後應自動重建已儲存的 session 結構。

若必須立即測試，只能在維護時段、確認所有 pane 工作均已寫入磁碟後執行：

> **警告**：`tmux kill-server` 會終止目前 server 內的所有 session 與程序。resurrect 不會保存程序記憶體或未寫入磁碟的資料。

```bash
tmux kill-server
tmux
```

#### 更新與停用

在 tmux 內按 `prefix + U`，選擇更新 `tmux-resurrect`、`tmux-continuum` 或全部 plugin。更新後重新載入設定，手動儲存一次並重做恢復測試。

若要停用自動恢復，移除 `set -g @continuum-restore 'on'`。若要保留 plugin 但停用定時儲存，設定：

```bash
set -g @continuum-save-interval '0'
```

緊急阻止下一次自動恢復時，可依官方 FAQ 建立旗標檔：

```bash
touch ~/tmux_no_auto_restore
```

排除問題後刪除該檔，才會重新允許自動恢復。

#### 恢復較舊快照

此流程必須從尚未執行自動恢復的全新 tmux server 開始。若目前已有 server，請等到計畫性重啟；需要立即處理時，先確認所有工作已寫入磁碟，再於維護時段結束現有 server。

先在一般終端建立官方停用旗標，再啟動空白 server：

```bash
touch ~/tmux_no_auto_restore
tmux
```

在新 server 的空白 pane 中找出快照目錄。檢查清單後，把 `snapshot` 改成實際檔名：

```bash
resurrect_dir="$HOME/.tmux/resurrect"
[ -d "$resurrect_dir" ] || resurrect_dir="${XDG_DATA_HOME:-$HOME/.local/share}/tmux/resurrect"
cd "$resurrect_dir"
ls -1t tmux_resurrect_*.txt
snapshot="tmux_resurrect_20260720T120000.txt"
ln -sf "$snapshot" last
```

按 `prefix + Ctrl+r` 手動恢復，確認完成後刪除旗標：

```bash
rm ~/tmux_no_auto_restore
```

此操作會改變 `last` 指向，但不會刪除其他時間戳快照。

#### 疑難排解

| 問題 | 檢查與處理 |
|------|------------|
| `source-file` 回報 tmux socket 不存在 | tmux server 尚未啟動。改執行 `tmux new -s main` |
| TPM 執行回傳 `127` | 執行 `command -v bash` 與 `ls -l ~/.tmux/plugins/tpm/tpm`；補裝 Bash 或重新安裝 TPM |
| `prefix + I` 沒有反應 | 確認 TPM 已安裝、`run '~/.tmux/plugins/tpm/tpm'` 位於設定檔最底部，並重新載入正確的設定檔路徑 |
| 重新載入設定後沒有自動恢復 | 這是預期行為；自動恢復只在 tmux server 啟動時觸發。可先用 `prefix + Ctrl+r` 手動恢復 |
| 15 分鐘後沒有新快照 | 執行 `tmux show-options -gqv status`，確認狀態列為 `on`；並把 continuum 移到 plugin 清單最後，避免 `status-right` 被後續 plugin 覆寫 |
| Layout 有恢復，但開發服務沒有啟動 | 該程序不在預設允許清單。先讀取快照中的實際程序名稱，再以 `@resurrect-processes` 逐項加入 |
| 恢復到錯誤的時間點 | 依「恢復較舊快照」重設 `last` 連結，再按 `prefix + Ctrl+r` |

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
- tmux-resurrect 設定選項：https://github.com/tmux-plugins/tmux-resurrect/blob/master/scripts/variables.sh
- tmux-resurrect 恢復程式設定：https://github.com/tmux-plugins/tmux-resurrect/blob/master/docs/restoring_programs.md
- tmux-resurrect Pane 內容：https://github.com/tmux-plugins/tmux-resurrect/blob/master/docs/restoring_pane_contents.md
- tmux-resurrect 恢復舊快照：https://github.com/tmux-plugins/tmux-resurrect/blob/master/docs/restoring_previously_saved_environment.md
- tmux-continuum：https://github.com/tmux-plugins/tmux-continuum
- tmux-continuum FAQ：https://github.com/tmux-plugins/tmux-continuum/blob/master/docs/faq.md
- tmux-continuum 開機啟動：https://github.com/tmux-plugins/tmux-continuum/blob/master/docs/automatic_start.md
- tmuxinator：https://github.com/tmuxinator/tmuxinator
- Catppuccin 主題：https://github.com/catppuccin/tmux
- 推薦設定檔：[config/tmux.conf](./config/tmux.conf)
