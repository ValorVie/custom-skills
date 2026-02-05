# WezTerm 終端模擬器完整指南

## 目錄

- [簡介與特色](#簡介與特色)
- [安裝方式](#安裝方式)
- [配置檔路徑](#配置檔路徑)
- [推薦設定](#推薦設定)
- [主題安裝](#主題安裝)
- [常用快捷鍵](#常用快捷鍵)
- [自訂快捷鍵](#自訂快捷鍵)
- [分頁與分割視窗](#分頁與分割視窗)
- [搭配工具建議](#搭配工具建議)

---

## 簡介與特色

[WezTerm](https://wezterm.org/) 是一款以 Rust 語言撰寫的現代終端模擬器，由 @wez 開發維護。其核心特色如下：

- **GPU 加速渲染** -- 透過 OpenGL/Metal/DirectX 進行畫面渲染，效能優異。
- **內建多工管理** -- 原生支援分頁（Tabs）與分割視窗（Panes），無需額外安裝 tmux。
- **Lua 配置語言** -- 使用 Lua 5.4 作為配置語言，支援條件判斷、函式、模組化配置。
- **跨平台支援** -- 可在 macOS、Linux、Windows 及 FreeBSD 系統上運行。
- **內建 735+ 色彩主題** -- 開箱即用，無需額外下載主題檔案。
- **Nerd Font 內建支援** -- 預設 fallback 包含 Nerd Font Symbols，不需特製字型也能顯示圖示。
- **SSH 與遠端連線** -- 內建 SSH 客戶端與多工支援。
- **即時重新載入** -- 修改配置後自動套用，無需重啟。

---

## 安裝方式

### Windows

```powershell
# winget（推薦）
winget install wez.wezterm

# Scoop
scoop install wezterm

# Chocolatey
choco install wezterm
```

### macOS

使用 Homebrew 安裝（推薦）：

```bash
brew install --cask wezterm
```

### Linux

各主要發行版的安裝方式：

```bash
# Debian / Ubuntu（官方 APT 倉庫）
curl -fsSL https://apt.fury.io/wez/gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/wezterm-fury.gpg
echo 'deb [signed-by=/etc/apt/keyrings/wezterm-fury.gpg] https://apt.fury.io/wez/ * *' | sudo tee /etc/apt/sources.list.d/wezterm.list
sudo apt update
sudo apt install wezterm

# Fedora（COPR）
sudo dnf copr enable wezfurlong/wezterm-nightly
sudo dnf install wezterm

# Arch Linux
sudo pacman -S wezterm

# Flatpak（通用）
flatpak install flathub org.wezfurlong.wezterm
```

### 從原始碼編譯

```bash
# 確保已安裝 Rust toolchain
git clone --depth=1 --branch=main https://github.com/wezterm/wezterm.git
cd wezterm
git submodule update --init --recursive
cargo build --release
```

---

## 配置檔路徑

WezTerm 使用 Lua 格式的配置檔。根據作業系統不同，預設路徑如下：

| 作業系統 | 配置檔路徑 |
|----------|-----------|
| Linux / macOS | `~/.wezterm.lua` 或 `~/.config/wezterm/wezterm.lua` |
| Windows | `%USERPROFILE%\.wezterm.lua` 或 `%USERPROFILE%\.config\wezterm\wezterm.lua` |

若配置檔不存在，需手動建立：

```bash
# Linux / macOS
touch ~/.wezterm.lua

# 或使用目錄結構（推薦，便於模組化）
mkdir -p ~/.config/wezterm
touch ~/.config/wezterm/wezterm.lua
```

```powershell
# Windows PowerShell
New-Item -Path "$env:USERPROFILE\.wezterm.lua" -ItemType File
```

### 配置檔基本結構

WezTerm 配置檔必須是有效的 Lua 腳本，並回傳一個 config table：

```lua
-- ~/.wezterm.lua
local wezterm = require 'wezterm'
local config = {}

-- 在此加入配置...

return config
```

---

## 推薦設定

以下是一份實用的完整配置範例，涵蓋常見的自訂需求：

```lua
-- ~/.wezterm.lua
local wezterm = require 'wezterm'
local config = {}

-- 使用 config_builder 可獲得更好的錯誤提示（WezTerm 20230320+）
if wezterm.config_builder then
  config = wezterm.config_builder()
end

-- ============================================================
-- 一般設定
-- ============================================================
config.automatically_reload_config = true
config.check_for_updates = true

-- ============================================================
-- 視窗設定
-- ============================================================
config.window_decorations = "RESIZE"  -- 隱藏標題列但保留調整大小功能
config.window_background_opacity = 0.95
config.window_padding = {
  left = 8,
  right = 8,
  top = 8,
  bottom = 8,
}
config.initial_rows = 30
config.initial_cols = 120

-- ============================================================
-- 字型設定
-- ============================================================
config.font = wezterm.font_with_fallback {
  'Maple Mono NL NF CN',
  'JetBrains Mono',
  'Noto Color Emoji',
}
config.font_size = 14.0
config.line_height = 1.1

-- ============================================================
-- 游標設定
-- ============================================================
config.default_cursor_style = 'BlinkingBlock'
config.cursor_blink_rate = 500
config.cursor_blink_ease_in = 'Constant'
config.cursor_blink_ease_out = 'Constant'

-- ============================================================
-- 分頁列設定
-- ============================================================
config.enable_tab_bar = true
config.hide_tab_bar_if_only_one_tab = false
config.use_fancy_tab_bar = true
config.tab_bar_at_bottom = false
config.show_tab_index_in_tab_bar = true

-- ============================================================
-- 捲動設定
-- ============================================================
config.scrollback_lines = 10000
config.enable_scroll_bar = false

-- ============================================================
-- 色彩主題
-- ============================================================
-- WezTerm 內建 735+ 主題，可直接使用名稱
config.color_scheme = 'Catppuccin Mocha'

-- 或自訂顏色（以 Vesper 主題為例）
-- config.colors = {
--   foreground = '#ffffff',
--   background = '#101010',
--   cursor_bg = '#ffffff',
--   cursor_fg = '#101010',
--   selection_bg = '#b0b0b0',
--   selection_fg = '#101010',
--   ansi = {
--     '#101010', '#f5a191', '#90b99f', '#e6b99d',
--     '#aca1cf', '#e29eca', '#ea83a5', '#a0a0a0',
--   },
--   brights = {
--     '#7e7e7e', '#ff8080', '#99ffe4', '#ffc799',
--     '#b9aeda', '#ecaad6', '#f591b2', '#ffffff',
--   },
-- }

-- ============================================================
-- 預設 Shell（Windows 專用）
-- ============================================================
-- 若在 Windows 上想預設使用 PowerShell 7 或 WSL
-- config.default_prog = { 'pwsh.exe' }
-- config.default_prog = { 'wsl.exe', '-d', 'Ubuntu' }

return config
```

### 推薦字型

以下字型都適合在終端中使用：

| 字型名稱 | 特色 |
|----------|------|
| Maple Mono NL NF CN | 支援中文與 Nerd Font 圖示，適合亞洲使用者 |
| JetBrains Mono | JetBrains 出品，專為程式碼設計，清晰易讀 |
| FiraCode Nerd Font | 支援 ligature 與 Nerd Font 圖示 |
| Cascadia Code | Microsoft 出品，Windows Terminal 預設字型 |
| Hack Nerd Font | 經典等寬字型，辨識度高 |

> **提示**：WezTerm 內建 Nerd Font Symbols fallback，即使主要字型不是 Nerd Font 版本，也能正確顯示 Powerline 與 Nerd Font 圖示。

---

## 主題安裝

WezTerm 內建超過 735 種色彩主題，無需額外下載。

### 查看所有可用主題

```bash
wezterm ls-fonts --list-builtin-color-schemes
```

或參考官方文件：[Color Schemes](https://wezterm.org/colorschemes/index.html)

### 套用主題

在配置檔中直接指定主題名稱：

```lua
config.color_scheme = 'Tokyo Night'
```

### 熱門主題推薦

| 主題名稱 | 風格描述 |
|----------|----------|
| `Catppuccin Mocha` | 柔和粉彩色系，社群活躍且持續更新 |
| `Tokyo Night` | 冷色調夜景風格，藍紫色系為主 |
| `Gruvbox Dark (Gogh)` | 暖色調復古風格，對比適中 |
| `Dracula` | 經典紫色暗色主題，辨識度高 |
| `Nord` | 北歐極簡風格，藍灰色系，低對比護眼 |
| `One Dark (Gogh)` | Atom 編輯器風格，受歡迎的深色主題 |
| `Solarized Dark` | 經典 Solarized 配色 |

### 根據時間自動切換主題

```lua
local function scheme_for_appearance(appearance)
  if appearance:find 'Dark' then
    return 'Catppuccin Mocha'
  else
    return 'Catppuccin Latte'
  end
end

config.color_scheme = scheme_for_appearance(wezterm.gui.get_appearance())
```

---

## 常用快捷鍵

以下是 WezTerm 內建的預設快捷鍵。

### 分頁操作

| 功能 | macOS | Windows / Linux |
|------|-------|-----------------|
| 新增分頁 | `Cmd + T` | `Ctrl + Shift + T` |
| 關閉分頁 | `Cmd + W` | `Ctrl + Shift + W` |
| 切換到第 N 個分頁 | `Cmd + 1~9` | `Ctrl + Shift + 1~9` 或 `Alt + 1~9` |
| 上一個分頁 | `Cmd + Shift + [` | `Ctrl + Shift + Tab` |
| 下一個分頁 | `Cmd + Shift + ]` | `Ctrl + Tab` |
| 移動分頁（向左） | `Ctrl + Shift + PageUp` | `Ctrl + Shift + PageUp` |
| 移動分頁（向右） | `Ctrl + Shift + PageDown` | `Ctrl + Shift + PageDown` |

### 分割視窗操作

| 功能 | macOS | Windows / Linux |
|------|-------|-----------------|
| 水平分割 | `Cmd + Shift + D` | `Ctrl + Shift + Alt + %` |
| 垂直分割 | `Cmd + D` | `Ctrl + Shift + Alt + "` |
| 切換面板 | `Cmd + [` / `Cmd + ]` | `Ctrl + Shift + Arrow` |
| 關閉面板 | `Cmd + W` | `Ctrl + Shift + W` |
| 調整面板大小 | `Cmd + Shift + Arrow` | `Ctrl + Shift + Alt + Arrow` |
| 全螢幕切換當前面板 | `Cmd + Z` | `Ctrl + Shift + Z` |

### 複製貼上

| 功能 | macOS | Windows / Linux |
|------|-------|-----------------|
| 複製 | `Cmd + C` | `Ctrl + Shift + C` |
| 貼上 | `Cmd + V` | `Ctrl + Shift + V` |
| 快速複製（選取即複製） | 需配置 | 需配置 |

### 字型縮放

| 功能 | macOS | Windows / Linux |
|------|-------|-----------------|
| 放大字型 | `Cmd + =` | `Ctrl + =` |
| 縮小字型 | `Cmd + -` | `Ctrl + -` |
| 重設字型大小 | `Cmd + 0` | `Ctrl + 0` |

### 搜尋

| 功能 | macOS | Windows / Linux |
|------|-------|-----------------|
| 開啟搜尋 | `Cmd + F` | `Ctrl + Shift + F` |
| 搜尋下一筆 | `Enter` 或 `Cmd + G` | `Enter` |
| 搜尋上一筆 | `Shift + Enter` 或 `Cmd + Shift + G` | `Shift + Enter` |

### 其他

| 功能 | macOS | Windows / Linux |
|------|-------|-----------------|
| 開啟命令面板 | `Cmd + Shift + P` | `Ctrl + Shift + P` |
| 全螢幕切換 | `Cmd + Enter` | `Alt + Enter` 或 `F11` |
| 顯示除錯覆蓋層 | `Ctrl + Shift + L` | `Ctrl + Shift + L` |

---

## 自訂快捷鍵

WezTerm 允許在配置檔中完全自訂快捷鍵。

### 基本語法

```lua
config.keys = {
  {
    key = '按鍵',
    mods = '修飾鍵',
    action = wezterm.action.動作名稱,
  },
}
```

### 實用範例

```lua
local act = wezterm.action

config.keys = {
  -- 使用 Cmd+D 垂直分割（macOS 風格）
  {
    key = 'd',
    mods = 'CMD',
    action = act.SplitVertical { domain = 'CurrentPaneDomain' },
  },

  -- 使用 Cmd+Shift+D 水平分割
  {
    key = 'd',
    mods = 'CMD|SHIFT',
    action = act.SplitHorizontal { domain = 'CurrentPaneDomain' },
  },

  -- 使用 Ctrl+Shift+方向鍵 切換面板
  {
    key = 'LeftArrow',
    mods = 'CTRL|SHIFT',
    action = act.ActivatePaneDirection 'Left',
  },
  {
    key = 'RightArrow',
    mods = 'CTRL|SHIFT',
    action = act.ActivatePaneDirection 'Right',
  },
  {
    key = 'UpArrow',
    mods = 'CTRL|SHIFT',
    action = act.ActivatePaneDirection 'Up',
  },
  {
    key = 'DownArrow',
    mods = 'CTRL|SHIFT',
    action = act.ActivatePaneDirection 'Down',
  },

  -- 使用 Cmd+K 清除螢幕與捲動歷史
  {
    key = 'k',
    mods = 'CMD',
    action = act.ClearScrollback 'ScrollbackAndViewport',
  },

  -- 使用 Cmd+Shift+Enter 切換全螢幕
  {
    key = 'Enter',
    mods = 'CMD|SHIFT',
    action = act.ToggleFullScreen,
  },

  -- 快速開啟特定程式（例如 htop）
  {
    key = 'h',
    mods = 'CTRL|SHIFT',
    action = act.SpawnCommandInNewTab {
      args = { 'htop' },
    },
  },
}
```

### 常用 Action 清單

| Action 名稱 | 說明 |
|-------------|------|
| `Copy` | 複製選取內容 |
| `Paste` | 貼上剪貼簿內容 |
| `SpawnTab 'CurrentPaneDomain'` | 新增分頁 |
| `CloseCurrentTab { confirm = true }` | 關閉當前分頁（帶確認） |
| `CloseCurrentPane { confirm = true }` | 關閉當前面板（帶確認） |
| `SplitVertical { domain = 'CurrentPaneDomain' }` | 垂直分割 |
| `SplitHorizontal { domain = 'CurrentPaneDomain' }` | 水平分割 |
| `ActivatePaneDirection 'Left/Right/Up/Down'` | 切換面板方向 |
| `AdjustPaneSize { 'Left', 5 }` | 調整面板大小 |
| `TogglePaneZoomState` | 切換面板全螢幕 |
| `ActivateTab(n)` | 切換到第 n 個分頁（從 0 開始） |
| `ActivateTabRelative(1/-1)` | 切換到下/上一個分頁 |
| `ClearScrollback 'ScrollbackAndViewport'` | 清除螢幕與歷史 |
| `ToggleFullScreen` | 切換全螢幕 |
| `ShowLauncher` | 顯示啟動器選單 |
| `ShowTabNavigator` | 顯示分頁導覽 |
| `ActivateCopyMode` | 進入複製模式（類似 Vi Mode） |
| `Search { CaseSensitiveString = '' }` | 開啟搜尋 |

---

## 分頁與分割視窗

WezTerm 原生支援分頁（Tabs）與分割視窗（Panes），這是相較於 Alacritty 的主要優勢。

### 分頁操作

```lua
-- 新增分頁
wezterm.action.SpawnTab 'CurrentPaneDomain'

-- 關閉分頁
wezterm.action.CloseCurrentTab { confirm = true }

-- 切換分頁
wezterm.action.ActivateTab(0)           -- 第一個分頁
wezterm.action.ActivateTabRelative(1)   -- 下一個分頁
wezterm.action.ActivateTabRelative(-1)  -- 上一個分頁
```

### 分割視窗操作

```lua
-- 垂直分割（上下）
wezterm.action.SplitVertical { domain = 'CurrentPaneDomain' }

-- 水平分割（左右）
wezterm.action.SplitHorizontal { domain = 'CurrentPaneDomain' }

-- 自訂分割（指定方向、大小、程式）
wezterm.action.SplitPane {
  direction = 'Right',           -- 'Up', 'Down', 'Left', 'Right'
  size = { Percent = 30 },       -- 或 { Cells = 20 }
  command = { args = { 'htop' } },
}

-- 切換面板焦點
wezterm.action.ActivatePaneDirection 'Left'
wezterm.action.ActivatePaneDirection 'Right'
wezterm.action.ActivatePaneDirection 'Up'
wezterm.action.ActivatePaneDirection 'Down'

-- 調整面板大小
wezterm.action.AdjustPaneSize { 'Left', 5 }
wezterm.action.AdjustPaneSize { 'Right', 5 }

-- 面板全螢幕切換（Zoom）
wezterm.action.TogglePaneZoomState
```

### 完整的分割視窗配置範例

```lua
config.keys = {
  -- 分割視窗
  { key = '-', mods = 'CTRL|SHIFT', action = act.SplitVertical { domain = 'CurrentPaneDomain' } },
  { key = '\\', mods = 'CTRL|SHIFT', action = act.SplitHorizontal { domain = 'CurrentPaneDomain' } },

  -- 切換面板（使用 Alt + 方向鍵）
  { key = 'LeftArrow', mods = 'ALT', action = act.ActivatePaneDirection 'Left' },
  { key = 'RightArrow', mods = 'ALT', action = act.ActivatePaneDirection 'Right' },
  { key = 'UpArrow', mods = 'ALT', action = act.ActivatePaneDirection 'Up' },
  { key = 'DownArrow', mods = 'ALT', action = act.ActivatePaneDirection 'Down' },

  -- 調整面板大小（使用 Alt + Shift + 方向鍵）
  { key = 'LeftArrow', mods = 'ALT|SHIFT', action = act.AdjustPaneSize { 'Left', 5 } },
  { key = 'RightArrow', mods = 'ALT|SHIFT', action = act.AdjustPaneSize { 'Right', 5 } },
  { key = 'UpArrow', mods = 'ALT|SHIFT', action = act.AdjustPaneSize { 'Up', 5 } },
  { key = 'DownArrow', mods = 'ALT|SHIFT', action = act.AdjustPaneSize { 'Down', 5 } },

  -- 面板 Zoom
  { key = 'z', mods = 'CTRL|SHIFT', action = act.TogglePaneZoomState },

  -- 關閉面板
  { key = 'w', mods = 'CTRL|SHIFT', action = act.CloseCurrentPane { confirm = true } },
}
```

---

## 搭配工具建議

雖然 WezTerm 已內建多工功能，但仍可搭配以下工具強化終端體驗。

### 提示列美化（Prompt）

| 工具 | 說明 |
|------|------|
| [Starship](https://starship.rs/) | 以 Rust 撰寫的跨 Shell 提示列，速度快、高度可自訂 |
| [Oh My Posh](https://ohmyposh.dev/) | 跨平台提示列，支援 PowerShell、Bash、Zsh 等 |

```bash
# 安裝 Starship
brew install starship          # macOS
winget install Starship.Starship  # Windows

# 加入 Shell 設定（以 Zsh 為例）
echo 'eval "$(starship init zsh)"' >> ~/.zshrc

# PowerShell
Add-Content $PROFILE 'Invoke-Expression (&starship init powershell)'
```

### 目錄跳轉

| 工具 | 說明 |
|------|------|
| [zoxide](https://github.com/ajeetdsouza/zoxide) | 智慧型 `cd` 替代工具，記住常用目錄 |

```bash
# 安裝
brew install zoxide            # macOS
winget install ajeetdsouza.zoxide  # Windows

# 使用方式
z projects    # 跳轉至最常存取的含 "projects" 的目錄
zi            # 互動式選擇目錄
```

### 模糊搜尋

| 工具 | 說明 |
|------|------|
| [fzf](https://github.com/junegunn/fzf) | 通用型模糊搜尋工具 |

```bash
# 安裝
brew install fzf               # macOS
winget install junegunn.fzf    # Windows

# 常用操作
Ctrl + R    # 模糊搜尋指令歷史
Ctrl + T    # 模糊搜尋檔案
```

### 現代 CLI 工具

| 工具 | 取代 | 說明 |
|------|------|------|
| [eza](https://github.com/eza-community/eza) | `ls` | 現代化的檔案列表，支援圖示與 Git 狀態 |
| [bat](https://github.com/sharkdp/bat) | `cat` | 語法高亮的檔案檢視器 |
| [ripgrep](https://github.com/BurntSushi/ripgrep) | `grep` | 極快的搜尋工具 |
| [fd](https://github.com/sharkdp/fd) | `find` | 更簡潔的檔案搜尋 |
| [delta](https://github.com/dandavison/delta) | `diff` | 美化的 Git diff 輸出 |

### 推薦工具組合總覽

```
WezTerm（終端模擬器 + 內建多工）
  + Starship 或 Oh My Posh（提示列）
  + zoxide（目錄跳轉）
  + fzf（模糊搜尋）
  + eza / bat / ripgrep（現代 CLI 工具）
  + Nerd Font 字型（圖示支援，WezTerm 已內建 fallback）
```

---

## 與 Alacritty 比較

| 功能 | WezTerm | Alacritty |
|------|---------|-----------|
| 分頁（Tabs） | 內建支援 | 不支援 |
| 分割視窗（Panes） | 內建支援 | 不支援 |
| 配置語言 | Lua | TOML |
| 內建主題 | 735+ | 需下載 |
| Nerd Font fallback | 內建 | 需手動配置 |
| SSH 客戶端 | 內建 | 不支援 |
| 即時重載配置 | 支援 | 支援 |
| GPU 加速 | 支援 | 支援 |
| 維護狀態 | 業餘專案（活躍） | 緩慢 |

**選擇建議**：
- 如果需要分頁/分割視窗且不想用 tmux → **WezTerm**
- 如果追求極簡且會搭配 tmux/zellij → **Alacritty**
- 如果在 Windows 原生環境 → **WezTerm**（內建多工更方便）

---

## 參考資源

- [WezTerm 官方文件](https://wezterm.org/)
- [WezTerm GitHub](https://github.com/wezterm/wezterm)
- [WezTerm 色彩主題列表](https://wezterm.org/colorschemes/index.html)
- [WezTerm Lua 配置參考](https://wezterm.org/config/lua/general.html)
