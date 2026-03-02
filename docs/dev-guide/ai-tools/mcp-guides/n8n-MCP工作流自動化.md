---
tags:
  - ai
  - mcp
  - n8n
  - automation
date created: 2026-03-02T15:00:00+08:00
date modified: 2026-03-02T15:00:00+08:00
description: n8n-MCP 使用指南 — 讓 AI 助手存取 n8n 工作流自動化的完整知識庫與 API 整合
---

# n8n-MCP — 工作流自動化知識庫

| 項目 | 內容 |
|------|------|
| **GitHub** | https://github.com/czlonkowski/n8n-mcp |
| **Stars** | 14,180 |
| **語言** | TypeScript |
| **授權** | MIT |
| **NPM 套件** | `n8n-mcp` |
| **Docker** | `ghcr.io/czlonkowski/n8n-mcp` |

---

## 解決什麼問題

n8n 擁有 1,084 個節點和數千種整合方式，但 AI 助手的訓練資料中 n8n 的覆蓋率很低。n8n-MCP 讓 AI 即時存取：

- **1,084 個節點**的完整文件（537 核心 + 547 社群）
- **2,709 個工作流範本**的完整 metadata
- **2,646 個預提取配置**（從熱門範本萃取）
- **265 個 AI 工具變體**的完整文件

| 沒有 n8n-MCP | 有 n8n-MCP |
|-------------|-----------|
| AI 猜測節點名稱和參數 | AI 查詢精確的節點 property schema |
| 自己到 n8n 文件網站搜尋 | AI 直接回傳相關節點與範例 |
| 工作流配置靠試錯 | 基於 2,646 個真實配置建議 |

---

## 安裝

### 方式一：Hosted 服務（最簡單）

無需任何安裝，直接使用雲端服務：

1. 到 https://dashboard.n8n-mcp.com 註冊
2. 免費方案：每日 100 次工具呼叫
3. 取得設定後加入你的 AI 工具

### 方式二：npx（快速本地安裝）

```bash
npx n8n-mcp
```

### 方式三：Docker（推薦正式環境）

```bash
docker pull ghcr.io/czlonkowski/n8n-mcp:latest
```

映像檔經過優化，僅 280MB。

---

## 設定

### 兩種使用模式

| 模式 | 說明 | 需要 n8n 實例 |
|------|------|--------------|
| **文件模式** | 只查詢節點文件和範本 | 否 |
| **完整模式** | 文件 + 連接 n8n 實例操作工作流 | 是 |

### Claude Code

**文件模式**（無需 n8n 實例）：
```bash
claude mcp add n8n-mcp --scope user -- npx -y n8n-mcp
```

**完整模式**（連接 n8n 實例）：
```bash
claude mcp add n8n-mcp --scope user \
  -e MCP_MODE=stdio \
  -e LOG_LEVEL=error \
  -e DISABLE_CONSOLE_OUTPUT=true \
  -e N8N_API_URL=https://your-n8n.example.com \
  -e N8N_API_KEY=your-api-key \
  -- npx -y n8n-mcp
```

### 手動設定（Claude Code / Cursor）

**文件模式**：
```json
{
  "mcpServers": {
    "n8n-mcp": {
      "command": "npx",
      "args": ["-y", "n8n-mcp"],
      "env": {
        "MCP_MODE": "stdio",
        "LOG_LEVEL": "error",
        "DISABLE_CONSOLE_OUTPUT": "true"
      }
    }
  }
}
```

**完整模式**：
```json
{
  "mcpServers": {
    "n8n-mcp": {
      "command": "npx",
      "args": ["-y", "n8n-mcp"],
      "env": {
        "MCP_MODE": "stdio",
        "LOG_LEVEL": "error",
        "DISABLE_CONSOLE_OUTPUT": "true",
        "N8N_API_URL": "https://your-n8n.example.com",
        "N8N_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Docker 設定

```json
{
  "mcpServers": {
    "n8n-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "MCP_MODE=stdio",
        "-e", "LOG_LEVEL=error",
        "-e", "DISABLE_CONSOLE_OUTPUT=true",
        "ghcr.io/czlonkowski/n8n-mcp:latest"
      ]
    }
  }
}
```

### OpenCode

```json
{
  "mcp": {
    "n8n-mcp": {
      "type": "local",
      "command": ["npx", "-y", "n8n-mcp"],
      "environment": {
        "MCP_MODE": "stdio",
        "LOG_LEVEL": "error",
        "DISABLE_CONSOLE_OUTPUT": "true"
      }
    }
  }
}
```

> `MCP_MODE: "stdio"` 是必要的環境變數，缺少會導致連線失敗。

---

## 環境變數

| 變數 | 必填 | 說明 |
|------|------|------|
| `MCP_MODE` | 是 | 設為 `"stdio"`（Claude Desktop 必需） |
| `LOG_LEVEL` | 否 | 建議設為 `"error"` 減少噪音 |
| `DISABLE_CONSOLE_OUTPUT` | 否 | 設為 `"true"` 避免干擾 stdio 通道 |
| `N8N_API_URL` | 否 | n8n 實例 URL（完整模式需要） |
| `N8N_API_KEY` | 否 | n8n API 金鑰（完整模式需要） |

### n8n API Key 取得方式

1. 登入 n8n 實例
2. 進入 Settings → API
3. 建立新的 API Key
4. 複製 Key 填入設定

### 本地 n8n 連線

Docker 環境內連接本機 n8n 時，URL 使用：
```
http://host.docker.internal:5678
```

---

## MCP 工具

n8n-MCP 提供以下類型的工具：

### 節點文件查詢
- 查詢特定節點的 property schema、操作方式
- 搜尋符合需求的節點
- 查看社群節點與驗證狀態

### 工作流範本
- 搜尋和瀏覽 2,709 個工作流範本
- 取得範本的完整 metadata 和配置
- 基於需求推薦合適的範本

### 工作流驗證
- 驗證工作流配置的正確性
- 分析工作流結構

### n8n API 整合（完整模式）
- 列出、建立、更新、刪除工作流
- 觸發工作流執行
- 管理 credential

---

## 使用範例

### 查詢節點文件

```
n8n 的 HTTP Request 節點有哪些設定選項？如何設定 OAuth2 認證？
```

### 搜尋適合的節點

```
我要用 n8n 連接 Slack 發送訊息，應該用哪個節點？幫我看一下完整的設定方式
```

### 取得工作流範本

```
有沒有把 Google Sheets 資料同步到 PostgreSQL 的 n8n 範本？
```

### 建構工作流

```
幫我設計一個 n8n 工作流：監聽 GitHub webhook，當有新 PR 時自動發送 Slack 通知
```

### AI 工具整合

```
如何在 n8n 中使用 AI Agent 節點？支援哪些 LLM？
```

---

## 安全注意事項

> **永遠不要讓 AI 直接編輯正式環境的工作流！**

建議的安全做法：
1. 在修改前先**複製一份工作流**
2. 在**開發環境**中測試
3. **匯出備份**重要工作流
4. **驗證變更**後再部署到正式環境

---

## 隱私與遙測

n8n-MCP 預設收集匿名使用統計。關閉方式：

```bash
# npx 安裝
npx n8n-mcp telemetry disable

# Docker
# 加入環境變數
N8N_MCP_TELEMETRY_DISABLED=true
```

---

## 故障排除

### Q: MCP Server 啟動後無回應

**A:** 確認 `MCP_MODE` 設為 `"stdio"`，這是最常見的遺漏。

### Q: 連接 n8n 實例失敗

**A:** 確認：
1. `N8N_API_URL` 格式正確（含 protocol，如 `https://`）
2. `N8N_API_KEY` 有效
3. 網路可存取目標 n8n 實例

### Q: Docker 記憶體佔用過高

**A:** n8n-MCP 包含完整的節點資料庫。預設使用 better-sqlite3（約 100-120MB），可透過 `SQLJS_SAVE_INTERVAL_MS` 調整儲存頻率。

### Q: 節點資訊過時

**A:** 更新到最新版本：
```bash
# npx 會自動使用最新版
npx n8n-mcp

# Docker
docker pull ghcr.io/czlonkowski/n8n-mcp:latest
```
