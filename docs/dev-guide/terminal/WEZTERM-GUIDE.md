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

```lua
-- ~/.wezterm.lua
-- 社群推薦完整配置 — Zellij 風格模式切換操作模型
-- 核心概念：Ctrl+快捷鍵 進入模式 → 簡單按鍵操作 → Esc 離開
local wezterm = require 'wezterm'
local act = wezterm.action
local config = wezterm.config_builder()

-- ============================================================
-- 一般設定
-- ============================================================
config.automatically_reload_config = true
config.check_for_updates = true

-- ============================================================
-- Mux Server（Session 持久化）
-- ============================================================
-- 關閉視窗後 session 繼續在背景執行，重新開啟時自動重連
-- 所有 tab、pane、執行中的程式都會保留
config.unix_domains = {
  { name = 'unix' },
}
config.default_gui_startup_args = { 'connect', 'unix' }

-- ============================================================
-- 視窗設定
-- ============================================================
-- config.window_decorations = "RESIZE"  -- 隱藏標題列但保留調整大小功能
config.window_background_opacity = 0.95
config.macos_window_background_blur = 20  -- macOS 毛玻璃效果
config.window_padding = {
  left = 8,
  right = 8,
  top = 8,
  bottom = 8,
}
config.initial_rows = 35
config.initial_cols = 130
-- 記住上次視窗大小（覆蓋上方預設值）
local size_file = (os.getenv('USERPROFILE') or os.getenv('HOME')) .. '/.wezterm-size'
do
  local f = io.open(size_file, 'r')
  if f then
    local data = f:read('*a')
    f:close()
    local cols, rows = data:match('(%d+),(%d+)')
    if cols and rows then
      config.initial_cols = tonumber(cols)
      config.initial_rows = tonumber(rows)
    end
  end
end
config.window_close_confirmation = 'AlwaysPrompt'

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
-- 分頁列字型（Fancy Tab Bar 使用獨立字型設定）
config.window_frame = {
  font = wezterm.font { family = 'Maple Mono NL NF CN', weight = 'Bold' },
  font_size = 11.0,
}

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
config.switch_to_last_active_tab_when_closing_tab = true

-- ============================================================
-- 捲動設定
-- ============================================================
config.scrollback_lines = 10000
config.enable_scroll_bar = false

-- ============================================================
-- 色彩主題
-- ============================================================
config.color_scheme = 'Catppuccin Mocha'

-- ============================================================
-- 預設 Shell（依平台自動切換）
-- ============================================================
if wezterm.target_triple == 'x86_64-pc-windows-msvc' then
  -- Windows：使用 PowerShell 7 或 WSL
  config.default_prog = { 'pwsh.exe' }
  -- config.default_prog = { 'wsl.exe', '-d', 'Ubuntu' }
end

-- ============================================================
-- Session 儲存/還原（重開機後恢復 tab/pane 佈局）
-- ============================================================
-- 限制：只能還原工作目錄，無法還原正在執行的程式
local session_file = (os.getenv('USERPROFILE') or os.getenv('HOME')) .. '/.wezterm-session.json'

local function save_session(window)
  local mux_win = window:mux_window()
  local data = { tabs = {} }
  for _, tab in ipairs(mux_win:tabs()) do
    local panes = {}
    for _, pane_info in ipairs(tab:panes_with_info()) do
      local cwd = pane_info.pane:get_current_working_dir()
      table.insert(panes, {
        cwd = cwd and tostring(cwd) or nil,
        left = pane_info.left,
        top = pane_info.top,
        width = pane_info.width,
        height = pane_info.height,
      })
    end
    table.insert(data.tabs, { panes = panes, title = tab:get_title() })
  end
  local f = io.open(session_file, 'w')
  if f then
    f:write(wezterm.json_encode(data))
    f:close()
  end
end

local function restore_session(mux_window)
  local f = io.open(session_file, 'r')
  if not f then return false end
  local json = f:read('*a')
  f:close()
  local ok, data = pcall(wezterm.json_parse, json)
  if not ok or not data or not data.tabs or #data.tabs == 0 then return false end

  -- 第一個 tab 用既有的 pane
  local first_tab = data.tabs[1]
  if first_tab.panes[1] and first_tab.panes[1].cwd then
    local first_pane = mux_window:active_tab():active_pane()
    first_pane:send_text('cd ' .. wezterm.shell_quote_arg(first_tab.panes[1].cwd) .. '\r')
    -- 同一 tab 的其他 pane：依位置判斷分割方向
    for i = 2, #first_tab.panes do
      local p = first_tab.panes[i]
      local direction = (p.left > 0 and p.top == 0) and 'Right' or 'Bottom'
      local new_pane = first_pane:split { direction = direction, cwd = p.cwd }
    end
  end

  -- 其餘 tab
  for i = 2, #data.tabs do
    local tab_data = data.tabs[i]
    local first_cwd = tab_data.panes[1] and tab_data.panes[1].cwd or nil
    local new_tab, new_pane = mux_window:spawn_tab { cwd = first_cwd }
    for j = 2, #tab_data.panes do
      local p = tab_data.panes[j]
      local direction = (p.left > 0 and p.top == 0) and 'Right' or 'Bottom'
      new_pane:split { direction = direction, cwd = p.cwd }
    end
  end
  return true
end

-- Mux Server 首次啟動時自動還原
wezterm.on('mux-startup', function()
  local mux = wezterm.mux
  local window = mux.all_windows()[1]
  if window then
    restore_session(window)
  end
end)

-- ============================================================
-- 視窗大小變更時儲存
-- ============================================================
wezterm.on('window-resized', function(window, pane)
  local dims = pane:get_dimensions()
  local f = io.open(size_file, 'w')
  if f then
    f:write(dims.cols .. ',' .. dims.viewport_rows)
    f:close()
  end
end)

-- ============================================================
-- 狀態列：顯示當前模式（Zellij 風格提示）
-- ============================================================
local mode_colors = {
  pane    = '#f38ba8',  -- 粉紅
  tab     = '#89b4fa',  -- 藍色
  resize  = '#a6e3a1',  -- 綠色
  scroll  = '#f9e2af',  -- 黃色
  session = '#cba6f7',  -- 紫色
  move    = '#fab387',  -- 橘色
  lock    = '#f38ba8',  -- 紅色
}

wezterm.on('update-right-status', function(window, pane)
  local mode = window:active_key_table()
  if mode then
    local color = mode_colors[mode] or '#a6adc8'
    window:set_right_status(wezterm.format {
      { Foreground = { Color = '#1e1e2e' } },
      { Background = { Color = color } },
      { Text = ' ' .. string.upper(mode) .. ' MODE ' },
    })
  else
    window:set_right_status(wezterm.format {
      { Foreground = { Color = '#6c7086' } },
      { Background = { Color = '#1e1e2e' } },
      { Text = ' NORMAL ' },
    })
  end
end)

-- ============================================================
-- 快捷鍵：進入各模式 + 全域快捷鍵
-- ============================================================
config.keys = {
  -- === 模式切換（Zellij 風格） ===

  -- Ctrl+P → 進入 Pane 模式
  {
    key = 'p',
    mods = 'CTRL',
    action = act.ActivateKeyTable {
      name = 'pane',
      one_shot = false,
    },
  },
  -- Ctrl+T → 進入 Tab 模式
  {
    key = 't',
    mods = 'CTRL',
    action = act.ActivateKeyTable {
      name = 'tab',
      one_shot = false,
    },
  },
  -- Ctrl+N → 進入 Resize 模式
  {
    key = 'n',
    mods = 'CTRL',
    action = act.ActivateKeyTable {
      name = 'resize',
      one_shot = false,
    },
  },
  -- Ctrl+S → 進入 Scroll 模式
  {
    key = 's',
    mods = 'CTRL',
    action = act.ActivateKeyTable {
      name = 'scroll',
      one_shot = false,
    },
  },
  -- Ctrl+O → 進入 Session 模式
  {
    key = 'o',
    mods = 'CTRL',
    action = act.ActivateKeyTable {
      name = 'session',
      one_shot = false,
    },
  },
  -- Ctrl+H → 進入 Move 模式（移動 Pane 焦點）
  {
    key = 'h',
    mods = 'CTRL',
    action = act.ActivateKeyTable {
      name = 'move',
      one_shot = false,
    },
  },
  -- Ctrl+G → 進入 Lock 模式（鎖定鍵盤，防止誤觸）
  {
    key = 'g',
    mods = 'CTRL',
    action = act.ActivateKeyTable {
      name = 'lock',
      one_shot = false,
    },
  },

  -- === 全域快捷鍵（不需進入模式，隨時可用） ===

  -- Alt + 方向鍵 → 快速切換 Pane
  { key = 'LeftArrow',  mods = 'ALT', action = act.ActivatePaneDirection 'Left' },
  { key = 'RightArrow', mods = 'ALT', action = act.ActivatePaneDirection 'Right' },
  { key = 'UpArrow',    mods = 'ALT', action = act.ActivatePaneDirection 'Up' },
  { key = 'DownArrow',  mods = 'ALT', action = act.ActivatePaneDirection 'Down' },

  -- Alt + 1~9 → 快速切換 Tab
  { key = '1', mods = 'ALT', action = act.ActivateTab(0) },
  { key = '2', mods = 'ALT', action = act.ActivateTab(1) },
  { key = '3', mods = 'ALT', action = act.ActivateTab(2) },
  { key = '4', mods = 'ALT', action = act.ActivateTab(3) },
  { key = '5', mods = 'ALT', action = act.ActivateTab(4) },
  { key = '6', mods = 'ALT', action = act.ActivateTab(5) },
  { key = '7', mods = 'ALT', action = act.ActivateTab(6) },
  { key = '8', mods = 'ALT', action = act.ActivateTab(7) },
  { key = '9', mods = 'ALT', action = act.ActivateTab(8) },

  -- Alt+Shift+Enter → 全螢幕切換
  { key = 'Enter', mods = 'ALT|SHIFT', action = act.ToggleFullScreen },
  -- Ctrl+Shift+P → 命令面板
  { key = 'p', mods = 'CTRL|SHIFT', action = act.ActivateCommandPalette },

  -- Ctrl+Alt+V → 貼上圖片（WSL 環境下從 Windows 剪貼簿取圖片）
  -- 支援截圖（Win+Shift+S）與資料夾中 Ctrl+C 複製的圖片檔
  {
    key = 'v',
    mods = 'CTRL|ALT',
    action = wezterm.action_callback(function(window, pane)
      local success, stdout = wezterm.run_child_process({
        'powershell.exe', '-NoProfile', '-Command',
        [[Add-Type -AssemblyName System.Windows.Forms; $i=[System.Windows.Forms.Clipboard]::GetImage(); if($i){$f="$env:TEMP\clip_"+(Get-Date -Format 'yyyyMMdd_HHmmss')+".png"; $i.Save($f,[System.Drawing.Imaging.ImageFormat]::Png); Write-Host $f} else {$fl=[System.Windows.Forms.Clipboard]::GetFileDropList(); if($fl.Count -gt 0){foreach($p in $fl){$ext=[System.IO.Path]::GetExtension($p).ToLower(); if($ext -match '\.(png|jpg|jpeg|gif|bmp|webp|svg)$'){Write-Host $p}}} else {Write-Host "NOIMAGE"}}]],
      })
      if success and stdout then
        local win_path = stdout:gsub('[\r\n]+$', '')
        if win_path ~= 'NOIMAGE' then
          -- Windows 路徑轉 WSL 路徑（C:\... → /mnt/c/...）
          local wsl_path = win_path:gsub('\\', '/')
          wsl_path = wsl_path:gsub('^(%a):', function(drive)
            return '/mnt/' .. drive:lower()
          end)
          pane:send_text(wsl_path)
        else
          window:perform_action(act.PasteFrom 'Clipboard', pane)
        end
      end
    end),
  },
}

-- ============================================================
-- Key Tables — 各模式內的操作（Zellij 風格）
-- ============================================================
config.key_tables = {

  -- ── Pane 模式 (Ctrl+P) ──────────────────────────────
  -- 新增、關閉、Zoom 窗格
  pane = {
    -- 新增窗格
    { key = 'n',          action = act.SplitHorizontal { domain = 'CurrentPaneDomain' } },  -- 預設右邊
    { key = 'r',          action = act.SplitHorizontal { domain = 'CurrentPaneDomain' } },  -- 右邊
    { key = 'd',          action = act.SplitVertical { domain = 'CurrentPaneDomain' } },    -- 下方
    -- 導航
    { key = 'LeftArrow',  action = act.ActivatePaneDirection 'Left' },
    { key = 'RightArrow', action = act.ActivatePaneDirection 'Right' },
    { key = 'UpArrow',    action = act.ActivatePaneDirection 'Up' },
    { key = 'DownArrow',  action = act.ActivatePaneDirection 'Down' },
    { key = 'h',          action = act.ActivatePaneDirection 'Left' },
    { key = 'l',          action = act.ActivatePaneDirection 'Right' },
    { key = 'k',          action = act.ActivatePaneDirection 'Up' },
    { key = 'j',          action = act.ActivatePaneDirection 'Down' },
    -- 操作
    { key = 'x',          action = act.CloseCurrentPane { confirm = true } },
    { key = 'f',          action = act.TogglePaneZoomState },
    -- 攔截其他模式切換鍵
    { key = 't', mods = 'CTRL', action = act.Nop },
    { key = 'n', mods = 'CTRL', action = act.Nop },
    { key = 's', mods = 'CTRL', action = act.Nop },
    { key = 'o', mods = 'CTRL', action = act.Nop },
    { key = 'h', mods = 'CTRL', action = act.Nop },
    { key = 'g', mods = 'CTRL', action = act.Nop },
    -- 離開
    { key = 'Escape',     action = 'PopKeyTable' },
    { key = 'Enter',      action = 'PopKeyTable' },
  },

  -- ── Tab 模式 (Ctrl+T) ──────────────────────────────
  -- 新增、關閉、切換、重命名分頁
  tab = {
    -- 新增 / 關閉
    { key = 'n',          action = act.SpawnTab 'CurrentPaneDomain' },
    { key = 'x',          action = act.CloseCurrentTab { confirm = true } },
    -- 導航
    { key = 'LeftArrow',  action = act.ActivateTabRelative(-1) },
    { key = 'RightArrow', action = act.ActivateTabRelative(1) },
    { key = 'h',          action = act.ActivateTabRelative(-1) },
    { key = 'l',          action = act.ActivateTabRelative(1) },
    -- 數字鍵直接切換
    { key = '1',          action = act.ActivateTab(0) },
    { key = '2',          action = act.ActivateTab(1) },
    { key = '3',          action = act.ActivateTab(2) },
    { key = '4',          action = act.ActivateTab(3) },
    { key = '5',          action = act.ActivateTab(4) },
    { key = '6',          action = act.ActivateTab(5) },
    { key = '7',          action = act.ActivateTab(6) },
    { key = '8',          action = act.ActivateTab(7) },
    { key = '9',          action = act.ActivateTab(8) },
    -- 重命名（先離開 Tab 模式再開啟輸入框，避免 h/l 被攔截為切換 Tab）
    {
      key = 'r',
      action = act.Multiple {
        'PopKeyTable',
        act.PromptInputLine {
          description = 'Enter new tab title',
          action = wezterm.action_callback(function(window, pane, line)
            if line then window:active_tab():set_title(line) end
          end),
        },
      },
    },
    -- 攔截其他模式切換鍵
    { key = 'p', mods = 'CTRL', action = act.Nop },
    { key = 'n', mods = 'CTRL', action = act.Nop },
    { key = 's', mods = 'CTRL', action = act.Nop },
    { key = 'o', mods = 'CTRL', action = act.Nop },
    { key = 'h', mods = 'CTRL', action = act.Nop },
    { key = 'g', mods = 'CTRL', action = act.Nop },
    -- 離開
    { key = 'Escape',     action = 'PopKeyTable' },
    { key = 'Enter',      action = 'PopKeyTable' },
  },

  -- ── Resize 模式 (Ctrl+N) ───────────────────────────
  -- 持續調整窗格大小
  resize = {
    { key = 'LeftArrow',  action = act.AdjustPaneSize { 'Left', 3 } },
    { key = 'RightArrow', action = act.AdjustPaneSize { 'Right', 3 } },
    { key = 'UpArrow',    action = act.AdjustPaneSize { 'Up', 3 } },
    { key = 'DownArrow',  action = act.AdjustPaneSize { 'Down', 3 } },
    { key = 'h',          action = act.AdjustPaneSize { 'Left', 3 } },
    { key = 'l',          action = act.AdjustPaneSize { 'Right', 3 } },
    { key = 'k',          action = act.AdjustPaneSize { 'Up', 3 } },
    { key = 'j',          action = act.AdjustPaneSize { 'Down', 3 } },
    -- Zoom 重設（取消單一 Pane 全螢幕）
    { key = '=',          action = act.TogglePaneZoomState },
    -- 攔截其他模式切換鍵
    { key = 'p', mods = 'CTRL', action = act.Nop },
    { key = 't', mods = 'CTRL', action = act.Nop },
    { key = 's', mods = 'CTRL', action = act.Nop },
    { key = 'o', mods = 'CTRL', action = act.Nop },
    { key = 'h', mods = 'CTRL', action = act.Nop },
    { key = 'g', mods = 'CTRL', action = act.Nop },
    -- 離開
    { key = 'Escape',     action = 'PopKeyTable' },
    { key = 'Enter',      action = 'PopKeyTable' },
  },

  -- ── Scroll 模式 (Ctrl+S) ───────────────────────────
  -- 捲動、搜尋、進入 Copy Mode
  scroll = {
    { key = 'UpArrow',    action = act.ScrollByLine(-1) },
    { key = 'DownArrow',  action = act.ScrollByLine(1) },
    { key = 'k',          action = act.ScrollByLine(-1) },
    { key = 'j',          action = act.ScrollByLine(1) },
    { key = 'u',          action = act.ScrollByPage(-0.5) },
    { key = 'd',          action = act.ScrollByPage(0.5) },
    { key = 'PageUp',     action = act.ScrollByPage(-1) },
    { key = 'PageDown',   action = act.ScrollByPage(1) },
    -- 搜尋
    { key = 's',          action = act.Search { CaseSensitiveString = '' } },
    -- 進入 Copy Mode（Vim 式瀏覽 + 選取）
    { key = 'c',          action = act.ActivateCopyMode },
    -- 攔截其他模式切換鍵
    { key = 'p', mods = 'CTRL', action = act.Nop },
    { key = 't', mods = 'CTRL', action = act.Nop },
    { key = 'n', mods = 'CTRL', action = act.Nop },
    { key = 'o', mods = 'CTRL', action = act.Nop },
    { key = 'h', mods = 'CTRL', action = act.Nop },
    { key = 'g', mods = 'CTRL', action = act.Nop },
    -- 離開
    { key = 'Escape',     action = 'PopKeyTable' },
    { key = 'Enter',      action = 'PopKeyTable' },
  },

  -- ── Session 模式 (Ctrl+O) ──────────────────────────
  -- 工作區、啟動器、Session 存檔
  session = {
    -- Session 存檔（儲存當前 tab/pane 佈局，重開機後可還原）
    {
      key = 's',
      action = wezterm.action_callback(function(window, pane)
        save_session(window)
        window:toast_notification('WezTerm', 'Session saved', nil, 3000)
      end),
    },
    -- 工作區選單
    { key = 'w',          action = act.ShowLauncherArgs { flags = 'WORKSPACES' } },
    -- 啟動器
    { key = 'l',          action = act.ShowLauncher },
    -- Tab 導覽
    { key = 't',          action = act.ShowTabNavigator },
    -- 除錯覆蓋層
    { key = 'd',          action = act.ShowDebugOverlay },
    -- 新增獨立 workspace
    {
      key = 'a',
      action = act.PromptInputLine {
        description = 'Enter new workspace name',
        action = wezterm.action_callback(function(window, pane, line)
          if line and #line > 0 then
            window:perform_action(act.SwitchToWorkspace { name = line }, pane)
          end
        end),
      },
    },
    -- 完全關閉 Mux Server
    {
      key = 'k',
      action = wezterm.action_callback(function(window, pane)
        save_session(window)
        window:toast_notification('WezTerm', 'Session saved. Killing server...', nil, 2000)
        wezterm.sleep_ms(500)
        pane:send_text('wezterm cli kill-server\r')
      end),
    },
    -- 攔截其他模式切換鍵
    { key = 'p', mods = 'CTRL', action = act.Nop },
    { key = 't', mods = 'CTRL', action = act.Nop },
    { key = 'n', mods = 'CTRL', action = act.Nop },
    { key = 's', mods = 'CTRL', action = act.Nop },
    { key = 'h', mods = 'CTRL', action = act.Nop },
    { key = 'g', mods = 'CTRL', action = act.Nop },
    -- 離開
    { key = 'Escape',     action = 'PopKeyTable' },
    { key = 'Enter',      action = 'PopKeyTable' },
  },

  -- ── Lock 模式 (Ctrl+G) ─────────────────────────────
  -- 鎖定鍵盤防止誤觸，僅 Ctrl+G 可解鎖
  -- 必須攔截所有全域模式切換鍵，否則會穿透到 config.keys
  lock = {
    { key = 'g', mods = 'CTRL', action = 'PopKeyTable' },
    { key = 'p', mods = 'CTRL', action = act.Nop },
    { key = 't', mods = 'CTRL', action = act.Nop },
    { key = 'n', mods = 'CTRL', action = act.Nop },
    { key = 's', mods = 'CTRL', action = act.Nop },
    { key = 'o', mods = 'CTRL', action = act.Nop },
    { key = 'h', mods = 'CTRL', action = act.Nop },
  },

  -- ── Move 模式 (Ctrl+H) ─────────────────────────────
  -- 在窗格間移動焦點（one-shot 風格，選完自動離開）
  move = {
    { key = 'LeftArrow',  action = act.ActivatePaneDirection 'Left' },
    { key = 'RightArrow', action = act.ActivatePaneDirection 'Right' },
    { key = 'UpArrow',    action = act.ActivatePaneDirection 'Up' },
    { key = 'DownArrow',  action = act.ActivatePaneDirection 'Down' },
    { key = 'h',          action = act.ActivatePaneDirection 'Left' },
    { key = 'l',          action = act.ActivatePaneDirection 'Right' },
    { key = 'k',          action = act.ActivatePaneDirection 'Up' },
    { key = 'j',          action = act.ActivatePaneDirection 'Down' },
    -- 攔截其他模式切換鍵
    { key = 'p', mods = 'CTRL', action = act.Nop },
    { key = 't', mods = 'CTRL', action = act.Nop },
    { key = 'n', mods = 'CTRL', action = act.Nop },
    { key = 's', mods = 'CTRL', action = act.Nop },
    { key = 'o', mods = 'CTRL', action = act.Nop },
    { key = 'g', mods = 'CTRL', action = act.Nop },
    -- 離開
    { key = 'Escape',     action = 'PopKeyTable' },
    { key = 'Enter',      action = 'PopKeyTable' },
  },
}

-- ============================================================
-- 滑鼠設定
-- ============================================================
config.mouse_bindings = {
  -- 左鍵選取後自動複製到系統剪貼簿
  {
    event = { Up = { streak = 1, button = 'Left' } },
    mods = 'NONE',
    action = act.CompleteSelection 'ClipboardAndPrimarySelection',
  },
}

return config
```

> **Zellij 風格模式速查表**：
>
> | 進入模式 | 模式名稱 | 模式內按鍵 | 功能 |
> |----------|----------|------------|------|
> | `Ctrl+P` | **Pane** | `n` / `r` | 新增窗格（右邊） |
> | | | `d` | 新增窗格（下方） |
> | | | 方向鍵 / `hjkl` | 切換 Pane |
> | | | `x` | 關閉 Pane |
> | | | `f` | Zoom 全螢幕 |
> | `Ctrl+T` | **Tab** | `n` | 新增 Tab |
> | | | `x` | 關閉 Tab |
> | | | 左右鍵 / `h` `l` | 切換 Tab |
> | | | `1`~`9` | 跳到第 N 個 Tab |
> | | | `r` | 重新命名 Tab |
> | `Ctrl+N` | **Resize** | 方向鍵 / `hjkl` | 調整 Pane 大小 |
> | | | `=` | 重設 Zoom |
> | `Ctrl+S` | **Scroll** | 上下鍵 / `j` `k` | 逐行捲動 |
> | | | `u` / `d` | 半頁上 / 下 |
> | | | `s` | 搜尋 |
> | | | `c` | 進入 Copy Mode |
> | `Ctrl+O` | **Session** | `s` | 儲存 Session（佈局存檔） |
> | | | `a` | 新增獨立 Workspace |
> | | | `k` | 關閉 Mux Server（自動存檔） |
> | | | `w` | 工作區選單 |
> | | | `l` | 啟動器 |
> | | | `t` | Tab 導覽 |
> | | | `d` | 除錯覆蓋層 |
> | `Ctrl+H` | **Move** | 方向鍵 / `hjkl` | 移動焦點 |
> | `Ctrl+G` | **Lock** | `Ctrl+G` | 解鎖（鎖定時所有按鍵無效） |
> | — | — | `Esc` / `Enter` | 離開任何模式（必須先離開才能切換到其他模式） |
> | **全域** | — | `Alt + 方向鍵` | 快速切換 Pane |
> | | | `Alt + 1~9` | 快速切 Tab |
> | | | `Alt+Shift+Enter` | 全螢幕 |
> | | | `Ctrl+Shift+P` | 命令面板 |
> | | | `Ctrl+Alt+V` | 貼上圖片（WSL 剪貼簿圖片） |

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

> **注意**：此功能需要 WezTerm 在 Windows 端運行且連線至 WSL。純 Linux 環境請改用 `xclip` 或 `wl-paste` 方案。

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
