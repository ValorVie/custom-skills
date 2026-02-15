# WezTerm 終端模擬器完整指南

## 目錄

- [簡介與特色](#簡介與特色)
- [安裝方式](#安裝方式)
- [配置檔路徑](#配置檔路徑)
- [推薦設定](#推薦設定)
- [跨平台支援](#跨平台支援)
- [主題安裝](#主題安裝)
- [常用快捷鍵](#常用快捷鍵)
- [自訂快捷鍵](#自訂快捷鍵)
- [分頁與分割視窗](#分頁與分割視窗)
- [搭配工具建議](#搭配工具建議)
- [WSL 圖片貼上（Claude Code 整合）](#wsl-圖片貼上claude-code-整合)

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

以下是一份社群推薦的完整配置範例，採用 **Zellij 風格的模式切換**操作模型，
透過 WezTerm 的 Key Table 機制實現。按下快捷鍵進入對應模式，模式內使用簡單按鍵操作，
`Esc` 返回正常模式。狀態列會即時顯示當前所在模式。

完整配置檔請參考 [`config/.wezterm.lua`](config/.wezterm.lua)。

以下說明設定的核心架構與跨平台設計。

### 設定架構總覽

```
.wezterm.lua
├── 平台偵測（is_windows / is_darwin / is_linux）
├── 一般設定（渲染引擎、dead keys、字體縮放行為）
├── 平台特定設定（macOS 右 Option、Windows Shell）
├── Mux Server（Session 持久化）
├── 視窗 / 字型 / 游標 / 分頁列 / 色彩主題
├── Tab 標題格式（format-tab-title 事件）
├── Session 儲存 / 還原（重開機後恢復佈局）
├── 狀態列（顯示當前模式 + 快捷鍵提示）
├── 快捷鍵速查面板（Ctrl+Shift+K）
├── 模式切換定義（data-driven，自動產生 Ctrl + macOS Cmd 版本）
├── 全域快捷鍵（Alt 系列、命令面板、Quick Select）
├── 條件式圖片貼上（僅 Windows/WSL）
├── Key Tables（7 個模式的操作定義）
├── macOS SUPER 攔截（動態插入 Nop 至所有 Key Table）
└── 滑鼠設定（選取複製、Ctrl+點擊開連結）
```

### 平台偵測

配置透過 `wezterm.target_triple` 自動偵測平台，並設定布林常數供後續條件判斷：

```lua
local is_windows = wezterm.target_triple:find('windows') ~= nil
local is_darwin  = wezterm.target_triple:find('darwin') ~= nil
local is_linux   = wezterm.target_triple:find('linux') ~= nil
```

### 資料驅動的模式切換

模式切換採用 table 定義 + 動態迴圈插入，避免手動重複 7 組綁定：

```lua
local mode_switches = {
  { key = 'p', name = 'pane',    desc = 'Pane 模式' },
  { key = 't', name = 'tab',     desc = 'Tab 模式' },
  { key = 'n', name = 'resize',  desc = 'Resize 模式' },
  { key = 's', name = 'scroll',  desc = 'Scroll 模式' },
  { key = 'o', name = 'session', desc = 'Session 模式' },
  { key = 'h', name = 'move',    desc = 'Move 模式' },
  { key = 'g', name = 'lock',    desc = 'Lock 模式' },
}

-- 自動產生 Ctrl 版（所有平台）+ Cmd 版（僅 macOS）
for _, m in ipairs(mode_switches) do
  table.insert(config.keys, {
    key = m.key, mods = 'CTRL',
    action = act.ActivateKeyTable { name = m.name, one_shot = false },
  })
  if is_darwin then
    table.insert(config.keys, {
      key = m.key, mods = 'SUPER',
      action = act.ActivateKeyTable { name = m.name, one_shot = false },
    })
  end
end
```

### 條件式功能（平台相關）

| 功能 | 平台 | 說明 |
|------|------|------|
| `send_composed_key_when_right_alt_is_pressed` | macOS | 讓右 Option 輸入 `~` `\` `\|` 等特殊字元 |
| `config.default_prog = { 'pwsh.exe' }` | Windows | 預設啟動 PowerShell 7 |
| `Ctrl+Alt+V` 圖片貼上 | Windows (WSL) | 透過 PowerShell 讀取剪貼簿，轉為 WSL 路徑 |
| `Cmd+鍵` 模式切換 | macOS | 自動產生 SUPER 版模式切換鍵 |
| SUPER Nop 攔截 | macOS | 在每個 Key Table 中攔截 Cmd 鍵防止模式穿透 |
| `macos_window_background_blur` | macOS | 毛玻璃背景效果（其他平台自動忽略） |

> **Zellij 風格模式速查表**：
>
> macOS 使用者可用 `Cmd` 代替 `Ctrl` 進入模式（自動偵測平台）。
>
> | 進入模式 | macOS 替代 | 模式名稱 | 模式內按鍵 | 功能 |
> |----------|-----------|----------|------------|------|
> | `Ctrl+P` | `Cmd+P` | **Pane** | `n` / `r` | 新增窗格（右邊） |
> | | | | `d` | 新增窗格（下方） |
> | | | | 方向鍵 / `hjkl` | 切換 Pane |
> | | | | `x` | 關閉 Pane |
> | | | | `f` | Zoom 全螢幕 |
> | `Ctrl+T` | `Cmd+T` | **Tab** | `n` | 新增 Tab |
> | | | | `x` | 關閉 Tab |
> | | | | 左右鍵 / `h` `l` | 切換 Tab |
> | | | | `Shift+左右` / `H` `L` | 移動 Tab 順序 |
> | | | | `1`~`9` | 跳到第 N 個 Tab |
> | | | | `r` | 重新命名 Tab |
> | `Ctrl+N` | `Cmd+N` | **Resize** | 方向鍵 / `hjkl` | 調整 Pane 大小 |
> | | | | `=` | 重設 Zoom |
> | `Ctrl+S` | `Cmd+S` | **Scroll** | 上下鍵 / `j` `k` | 逐行捲動 |
> | | | | `u` / `d` | 半頁上 / 下 |
> | | | | `s` | 搜尋 |
> | | | | `c` | 進入 Copy Mode |
> | `Ctrl+O` | `Cmd+O` | **Session** | `s` | 儲存 Session（佈局存檔） |
> | | | | `a` | 新增獨立 Workspace |
> | | | | `k` | 關閉 Mux Server（自動存檔） |
> | | | | `w` | 工作區選單 |
> | | | | `l` | 啟動器 |
> | | | | `t` | Tab 導覽 |
> | | | | `d` | 除錯覆蓋層 |
> | `Ctrl+H` | `Cmd+H` | **Move** | 方向鍵 / `hjkl` | 移動焦點 |
> | `Ctrl+G` | `Cmd+G` | **Lock** | `Ctrl+G` / `Cmd+G` | 解鎖（鎖定時所有按鍵無效） |
> | — | — | — | `Esc` / `Enter` | 離開任何模式 |
> | **全域** | | — | `Alt + 方向鍵` | 快速切換 Pane |
> | | | | `Alt + 1~9` | 快速切 Tab |
> | | | | `Alt+Shift+Enter` | 全螢幕 |
> | | | | `Ctrl+Shift+P` | 命令面板 |
> | | | | `Ctrl+Shift+K` | 快捷鍵速查面板 |
> | | | | `Ctrl+Alt+V` | 貼上圖片（僅 Windows/WSL） |
> | | | | `Ctrl+Shift+Space` | Quick Select（選取 URL / 路徑） |
> | | | | `Ctrl+左鍵` | 開啟超連結 |

---

## 跨平台支援

本配置透過 `wezterm.target_triple` 自動偵測平台，單一檔案即可在 Windows、macOS、Linux 三端使用。

### 各平台差異對照

| 設定項目 | Windows | macOS | Linux |
|----------|---------|-------|-------|
| 模式切換鍵 | `Ctrl+鍵` | `Ctrl+鍵` 或 `Cmd+鍵` | `Ctrl+鍵` |
| 預設 Shell | PowerShell 7 (`pwsh.exe`) | 系統預設 Shell | 系統預設 Shell |
| 圖片貼上 (`Ctrl+Alt+V`) | 啟用（透過 PowerShell 讀取剪貼簿） | 不需要（原生支援） | 不需要（原生支援） |
| 右 Option 鍵 | — | 啟用 `send_composed_key_when_right_alt_is_pressed` | — |
| 視窗背景模糊 | — | `macos_window_background_blur = 20` | — |
| GPU 渲染引擎 | WebGpu | WebGpu | WebGpu |
| Mux Server | 支援 | 支援 | 支援 |
| Session 持久化 | `%USERPROFILE%/.wezterm-session.json` | `~/.wezterm-session.json` | `~/.wezterm-session.json` |

### macOS 使用注意

1. **Cmd 鍵模式切換**：所有 `Ctrl+鍵` 的模式切換都額外綁定了 `Cmd+鍵`，更符合 macOS 操作習慣。
2. **右 Option 鍵**：啟用 `send_composed_key_when_right_alt_is_pressed`，讓右 Option 能輸入程式常用的特殊字元（`~`、`\`、`|`、`[`、`]` 等）。
3. **SUPER 攔截**：在所有 Key Table 中自動插入 `Cmd+鍵` 的 Nop 綁定，防止模式切換鍵穿透到全域。
4. **毛玻璃效果**：`macos_window_background_blur = 20` 在 macOS 上啟用半透明視窗的毛玻璃背景。

### Linux 使用注意

1. **無額外平台設定**：Linux 使用基礎的 `Ctrl+鍵` 模式切換，無需特殊處理。
2. **圖片貼上**：Claude Code 在原生 Linux 環境下支援直接貼上圖片，不需要 `Ctrl+Alt+V` workaround。如需手動處理，可使用 `xclip`（X11）或 `wl-paste`（Wayland）。
3. **GPU 渲染**：WebGpu 後端在 Linux 上需要 Vulkan 驅動支援。若遇到相容性問題，可改回 `config.front_end = 'OpenGL'`。
4. **Mux Server**：`unix_domains` 在 Linux 上使用 Unix socket，行為與 macOS 一致。

### Windows (WSL) 使用注意

1. **預設 Shell**：自動偵測 Windows 平台並設定 PowerShell 7 為預設 Shell。可取消註解改用 WSL。
2. **圖片貼上**：WSL 環境中 Claude Code 無法直接貼上圖片（[#13738](https://github.com/anthropics/claude-code/issues/13738)），透過 `Ctrl+Alt+V` 繞過。詳見 [WSL 圖片貼上](#wsl-圖片貼上claude-code-整合) 章節。
3. **路徑轉換**：圖片貼上功能自動將 Windows 路徑轉為 WSL 路徑（`C:\Users\...` → `/mnt/c/Users/...`）。

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

## WSL 圖片貼上（Claude Code 整合）

在 WSL 環境中，Claude Code 無法直接透過 `Ctrl+V` 貼上剪貼簿中的圖片（[已知問題](https://github.com/anthropics/claude-code/issues/13738)）。透過 WezTerm 的 `action_callback` 可以繞過此限制。

### 運作原理

1. WezTerm 在 Windows 端執行，透過 `powershell.exe` 存取 Windows 剪貼簿
2. 偵測到圖片資料時，存為 `%TEMP%\clip_<timestamp>.png`
3. 將 Windows 路徑轉換為 WSL 路徑（`C:\...` → `/mnt/c/...`）
4. 將路徑文字送入當前 pane

### 支援的來源

| 來源 | 說明 |
|------|------|
| `Win+Shift+S` 截圖 | 螢幕截圖直接存為 PNG |
| 資料夾中 `Ctrl+C` 複製圖片檔 | 取得檔案路徑（支援 png/jpg/gif/bmp/webp/svg） |
| 非圖片內容 | 自動降級為一般文字貼上 |

### 使用方式

1. 截圖（`Win+Shift+S`）或在檔案總管中複製圖片檔
2. 在 Claude Code 中按 `Ctrl+Alt+V`
3. 圖片路徑會自動貼入，例如：`/mnt/c/Users/username/AppData/Local/Temp/clip_20260215_143022.png`

> **注意**：此功能僅在 Windows (WSL) 環境下啟用，配置中透過 `if is_windows` 條件判斷。macOS 與原生 Linux 的 Claude Code 原生支援圖片貼上，不需要此 workaround。

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
