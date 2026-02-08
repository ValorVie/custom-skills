# Yazi 終端檔案管理器完整指南

## 目錄

- [簡介與定位](#簡介與定位)
- [安裝方式（多平台）](#安裝方式多平台)
- [必要與選配依賴](#必要與選配依賴)
- [設定檔路徑與初始化](#設定檔路徑與初始化)
- [快速開始](#快速開始)
- [完整快捷鍵參考](#完整快捷鍵參考)
- [推薦設定](#推薦設定)
- [Plugin 系統](#plugin-系統)
- [實用整合](#實用整合)
- [遠端檔案傳輸（SFTP/SSH）](#遠端檔案傳輸sftpssh)
- [常見問題](#常見問題)
- [參考資料](#參考資料)

---

## 簡介與定位

Yazi 是以 Rust 實作的終端檔案管理器，重點在高效瀏覽、預覽與鍵盤操作。

在開發工作流中，Yazi 適合負責：

- 快速瀏覽專案目錄與檔案
- 搭配預覽器快速確認內容
- 在終端內完成移動、複製、重命名等檔案操作

---

## 安裝方式（多平台）

### macOS

```bash
brew install yazi ffmpeg sevenzip jq poppler fd ripgrep fzf zoxide resvg imagemagick
```

### Windows

```powershell
# WinGet
winget install sxyazi.yazi

# Scoop
scoop install yazi
```

### Linux

```bash
# Arch
sudo pacman -S yazi ffmpeg 7zip jq poppler fd ripgrep fzf zoxide resvg imagemagick

# Debian / Ubuntu（依官方說明，部分版本建議使用官方 binaries 或自行編譯）
sudo apt install ffmpeg 7zip jq poppler-utils fd-find ripgrep fzf zoxide imagemagick

# Fedora（COPR）
sudo dnf copr enable lihaohong/yazi
sudo dnf install yazi
```

### 手動下載官方 binary（一條龍指令，適合 apt 套件過舊）

Linux / macOS（自動抓最新版 + 自動判斷架構）：

系統級安裝（需要 `sudo`，安裝到 `/usr/local/bin`）：

```bash
YAZI_TAG="$(curl -fsSL https://api.github.com/repos/sxyazi/yazi/releases/latest | sed -n 's/.*"tag_name": "\([^"]*\)".*/\1/p')" && case "$(uname -s)-$(uname -m)" in Linux-x86_64) ASSET="yazi-x86_64-unknown-linux-gnu.zip";; Linux-aarch64|Linux-arm64) ASSET="yazi-aarch64-unknown-linux-gnu.zip";; Darwin-x86_64) ASSET="yazi-x86_64-apple-darwin.zip";; Darwin-arm64|Darwin-aarch64) ASSET="yazi-aarch64-apple-darwin.zip";; *) echo "Unsupported platform: $(uname -s)-$(uname -m)"; exit 1;; esac && TMP_DIR="$(mktemp -d)" && curl -fL -o "$TMP_DIR/yazi.zip" "https://github.com/sxyazi/yazi/releases/download/${YAZI_TAG}/${ASSET}" && unzip -oq "$TMP_DIR/yazi.zip" -d "$TMP_DIR" && YAZI_BIN="$(find "$TMP_DIR" -type f -name yazi -print -quit)" && YA_BIN="$(find "$TMP_DIR" -type f -name ya -print -quit)" && [ -n "$YAZI_BIN" ] && [ -n "$YA_BIN" ] && sudo install "$YAZI_BIN" "$YA_BIN" -t /usr/local/bin && yazi --version && rm -rf "$TMP_DIR"
```

使用者層安裝（無 `sudo`，推薦給一般使用者，安裝到 `~/.local/bin`）：

```bash
YAZI_TAG="$(curl -fsSL https://api.github.com/repos/sxyazi/yazi/releases/latest | sed -n 's/.*"tag_name": "\([^"]*\)".*/\1/p')" && case "$(uname -s)-$(uname -m)" in Linux-x86_64) ASSET="yazi-x86_64-unknown-linux-gnu.zip";; Linux-aarch64|Linux-arm64) ASSET="yazi-aarch64-unknown-linux-gnu.zip";; Darwin-x86_64) ASSET="yazi-x86_64-apple-darwin.zip";; Darwin-arm64|Darwin-aarch64) ASSET="yazi-aarch64-apple-darwin.zip";; *) echo "Unsupported platform: $(uname -s)-$(uname -m)"; exit 1;; esac && TMP_DIR="$(mktemp -d)" && curl -fL -o "$TMP_DIR/yazi.zip" "https://github.com/sxyazi/yazi/releases/download/${YAZI_TAG}/${ASSET}" && unzip -oq "$TMP_DIR/yazi.zip" -d "$TMP_DIR" && YAZI_BIN="$(find "$TMP_DIR" -type f -name yazi -print -quit)" && YA_BIN="$(find "$TMP_DIR" -type f -name ya -print -quit)" && [ -n "$YAZI_BIN" ] && [ -n "$YA_BIN" ] && mkdir -p "$HOME/.local/bin" && install "$YAZI_BIN" "$YA_BIN" -t "$HOME/.local/bin" && "$HOME/.local/bin/yazi" --version && rm -rf "$TMP_DIR"
```

若你的 shell 還沒把 `~/.local/bin` 放進 PATH，可加入：

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
# zsh 使用者改寫到 ~/.zshrc
```

這兩版都會自動在解壓後目錄遞迴找 `yazi` 與 `ya`，可避免 zip 內含子目錄時安裝失敗。

Windows（PowerShell，一條龍）：

```powershell
$tag=(Invoke-RestMethod https://api.github.com/repos/sxyazi/yazi/releases/latest).tag_name; $asset=if($env:PROCESSOR_ARCHITECTURE -eq 'ARM64'){'yazi-aarch64-pc-windows-msvc.zip'}else{'yazi-x86_64-pc-windows-msvc.zip'}; $zip="$env:TEMP\$asset"; $dst="$env:TEMP\yazi-bin"; Remove-Item $dst -Recurse -Force -ErrorAction SilentlyContinue; Invoke-WebRequest -Uri "https://github.com/sxyazi/yazi/releases/download/$tag/$asset" -OutFile $zip; Expand-Archive $zip $dst -Force; New-Item -ItemType Directory -Force "$env:ProgramFiles\yazi" | Out-Null; Copy-Item (Get-ChildItem -Path $dst -Recurse -Filter yazi.exe | Select-Object -First 1).FullName "$env:ProgramFiles\yazi\yazi.exe" -Force; Copy-Item (Get-ChildItem -Path $dst -Recurse -Filter ya.exe | Select-Object -First 1).FullName "$env:ProgramFiles\yazi\ya.exe" -Force; & "$env:ProgramFiles\yazi\yazi.exe" --version
```

執行後若 `yazi` 指令仍找不到，請把安裝目錄加入 PATH：

- Linux / macOS：`/usr/local/bin`
- Windows：`%ProgramFiles%\yazi`

---

## 必要與選配依賴

必要依賴：

- `file`（用於檔案類型判斷）

常用選配：

- `ffmpeg`（影片縮圖）
- `7zip`（壓縮檔處理）
- `jq`（JSON 預覽）
- `poppler`（PDF 預覽）
- `fd` / `ripgrep`（搜尋）
- `fzf` / `zoxide`（快速跳轉）

Windows 額外注意：

- 建議安裝 Git for Windows，並設定 `YAZI_FILE_ONE` 指向 `file.exe`。

---

## 設定檔路徑與初始化

Yazi 主要設定檔：

- `yazi.toml`（一般設定）
- `keymap.toml`（按鍵設定）
- `theme.toml`（主題設定）

預設路徑：

| 平台 | 路徑 |
|------|------|
| Linux / macOS | `~/.config/yazi/` |
| Windows | `%AppData%\yazi\config\` |

可用環境變數覆寫設定目錄：

```bash
YAZI_CONFIG_HOME=~/.config/yazi-alt yazi
```

---

## 快速開始

### 1) 啟動

```bash
yazi
```

### 2) 建議使用 shell wrapper（離開後同步 cwd）

以 Bash/Zsh 為例：

```bash
function y() {
  local tmp="$(mktemp -t "yazi-cwd.XXXXXX")" cwd
  yazi "$@" --cwd-file="$tmp"
  IFS= read -r -d '' cwd < "$tmp"
  [ -n "$cwd" ] && [ "$cwd" != "$PWD" ] && [ -d "$cwd" ] && cd -- "$cwd"
  rm -f -- "$tmp"
}
```

之後可用 `y` 取代 `yazi`。

---

## 完整快捷鍵參考

### 導覽與移動

| 按鍵 | 功能 |
|------|------|
| `k` / `↑` | 向上移動 |
| `j` / `↓` | 向下移動 |
| `h` / `←` | 返回上層目錄 |
| `l` / `→` / `Enter` | 進入目錄或開啟檔案 |
| `H` | 返回上一個瀏覽位置（歷史回退） |
| `L` | 前進至下一個瀏覽位置（歷史前進） |
| `gg` | 跳到清單頂部 |
| `G` | 跳到清單底部 |
| `Ctrl+u` | 向上捲動半頁 |
| `Ctrl+d` | 向下捲動半頁 |
| `Ctrl+b` / `PageUp` | 向上捲動一整頁 |
| `Ctrl+f` / `PageDown` | 向下捲動一整頁 |

### 選取

| 按鍵 | 功能 |
|------|------|
| `Space` | 切換選取當前項目，然後移到下一項 |
| `v` | 進入視覺模式（連續選取） |
| `V` | 進入視覺模式（反向取消選取） |
| `Ctrl+a` | 全選 |
| `Ctrl+r` | 反轉選取 |
| `Esc` | 退出視覺模式 / 清除選取 / 取消搜尋 |

### 檔案操作

| 按鍵 | 功能 |
|------|------|
| `o` / `Enter` | 開啟選取的檔案 |
| `O` / `Shift+Enter` | 互動式開啟（選擇開啟方式） |
| `y` | 複製（yank）選取的檔案 |
| `x` | 剪下（cut）選取的檔案 |
| `p` | 貼上檔案 |
| `P` | 貼上檔案（同名時覆蓋） |
| `Y` / `X` | 取消 yank 狀態 |
| `d` | 移至回收桶（trash） |
| `D` | 永久刪除 |
| `a` | 建立檔案或目錄（名稱以 `/` 結尾為目錄） |
| `r` | 重命名（游標停在副檔名前） |
| `-` | 建立符號連結（絕對路徑） |
| `_` | 建立符號連結（相對路徑） |
| `Ctrl+-` | 建立硬連結 |
| `.` | 顯示 / 隱藏隱藏檔案 |

### 路徑複製（`c` 前綴）

| 按鍵 | 功能 |
|------|------|
| `cc` | 複製檔案完整路徑 |
| `cd` | 複製目錄路徑 |
| `cf` | 複製檔案名稱 |
| `cn` | 複製檔案名稱（不含副檔名） |

### 搜尋與過濾

| 按鍵 | 功能 |
|------|------|
| `f` | 過濾檔案（智慧模式） |
| `/` | 向前搜尋（智慧模式） |
| `?` | 向後搜尋（智慧模式） |
| `n` | 跳至下一個搜尋結果 |
| `N` | 跳至上一個搜尋結果 |
| `s` | 使用 `fd` 搜尋檔案名稱 |
| `S` | 使用 `ripgrep` 搜尋檔案內容 |
| `Ctrl+s` | 取消進行中的搜尋 |

### 排序（`,` 前綴）

| 按鍵 | 功能 |
|------|------|
| `,m` / `,M` | 依修改時間排序（正序 / 逆序） |
| `,b` / `,B` | 依建立時間排序（正序 / 逆序） |
| `,e` / `,E` | 依副檔名排序（正序 / 逆序） |
| `,a` / `,A` | 依字母排序（正序 / 逆序） |
| `,n` / `,N` | 依自然排序（正序 / 逆序） |
| `,s` / `,S` | 依檔案大小排序（正序 / 逆序） |
| `,r` | 隨機排序 |

### 顯示模式（`m` 前綴）

| 按鍵 | 功能 |
|------|------|
| `ms` | 顯示檔案大小 |
| `mp` | 顯示權限 |
| `mb` | 顯示建立時間 |
| `mm` | 顯示修改時間 |
| `mo` | 顯示擁有者 |
| `mn` | 不顯示額外資訊（預設） |

### 快速跳轉（`g` 前綴）

| 按鍵 | 功能 |
|------|------|
| `gh` | 跳至家目錄 `~` |
| `gc` | 跳至 `~/.config` |
| `gd` | 跳至 `~/Downloads` |
| `gSpace` | 互動式跳轉目錄 |
| `gf` | 追蹤符號連結的目標 |

### Tab 管理

| 按鍵 | 功能 |
|------|------|
| `t` | 在當前目錄建立新 Tab |
| `1`-`9` | 切換至第 1-9 個 Tab |
| `[` | 切換至上一個 Tab |
| `]` | 切換至下一個 Tab |
| `{` | 將當前 Tab 與上一個交換位置 |
| `}` | 將當前 Tab 與下一個交換位置 |
| `Ctrl+c` | 關閉當前 Tab（最後一個 Tab 會退出 Yazi） |

### 預覽與檢視

| 按鍵 | 功能 |
|------|------|
| `K` | 在預覽中向上捲動 5 行 |
| `J` | 在預覽中向下捲動 5 行 |
| `Tab` | 開啟 Spot 檢視（詳細資訊面板） |

### Shell 與工作管理

| 按鍵 | 功能 |
|------|------|
| `;` | 執行 Shell 指令（互動式） |
| `:` | 執行 Shell 指令（阻塞式） |
| `w` | 開啟工作管理員 |
| `z` | 透過 fzf 跳轉目錄 / 檔案 |
| `Z` | 透過 zoxide 跳轉目錄 |

### 系統

| 按鍵 | 功能 |
|------|------|
| `q` | 退出（輸出 cwd） |
| `Q` | 退出（不輸出 cwd） |
| `Ctrl+z` | 暫停 Yazi 行程 |
| `~` / `F1` | 開啟快捷鍵說明 |

---

## 推薦設定

### yazi.toml（核心設定）

```toml
# ~/.config/yazi/yazi.toml

# ============================================================
# 管理器設定
# ============================================================
[mgr]
# 面板寬度比例 [上層目錄, 當前目錄, 預覽]
ratio = [ 1, 4, 3 ]

# 排序方式：alphabetical, natural, size, mtime, btime, extension, random
sort_by = "natural"
sort_sensitive = false
sort_reverse = false
sort_dir_first = true

# 預設顯示模式：none, size, permissions, mtime, owner
linemode = "size"

# 預設顯示隱藏檔
show_hidden = false

# 顯示符號連結目標
show_symlink = true

# 游標上下保留的可見行數
scrolloff = 5

# 視窗標題格式
title_format = "Yazi: {cwd}"

# ============================================================
# 預覽設定
# ============================================================
[preview]
# 文字換行：no, wrap
wrap = "no"

# Tab 寬度
tab_size = 2

# 預覽最大尺寸
max_width = 600
max_height = 900

# 圖片預覽品質（JPEG）
image_quality = 75

# ============================================================
# 工作管理
# ============================================================
[tasks]
micro_workers = 10
macro_workers = 10
bizarre_retry = 3

# ============================================================
# 開啟方式
# ============================================================
[opener]
edit = [
  { run = "${EDITOR:-vi} %s", desc = "$EDITOR", for = "unix", block = true },
  { run = "code %s", desc = "VS Code", for = "windows", orphan = true },
]
play = [
  { run = "xdg-open %s1", desc = "Play", for = "linux" },
  { run = "open %s1", desc = "Play", for = "macos" },
]
reveal = [
  { run = "xdg-open \"$(dirname %s1)\"", desc = "Reveal", for = "linux" },
  { run = "open -R %s1", desc = "Reveal", for = "macos" },
  { run = "explorer /select,%s1", orphan = true, desc = "Reveal", for = "windows" },
]

# ============================================================
# 開啟規則
# ============================================================
[open]
rules = [
  { url = "*/", use = [ "edit", "reveal" ] },
  { mime = "text/*", use = [ "edit", "reveal" ] },
  { mime = "image/*", use = [ "open", "reveal" ] },
  { mime = "{audio,video}/*", use = [ "play", "reveal" ] },
  { mime = "application/{zip,gzip,x-tar,x-bzip2,x-7z-compressed,x-rar}", use = [ "extract", "reveal" ] },
  { url = "*", use = [ "open", "reveal" ] },
]
```

### theme.toml（主題設定）

```toml
# ~/.config/yazi/theme.toml

# 使用社群 flavor（可選）
# [flavor]
# dark = "catppuccin-mocha"
# light = "catppuccin-latte"

# 自訂 Tab 列外觀
[tabs]
active   = { fg = "white", bg = "blue", bold = true }
inactive = { fg = "blue" }

# 自訂檔案類型顏色
[filetype]
rules = [
  { mime = "image/*", fg = "yellow" },
  { mime = "{audio,video}/*", fg = "magenta" },
  { mime = "application/zip", fg = "red" },
  { url = "*/", fg = "blue", bold = true },
  { url = "*", is = "exec", fg = "green" },
]
```

---

## Plugin 系統

Yazi 支援以 Lua 撰寫的 Plugin，透過 `ya` CLI 工具進行安裝與管理。

### ya pkg 指令

```bash
# 安裝 Plugin
ya pkg add owner/repo-name              # 從 GitHub 安裝
ya pkg add yazi-rs/plugins:git          # 從 monorepo 安裝子目錄
ya pkg add owner/plugin1 owner/plugin2  # 同時安裝多個

# 管理 Plugin
ya pkg list                             # 列出已安裝的 Plugin
ya pkg upgrade                          # 升級所有 Plugin
ya pkg install                          # 從 package.toml 安裝所有依賴
ya pkg delete owner/repo-name           # 移除 Plugin
```

### init.lua 設定

Plugin 的初始化與設定寫在 `~/.config/yazi/init.lua`：

```lua
-- ~/.config/yazi/init.lua

-- 載入並設定 Plugin
require("sshfs"):setup()

-- 帶參數的 Plugin 設定
require("git"):setup {
  show_branch = true,
}
```

### 推薦 Plugin

| Plugin | 功能 | 安裝指令 |
|--------|------|----------|
| `yazi-rs/plugins:git` | Git 狀態顯示 | `ya pkg add yazi-rs/plugins:git` |
| `yazi-rs/plugins:smart-filter` | 智慧過濾 | `ya pkg add yazi-rs/plugins:smart-filter` |
| `uhs-robert/sshfs` | SFTP/SSH 掛載 | `ya pkg add uhs-robert/sshfs` |
| `boydaihungst/gvfs` | 多協定掛載 | `ya pkg add boydaihungst/gvfs` |

### Plugin 目錄結構

```
~/.config/yazi/
├── yazi.toml          # 核心設定
├── keymap.toml        # 按鍵設定
├── theme.toml         # 主題設定
├── init.lua           # Plugin 初始化
└── plugins/           # Plugin 目錄
    └── my-plugin.yazi/
        └── main.lua   # Plugin 進入點
```

### Flavor（主題包）安裝

Flavor 是預先打包好的完整主題設定：

```bash
# 安裝 Catppuccin 主題
ya pkg add yazi-rs/flavors:catppuccin-mocha
```

安裝後在 `theme.toml` 中啟用：

```toml
[flavor]
dark = "catppuccin-mocha"
```

---

## 實用整合

### 搭配 Zellij

建議在 Zellij layout 中固定一個 pane/tab 給 Yazi，作為檔案入口：

```kdl
// ~/.config/zellij/layouts/dev.kdl
layout {
    tab name="Code" focus=true {
        pane
    }
    tab name="Files" {
        pane {
            command "yazi"
        }
    }
    tab name="Git" {
        pane {
            command "lazygit"
        }
    }
}
```

### 搭配 VS Code / 編輯器

推薦節奏：

1. 在 Yazi 中瀏覽專案結構、定位檔案
2. 按 `o` 或 `Enter` 用 `$EDITOR` 開啟檔案
3. 編輯完成後回到 Yazi 繼續瀏覽

確保 `$EDITOR` 環境變數已設定：

```bash
# ~/.bashrc 或 ~/.zshrc
export EDITOR="code --wait"   # VS Code
# export EDITOR="nvim"        # Neovim
```

### 搭配 Claude Code / OpenCode

在 AI 輔助開發流程中，Yazi 適合作為：

- 快速確認 AI 產生的檔案結構
- 批次重命名或搬移檔案
- 搭配 Tab 管理在多個專案目錄間切換

### Shell Wrapper（多 Shell 支援）

Shell wrapper 讓退出 Yazi 時自動切換到最後瀏覽的目錄。

**Bash / Zsh**（已在快速開始中介紹）：

```bash
function y() {
  local tmp="$(mktemp -t "yazi-cwd.XXXXXX")" cwd
  command yazi "$@" --cwd-file="$tmp"
  IFS= read -r -d '' cwd < "$tmp"
  [ "$cwd" != "$PWD" ] && [ -d "$cwd" ] && builtin cd -- "$cwd"
  rm -f -- "$tmp"
}
```

**Fish**：

```fish
function y
    set tmp (mktemp -t "yazi-cwd.XXXXXX")
    yazi $argv --cwd-file="$tmp"
    if set cwd (cat -- "$tmp"); and [ -n "$cwd" ]; and [ "$cwd" != "$PWD" ]
        cd -- "$cwd"
    end
    rm -f -- "$tmp"
end
```

**PowerShell**：

```powershell
function y {
    $tmp = [System.IO.Path]::GetTempFileName()
    yazi $args --cwd-file="$tmp"
    $cwd = Get-Content -Path $tmp
    if (-not [String]::IsNullOrEmpty($cwd) -and $cwd -ne $PWD.Path) {
        Set-Location -LiteralPath $cwd
    }
    Remove-Item -Path $tmp
}
```

**Nushell**：

```nushell
def --env y [...args] {
    let tmp = (mktemp -t "yazi-cwd.XXXXXX")
    yazi ...$args --cwd-file $tmp
    let cwd = (open $tmp)
    if $cwd != "" and $cwd != $env.PWD {
        cd $cwd
    }
    rm -fp $tmp
}
```

> 使用 `y` 啟動時，按 `q` 退出會切換到最後瀏覽的目錄；按 `Q` 退出則不切換。

---

## 遠端檔案傳輸（SFTP/SSH）

如果你平常就是走 SSH，Yazi 可用外掛補上遠端檔案工作流。

### 方案 A：`sshfs.yazi`（SFTP/SSH 優先推薦）

適用情境：

- 你已經有 `~/.ssh/config`
- 想把遠端目錄掛載後，像本地檔案一樣操作

安裝需求：

- Linux/macOS
- 系統需有 `sshfs`

安裝與設定：

```bash
ya pkg add uhs-robert/sshfs
```

`~/.config/yazi/init.lua`：

```lua
require("sshfs"):setup()
```

`~/.config/yazi/keymap.toml`（建議最小鍵位）：

```toml
[mgr]
prepend_keymap = [
  { on = ["M", "s"], run = "plugin sshfs -- menu", desc = "Open SSHFS menu" },
]
```

使用方式：

- `M s` 開啟 SSHFS 功能選單
- 常用動作：mount + jump、unmount、jump to mount、add/remove host

### 方案 B：`gvfs.yazi`（Linux 多協定掛載，含 SFTP）

適用情境：

- Linux 桌面環境，想要同時處理 SFTP/SMB/NFS/FTP 等協定

安裝需求（Linux）：

- `gvfs` + `glib`，且有 DBus Session
- 依需求安裝協定 backend（例如 `gvfs-backends`）

安裝與設定：

```bash
ya pkg add boydaihungst/gvfs
```

`~/.config/yazi/init.lua`：

```lua
require("gvfs"):setup()
```

`~/.config/yazi/keymap.toml`（建議最小鍵位）：

```toml
[mgr]
prepend_keymap = [
  { on = ["M", "m"], run = "plugin gvfs -- select-then-mount --jump", desc = "Mount and jump" },
  { on = ["M", "u"], run = "plugin gvfs -- select-then-unmount", desc = "Unmount" },
  { on = ["M", "a"], run = "plugin gvfs -- add-mount", desc = "Add SFTP/SMB/FTP URI" },
  { on = ["g", "m"], run = "plugin gvfs -- jump-to-device", desc = "Jump to mounted device" },
]
```

使用方式（以 SFTP 為例）：

1. `M a` 新增 mount URI（例如 `sftp://user@host/home/user`）
2. `M m` 選擇並掛載，掛載後自動跳轉
3. 完成後 `M u` 卸載

選型建議：

- 日常 SSH/SFTP：優先 `sshfs.yazi`
- 多協定整合：使用 `gvfs.yazi`

---

## 常見問題

### 預覽異常或功能缺失

- 先檢查依賴版本是否過舊（`ffmpeg`, `ripgrep`, `fd` 等）。
- 確認 `file` 指令可用：Yazi 依賴 `file` 判斷 MIME 類型，若缺少會導致預覽失效。
- 圖片預覽需要終端支援（Kitty、iTerm2、Sixel 等協定），純 SSH 環境可能無法顯示。

### Windows 無法正確判斷類型

- 檢查 `YAZI_FILE_ONE` 是否正確指向 Git for Windows 的 `file.exe`。
- 典型路徑：`C:\Program Files\Git\usr\bin\file.exe`。

### 設定沒有生效

- 確認實際使用的設定目錄（是否設定了 `YAZI_CONFIG_HOME`）。
- 檢查 TOML 語法是否正確，Yazi 遇到語法錯誤會靜默使用預設值。
- 使用 `yazi --debug` 可檢視載入的設定檔路徑。

### 快捷鍵與 Zellij / tmux 衝突

- Yazi 使用 `Ctrl+` 組合鍵（如 `Ctrl+a` 全選、`Ctrl+d` 半頁捲動）可能與多工器衝突。
- Zellij：切換至 Locked 模式（`Ctrl+g`），或使用 Normal 模式（按鍵會直接傳遞給 Yazi）。
- tmux：使用 `Ctrl+b` 前綴鍵避開，或自訂 Yazi 的 `keymap.toml` 改用其他按鍵。

### 中文 / Unicode 顯示異常

- 確認終端使用支援 Unicode 的字型（推薦 Nerd Font）。
- Yazi 的圖示顯示依賴 Nerd Font，安裝後需在終端模擬器中指定為主要字型。

---

## 參考資料

- 官方文件（Installation）：https://yazi-rs.github.io/docs/installation
- 官方文件（Quick Start）：https://yazi-rs.github.io/docs/quick-start
- 官方文件（Configuration）：https://yazi-rs.github.io/docs/configuration/overview
- 官方文件（Resources/Plugins）：https://yazi-rs.github.io/docs/resources
- sshfs.yazi README：https://github.com/uhs-robert/sshfs.yazi
- gvfs.yazi README：https://github.com/boydaihungst/gvfs.yazi
- GitHub Releases：https://github.com/sxyazi/yazi/releases
