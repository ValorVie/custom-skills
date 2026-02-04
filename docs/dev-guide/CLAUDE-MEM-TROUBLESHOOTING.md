# claude-mem 除錯指南

本指南涵蓋 claude-mem 插件的常見問題診斷、日誌分析與修復命令。

---

## 架構概覽

```
Claude Code Session
  |-- Hook (worker-service.cjs)      --> 與 Worker 通訊
  |-- MCP Server (mcp-server.cjs)    --> 提供搜尋工具
  +-- Worker Daemon (worker-wrapper.cjs -> worker-service.cjs)
        +-- HTTP Server @ 127.0.0.1:37777
```

| 元件 | 說明 |
|------|------|
| **Worker Daemon** | 常駐 HTTP 服務，處理觀察紀錄、搜尋、session 管理 |
| **Hook Scripts** | 在 Claude Code 事件觸發時與 Worker 通訊 |
| **MCP Server** | 提供 search、timeline、get_observations 等工具 |

---

## 1. 檢查：確認系統狀態

### 1.1 檢查 Worker 是否存活

```bash
# Linux/WSL
ss -tlnp | grep 37777
# 或
netstat -tlnp 2>/dev/null | grep 37777

# Windows (PowerShell)
Get-NetTCPConnection -LocalPort 37777 -ErrorAction SilentlyContinue

# Windows (cmd)
netstat -ano | findstr "37777"
```

### 1.2 檢查 bun 是否安裝

```bash
which bun && bun --version
```

若未安裝，參考 https://bun.sh 安裝。

### 1.3 確認插件路徑

```bash
# 插件快取路徑（版本號可能不同）
PLUGIN_DIR="$HOME/.claude/plugins/cache/thedotmack/claude-mem"
ls "$PLUGIN_DIR"/

# Windows 路徑
# %USERPROFILE%\.claude\plugins\cache\thedotmack\claude-mem\<version>
```

### 1.4 檢查設定檔

```bash
cat ~/.claude-mem/settings.json
```

關鍵欄位：

| 設定 | 預設值 | 說明 |
|------|--------|------|
| `CLAUDE_MEM_WORKER_PORT` | `37777` | Worker HTTP 服務端口 |
| `CLAUDE_MEM_WORKER_HOST` | `127.0.0.1` | Worker 綁定地址 |
| `CLAUDE_MEM_DATA_DIR` | `~/.claude-mem` | 資料與日誌目錄 |
| `CLAUDE_MEM_LOG_LEVEL` | `INFO` | 日誌等級 (DEBUG/INFO/WARN/ERROR) |
| `CLAUDE_MEM_PROVIDER` | `claude` | AI 提供商 (claude/gemini/openrouter) |

### 1.5 Health Check

```bash
curl -s http://127.0.0.1:37777/health | jq .
```

成功回應表示 Worker 正常運行。無回應表示 Worker 未啟動。

---

## 2. 分析：查看日誌

### 2.1 日誌位置

```bash
ls ~/.claude-mem/logs/
# 格式: claude-mem-YYYY-MM-DD.log
```

### 2.2 查看今日日誌

```bash
cat ~/.claude-mem/logs/claude-mem-$(date +%Y-%m-%d).log
```

### 2.3 即時追蹤日誌

```bash
tail -f ~/.claude-mem/logs/claude-mem-$(date +%Y-%m-%d).log
```

### 2.4 只看錯誤

```bash
grep '\[ERROR\]' ~/.claude-mem/logs/claude-mem-$(date +%Y-%m-%d).log
```

### 2.5 常見日誌模式解讀

| 日誌訊息 | 含義 | 處理方式 |
|----------|------|----------|
| `Worker available` | Worker 正常運行 | 無需處理 |
| `Worker already running and healthy` | Worker 健康檢查通過 | 無需處理 |
| `Worker not available` | Worker 未啟動或已崩潰 | 見 3.1 |
| `Failed to start server. Is port 37777 in use?` | 端口被佔用 | 見 3.2 |
| `Worker failed to start (health check timeout)` | 啟動後 health check 超時 | 見 3.3 |
| `Worker did not become ready within 15 seconds` | Hook 等待 Worker 回應超時 | 見 3.4 |
| `INIT_COMPLETE` | Session 初始化成功 | 無需處理 |

---

## 3. 執行：修復命令

### 3.1 手動啟動 Worker

```bash
# 找到最新版本的插件目錄
PLUGIN_DIR=$(ls -d ~/.claude/plugins/cache/thedotmack/claude-mem/*/ | sort -V | tail -1)

# 啟動 Worker（前台模式，用於除錯）
cd "$PLUGIN_DIR/scripts"
bun worker-service.cjs start

# 啟動 Worker（透過 wrapper，正式模式）
bun worker-wrapper.cjs
```

### 3.2 端口被佔用：殺掉舊進程

```bash
# Linux/WSL: 找到佔用 37777 的進程
lsof -i :37777
# 或
ss -tlnp | grep 37777

# 殺掉佔用端口的進程
kill $(lsof -t -i :37777)

# 確認端口已釋放（應該無輸出）
ss -tlnp | grep 37777

# 重新啟動 Worker
PLUGIN_DIR=$(ls -d ~/.claude/plugins/cache/thedotmack/claude-mem/*/ | sort -V | tail -1)
cd "$PLUGIN_DIR/scripts" && bun worker-service.cjs start
```

Windows PowerShell:

```powershell
$pid = (Get-NetTCPConnection -LocalPort 37777 -ErrorAction SilentlyContinue).OwningProcess
if ($pid) { Stop-Process -Id $pid -Force }
```

### 3.3 Health Check 超時：完整重啟流程

```bash
# 1. 殺掉所有相關進程
pkill -f "worker-service.cjs" 2>/dev/null
pkill -f "worker-wrapper.cjs" 2>/dev/null

# 2. 等待端口釋放
sleep 3

# 3. 確認端口已釋放
ss -tlnp | grep 37777

# 4. 重新啟動
PLUGIN_DIR=$(ls -d ~/.claude/plugins/cache/thedotmack/claude-mem/*/ | sort -V | tail -1)
cd "$PLUGIN_DIR/scripts" && bun worker-wrapper.cjs &

# 5. 驗證
sleep 5
curl -s http://127.0.0.1:37777/health
```

### 3.4 Hook 15 秒超時：最簡修復

這通常發生在 Claude Code 啟動時 Worker 尚未就緒。

```bash
# 最簡單的方法：完全退出 Claude Code，等待端口釋放，再重啟
# Hook 會自動啟動 Worker

# 如果反覆發生，手動預啟動 Worker：
PLUGIN_DIR=$(ls -d ~/.claude/plugins/cache/thedotmack/claude-mem/*/ | sort -V | tail -1)
cd "$PLUGIN_DIR/scripts" && bun worker-wrapper.cjs &
sleep 5
# 然後再啟動 Claude Code
```

### 3.5 變更 Worker 端口

如果 37777 經常被其他程式佔用：

```bash
# 編輯設定檔
vi ~/.claude-mem/settings.json
# 將 CLAUDE_MEM_WORKER_PORT 改為其他端口，例如 "38888"

# 重啟 Worker 使其生效
pkill -f "worker-service.cjs" 2>/dev/null
sleep 2
# 下次啟動 Claude Code 時會自動用新端口
```

### 3.6 完全重置（保留資料）

```bash
# 1. 殺掉所有 Worker 進程
pkill -f "worker-service.cjs" 2>/dev/null
pkill -f "worker-wrapper.cjs" 2>/dev/null

# 2. 清除日誌（保留設定和資料）
rm -f ~/.claude-mem/logs/*.log

# 3. 重新啟動 Claude Code（Hook 會自動啟動 Worker）
```

---

## 4. Windows 專用注意事項

### 路徑對照

| 項目 | Linux/macOS | Windows |
|------|------------|---------|
| 設定檔 | `~/.claude-mem/settings.json` | `%USERPROFILE%\.claude-mem\settings.json` |
| 日誌 | `~/.claude-mem/logs/` | `%USERPROFILE%\.claude-mem\logs\` |
| 插件 | `~/.claude/plugins/cache/` | `%USERPROFILE%\.claude\plugins\cache\` |

### npm run worker:restart 無法使用

`npm run worker:restart` 是插件開發者的指令，需要在插件**原始碼**目錄執行，而非插件快取目錄或使用者的專案目錄。使用者應直接用 bun 命令：

```cmd
cd %USERPROFILE%\.claude\plugins\cache\thedotmack\claude-mem\<version>\scripts
bun worker-service.cjs start
```

### Windows 殺進程

```powershell
# 找到並殺掉佔用端口的進程
$pid = (Get-NetTCPConnection -LocalPort 37777 -ErrorAction SilentlyContinue).OwningProcess
if ($pid) { Stop-Process -Id $pid -Force }

# 或殺掉所有 bun 進程
Get-Process -Name bun -ErrorAction SilentlyContinue | Stop-Process -Force
```

---

## 5. 快速診斷流程

```
錯誤發生
  |
  +-- "Worker did not become ready within 15 seconds"
  |     --> 退出 Claude Code -> 等 5 秒 -> 重啟
  |
  +-- "Failed to start server. Is port 37777 in use?"
  |     --> 殺掉佔用端口的進程 -> 重啟 Worker (3.2)
  |
  +-- "Worker not available"
  |     --> 手動啟動 Worker (3.1)
  |
  +-- "Worker failed to start (health check timeout)"
  |     --> 完全重啟流程 (3.3)
  |
  +-- 其他錯誤
        --> 查看日誌 (2.4) -> 回報 issue
            https://github.com/thedotmack/claude-mem/issues
```
