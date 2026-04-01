# cmux AI 代理終端完整指南

## 目錄

- [簡介與特色](#簡介與特色)
- [安裝方式](#安裝方式)
- [核心概念](#核心概念)
- [基本操作](#基本操作)
- [快捷鍵速查表](#快捷鍵速查表)
- [CLI 指令參考](#cli-指令參考)
- [內建瀏覽器](#內建瀏覽器)
- [SSH 遠端工作區](#ssh-遠端工作區)
- [通知系統](#通知系統)
- [自訂指令（cmux.json）](#自訂指令cmuxjson)
- [設定檔](#設定檔)
- [Claude Code Teams 整合](#claude-code-teams-整合)
- [與其他終端工具比較](#與其他終端工具比較)
- [疑難排解](#疑難排解)
- [參考資源](#參考資源)

---

## 簡介與特色

[cmux](https://cmux.com) 是一款原生 macOS 終端應用程式，由 [manaflow-ai](https://github.com/manaflow-ai) 開發，基於 [Ghostty](https://ghostty.org/) 的 libghostty 進行 GPU 加速渲染。專為同時管理多個 AI 程式碼代理（如 Claude Code、Codex、OpenCode 等）會話而設計。

### 核心特色

- **GPU 加速渲染** -- 基於 Ghostty 的 libghostty，以 Swift + AppKit 原生建構，渲染效能優異。
- **通知系統** -- AI agent 需要注意時，分頁亮起藍色環形指示燈，不再漏看回應。
- **智慧側邊欄** -- 垂直分頁顯示 git 分支、PR 狀態/編號、工作目錄、監聽 port 及最新通知。
- **內建瀏覽器** -- 在終端旁分割一個可腳本化的 WebKit 瀏覽器面板，無需切換視窗。
- **SSH 遠端工作區** -- 一鍵建立遠端工作區，瀏覽器面板自動透過遠端網路路由。
- **Claude Code Teams 整合** -- 原生支援 teammate mode，隊友在獨立分割視窗中執行。
- **Session 還原** -- 重啟後還原視窗配置、工作目錄、scrollback 和瀏覽器 URL。
- **Socket API** -- 完整的 CLI + JSON-RPC socket API，支援工作區建立、按鍵發送、瀏覽器自動化。
- **自訂指令** -- 透過 `cmux.json` 定義專案級動作，從 Command Palette 快速存取。
- **Ghostty 設定相容** -- 完全相容 Ghostty 設定檔，字型、主題等可直接沿用。

**授權：** GPL-3.0-or-later（另有商業授權選項）

**版本：** v0.63.1（2026-03-28，更新頻率極高）

---

## 安裝方式

### 系統需求

- macOS 14.0（Sonoma）或更新版本
- Apple Silicon 或 Intel Mac（Universal Binary）
- **不支援 Linux 或 Windows**

### Homebrew（推薦）

```bash
brew tap manaflow-ai/cmux
brew install --cask cmux
```

更新：

```bash
brew upgrade --cask cmux
```

### DMG 手動安裝

從 [GitHub Releases](https://github.com/manaflow-ai/cmux/releases) 下載 DMG，拖入 Applications。包含透過 Sparkle 的自動更新。

### Nightly 版本

獨立的應用程式包（`com.cmuxterm.app.nightly`），有獨立的自動更新 feed，可與穩定版並行安裝。從 GitHub Releases 頁面下載 nightly DMG。

### CLI 設置

安裝應用程式後，需手動建立 CLI symlink 以便從終端存取 `cmux` 指令：

```bash
sudo ln -sf "/Applications/cmux.app/Contents/Resources/bin/cmux" /usr/local/bin/cmux
```

### 驗證安裝

```bash
cmux ping
# 應回傳 pong，確認 cmux 正在運行
```

---

## 核心概念

### 架構階層

cmux 採用 Application → Workspace → Surface 的三層架構：

```
cmux.app
├── Workspace: "backend"
│   ├── Surface 1: Claude Code     [active]
│   ├── Surface 2: terminal
│   └── Browser Panel: localhost:3000
├── Workspace: "frontend"
│   ├── Surface 1: Codex
│   └── Surface 2: dev server
└── Workspace: "remote"
    └── SSH: user@prod-server
```

| 層級 | 說明 | 類比 |
|------|------|------|
| **Application** | cmux 主程序，管理所有工作區 | 桌面環境 |
| **Workspace** | 一組相關的 surface 和瀏覽器面板 | tmux Session / 瀏覽器視窗 |
| **Surface** | 工作區中的獨立終端面板，可分割排列 | tmux Pane |
| **Browser Panel** | 內嵌的 WebKit 瀏覽器，與 surface 並排 | 獨立瀏覽器視窗 |

### 側邊欄資訊

cmux 的垂直分頁側邊欄自動顯示每個工作區的上下文資訊：

- **工作區名稱** -- 手動命名或自動偵測
- **Git 分支** -- 當前工作目錄的分支名稱
- **PR 狀態** -- Pull Request 編號與狀態
- **工作目錄** -- 當前路徑
- **監聽 Port** -- 自動偵測正在監聽的 port
- **通知文字** -- 最新的通知訊息
- **通知環** -- 藍色環形指示燈，標記需要注意的工作區

### 與 tmux 的關鍵差異

cmux 不是 tmux 的替代品，而是不同層級的工具：

| 面向 | cmux | tmux |
|------|------|------|
| 本質 | 原生 macOS 終端應用程式 | 在任何終端內運行的多工器 |
| 渲染 | GPU 加速（libghostty） | 純文字 |
| 分割管理 | 內建，原生 UI | 內建，文字 UI |
| 斷線恢復 | Session 還原（重啟後恢復配置） | detach/attach（保持 process 運行） |
| 遠端使用 | 透過 SSH 工作區 | 可直接在遠端執行 |
| 瀏覽器 | 內建可腳本化瀏覽器 | 無 |
| 跨平台 | 僅 macOS | Linux / macOS / BSD |

> **提示**：若需在遠端伺服器上持久運行 process 並在 SSH 斷線後恢復，仍建議使用 tmux。cmux 的 Session 還原僅恢復視窗配置，不會保持活動 process 狀態。

---

## 基本操作

### 啟動

雙擊 cmux.app 啟動，或從終端：

```bash
open -a cmux
```

### 工作區管理

| 操作 | 方式 |
|------|------|
| 新建工作區 | `Cmd+N` 或 `cmux new-workspace --name "project"` |
| 切換工作區 | `Cmd+1` ~ `Cmd+9` 或點擊側邊欄 |
| 關閉工作區 | `Cmd+W` |
| 重新命名 | `Cmd+R` |
| 列出所有 | `cmux list-workspaces` |

### Surface 分割

| 操作 | 快捷鍵 | 說明 |
|------|--------|------|
| 右側分割 | `Cmd+D` | 水平分割，新 surface 在右方 |
| 下方分割 | `Cmd+Shift+D` | 垂直分割，新 surface 在下方 |
| 新 Tab | `Cmd+T` | 建立新分頁 |
| 切換 Tab | `Cmd+Shift+]` / `Cmd+Shift+[` | 前後切換 |
| 方向聚焦 | `Option+Cmd+方向鍵` | 聚焦指定方向的 surface |

### 瀏覽器面板

| 操作 | 快捷鍵 |
|------|--------|
| 開啟瀏覽器 | `Cmd+B` |
| 網址列 | `Cmd+L` |
| 開發者工具 | `Cmd+Option+I` |

### 終端操作

| 操作 | 快捷鍵 |
|------|--------|
| 清除終端 | `Cmd+K` |
| 搜尋 | `Cmd+F` |
| 放大字體 | `Cmd++` |
| 縮小字體 | `Cmd+-` |
| Command Palette | `Cmd+Shift+P` |

---

## 快捷鍵速查表

### 工作區

| 快捷鍵 | 功能 |
|--------|------|
| `Cmd+N` | 新建工作區 |
| `Cmd+1` ~ `Cmd+9` | 跳轉至指定工作區 |
| `Cmd+W` | 關閉當前工作區 |
| `Cmd+R` | 重新命名工作區 |

### Surface / Tab

| 快捷鍵 | 功能 |
|--------|------|
| `Cmd+T` | 新建分頁 |
| `Cmd+D` | 右側分割 |
| `Cmd+Shift+D` | 下方分割 |
| `Cmd+Shift+]` / `[` | 切換分頁（前/後） |
| `Ctrl+Tab` | 切換分頁 |
| `Option+Cmd+方向鍵` | 方向聚焦 surface |

### 瀏覽器

| 快捷鍵 | 功能 |
|--------|------|
| `Cmd+B` | 開啟/關閉瀏覽器面板 |
| `Cmd+L` | 聚焦網址列 |
| `Cmd+Option+I` | 開發者工具 |

### 通知

| 快捷鍵 | 功能 |
|--------|------|
| `Cmd+Shift+I` | 通知面板 |
| `Cmd+Shift+U` | 跳到最新未讀 |

### 終端

| 快捷鍵 | 功能 |
|--------|------|
| `Cmd+K` | 清除終端 |
| `Cmd+F` | 搜尋 |
| `Cmd++` / `Cmd+-` | 調整字體大小 |
| `Cmd+Shift+P` | Command Palette |

---

## CLI 指令參考

cmux 提供完整的 CLI 介面，所有指令皆可在任何終端中執行（需先完成 CLI 設置）。

### 工作區管理

```bash
# 列出所有工作區
cmux list-workspaces

# 建立新工作區
cmux new-workspace --name "my-project"

# 切換工作區
cmux select-workspace WORKSPACE_ID

# 關閉工作區
cmux close-workspace WORKSPACE_ID
```

### 分割操作

```bash
# 建立分割（方向：left / right / up / down）
cmux new-split right
cmux new-split down

# 列出所有 surface
cmux list-surfaces

# 聚焦指定 surface
cmux focus-surface SURFACE_ID
```

### 輸入控制

```bash
# 發送文字到當前面板
cmux send "echo hello"

# 發送按鍵（enter / tab / escape 等）
cmux send-key enter

# 發送到指定 surface
cmux send-surface SURFACE_ID "ls -la"
```

### 側邊欄 Metadata

```bash
# 設定自訂狀態
cmux set-status --key "build" --text "Building..." --color green

# 清除狀態
cmux clear-status --key "build"

# 設定進度百分比
cmux set-progress 75

# 記錄日誌
cmux log --level info "Deployment started"
```

### 診斷工具

```bash
cmux ping              # 測試連線
cmux capabilities      # 列出支援的功能
cmux identify          # 識別當前 surface
```

---

## 內建瀏覽器

cmux 內建一個基於 WebKit/WKWebView 的可腳本化瀏覽器面板，可在終端旁直接操作，無需切換視窗。

### 開啟方式

- 快捷鍵 `Cmd+B` 開啟/關閉瀏覽器面板
- CLI：`cmux browser navigate https://localhost:3000`

### 瀏覽器 CLI 指令

#### 導覽

```bash
cmux browser navigate "https://localhost:3000"
cmux browser back
cmux browser forward
cmux browser reload
cmux browser url          # 取得當前 URL
cmux browser wait         # 等待頁面載入完成
```

#### DOM 互動

```bash
cmux browser click "button.submit"
cmux browser fill "input[name=email]" "user@example.com"
cmux browser type "Hello World"
cmux browser press Enter
cmux browser select "select#country" "TW"
cmux browser scroll down 500
cmux browser hover ".menu-item"
cmux browser check "input[type=checkbox]"
```

#### 檢查與截圖

```bash
cmux browser snapshot         # 取得頁面 DOM 快照
cmux browser screenshot       # 截圖
cmux browser get "h1"         # 取得元素內容
cmux browser find ".item"     # 搜尋元素
cmux browser highlight ".btn" # 高亮元素
```

#### JavaScript 執行

```bash
cmux browser eval "document.title"
cmux browser addinitscript "console.log('loaded')"
cmux browser addscript "/path/to/script.js"
cmux browser addstyle "/path/to/style.css"
```

#### Session 管理

```bash
cmux browser state save session.json     # 儲存 cookies + storage
cmux browser state load session.json     # 載入 session
cmux browser cookies                     # 列出 cookies
cmux browser storage                     # 列出 localStorage
```

### Browser Data Import

cmux 支援從 20+ 瀏覽器匯入 cookies、歷史記錄和 session 資料，方便在內建瀏覽器中使用已有的登入狀態。

---

## SSH 遠端工作區

cmux 提供原生 SSH 工作區支援，特色在於瀏覽器面板會自動透過遠端網路路由，無需手動設定 port forwarding。

### 建立 SSH 工作區

```bash
# 基本連線
cmux ssh user@remote-server

# 指定名稱
cmux ssh user@remote-server --name "prod"

# 指定 port 與金鑰
cmux ssh user@remote-server -p 2222 -i ~/.ssh/id_ed25519

# 不自動聚焦
cmux ssh user@remote-server --no-focus
```

### 特色功能

- **瀏覽器自動路由** -- 瀏覽器面板自動透過遠端網路存取，例如開啟 `localhost:8080` 會連到遠端的 8080 port
- **拖放上傳** -- 將本機檔案拖放到 SSH 工作區，自動透過 SCP 上傳
- **完整終端功能** -- 所有 cmux 功能在 SSH 工作區中皆可使用

---

## 通知系統

cmux 的通知系統是其最核心的特色之一，專為 AI agent 工作流設計，確保你不會錯過任何需要注意的訊息。

### 通知環（Notification Rings）

當 AI agent 需要你的注意時（例如等待輸入、完成任務、發生錯誤），對應工作區的分頁會亮起**藍色環形指示燈**，側邊欄標籤同步高亮。

### 通知觸發方式

**終端序列（自動偵測）：**

支援 OSC 9、OSC 99、OSC 777 終端序列。大多數 AI agent 工具在需要注意時會自動發送這些序列，無需額外設定。

**CLI 指令（手動觸發）：**

```bash
# 發送通知
cmux notify --title "Build Complete" --body "Frontend build finished successfully"

# 列出通知
cmux list-notifications

# 清除通知
cmux clear-notifications
```

### 通知快捷鍵

| 快捷鍵 | 功能 |
|--------|------|
| `Cmd+Shift+I` | 開啟通知面板 |
| `Cmd+Shift+U` | 跳到最新未讀工作區 |

---

## 自訂指令（cmux.json）

透過 `cmux.json` 定義專案級或全域的自訂指令，可從 Command Palette（`Cmd+Shift+P`）快速存取。

### 設定檔位置

| 層級 | 路徑 |
|------|------|
| 專案（優先） | `./cmux.json`（專案根目錄） |
| 全域 | `~/.config/cmux/cmux.json` |

### 範例

```json
{
  "commands": [
    {
      "name": "Start Dev Server",
      "command": "npm run dev"
    },
    {
      "name": "Run Tests",
      "command": "npm test"
    },
    {
      "name": "Deploy Staging",
      "command": "git push staging main"
    }
  ]
}
```

自訂指令也支援定義工作區佈局（多個 surface 的排列與初始指令），適合複雜的開發環境快速啟動。

---

## 設定檔

cmux 繼承 Ghostty 的設定系統，字型、主題、顏色等設定可直接沿用。

### 設定檔路徑

| 檔案 | 說明 |
|------|------|
| `~/.config/ghostty/config` | 主要設定檔 |
| `~/.config/ghostty/config.local` | 本機覆蓋（不提交到 git） |
| `~/Library/Application Support/com.mitchellh.ghostty/config` | macOS 標準路徑 |

### 常用設定項目

```ini
# 字型
font-family = "JetBrains Mono"
font-size = 14

# 主題
theme = catppuccin-mocha

# 背景與前景色
background = #1e1e2e
foreground = #cdd6f4

# 游標
cursor-color = #f5e0dc

# 分割面板樣式
unfocused-split-opacity = 0.7
split-divider-color = #45475a

# 捲動緩衝
scrollback-limit = 10000

# 工作目錄
working-directory = home
```

### 應用程式設定

透過 `Cmd+,` 開啟 cmux 的應用程式設定：

| 設定項 | 選項 | 說明 |
|--------|------|------|
| 主題模式 | System / Light / Dark | 跟隨系統或固定明暗 |
| 自動化模式 | Off / cmux only / allowAll | 控制 socket API 的存取權限 |
| 瀏覽器連結行為 | — | 設定連結點擊行為 |

### 主題選擇

cmux 內建 Ghostty 主題選擇器：

```bash
cmux themes
```

### 環境變數

cmux 自動設定以下環境變數：

| 變數 | 值 | 說明 |
|------|-----|------|
| `CMUX_WORKSPACE_ID` | （自動） | 當前工作區 ID |
| `CMUX_SURFACE_ID` | （自動） | 當前 surface ID |
| `TERM_PROGRAM` | `ghostty` | 終端程式識別 |
| `TERM` | `xterm-ghostty` | 終端類型 |

可手動覆蓋的變數：

| 變數 | 說明 |
|------|------|
| `CMUX_SOCKET_PATH` | 覆蓋 socket 路徑（預設 `~/.cmux/socket`） |
| `CMUX_SOCKET_MODE` | 存取模式：`cmuxOnly` / `allowAll` / `off` |

---

## Claude Code Teams 整合

cmux 原生支援 Claude Code 的 teammate mode，提供比 tmux 更流暢的多 agent 協作體驗。

### 啟動方式

```bash
cmux claude-teams
```

### 運作原理

cmux 在 `~/.cmuxterm/claude-teams-bin/` 建立一個 tmux shim，將 Claude Code 的 tmux 指令翻譯為 cmux 原生分割操作。同時設定 `TMUX` 環境變數，讓 Claude Code 認為自己在 tmux 中運行。

### 效果

- 隊友（teammate）產生為原生分割視窗，而非 tmux pane
- 每個隊友獨立顯示在側邊欄，可單獨監控通知狀態
- GPU 加速渲染，大量輸出時效能優於 tmux

### 其他整合

```bash
# oh-my-openagent (OpenCode) 整合
cmux omo [ARGS...]
```

---

## 與其他終端工具比較

### 與同類 AI Agent 終端比較

| 特性 | cmux | BAT | 傳統終端 + tmux |
|------|------|-----|-----------------|
| 平台 | macOS only | Windows / macOS / Linux | 全平台 |
| 渲染引擎 | GPU（libghostty） | Electron（xterm.js） | 依終端而異 |
| AI 通知 | 通知環 + OSC 序列 | Agent 預設角色 | 無內建 |
| 內建瀏覽器 | WebKit（可腳本化） | 無 | 無 |
| SSH 整合 | 原生工作區 + 瀏覽器路由 | 無 | tmux detach/attach |
| Claude Code Teams | 原生分割 | SDK 整合 | tmux pane |
| 自動化 API | Socket API + CLI | WebSocket | tmux 指令 |
| 斷線恢復 | Session 還原（配置） | 無 | tmux detach（process） |
| 設定格式 | Ghostty config（INI） | Electron 設定 | tmux.conf |
| 授權 | GPL-3.0 | MIT | 依工具而異 |

### 適用場景建議

| 場景 | 推薦工具 |
|------|----------|
| macOS 上同時管理多個 AI agent | **cmux** -- 通知系統 + 側邊欄狀態一目了然 |
| 需要內建瀏覽器查看開發中的 Web 應用 | **cmux** -- 終端旁直接操作，無需切換視窗 |
| 遠端伺服器持久運行 process | **tmux** -- detach/attach 保持 process 存活 |
| 跨平台一致體驗 | **BAT** 或 **tmux** -- cmux 僅支援 macOS |
| 輕量無依賴的終端多工 | **tmux** 或 **Zellij** |
| 需要完整瀏覽器自動化（類 Playwright） | **cmux** -- 內建完整 DOM 操作 API |

---

## 疑難排解

| 問題 | 原因 | 解決方式 |
|------|------|----------|
| `cmux: command not found` | 未建立 CLI symlink | `sudo ln -sf "/Applications/cmux.app/Contents/Resources/bin/cmux" /usr/local/bin/cmux` |
| `cmux ping` 無回應 | cmux.app 未啟動 | 先啟動 cmux.app |
| 首次啟動被 macOS 阻擋 | 未識別開發者 | 系統設定 > 隱私權與安全性 > 仍要打開 |
| Ghostty 設定未生效 | 設定檔路徑錯誤 | 確認 `~/.config/ghostty/config` 存在 |
| 瀏覽器面板無法載入 | 自動化模式為 Off | `Cmd+,` > 設定自動化模式為 `cmux only` 或 `allowAll` |
| CJK 輸入法問題 | 已知問題，v0.63 已修正 | 更新至最新版本 |

---

## 參考資源

- [cmux 官方網站](https://cmux.com)
- [cmux 官方文件](https://cmux.com/docs)
- [GitHub Repository](https://github.com/manaflow-ai/cmux)
- [GitHub Releases](https://github.com/manaflow-ai/cmux/releases)
- [Discord 社群](https://discord.gg/cmux)
- [Reddit r/cmux](https://reddit.com/r/cmux)
- [Ghostty 設定參考](https://ghostty.org/docs/config)
