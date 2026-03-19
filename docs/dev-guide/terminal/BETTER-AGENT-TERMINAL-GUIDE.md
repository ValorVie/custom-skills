# Better Agent Terminal (BAT) 完整指南

## 目錄

- [簡介與特色](#簡介與特色)
- [安裝方式](#安裝方式)
- [首次啟動設定](#首次啟動設定)
- [工作區管理](#工作區管理)
- [終端機功能](#終端機功能)
- [Claude Code Agent 整合](#claude-code-agent-整合)
- [常用快捷鍵](#常用快捷鍵)
- [Slash 指令](#slash-指令)
- [程式碼片段管理](#程式碼片段管理)
- [遠端存取與行動裝置連線](#遠端存取與行動裝置連線)
- [設定檔路徑](#設定檔路徑)
- [除錯日誌](#除錯日誌)
- [從原始碼建置](#從原始碼建置)
- [技術架構](#技術架構)

---

## 簡介與特色

[Better Agent Terminal](https://github.com/tony1223/better-agent-terminal)（簡稱 BAT）是由 TonyQ（[@tony1223](https://github.com/tony1223)）開發的跨平台終端機聚合器，以 Electron 框架建構，核心特色如下：

- **多工作區管理** -- 以專案資料夾為單位組織終端機，所有專案集中在單一視窗。
- **內建 Claude Code Agent** -- 透過 SDK 直接在應用程式內執行 AI 代理，無需額外開啟終端。
- **Google Meet 風格佈局** -- 70% 主面板 + 30% 可捲動縮圖列，一覽所有終端。
- **Agent 預設角色** -- 支援 Claude Code、Gemini CLI、Codex、GitHub Copilot 及純終端等預設。
- **檔案瀏覽器** -- 內建搜尋、瀏覽與語法高亮預覽。
- **Git 整合** -- 提交日誌、Diff 檢視、分支顯示、未追蹤檔案清單。
- **程式碼片段管理** -- SQLite 支援的片段儲存，含分類與收藏功能。
- **遠端存取** -- 內建 WebSocket 伺服器，支援跨裝置控制。
- **跨平台** -- 支援 Windows、macOS、Linux。

**版本格式：** `1.YY.MMDDHHmmss`（例：`v1.52.0`）

**授權：** MIT License

---

## 安裝方式

### macOS（推薦：Homebrew）

```bash
brew tap tonyq-org/tap
brew install --cask better-agent-terminal
```

安裝後首次啟動，macOS 可能會阻擋未驗證的應用程式：

1. 前往 **系統設定 > 隱私權與安全性**
2. 捲動到下方，點擊 **仍要打開**

### 各平台安裝包下載

從 [GitHub Releases](https://github.com/tony1223/better-agent-terminal/releases/latest) 下載對應平台的安裝檔：

| 平台 | 格式 |
|------|------|
| Windows | NSIS 安裝程式、`.zip` |
| macOS | `.dmg`（Universal Binary，同時支援 Intel 與 Apple Silicon） |
| Linux | `.AppImage` |

#### macOS DMG 安裝步驟

1. 下載 `.dmg` 檔案
2. 雙擊掛載映像
3. 將 **Better Agent Terminal** 拖入 **Applications** 資料夾
4. 首次啟動時，至 **系統設定 > 隱私權與安全性** 點擊 **仍要打開**

### 前置需求

使用 Agent 功能前，需確保已安裝 [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)：

```bash
npm install -g @anthropic-ai/claude-code
```

---

## 首次啟動設定

1. **建立工作區** -- 點擊側邊欄的 `+` 按鈕，選擇專案資料夾
2. **設定 Agent 預設** -- 每個終端可選擇預設角色（Claude Code、Gemini CLI、Codex 等）
3. **設定環境變數** -- 可為每個工作區配置獨立的環境變數
4. **驗證 Claude Code** -- 確認已登入 Anthropic 帳號或設定 API Key

---

## 工作區管理

### 基本操作

| 操作 | 方式 |
|------|------|
| 新增工作區 | 點擊側邊欄 `+` 按鈕 |
| 重新命名 | 雙擊工作區名稱 |
| 排序 | 拖放工作區項目 |
| 其他動作 | 右鍵開啟上下文選單 |

### 群組分類

工作區可歸入命名群組，透過下拉式選單篩選顯示特定群組。

### 設定檔（Profiles）

支援多組工作區配置的儲存與切換，可用於不同的工作情境（如本地開發、遠端連線）。

### 獨立視窗

可將個別工作區彈出為獨立視窗，重新啟動時自動重新附加。

### 活動指示器

側邊欄以視覺圓點標示哪些工作區有活躍的終端處理程序。

### 工作區環境變數

每個工作區可設定獨立的環境變數，適用於不同專案需要不同環境配置的情境。

---

## 終端機功能

### 佈局

採用 Google Meet 風格的佈局：
- **主面板（70%）** -- 顯示當前活躍的終端
- **縮圖列（30%）** -- 可捲動的條狀列，顯示所有終端的縮圖

### 多終端

每個工作區支援多個終端實例，以 xterm.js 驅動，完整支援 Unicode 及 CJK 字元。

### 分頁導覽

每個工作區含三個分頁：
- **Terminal** -- 終端機
- **Files** -- 檔案瀏覽器（含搜尋與語法高亮預覽）
- **Git** -- 提交日誌、Diff 檢視、分支資訊

### Agent 預設角色

建立終端時可選擇預設角色：

| 預設 | 說明 |
|------|------|
| Claude Code | Anthropic Claude Code CLI |
| Gemini CLI | Google Gemini CLI |
| Codex | OpenAI Codex CLI |
| GitHub Copilot | GitHub Copilot CLI |
| Terminal | 純終端（無 Agent） |

---

## Claude Code Agent 整合

BAT 內建的 Claude Code Agent 是其核心功能之一，透過 `@anthropic-ai/claude-agent-sdk` 直接在應用程式內執行。

### 功能一覽

- **訊息串流** -- 即時顯示回應，含可折疊的 Extended Thinking 區塊
- **權限控制** -- 每個工具呼叫都可個別核准，或啟用 Bypass/Plan 模式自動核准
- **子代理追蹤** -- 檢視產生的子代理任務，含進度指示與停滯偵測
- **對話恢復** -- 持久化對話，跨應用程式重啟恢復
- **對話分支** -- 從對話中的任意點分支出新對話
- **休息/喚醒** -- 從右鍵選單暫停與恢復 Agent 對話以節省資源
- **圖片附加** -- 拖放或使用附加按鈕（每則訊息最多 5 張圖片）
- **可點擊連結** -- Markdown 連結與裸網址可直接在預設瀏覽器開啟
- **可點擊檔案路徑** -- 點擊 Agent 輸出中的檔案路徑即可預覽，含語法高亮與搜尋（Ctrl+F）
- **檔案選取器** -- `Ctrl+P` 模糊搜尋專案檔案並附加到對話上下文

### 狀態列資訊

Agent 面板底部的狀態列顯示：
- Token 使用量與費用
- Context Window 使用百分比
- 模型名稱
- Git 分支
- 回合數
- 對話持續時間

### 用量監控

支援透過 Anthropic OAuth 追蹤 API 速率限制（5 小時及 7 天視窗）。

### 更新通知

自動檢查 GitHub 上的新版本釋出。

---

## 常用快捷鍵

| 快捷鍵 | 動作 |
|--------|------|
| `Ctrl+P` / `Cmd+P` | 檔案選取器（搜尋並附加檔案至 Agent 上下文） |
| `Shift+Tab` | 切換 Terminal 與 Agent 模式 |
| `Enter` | 傳送訊息 |
| `Shift+Enter` | 插入換行（多行輸入） |
| `Escape` | 停止串流 / 關閉對話框 |
| `Ctrl+Shift+C` | 複製選取文字 |
| `Ctrl+Shift+V` | 從剪貼簿貼上 |
| 右鍵 | 複製（有選取文字時）或貼上 |

---

## Slash 指令

在 Agent 輸入框中可使用以下指令：

| 指令 | 說明 |
|------|------|
| `/resume` | 從歷史記錄恢復先前的 Claude 對話 |
| `/model` | 切換可用的 Claude 模型 |

---

## 程式碼片段管理

BAT 內建 SQLite 驅動的程式碼片段管理器：

- **儲存片段** -- 將常用程式碼保存為可重用片段
- **分類管理** -- 以分類組織片段
- **收藏功能** -- 標記常用片段為收藏
- **搜尋** -- 快速搜尋已儲存的片段
- **一鍵貼上** -- 直接將片段貼入終端

---

## 遠端存取與行動裝置連線

> ⚠️ 此功能目前為**實驗性功能**。

BAT 內建 WebSocket 伺服器，允許其他 BAT 實例或行動裝置遠端連線控制。

### 運作方式

1. **主機端** -- 在 Settings → Remote Access 啟用 WebSocket 伺服器（預設 Port: 9876）
2. 啟動時自動產生 **Connection Token**（32 字元 hex 字串）用於驗證連線
3. **客戶端** -- 輸入主機 IP、Port 及 Token 連線
4. 連線後可操作所有終端、Agent 對話、工作區等功能

### 連線方式

#### 方式一：Remote Profile（BAT 對 BAT）

1. 開啟 Settings → Profiles
2. 建立新 Profile，類型設為 **Remote**
3. 輸入主機 IP、Port（9876）及 Token
4. 載入 Profile 即可連線

#### 方式二：QR Code（行動裝置）

1. 開啟 Settings → Remote Access → **Generate QR Code**
2. 若伺服器未啟動會自動啟動
3. 使用行動裝置掃描 QR Code 取得連線資訊

### 推薦：使用 Tailscale 跨網路連線

若主機與客戶端不在同一區域網路，建議使用 [Tailscale](https://tailscale.com/) 建立安全的點對點 VPN：

- 免費方案支援最多 100 台裝置
- 無需設定 Port Forwarding
- 每台裝置取得穩定的 `100.x.x.x` IP
- BAT 自動偵測 Tailscale IP 並優先使用

**安裝 Tailscale：**

| 平台 | 安裝方式 |
|------|---------|
| macOS | `brew install tailscale` 或[下載](https://tailscale.com/download/macos) |
| Windows | [下載](https://tailscale.com/download/windows) |
| iOS | [App Store](https://apps.apple.com/app/tailscale/id1470499037) |
| Android | [Google Play](https://play.google.com/store/apps/details?id=com.tailscale.ipn) |
| Linux | [安裝指南](https://tailscale.com/download/linux) |

### 安全注意事項

> **警告：** 啟用遠端伺服器會開啟 WebSocket 連線。任何持有 Token 的裝置可完全控制主機上的 BAT，包括執行終端指令、存取檔案系統及控制 Agent 對話。
>
> - 勿在不受信任的網路上啟動伺服器
> - 勿將 Token 分享給不受信任的對象
> - 不使用時關閉伺服器
> - 強烈建議使用 Tailscale 避免直接暴露於公網

---

## 設定檔路徑

工作區、設定及對話資料儲存於：

| 平台 | 路徑 |
|------|------|
| Windows | `%APPDATA%/better-agent-terminal/` |
| macOS | `~/Library/Application Support/better-agent-terminal/` |
| Linux | `~/.config/better-agent-terminal/` |

---

## 除錯日誌

設定環境變數 `BAT_DEBUG=1` 啟用磁碟日誌記錄：

```bash
# macOS / Linux
BAT_DEBUG=1 open -a "Better Agent Terminal"

# 或在 shell 設定中加入
export BAT_DEBUG=1
```

日誌檔案 `debug.log` 寫入設定檔目錄中。

---

## 從原始碼建置

### 前置需求

- [Node.js](https://nodejs.org/) 18+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) 已安裝並完成驗證

### macOS 額外需求

原生依賴（`node-pty`、`better-sqlite3`）需要 Xcode Command Line Tools：

```bash
xcode-select --install
```

### 建置步驟

```bash
# 取得原始碼
git clone https://github.com/tony1223/better-agent-terminal.git
cd better-agent-terminal

# 安裝依賴
npm install

# 開發模式
npm run dev

# 建置生產版本
npm run build
```

---

## 技術架構

### 技術堆疊

| 組件 | 技術 |
|------|------|
| 前端 | React 18 + TypeScript |
| 終端 | xterm.js + node-pty |
| 框架 | Electron 28 |
| AI | @anthropic-ai/claude-agent-sdk |
| 建置 | Vite 5 + electron-builder |
| 儲存 | better-sqlite3（片段、對話資料） |
| 遠端 | ws（WebSocket）+ qrcode |
| 語法高亮 | highlight.js |

### 目錄結構概覽

```
better-agent-terminal/
├── electron/           # 主程序（Node.js）
│   ├── main.ts         # 應用程式入口、IPC 處理、視窗管理
│   ├── preload.ts      # Context Bridge（window.electronAPI）
│   ├── pty-manager.ts  # PTY 程序生命週期管理
│   ├── claude-agent-manager.ts  # Claude SDK 對話管理
│   ├── snippet-db.ts   # SQLite 片段儲存
│   └── remote/         # 遠端存取模組（WebSocket 伺服器/客戶端）
├── src/                # 渲染程序（React）
│   ├── App.tsx         # 根元件
│   ├── components/     # UI 元件（Sidebar、Agent Panel、Terminal 等）
│   ├── stores/         # 狀態管理（workspace-store、settings-store）
│   ├── types/          # TypeScript 型別定義
│   └── styles/         # CSS 樣式
├── assets/             # 應用程式圖示與截圖
└── package.json
```

---

## 相關連結

- **GitHub 儲存庫：** <https://github.com/tony1223/better-agent-terminal>
- **最新釋出：** <https://github.com/tony1223/better-agent-terminal/releases/latest>
- **作者：** TonyQ（[@tony1223](https://github.com/tony1223)）
