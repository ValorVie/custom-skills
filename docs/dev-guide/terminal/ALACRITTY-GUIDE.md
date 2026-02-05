# Alacritty 終端模擬器完整指南

## 目錄

- [簡介與特色](#簡介與特色)
- [安裝方式](#安裝方式)
- [配置檔路徑](#配置檔路徑)
- [推薦設定](#推薦設定)
- [主題安裝](#主題安裝)
- [常用快捷鍵](#常用快捷鍵)
- [自訂快捷鍵](#自訂快捷鍵)
- [搭配工具建議](#搭配工具建議)

---

## 簡介與特色

[Alacritty](https://alacritty.org/) 是一款以 Rust 語言撰寫的現代終端模擬器，主打效能與簡潔。其核心特色如下：

- **GPU 加速渲染** -- 透過 OpenGL 進行畫面渲染，滾動與輸出大量文字時明顯比傳統終端流暢。
- **以 Rust 撰寫** -- 記憶體安全且執行效率高，不易發生崩潰。
- **跨平台支援** -- 可在 macOS、Linux、Windows 及 BSD 系統上運行，配置檔格式一致。
- **合理的預設值** -- 開箱即用，不需要大量配置就能獲得良好的使用體驗。
- **無內建分頁或分割視窗** -- Alacritty 專注於做好「終端模擬」這一件事，多工管理交由 tmux 或 Zellij 等工具處理。
- **TOML 格式配置** -- 使用簡潔易讀的 TOML 格式，支援即時重新載入（live reload）。

---

## 安裝方式

### macOS

使用 Homebrew 安裝（推薦）：

```bash
brew install --cask alacritty
```

### Linux

各主要發行版的安裝方式：

```bash
# Debian / Ubuntu
sudo apt install alacritty

# Fedora
sudo dnf install alacritty

# Arch Linux
sudo pacman -S alacritty

# 使用 Cargo（適用於所有發行版）
cargo install alacritty
```

> **注意**：透過 `cargo install` 安裝時，需先確保系統已安裝必要的開發依賴，包括 `cmake`、`pkg-config`、`libfreetype6-dev`、`libfontconfig1-dev` 等。

### Windows

```bash
# winget（推薦）
winget install Alacritty.Alacritty

# Scoop
scoop install alacritty

# Chocolatey
choco install alacritty
```

### 從原始碼編譯

若想使用最新開發版本，可直接從原始碼編譯：

```bash
# 確保已安裝 Rust toolchain
rustup override set stable
rustup update stable

# 透過 Cargo 編譯安裝
cargo install alacritty
```

---

## 配置檔路徑

Alacritty 使用 TOML 格式的配置檔。根據作業系統不同，預設路徑如下：

| 作業系統 | 配置檔路徑 |
|----------|-----------|
| Linux / macOS | `~/.config/alacritty/alacritty.toml` |
| Windows | `%APPDATA%\alacritty\alacritty.toml` |

若配置檔不存在，需手動建立：

```bash
# Linux / macOS
mkdir -p ~/.config/alacritty
touch ~/.config/alacritty/alacritty.toml
```

### 即時重新載入

Alacritty 支援 `live_config_reload` 功能。啟用後，儲存配置檔時終端會即時套用變更，無需重新啟動。這在調整字型、顏色等視覺設定時非常方便。

---

## 推薦設定

以下是一份實用的完整配置範例，涵蓋常見的自訂需求：

```toml
# ~/.config/alacritty/alacritty.toml

# ============================================================
# 一般設定
# ============================================================
[general]
live_config_reload = true

# ============================================================
# 視窗設定
# ============================================================
[window]
dynamic_padding = true
decorations = "Full"
opacity = 0.95
startup_mode = "Windowed"

[window.padding]
x = 8
y = 8

# ============================================================
# 字型設定
# ============================================================
[font]
size = 14.0

[font.normal]
family = "Maple Mono NL NF CN"
style = "Regular"

[font.bold]
family = "Maple Mono NL NF CN"
style = "Bold"

[font.italic]
family = "Maple Mono NL NF CN"
style = "Italic"

[font.bold_italic]
family = "Maple Mono NL NF CN"
style = "Bold Italic"

[font.offset]
x = 0
y = 2

# ============================================================
# 游標設定
# ============================================================
[cursor]
unfocused_hollow = true

[cursor.style]
shape = "Block"
blinking = "On"

[cursor.vi_mode_style]
shape = "Beam"
blinking = "Off"

# ============================================================
# 捲動設定
# ============================================================
[scrolling]
history = 10000
multiplier = 3

# ============================================================
# 選取設定
# ============================================================
[selection]
save_to_clipboard = true

# ============================================================
# 顏色主題 - Vesper（黑底白字）
# 來源：https://github.com/raunofreiberg/vesper
# ============================================================
[colors.primary]
background = "#101010"
foreground = "#ffffff"

[colors.cursor]
text    = "#101010"
cursor  = "#ffffff"

[colors.selection]
text       = "#101010"
background = "#b0b0b0"

[colors.normal]
black   = "#101010"
red     = "#f5a191"
green   = "#90b99f"
yellow  = "#e6b99d"
blue    = "#aca1cf"
magenta = "#e29eca"
cyan    = "#ea83a5"
white   = "#a0a0a0"

[colors.bright]
black   = "#7e7e7e"
red     = "#ff8080"
green   = "#99ffe4"
yellow  = "#ffc799"
blue    = "#b9aeda"
magenta = "#ecaad6"
cyan    = "#f591b2"
white   = "#ffffff"
```

### 推薦字型

以下字型都適合在終端中使用，且支援 ligature 或 Nerd Font 圖示：

| 字型名稱 | 特色 |
|----------|------|
| Maple Mono NL NF CN | JetBrains 出品，專為程式碼設計，清晰易讀 |
| FiraCode Nerd Font | 支援 ligature 與 Nerd Font 圖示，搭配 Starship 等工具最佳 |
| Cascadia Code | Microsoft 出品，Windows Terminal 預設字型 |
| Hack Nerd Font | 經典等寬字型，辨識度高 |
| Iosevka | 極窄設計，適合小螢幕或需要更多欄位的場景 |

安裝 Nerd Font 的方式（macOS）：

```bash
brew install --cask font-jetbrains-mono-nerd-font
brew install --cask font-fira-code-nerd-font
```

---

## 主題安裝

Alacritty 官方維護了一個主題倉庫 [alacritty-theme](https://github.com/alacritty/alacritty-theme)，收錄了大量社群製作的色彩主題。

### 下載主題

```bash
git clone https://github.com/alacritty/alacritty-theme ~/.config/alacritty/themes
```

### 套用主題

在配置檔的 `[general]` 區段中使用 `import` 匯入主題檔案：

```toml
[general]
import = ["~/.config/alacritty/themes/themes/gruvbox_dark.toml"]
live_config_reload = true
```

> **注意**：`import` 中的路徑需指向 `themes/themes/` 目錄下的 `.toml` 檔案（注意有兩層 `themes`）。匯入的主題會覆蓋配置檔中對應的顏色設定。

### 切換主題

只需修改 `import` 路徑並儲存，啟用 `live_config_reload` 後即可即時預覽效果：

```toml
# 切換為 Tokyo Night
import = ["~/.config/alacritty/themes/themes/tokyo_night.toml"]

# 切換為 Catppuccin Mocha
import = ["~/.config/alacritty/themes/themes/catppuccin_mocha.toml"]
```

### 熱門主題推薦

| 主題名稱 | 檔案名稱 | 風格描述 |
|----------|----------|----------|
| Gruvbox Dark | `gruvbox_dark.toml` | 暖色調復古風格，對比適中，長時間使用舒適 |
| Tokyo Night | `tokyo_night.toml` | 冷色調夜景風格，藍紫色系為主 |
| Catppuccin Mocha | `catppuccin_mocha.toml` | 柔和粉彩色系，社群活躍且持續更新 |
| Dracula | `dracula.toml` | 經典紫色暗色主題，辨識度高 |
| Nord | `nord.toml` | 北歐極簡風格，藍灰色系，低對比護眼 |

### 瀏覽所有可用主題

```bash
ls ~/.config/alacritty/themes/themes/
```

---

## 常用快捷鍵

以下是 Alacritty 內建的常用快捷鍵。macOS 使用 `Cmd` 鍵，Linux / Windows 使用 `Ctrl` 鍵。

### 基本操作

| 功能 | macOS | Linux / Windows |
|------|-------|-----------------|
| 複製 | `Cmd + C` | `Ctrl + Shift + C` |
| 貼上 | `Cmd + V` | `Ctrl + Shift + V` |
| 開新視窗 | `Cmd + N` | `Ctrl + Shift + N` |
| 關閉視窗 | `Cmd + Q` | -- |
| 全螢幕切換 | `Cmd + Enter` | `F11` |

### 字型大小調整

| 功能 | macOS | Linux / Windows |
|------|-------|-----------------|
| 放大字型 | `Cmd + =` | `Ctrl + =` |
| 縮小字型 | `Cmd + -` | `Ctrl + -` |
| 重設字型大小 | `Cmd + 0` | `Ctrl + 0` |

### 搜尋與 Vi Mode

| 功能 | macOS | Linux / Windows |
|------|-------|-----------------|
| 開啟搜尋 | `Cmd + F` | `Ctrl + Shift + F` |
| 搜尋下一筆 | `Enter` | `Enter` |
| 搜尋上一筆 | `Shift + Enter` | `Shift + Enter` |
| 進入 Vi Mode | -- | `Ctrl + Shift + Space` |
| 離開 Vi Mode | `Escape` | `Escape` |

### Vi Mode 操作

進入 Vi Mode 後，可使用類似 Vim 的按鍵在畫面中移動與選取：

| 按鍵 | 功能 |
|------|------|
| `h` / `j` / `k` / `l` | 左 / 下 / 上 / 右 移動 |
| `w` / `b` | 前進 / 後退一個單字 |
| `0` / `$` | 移到行首 / 行尾 |
| `g` / `G` | 移到最頂端 / 最底端 |
| `v` | 開始選取 |
| `y` | 複製選取內容 |
| `/` | 向前搜尋 |
| `?` | 向後搜尋 |
| `n` / `N` | 下一筆 / 上一筆搜尋結果 |

---

## 自訂快捷鍵

Alacritty 允許在配置檔中自訂快捷鍵。使用 `[[keyboard.bindings]]` 區段定義每一組綁定。

### 基本語法

```toml
[[keyboard.bindings]]
key = "按鍵名稱"
mods = "修飾鍵"
action = "動作名稱"
```

### 實用範例

```toml
# 使用 Cmd+K 清除螢幕（macOS）
[[keyboard.bindings]]
key = "K"
mods = "Command"
action = "ClearHistory"

# 使用 Ctrl+Shift+T 開啟新視窗（Linux / Windows）
[[keyboard.bindings]]
key = "T"
mods = "Control|Shift"
action = "CreateNewWindow"

# 使用 Cmd+Shift+F 切換全螢幕（macOS）
[[keyboard.bindings]]
key = "F"
mods = "Command|Shift"
action = "ToggleFullscreen"

# 綁定快捷鍵執行指定程式（例如開啟 htop）
[[keyboard.bindings]]
key = "H"
mods = "Control|Shift"
command = { program = "htop" }
```

### 可用的 Action 清單

| Action 名稱 | 說明 |
|-------------|------|
| `Copy` | 複製選取內容 |
| `Paste` | 貼上剪貼簿內容 |
| `ClearHistory` | 清除捲動歷史 |
| `ResetFontSize` | 重設字型大小為預設值 |
| `IncreaseFontSize` | 放大字型 |
| `DecreaseFontSize` | 縮小字型 |
| `CreateNewWindow` | 開啟新視窗 |
| `ToggleFullscreen` | 切換全螢幕 |
| `ToggleViMode` | 切換 Vi Mode |
| `SearchForward` | 向前搜尋 |
| `SearchBackward` | 向後搜尋 |
| `None` | 取消預設綁定 |

---

## 搭配工具建議

Alacritty 不內建分頁、分割視窗或進階提示列功能，因此建議搭配以下工具來打造完整的終端工作環境。

### 多工管理（Multiplexer）

| 工具 | 說明 |
|------|------|
| [Zellij](https://zellij.dev/) | 以 Rust 撰寫的現代多工管理器，預設按鍵提示對新手友善，支援 floating pane 與 plugin 系統 |
| [tmux](https://github.com/tmux/tmux) | 歷史悠久的終端多工管理器，生態豐富，適合已熟悉 Vim 風格操作的使用者 |

搭配範例（Zellij）：

```bash
# 安裝
brew install zellij    # macOS
cargo install zellij   # 跨平台

# 啟動
zellij
```

搭配範例（tmux）：

```bash
# 安裝
brew install tmux      # macOS
sudo apt install tmux  # Debian / Ubuntu

# 啟動
tmux
```

### 提示列美化（Prompt）

| 工具 | 說明 |
|------|------|
| [Starship](https://starship.rs/) | 以 Rust 撰寫的跨 Shell 提示列，速度快、高度可自訂，支援 Git 狀態、語言版本等資訊顯示 |

```bash
# 安裝
brew install starship

# 加入 Shell 設定（以 Zsh 為例）
echo 'eval "$(starship init zsh)"' >> ~/.zshrc
```

> **提示**：使用 Starship 時建議搭配 Nerd Font 字型（如 `FiraCode Nerd Font`），以正確顯示圖示。

### 目錄跳轉

| 工具 | 說明 |
|------|------|
| [zoxide](https://github.com/ajeetdsouza/zoxide) | 智慧型 `cd` 替代工具，會記住你常用的目錄，輸入部分路徑即可跳轉 |

```bash
# 安裝
brew install zoxide

# 加入 Shell 設定（以 Zsh 為例）
echo 'eval "$(zoxide init zsh)"' >> ~/.zshrc

# 使用方式
z projects    # 跳轉至最常存取的含 "projects" 的目錄
zi            # 互動式選擇目錄
```

### 模糊搜尋

| 工具 | 說明 |
|------|------|
| [fzf](https://github.com/junegunn/fzf) | 通用型模糊搜尋工具，可整合至檔案搜尋、歷史指令搜尋、Git 操作等場景 |

```bash
# 安裝
brew install fzf

# 啟用快捷鍵綁定與自動補全
echo 'source <(fzf --zsh)' >> ~/.zshrc

# 常用操作
Ctrl + R    # 模糊搜尋指令歷史
Ctrl + T    # 模糊搜尋檔案
Alt  + C    # 模糊搜尋並跳轉目錄
```

### 推薦工具組合總覽

以下是一套經過驗證、彼此相容的終端工具組合：

```
Alacritty（終端模擬器）
  + Zellij 或 tmux（多工管理）
  + Starship（提示列）
  + zoxide（目錄跳轉）
  + fzf（模糊搜尋）
  + Nerd Font 字型（圖示支援）
```

這套組合全部以 Rust 或 Go 撰寫（fzf 為 Go），啟動速度快，資源佔用低，適合日常開發使用。
