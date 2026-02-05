# Zellij 終端多工器完整指南

## 目錄

- [簡介與特色](#簡介與特色)
- [安裝方式](#安裝方式)
- [基本操作](#基本操作)
- [快捷鍵與模式](#快捷鍵與模式)
- [macOS Alt 鍵設定](#macos-alt-鍵設定)
- [設定檔](#設定檔)
- [Layout 管理](#layout-管理)
- [Session 管理](#session-管理)
- [Plugin 系統](#plugin-系統)
- [與 tmux 比較](#與-tmux-比較)
- [搭配工具建議](#搭配工具建議)

---

## 簡介與特色

Zellij 是一款以 Rust 撰寫的現代化終端多工器（terminal multiplexer），定位為 tmux 和 screen 的替代方案。其設計理念為「開箱即用」（batteries included），讓使用者無需大量設定即可獲得良好的預設體驗。

### 核心特色

- **Rust 建構**：以 Rust 語言開發，兼顧效能與記憶體安全。
- **開箱即用**：預設即帶有 status bar、tab bar 等 UI 元件，新手無需額外設定。
- **可探索的快捷鍵**（Discoverable Keybindings）：畫面底部永遠顯示當前模式可用的快捷鍵提示，大幅降低學習門檻。
- **Plugin 系統**：支援 WebAssembly（WASM）plugin，可用任何能編譯為 WASM 的語言撰寫擴充功能。
- **Session 管理**：內建 session 的 detach、attach、resurrect 功能，斷線後可無縫恢復工作環境。
- **Layout 系統**：使用 KDL 格式定義 layout，可預先規劃並重複使用工作區配置。
- **浮動面板**（Floating Panes）：支援浮動視窗，可在現有面板之上疊加臨時的操作面板。

---

## 安裝方式

### macOS

使用 Homebrew 安裝：

```bash
brew install zellij
```

### Linux

各發行版的套件管理器：

```bash
# Arch Linux
pacman -S zellij

# Fedora (COPR)
dnf copr enable varlad/zellij
dnf install zellij

# NixOS / Nix
nix-env -i zellij
```

使用 Cargo 安裝（需要 Rust toolchain）：

```bash
cargo install --locked zellij
```

直接下載預編譯 binary：

```bash
# 下載最新版本（以 x86_64 Linux 為例）
curl -LO https://github.com/zellij-org/zellij/releases/latest/download/zellij-x86_64-unknown-linux-musl.tar.gz
tar -xvf zellij-x86_64-unknown-linux-musl.tar.gz
sudo mv zellij /usr/local/bin/
```

### 從原始碼編譯

```bash
git clone https://github.com/zellij-org/zellij.git
cd zellij
cargo build --release
sudo mv target/release/zellij /usr/local/bin/
```

### 驗證安裝

```bash
zellij --version
```

---

## 基本操作

### 啟動 Zellij

```bash
# 直接啟動（建立匿名 session）
zellij

# 以指定名稱建立 session
zellij -s my-project

# 以指定 layout 啟動
zellij --layout compact
```

### Session 基本操作

```bash
# 列出所有 session
zellij list-sessions
# 簡寫
zellij ls

# 附加到現有 session
zellij attach my-project
# 簡寫
zellij a my-project

# 附加到最近的 session，若不存在則建立新的
zellij attach

# 終止指定 session
zellij kill-session my-project

# 終止所有 session
zellij kill-all-sessions

# 刪除指定已終止的 session（清除 resurrect 資料）
zellij delete-session my-project

# 刪除所有已終止的 session
zellij delete-all-sessions
```

### 在 Zellij 中執行單一指令

```bash
# 在新的 Zellij session 中執行指令
zellij run -- htop

# 在浮動面板中執行指令
zellij run --floating -- git log --oneline
```

---

## 快捷鍵與模式

Zellij 採用「模式」（mode）機制來組織快捷鍵，避免與終端應用程式的快捷鍵衝突。每個模式有各自的按鍵綁定，按下對應的觸發鍵即可進入該模式。

### 模式總覽

| 模式 | 觸發鍵 | 說明 |
|------|---------|------|
| Normal | 預設模式 | Zellij 不攔截按鍵，所有輸入傳遞至終端程式 |
| Pane | `Ctrl+p` | 面板操作：建立、移動、調整大小、關閉 |
| Tab | `Ctrl+t` | 分頁操作：建立、切換、重新命名、關閉 |
| Resize | `Ctrl+n` | 調整面板大小 |
| Scroll | `Ctrl+s` | 捲動畫面、搜尋內容 |
| Session | `Ctrl+o` | Session 操作：detach、設定等 |
| Locked | `Ctrl+g` | 鎖定模式，停用所有 Zellij 快捷鍵 |
| Move | `Ctrl+h` | 移動面板位置 |

> 在任何模式下按 `Esc` 或 `Enter` 可返回 Normal 模式。

### Pane 模式（`Ctrl+p`）

| 按鍵 | 功能 |
|------|------|
| `n` | 開啟新面板（向下分割） |
| `d` | 開啟新面板（向右分割） |
| `x` | 關閉當前面板 |
| `f` | 切換面板全螢幕（fullscreen） |
| `w` | 切換浮動面板（floating pane） |
| `e` | 嵌入/取消嵌入浮動面板 |
| `r` | 重新命名面板 |
| `h` / `Left` | 移動焦點至左方面板 |
| `j` / `Down` | 移動焦點至下方面板 |
| `k` / `Up` | 移動焦點至上方面板 |
| `l` / `Right` | 移動焦點至右方面板 |

### 全域快捷鍵（不需進入特定模式）

以下快捷鍵在所有模式下皆可使用（Locked 模式除外）：

| 按鍵 | 功能 |
|------|------|
| `Alt+h` / `Alt+Left` | 移動焦點至左方面板（或切換至前一個分頁） |
| `Alt+l` / `Alt+Right` | 移動焦點至右方面板（或切換至下一個分頁） |
| `Alt+j` / `Alt+Down` | 移動焦點至下方面板 |
| `Alt+k` / `Alt+Up` | 移動焦點至上方面板 |
| `Alt+i` | 將當前分頁往左移動（重新排序） |
| `Alt+o` | 將當前分頁往右移動（重新排序） |
| `Alt+n` | 開啟新面板 |
| `Alt+f` | 切換浮動面板 |
| `Alt+=` / `Alt++` | 放大面板 |
| `Alt+-` | 縮小面板 |
| `Alt+[` | 切換至上一個 Swap Layout |
| `Alt+]` | 切換至下一個 Swap Layout |

> **macOS 注意事項**：macOS 的 Option 鍵預設會輸入特殊字元（如 `Option+I` 產生 `ˆ`），而非送出 Alt 訊號給終端。需要在終端模擬器中設定 Option 作為 Alt 使用，詳見下方[macOS Alt 鍵設定](#macos-alt-鍵設定)。

### Tab 模式（`Ctrl+t`）

| 按鍵 | 功能 |
|------|------|
| `n` | 建立新分頁 |
| `x` | 關閉當前分頁 |
| `r` | 重新命名當前分頁 |
| `h` / `Left` | 切換至前一個分頁 |
| `l` / `Right` | 切換至下一個分頁 |
| `1`-`9` | 切換至指定編號分頁 |
| `Tab` | 切換至上次使用的分頁 |
| `s` | 切換 sync 模式（同步輸入至所有面板） |

### Resize 模式（`Ctrl+n`）

| 按鍵 | 功能 |
|------|------|
| `h` / `Left` | 向左縮小 |
| `j` / `Down` | 向下擴大 |
| `k` / `Up` | 向上擴大 |
| `l` / `Right` | 向右擴大 |
| `=` | 平均分配面板大小 |

### Scroll 模式（`Ctrl+s`）

| 按鍵 | 功能 |
|------|------|
| `j` / `Down` | 向下捲動 |
| `k` / `Up` | 向上捲動 |
| `d` | 向下捲動半頁 |
| `u` | 向上捲動半頁 |
| `s` | 進入搜尋模式 |
| `n` | 搜尋下一個結果 |
| `p` | 搜尋上一個結果 |
| `e` | 以預設編輯器開啟捲動緩衝區 |

### Session 模式（`Ctrl+o`）

| 按鍵 | 功能 |
|------|------|
| `d` | Detach（脫離當前 session） |
| `w` | 開啟 session manager |

### Move 模式（`Ctrl+h`）

用於移動面板在佈局中的位置（非移動焦點，而是實際搬動面板）。

| 按鍵 | 功能 |
|------|------|
| `h` / `Left` | 將面板往左移 |
| `j` / `Down` | 將面板往下移 |
| `k` / `Up` | 將面板往上移 |
| `l` / `Right` | 將面板往右移 |
| `n` / `Tab` | 將面板移至下一個位置 |
| `p` | 將面板移至上一個位置 |

### Locked 模式（`Ctrl+g`）

進入 Locked 模式後，Zellij 不會攔截任何按鍵（除了 `Ctrl+g` 用來解除鎖定）。當你需要使用的終端程式快捷鍵與 Zellij 衝突時，可切換至此模式。

---

## macOS Alt 鍵設定

macOS 的 Option 鍵預設行為是輸入特殊字元，而非送出 Alt 訊號。這會導致 Zellij 的所有 `Alt` 系列快捷鍵（如 `Alt+I` 移動分頁、`Alt+H/L` 切換焦點等）無法使用。需要在終端模擬器中將 Option 映射為 Alt。

### Alacritty

在 Alacritty 設定檔（`~/.config/alacritty/alacritty.toml`）中加入：

```toml
[window]
option_as_alt = "Both"
```

`"Both"` 表示左右兩個 Option 鍵都作為 Alt 使用。也可設為 `"OnlyLeft"` 或 `"OnlyRight"` 保留其中一個 Option 鍵的原始功能（用於輸入特殊字元）。

### Ghostty

Ghostty 預設已將 Option 作為 Alt 處理，通常無需額外設定。若有問題，在設定中確認：

```
macos-option-as-alt = true
```

### WezTerm

```lua
-- ~/.wezterm.lua
config.send_composed_key_when_left_alt_is_pressed = false
config.send_composed_key_when_right_alt_is_pressed = false
```

### kitty

在 `~/.config/kitty/kitty.conf` 中加入：

```
macos_option_as_alt yes
```

### iTerm2

前往 Preferences → Profiles → Keys，將 Left Option Key 和 Right Option Key 設為 **Esc+**。

---

## 設定檔

Zellij 使用 KDL（KDL Document Language）格式作為設定檔格式。預設設定檔路徑為：

```
~/.config/zellij/config.kdl
```

### 推薦設定檔

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
option_as_alt = "Both"

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



### 產生預設設定檔

```bash
# 將預設設定匯出至設定檔
zellij setup --dump-config > ~/.config/zellij/config.kdl
```

### 實用設定範例

```kdl
// ~/.config/zellij/config.kdl

// 主題設定
theme "catppuccin-mocha"

// 預設模式：設為 locked 可避免快捷鍵誤觸
// 需要操作 Zellij 時按 Ctrl+g 切換至 Normal 模式
default_mode "normal"

// 預設 layout
default_layout "compact"

// 簡化 UI：隱藏面板邊框的標題列
simplified_ui true

// 是否啟用滑鼠支援
mouse_mode true

// 是否在面板邊框顯示面板名稱
pane_frames true

// 複製時是否同時複製到系統剪貼簿
copy_on_select true

// 捲動緩衝區大小
scroll_buffer_size 50000

// Session 序列化間隔（秒），用於 resurrect 功能
session_serialization true

// 鏡像 session（多 client 連同一 session 時是否同步畫面）
mirror_session false
```

### 自訂快捷鍵

```kdl
// ~/.config/zellij/config.kdl

keybinds {
    // 在 Normal 模式下新增快捷鍵
    normal {
        // Alt+n 開啟新面板
        bind "Alt n" { NewPane; }
        // Alt+t 開啟新分頁
        bind "Alt t" { NewTab; }
        // Alt+h/l 切換分頁
        bind "Alt h" { GoToPreviousTab; }
        bind "Alt l" { GoToNextTab; }
        // Alt+1 到 Alt+9 切換分頁
        bind "Alt 1" { GoToTab 1; }
        bind "Alt 2" { GoToTab 2; }
        bind "Alt 3" { GoToTab 3; }
    }

    // 清除預設的某個快捷鍵
    // unbind "Ctrl q"

    // 在所有模式下共用的快捷鍵
    shared_except "locked" {
        bind "Alt f" { ToggleFloatingPanes; }
    }
}
```

### 自訂主題

```kdl
// ~/.config/zellij/config.kdl

themes {
    my-theme {
        fg "#D8DEE9"
        bg "#2E3440"
        black "#3B4252"
        red "#BF616A"
        green "#A3BE8C"
        yellow "#EBCB8B"
        blue "#81A1C1"
        magenta "#B48EAD"
        cyan "#88C0D0"
        white "#E5E9F0"
        orange "#D08770"
    }
}

theme "my-theme"
```

---

## Layout 管理

Layout 定義了 Zellij 啟動時的面板配置。同樣使用 KDL 格式撰寫。

### Layout 檔案位置

```
~/.config/zellij/layouts/
```

### 產生預設 layout

```bash
zellij setup --dump-layout default > ~/.config/zellij/layouts/default.kdl
```

### 基本雙面板 Layout

```kdl
// ~/.config/zellij/layouts/two-pane.kdl
layout {
    pane split_direction="vertical" {
        pane
        pane
    }
}
```

### 開發用 Layout

以下範例建立一個包含編輯器、終端、檔案樹的開發環境：

```kdl
// ~/.config/zellij/layouts/dev.kdl
layout {
    // 預設給面板的 cwd
    cwd "/path/to/project"

    tab name="Editor" focus=true {
        pane split_direction="vertical" {
            pane name="Files" size="20%" {
                command "lsd"
                args "--tree" "--depth" "2"
            }
            pane name="Editor" {
                command "nvim"
                args "."
            }
        }
    }

    tab name="Terminal" {
        pane split_direction="horizontal" {
            pane name="Shell" size="70%"
            pane name="Logs" size="30%" {
                command "tail"
                args "-f" "logs/app.log"
            }
        }
    }

    tab name="Git" {
        pane {
            command "lazygit"
        }
    }
}
```

### 帶有 Plugin 的 Layout

```kdl
// ~/.config/zellij/layouts/with-plugins.kdl
layout {
    // 頂部分頁列
    pane size=1 borderless=true {
        plugin location="tab-bar"
    }

    // 主要工作區
    pane split_direction="vertical" {
        // 左側檔案瀏覽器（使用內建 strider plugin）
        pane size="15%" {
            plugin location="strider"
        }
        // 右側主面板
        pane
    }

    // 底部狀態列
    pane size=2 borderless=true {
        plugin location="status-bar"
    }
}
```

### 使用 Layout

```bash
# 使用絕對路徑指定 layout
zellij --layout /path/to/layout.kdl

# 使用 layouts 目錄中的 layout（僅需名稱）
zellij --layout dev

# 建立帶有 layout 的具名 session
zellij -s my-project --layout dev
```

---

## Session 管理

Zellij 的 session 管理功能可讓你保存、離開並恢復工作環境。

### 基本流程

```bash
# 1. 建立具名 session
zellij -s work

# 2. 在 session 中工作...

# 3. Detach（在 Zellij 內按 Ctrl+o 再按 d，或使用指令）
zellij action detach

# 4. 列出現有 session
zellij ls

# 5. 重新 attach
zellij a work
```

### Session Resurrect

Zellij 支援 session 復活功能。即使 Zellij 程序被終止（如系統重開機），仍可嘗試恢復先前的 session 配置。

```bash
# 列出所有 session（包含已終止但可復活的）
zellij ls

# 復活已終止的 session
zellij attach my-project

# 如果 session 已終止，Zellij 會詢問是否要 resurrect
```

Session 序列化資料儲存位置：

```
~/.cache/zellij/
```

### Session Manager

在 Zellij 中按 `Ctrl+o` 進入 Session 模式，再按 `w` 可開啟內建的 session manager，提供互動式的 session 切換與管理介面。

---

## Plugin 系統

Zellij 支援以 WebAssembly（WASM）撰寫的 plugin，可擴充終端多工器的功能。

### 內建 Plugin

| Plugin | 說明 |
|--------|------|
| `tab-bar` | 頂部分頁列，顯示所有分頁名稱與狀態 |
| `status-bar` | 底部狀態列，顯示當前模式與可用快捷鍵 |
| `strider` | 檔案瀏覽器面板，可在面板中瀏覽目錄結構 |
| `compact-bar` | 精簡版的合併分頁列與狀態列 |
| `session-manager` | Session 管理介面 |

### 在 Layout 中使用 Plugin

```kdl
layout {
    pane size=1 borderless=true {
        plugin location="compact-bar"
    }
    pane
}
```

### 載入外部 Plugin

```kdl
layout {
    pane {
        // 從檔案載入
        plugin location="file:/path/to/plugin.wasm"
    }
    pane {
        // 從網路載入
        plugin location="https://example.com/plugin.wasm"
    }
}
```

### 開發自訂 Plugin

Zellij plugin 使用 WASM 格式，可以用以下語言開發：

- **Rust**：官方提供 `zellij-tile` crate 作為 plugin SDK。
- **其他語言**：任何能編譯為 WASM 的語言皆可使用，如 Go（TinyGo）、C/C++、AssemblyScript 等。

基本的 Rust plugin 結構：

```bash
cargo generate zellij-org/zellij-templates rust-plugin
```

---

## 與 tmux 比較

| 比較項目 | Zellij | tmux |
|----------|--------|------|
| **實作語言** | Rust | C |
| **學習曲線** | 較低，UI 內建快捷鍵提示 | 較高，需記憶或查閱快捷鍵 |
| **預設體驗** | 開箱即用，預設帶有 status bar 與 tab bar | 需要手動設定才能獲得類似體驗 |
| **設定格式** | KDL（結構化、易讀） | 自訂格式（tmux.conf） |
| **Plugin 系統** | WASM plugin，語言無關 | Shell script 為主，依賴外部工具 |
| **Layout 系統** | KDL 格式，支援巢狀定義與 plugin | 自訂格式，功能相對陽春 |
| **Session 管理** | 內建 detach / attach / resurrect | 內建 detach / attach，resurrect 需外掛 |
| **浮動面板** | 原生支援 | 需要 tmux 3.3+ 的 popup 功能 |
| **效能** | 優秀（Rust，記憶體安全） | 優秀（C，輕量） |
| **生態系統** | 較新，社群成長中 | 成熟，大量外掛與設定範例 |
| **遠端伺服器** | 需另行安裝 | 幾乎所有伺服器皆預裝 |
| **穩定性** | 持續開發中，偶有 breaking change | 非常穩定，API 變動極少 |

### 選擇建議

- **選擇 Zellij**：偏好現代化的開箱即用體驗、不想花時間設定、喜歡 UI 內建的快捷鍵提示、有興趣開發 WASM plugin。
- **選擇 tmux**：需要在各種遠端伺服器上使用、已有成熟的 tmux 設定、重視長期穩定性與生態系統。

---

## 搭配工具建議

### 終端模擬器

Zellij 搭配支援 GPU 加速的現代終端模擬器效果最佳：

- **Ghostty**：新一代終端模擬器，原生效能優秀，設定簡潔。
- **Alacritty**：以 Rust 撰寫的 GPU 加速終端，輕量快速。
- **WezTerm**：以 Rust 撰寫，內建多工功能，但搭配 Zellij 時建議關閉 WezTerm 自身的 tab/pane 功能。
- **kitty**：功能豐富的 GPU 加速終端，支援圖片顯示。

> 搭配建議：使用 Zellij 時，建議將終端模擬器設定為單一視窗、無 tab 模式，將多工管理全權交給 Zellij 處理。

### Shell Prompt

- **Starship**：跨 shell 的高速 prompt，以 Rust 撰寫，與 Zellij 搭配效果良好，可在 prompt 中顯示 Git 狀態、語言版本等資訊。

```bash
# 安裝 Starship
brew install starship

# 在 ~/.zshrc 或 ~/.bashrc 加入
eval "$(starship init zsh)"
```

### 搭配常用的 CLI 工具

| 工具 | 說明 | 搭配方式 |
|------|------|----------|
| `lazygit` | 終端 Git UI | 在 layout 中指定一個 tab 專門開啟 lazygit |
| `lsd` / `eza` | 現代化 ls 替代品 | 搭配 strider plugin 或在檔案瀏覽面板使用 |
| `bat` | 帶有語法高亮的 cat | 在 Zellij 面板中瀏覽檔案時使用 |
| `fd` | 快速檔案搜尋 | 在浮動面板中執行快速搜尋 |
| `ripgrep` | 快速文字搜尋 | 在專用面板中執行全文搜尋 |
| `btop` / `htop` | 系統監控 | 在 layout 中配置監控分頁 |
| `zoxide` | 智慧目錄切換 | 在 Zellij 的不同面板間搭配使用 |

### 自動啟動設定

若希望開啟終端時自動進入 Zellij，可在 shell 設定檔中加入：

```bash
# ~/.zshrc 或 ~/.bashrc
# 僅在非 Zellij 環境下自動啟動（避免巢狀）
if [[ -z "$ZELLIJ" ]]; then
    zellij attach -c default
fi
```

上述指令會嘗試 attach 到名為 `default` 的 session，若不存在則自動建立（`-c` 選項代表 create if not exists）。

---

## 參考資源

- 官方網站：https://zellij.dev
- GitHub 倉庫：https://github.com/zellij-org/zellij
- 官方文件：https://zellij.dev/documentation
- Plugin 開發指南：https://zellij.dev/documentation/plugins
- Layout 文件：https://zellij.dev/documentation/layouts
