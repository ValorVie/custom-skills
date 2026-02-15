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
-- 狀態列：顯示當前模式（Zellij 風格）
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
      { Foreground = { Color = '#a6adc8' } },
      { Background = { Color = '#313244' } },
      { Text = ' Ctrl+Shift+K ' },
      { Foreground = { Color = '#1e1e2e' } },
      { Background = { Color = color } },
      { Text = ' ' .. string.upper(mode) .. ' ' },
    })
  else
    window:set_right_status(wezterm.format {
      { Foreground = { Color = '#585b70' } },
      { Background = { Color = '#313244' } },
      { Text = ' Ctrl+Shift+K ' },
      { Foreground = { Color = '#6c7086' } },
      { Background = { Color = '#313244' } },
      { Text = ' NORMAL ' },
    })
  end
end)

-- ============================================================
-- 快捷鍵速查面板（Ctrl+/ 開啟，類似命令面板）
-- ============================================================
local shortcut_items = {
  { label = '── 模式切換 ──────────────────────────', id = '' },
  { label = 'Ctrl+P    Pane 模式（窗格管理）',       id = '' },
  { label = 'Ctrl+T    Tab 模式（分頁管理）',        id = '' },
  { label = 'Ctrl+N    Resize 模式（調整大小）',     id = '' },
  { label = 'Ctrl+S    Scroll 模式（捲動/搜尋）',    id = '' },
  { label = 'Ctrl+O    Session 模式（工作區管理）',   id = '' },
  { label = 'Ctrl+H    Move 模式（移動焦點）',       id = '' },
  { label = 'Ctrl+G    Lock 模式（鎖定鍵盤）',       id = '' },
  { label = '── Pane 模式 (Ctrl+P) ───────────────', id = '' },
  { label = 'n / r     新增窗格（右邊）',            id = '' },
  { label = 'd         新增窗格（下方）',            id = '' },
  { label = '←→↑↓/hjkl 切換窗格焦點',               id = '' },
  { label = 'x         關閉窗格',                    id = '' },
  { label = 'f         Zoom 全螢幕切換',             id = '' },
  { label = '── Tab 模式 (Ctrl+T) ────────────────', id = '' },
  { label = 'n         新增分頁',                    id = '' },
  { label = 'x         關閉分頁',                    id = '' },
  { label = '←→ / h l  切換分頁',                    id = '' },
  { label = '1-9       跳到第 N 個分頁',             id = '' },
  { label = 'r         重新命名分頁',                id = '' },
  { label = '── Resize 模式 (Ctrl+N) ─────────────', id = '' },
  { label = '←→↑↓/hjkl 調整窗格大小',               id = '' },
  { label = '=         重設 Zoom',                   id = '' },
  { label = '── Scroll 模式 (Ctrl+S) ─────────────', id = '' },
  { label = '↑↓ / j k  逐行捲動',                   id = '' },
  { label = 'u / d     半頁捲動',                    id = '' },
  { label = 'PgUp/PgDn 整頁捲動',                   id = '' },
  { label = 's         搜尋',                        id = '' },
  { label = 'c         進入 Copy Mode',              id = '' },
  { label = '── Session 模式 (Ctrl+O) ────────────', id = '' },
  { label = 's         儲存 Session',                id = '' },
  { label = 'a         新增 Workspace',              id = '' },
  { label = 'k         關閉 Mux Server',             id = '' },
  { label = 'w         工作區選單',                   id = '' },
  { label = 'l         啟動器',                      id = '' },
  { label = 't         Tab 導覽',                    id = '' },
  { label = 'd         除錯覆蓋層',                  id = '' },
  { label = '── 全域快捷鍵 ────────────────────────', id = '' },
  { label = 'Alt+方向鍵      快速切換 Pane',         id = '' },
  { label = 'Alt+1~9         快速切換 Tab',          id = '' },
  { label = 'Ctrl+Shift+W    關閉當前分頁',            id = '' },
  { label = 'Alt+Shift+Enter 全螢幕切換',            id = '' },
  { label = 'Ctrl+Shift+P    命令面板',              id = '' },
  { label = 'Ctrl+Shift+K    本速查表',              id = '' },
  { label = 'Ctrl+Alt+V      貼上圖片',              id = '' },
  { label = 'Esc / Enter     離開任何模式',          id = '' },
}

local function show_shortcuts(window, pane)
  window:perform_action(act.InputSelector {
    title = '快捷鍵速查',
    choices = shortcut_items,
    action = wezterm.action_callback(function() end),
  }, pane)
end

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
  -- Ctrl+Shift+W → 關閉當前分頁
  { key = 'w', mods = 'CTRL|SHIFT', action = act.CloseCurrentTab { confirm = true } },
  -- Ctrl+Shift+K → 快捷鍵速查面板（K = Keys）
  {
    key = 'k',
    mods = 'CTRL|SHIFT',
    action = wezterm.action_callback(function(window, pane)
      show_shortcuts(window, pane)
    end),
  },
  -- Ctrl+Alt+V → 貼上圖片（剪貼簿圖片存檔後貼入路徑）
  -- WezTerm 在 Windows 端執行，用 PowerShell 取剪貼簿圖片
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
          -- 直接在 Lua 中轉換 Windows → WSL 路徑
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
  -- 分割、關閉、Zoom、旋轉窗格
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
        window:toast_notification('WezTerm', 'Session saved. Shutting down...', nil, 2000)
        wezterm.sleep_ms(500)
        window:perform_action(act.QuitApplication, pane)
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
