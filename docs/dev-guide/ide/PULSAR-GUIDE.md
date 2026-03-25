# Pulsar Editor 完整指南

## 目錄

- [簡介與特色](#簡介與特色)
- [安裝方式](#安裝方式)
- [配置檔路徑](#配置檔路徑)
- [推薦設定](#推薦設定)
- [推薦插件](#推薦插件)
- [常用快捷鍵](#常用快捷鍵)
- [套件管理 (ppm)](#套件管理-ppm)
- [搭配工具建議](#搭配工具建議)

---

## 簡介與特色

[Pulsar](https://pulsar-edit.dev/) 是 GitHub Atom 編輯器的社群驅動繼承者。2022 年 12 月 Atom 正式終止後，社群團隊 fork 並持續開發，目標不僅是維護，而是全面現代化其架構。

- **高度可 hack** -- 所有核心功能（tree-view、tabs、find-and-replace）都是可替換的套件，透過 `init.js` 可在啟動時執行任意程式碼。
- **100% 開源、社群主導** -- 無企業遙測（telemetry），套件倉庫由社群自行營運。
- **CSON 格式配置** -- 比 JSON 更易讀的縮排式格式，支援註解。
- **內建套件管理器 (ppm)** -- 從命令列或 GUI 安裝、更新、發布套件。
- **多窗格分割** -- 任意分割編輯器面板，支援並排編輯。
- **Tree-sitter 語法高亮** -- 現代增量式解析，語法標記更精準。
- **I18n API** -- 支援介面國際化（v1.131.0+）。
- **Electron 30 / Node 20 / Chromium 124** -- 持續升級底層框架（v1.131.0+）。

> **與 VS Code 的定位差異**：Pulsar 專注於「可 hack 的文字編輯器」，輕量且高度自訂；VS Code 則是功能完整的 IDE。Pulsar 適合喜歡掌控每個細節、偏好簡潔工具鏈的開發者。

---

## 安裝方式

### macOS

使用 Homebrew 安裝（推薦）：

```bash
brew install --cask pulsar
```

安裝後會同時取得兩個 CLI 指令：
- `pulsar` -- 從終端啟動編輯器
- `ppm` -- Pulsar 套件管理器

也可從[官方下載頁](https://pulsar-edit.dev/download/)取得 DMG（支援 Apple Silicon 與 Intel）。

### Linux

```bash
# Debian / Ubuntu（.deb）
# 從 GitHub Releases 下載 .deb 後：
sudo dpkg -i pulsar_*.deb

# Fedora / RHEL（.rpm）
sudo rpm -i pulsar-*.rpm

# Arch Linux（AUR）
yay -S pulsar-bin

# AppImage（通用）
chmod +x Pulsar-*.AppImage && ./Pulsar-*.AppImage
```

### Windows

從[官方下載頁](https://pulsar-edit.dev/download/)取得安裝檔（.exe），或使用 Chocolatey / Scoop。

> **注意**：macOS 首次啟動可能會被 Gatekeeper 阻擋，需至「系統設定 > 隱私權與安全性」手動允許。

---

## 配置檔路徑

| 用途 | 路徑 |
|------|------|
| 主設定檔 | `~/.pulsar/config.cson` |
| 自訂樣式 | `~/.pulsar/styles.less` |
| 啟動腳本 | `~/.pulsar/init.js`（或 `init.coffee`） |
| 自訂片段 | `~/.pulsar/snippets.cson` |
| 快捷鍵覆寫 | `~/.pulsar/keymap.cson` |
| 已安裝套件 | `~/.pulsar/packages/` |

開啟設定檔：Command Palette → `Application: Open Your Config`

### CSON 格式要點

```cson
# 這是註解
"*":
  core:
    telemetryConsent: "no"  # 關閉遙測
  editor:
    fontSize: 14

# 語言專用覆寫
".python.source":
  editor:
    tabLength: 4
```

- 縮排式，不需要大括號或逗號
- `#` 行註解
- `"*"` 下為全域設定，語法範圍字串（如 `".python.source"`）下為語言專用覆寫
- **注意**：同一層不可有重複 key（不會報錯，後者會靜默覆蓋前者）

---

## 推薦設定

本專案提供的參考設定檔位於 [`config/config.cson`](config/config.cson)，主要配置：

| 類別 | 設定 | 說明 |
|------|------|------|
| **字型** | `Maple Mono NL NF CN` | Nerd Font 變體，支援中文與連字 |
| **縮排** | `softTabs: true`, `tabLength: 2` | 預設 2 空格；Python 覆寫為 4 空格 |
| **換行** | `softWrap: true` | 自動折行，避免水平捲動 |
| **輔助線** | `showIndentGuide: true` | 顯示縮排參考線 |
| **VCS 排除** | `excludeVcsIgnoredPaths: true` | tree-view 隱藏 `.gitignore` 指定的檔案 |
| **忽略目錄** | `node_modules`, `dist`, `.venv` 等 | 全域 + fuzzy-finder 雙重排除 |
| **停用套件** | `wrap-guide` | 移除 80 字元參考線（搭配 soft wrap 使用） |

### 套用方式

```bash
# 備份現有設定
cp ~/.pulsar/config.cson ~/.pulsar/config.cson.bak

# 複製參考設定
cp config/config.cson ~/.pulsar/config.cson
```

---

## 推薦插件

### 安裝方式

```bash
ppm install editorconfig file-icons highlight-selected
```

或透過 GUI：Settings → Install → 搜尋套件名稱。

### editorconfig

統一團隊程式碼風格的核心套件。讀取專案根目錄的 `.editorconfig` 檔案，自動套用縮排、換行、尾行空白等規則。

- 支援屬性：`indent_style`, `indent_size`, `end_of_line`, `charset`, `trim_trailing_whitespace`, `insert_final_newline`, `max_line_length`
- 指令：`EditorConfig: Fix File` 可修正既有檔案的格式
- **前提**：Pulsar 的 Tab Type 設定需為 `auto`，`indent_style` 才會生效

### file-icons

為 tree-view、標籤頁、fuzzy-finder 等處的檔案加上對應的圖示與色彩，大幅提升視覺辨識度。

- 圖示來源：File-Icons、FontAwesome 4.7、Mfizz、Devicons 四套字型
- 全 CSS class 驅動，可透過 `styles.less` 自訂覆寫

### highlight-selected

雙擊選取文字時，自動高亮當前檔案中所有相同文字，方便快速瀏覽變數或函式的使用位置。

- 切換開關：`Ctrl+Cmd+H`
- 全選標記：`Ctrl+Cmd+U`
- 建議搭配 `minimap-highlight-selected` 在 minimap 同步顯示

---

## 常用快捷鍵

### 一般操作

| 快捷鍵 | 功能 |
|--------|------|
| `Cmd+Shift+P` | Command Palette |
| `Cmd+,` | 開啟 Settings |
| `Cmd+P` | 快速開啟檔案（fuzzy finder） |
| `Cmd+Shift+N` | 新視窗 |
| `Cmd+N` | 新分頁 |
| `Cmd+W` | 關閉分頁 |
| `Cmd+S` | 儲存 |
| `Cmd+Shift+S` | 另存新檔 |

### 編輯

| 快捷鍵 | 功能 |
|--------|------|
| `Cmd+D` | 選取下一個相同文字 |
| `Cmd+Shift+D` | 複製當前行 |
| `Cmd+Shift+K` | 刪除當前行 |
| `Ctrl+Shift+K` | 刪除至行尾 |
| `Cmd+L` | 選取整行 |
| `Cmd+/` | 切換行註解 |
| `Cmd+]` / `Cmd+[` | 增加 / 減少縮排 |
| `Cmd+Enter` | 在下方插入新行 |
| `Cmd+Shift+Enter` | 在上方插入新行 |

### 尋找與取代

| 快捷鍵 | 功能 |
|--------|------|
| `Cmd+F` | 檔案內搜尋 |
| `Cmd+Shift+F` | 專案內搜尋 |
| `Cmd+G` | 下一個匹配 |
| `Cmd+Shift+G` | 上一個匹配 |
| `Cmd+Alt+F` | 尋找並取代 |

### 窗格與導覽

| 快捷鍵 | 功能 |
|--------|------|
| `Cmd+K` → 方向鍵 | 分割窗格 |
| `Cmd+K` → `Cmd+` 方向鍵 | 聚焦至窗格 |
| `Cmd+\` | 切換 tree-view |
| `Ctrl+G` | 跳至行號 |
| `Cmd+R` | 跳至符號（當前檔案） |
| `Ctrl+Tab` | 切換分頁 |

---

## 套件管理 (ppm)

```bash
# 搜尋套件
ppm search <query>

# 安裝
ppm install <package-name>

# 列出已安裝
ppm list

# 更新全部
ppm update

# 移除
ppm uninstall <package-name>

# 查看精選套件
ppm featured

# 查看說明
ppm help
```

套件倉庫：https://packages.pulsar-edit.dev/

---

## 搭配工具建議

| 工具 | 用途 | 指南連結 |
|------|------|----------|
| [EditorConfig](https://editorconfig.org/) | 跨編輯器統一程式碼風格 | `.editorconfig` 放在專案根目錄 |
| [Alacritty](../terminal/ALACRITTY-GUIDE.md) / [WezTerm](../terminal/WEZTERM-GUIDE.md) | GPU 加速終端 | 搭配 Pulsar 作為外部終端 |
| [Lazygit](../git/LAZYGIT-GUIDE.md) | 終端 Git UI | 在終端中操作 Git |
| [Yazi](../terminal/YAZI-GUIDE.md) | 終端檔案管理器 | 快速導覽專案目錄 |
| [LSP](../workflow/LSP-INSTALLATION-GUIDE.md) | 語言伺服器協定 | Pulsar 可透過 `pulsar-ide` 系列套件整合 LSP |
